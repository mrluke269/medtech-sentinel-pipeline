import time
import boto3
import requests
import json
from pathlib import Path
from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from config import SNOWFLAKE_CONFIG
import snowflake.connector
from datetime import datetime
from airflow.exceptions import AirflowSkipException



# task 1: extract and upload events to Amazon S3
def extract_and_save(product_code, **context):
    
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    
    start_date = start_date.strftime('%Y%m%d')
    end_date = end_date.strftime('%Y%m%d')


    print(f"Querying events from {start_date} to {end_date} for product_code={product_code}")

    # Build the API request URL and parameters
    base_url = 'https://api.fda.gov/device/event.json'
    skip = 0
    limit = 1000
    results_combined = []
    params = {
        'search': f'device.device_report_product_code:"{product_code}" AND date_received:[{start_date} TO {end_date}]',
        'limit': limit,
        'skip': skip
    }

    # Initial request
    print(f"Request URL: {base_url}")
    print(f"Params: {params}")

    response = requests.get(base_url, params=params)

    if response.status_code == 404:
        msg = (
        f"No data found for product_code={product_code} "
        f"between {start_date} and {end_date}. Skipping this run."
        )
        print(msg)
        raise AirflowSkipException(msg)

    if response.status_code != 200:
        try:
            error_info = response.json()
            print("Error JSON from openFDA:", json.dumps(error_info, indent=2))
        except Exception:
            print("Error response (not JSON):", response.text)
        raise Exception(f"API request failed with status code {response.status_code}")
    
    data = response.json()

    # Get meta info
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)
    if total_records == 0:
        print(f"No records found for {product_code} between {start_date} and {end_date}. Skipping upload and load.")
        return False

    # Current batch of results
    batch = data.get('results', [])
    results_combined.extend(batch)
    print(f"Total records to extract: {total_records}")
    print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

    # Update skip for pagination
    skip += len(batch)

    # ---- Pagination loop ----
    while skip < total_records: # Continue until all records are fetched
        params['skip'] = skip
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}")

        data = response.json()
        batch = data.get('results', [])
        if not batch:
            print("No more results returned by API, stopping...")
            break
        results_combined.extend(batch) # Append new batch to combined results
        print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")

        skip += len(batch)
        time.sleep(0.1)  # be polite to the API

    # Upload to S3
    # Initialize S3 client
    s3_client = boto3.client('s3')
    
    # Define S3 path
    product_folders = {
        'DYE': 'heart-valves',
        'MUD': 'pulse-oximeters'
    }
    folder = product_folders[product_code]
    S3_path = f"data/{folder}/{product_code}_{start_date}_{end_date}.json"

    # Define S3 bucket name
    bucket_name = 'medtech-sentinel-raw-luke'

    # Upload JSON data to S3
    s3_client.put_object(
    Body=json.dumps(results_combined),
    Bucket=bucket_name,
    Key=S3_path
)
    
    # Save S3 path to XCom
    ti = context['ti']
    file_path_in_stage = f"{folder}/{product_code}_{start_date}_{end_date}.json"
    ti.xcom_push(key='file_path', value= file_path_in_stage)
    print(f"Uploaded {len(results_combined)} "
          f"records to s3://{bucket_name}/{S3_path} on {start_date} "
          f"to {end_date} for {product_code}.")
    return True
    
# Task 2: COPY INTO SNOWFLAKE FROM S3
def load_to_snowflake(product_code,**context):
    ti = context['ti']
    file_path_in_stage = ti.xcom_pull(key='file_path', task_ids=f'extract_and_save_{product_code}')
   
    # Establish Snowflake connection
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    # Create a cursor object
    cs = conn.cursor()

    try:
        # Delete existing records for idempotency
        delete_command = f"""
        DELETE FROM RAW.MEDTECH_SENTINEL.RAW_ADVERSE_EVENTS
        WHERE source_file = '{file_path_in_stage}';
        """

        cs.execute(delete_command)
    except Exception as e:
        print(f"Error during deletion for idempotency: {e}")
        raise

    try:
    #  COPY INTO command
        copy_command = f"""
        COPY INTO RAW.MEDTECH_SENTINEL.RAW_ADVERSE_EVENTS(
        raw_data,
        loaded_at,
        source_file
        )
        FROM (
            SELECT
                $1,
                current_timestamp(),
                '{file_path_in_stage}'
            FROM @RAW.MEDTECH_SENTINEL.MEDTECH_RAW_STAGE/{file_path_in_stage}
        )
        FILE_FORMAT = (TYPE = 'JSON', STRIP_OUTER_ARRAY = TRUE);
        """
        cs.execute(copy_command)

        # log number of rows loaded
        rows_loaded = cs.rowcount
        print(f"Events loaded into Snowflake: {rows_loaded}")

    except Exception as e:
        print(f"Error COPY INTO SNOWFLAKE: {e}")
        raise

    finally:
        cs.close()
        conn.close()

# Define the DAG
with DAG(
    dag_id = 'extract_fda_events_v2',
    start_date = datetime(2024, 1, 1),
    schedule_interval = "@weekly",
    catchup = True
) as dag:
    for product_code in ['DYE', 'MUD']:
        extract_task = PythonOperator(
        task_id=f'extract_and_save_{product_code}',
        python_callable=extract_and_save,
        retries=2,
        retry_delay=timedelta(seconds=5),
        retry_exponential_backoff=True,
        op_kwargs={'product_code': product_code}
    )

        load_task = PythonOperator(
        task_id=f'load_to_snowflake_{product_code}',
        python_callable=load_to_snowflake,
        retries=2,
        retry_delay=timedelta(seconds=5),
        retry_exponential_backoff=True,
        op_kwargs={'product_code': product_code}
    )
        extract_task >> load_task