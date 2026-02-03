"""
FDA Adverse Events Extraction Pipeline

This DAG extracts medical device adverse event data from the FDA openFDA API,
stores it in S3, loads it into Snowflake, and transforms it with dbt.

Refactored version demonstrating:
- Separation of concerns (single responsibility principle)
- Configuration management
- Type safety with type hints
- Better error handling
- SQL injection prevention
- Resource management
"""
import time
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import boto3
import requests
import snowflake.connector
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.exceptions import AirflowSkipException

from config import SNOWFLAKE_CONFIG


# ============================================================================
# CONFIGURATION - Centralized constants for easy maintenance
# ============================================================================

@dataclass
class PipelineConfig:
    """Centralized configuration for the pipeline."""
    # API Configuration
    FDA_API_BASE_URL: str = 'https://api.fda.gov/device/event.json'
    API_LIMIT: int = 1000  # FDA API maximum per request
    API_RATE_LIMIT_DELAY: float = 0.1  # Seconds between requests
    
    # S3 Configuration
    S3_BUCKET: str = 'medtech-sentinel-raw-luke'
    S3_DATA_PREFIX: str = 'data'
    
    # Product Code Mapping
    PRODUCT_FOLDERS: Dict[str, str] = None
    
    # Snowflake Configuration
    SNOWFLAKE_DATABASE: str = 'RAW'
    SNOWFLAKE_SCHEMA: str = 'MEDTECH_SENTINEL'
    SNOWFLAKE_TABLE: str = 'RAW_ADVERSE_EVENTS'
    SNOWFLAKE_STAGE: str = 'MEDTECH_RAW_STAGE'
    
    def __post_init__(self):
        """Initialize default product folders if not provided."""
        if self.PRODUCT_FOLDERS is None:
            self.PRODUCT_FOLDERS = {
                'DYE': 'heart-valves',
                'MUD': 'pulse-oximeters'
            }


# Global config instance
CONFIG = PipelineConfig()


# ============================================================================
# EXCEPTIONS - Custom exceptions for better error handling
# ============================================================================

class FDAAPIError(Exception):
    """Raised when FDA API request fails."""
    pass


class NoDataFoundError(Exception):
    """Raised when no data is found for the query (404)."""
    pass


# ============================================================================
# FDA API EXTRACTION - Separated into focused functions
# ============================================================================

def build_fda_search_query(product_code: str, start_date: str, end_date: str) -> str:
    """
    Build FDA API search query string.
    
    Args:
        product_code: FDA product code (e.g., 'DYE', 'MUD')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
    
    Returns:
        Search query string for FDA API
    """
    return f'device.device_report_product_code:"{product_code}" AND date_received:[{start_date} TO {end_date}]'


def fetch_fda_api_page(
    base_url: str,
    search_query: str,
    skip: int,
    limit: int
) -> Dict[str, Any]:
    """
    Fetch a single page of results from FDA API.
    
    Args:
        base_url: FDA API endpoint URL
        search_query: Search query string
        skip: Number of records to skip (for pagination)
        limit: Maximum records to return
    
    Returns:
        Parsed JSON response from API
    
    Raises:
        NoDataFoundError: If API returns 404 (no data found)
        FDAAPIError: If API returns non-200 status code
    """
    params = {
        'search': search_query,
        'limit': limit,
        'skip': skip
    }
    
    response = requests.get(base_url, params=params)
    
    if response.status_code == 404:
        raise NoDataFoundError(f"FDA API returned 404: No data found for query")
    
    if response.status_code != 200:
        try:
            error_info = response.json()
            error_msg = json.dumps(error_info, indent=2)
        except Exception:
            error_msg = response.text
        raise FDAAPIError(
            f"FDA API request failed with status {response.status_code}: {error_msg}"
        )
    
    return response.json()


def extract_fda_events(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> List[Dict[str, Any]]:
    """
    Extract all FDA events for a product code and date range with pagination.
    
    This function handles pagination automatically, fetching all records
    across multiple API requests if needed.
    
    Args:
        product_code: FDA product code (e.g., 'DYE', 'MUD')
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        config: Pipeline configuration object
    
    Returns:
        List of all adverse event records (empty list if no records found)
    
    Raises:
        FDAAPIError: If API requests fail
        NoDataFoundError: If no data exists for the query
    """
    search_query = build_fda_search_query(product_code, start_date, end_date)
    results_combined: List[Dict[str, Any]] = []
    skip = 0
    
    # Initial request to get total count
    print(f"Fetching FDA events for {product_code} from {start_date} to {end_date}")
    data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
    
    # Extract metadata
    meta = data.get('meta', {})
    meta_results = meta.get('results', {})
    total_records = meta_results.get('total', 0)
    
    if total_records == 0:
        print(f"No records found for {product_code} between {start_date} and {end_date}")
        return []
    
    # Process first batch
    batch = data.get('results', [])
    results_combined.extend(batch)
    print(f"Total records to extract: {total_records}")
    print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")
    
    skip += len(batch)
    
    # Pagination loop - continue until all records fetched
    while skip < total_records:
        data = fetch_fda_api_page(config.FDA_API_BASE_URL, search_query, skip, config.API_LIMIT)
        batch = data.get('results', [])
        
        if not batch:
            print("No more results returned by API, stopping pagination")
            break
        
        results_combined.extend(batch)
        print(f"Extracted {len(batch)} records. Total so far: {len(results_combined)}")
        
        skip += len(batch)
        time.sleep(config.API_RATE_LIMIT_DELAY)  # Rate limiting
    
    return results_combined


# ============================================================================
# S3 OPERATIONS - Separated S3 upload logic
# ============================================================================

def build_s3_path(
    product_code: str,
    start_date: str,
    end_date: str,
    config: PipelineConfig = CONFIG
) -> Tuple[str, str]:
    """
    Build S3 path for storing extracted data.
    
    Args:
        product_code: FDA product code
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        config: Pipeline configuration
    
    Returns:
        Tuple of (full_s3_path, file_path_in_stage)
        - full_s3_path: Complete S3 path including prefix (for upload)
        - file_path_in_stage: Path relative to stage root (for Snowflake)
    """
    folder = config.PRODUCT_FOLDERS.get(product_code)
    if not folder:
        raise ValueError(f"Unknown product code: {product_code}")
    
    filename = f"{product_code}_{start_date}_{end_date}.json"
    full_s3_path = f"{config.S3_DATA_PREFIX}/{folder}/{filename}"
    file_path_in_stage = f"{folder}/{filename}"
    
    return full_s3_path, file_path_in_stage


def upload_to_s3(
    data: List[Dict[str, Any]],
    s3_path: str,
    config: PipelineConfig = CONFIG
) -> None:
    """
    Upload JSON data to S3 bucket.
    
    Args:
        data: List of records to upload as JSON
        s3_path: S3 key (path) where data will be stored
        config: Pipeline configuration
    
    Raises:
        Exception: If S3 upload fails
    """
    s3_client = boto3.client('s3')
    
    try:
        s3_client.put_object(
            Body=json.dumps(data),
            Bucket=config.S3_BUCKET,
            Key=s3_path
        )
        print(f"Uploaded {len(data)} records to s3://{config.S3_BUCKET}/{s3_path}")
    except Exception as e:
        raise Exception(f"Failed to upload to S3: {e}") from e


# ============================================================================
# SNOWFLAKE OPERATIONS - Separated Snowflake load logic
# ============================================================================

def execute_snowflake_command(
    conn: snowflake.connector.SnowflakeConnection,
    command: str,
    description: str
) -> None:
    """
    Execute a SQL command in Snowflake with error handling.
    
    Args:
        conn: Snowflake connection object
        command: SQL command to execute
        description: Human-readable description for logging
    
    Raises:
        Exception: If command execution fails
    """
    cs = conn.cursor()
    try:
        cs.execute(command)
        conn.commit()
        print(f"{description} completed successfully")
    except Exception as e:
        print(f"Error during {description}: {e}")
        raise
    finally:
        cs.close()


def delete_existing_records(
    conn: snowflake.connector.SnowflakeConnection,
    file_path: str,
    config: PipelineConfig = CONFIG
) -> None:
    """
    Delete existing records for idempotency (prevents duplicates on reruns).
    
    Uses parameterized query to prevent SQL injection.
    
    Args:
        conn: Snowflake connection
        file_path: Source file path to delete records for
        config: Pipeline configuration
    """
    # Use parameterized query instead of f-string to prevent SQL injection
    delete_command = f"""
    DELETE FROM {config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}.{config.SNOWFLAKE_TABLE}
    WHERE source_file = %(file_path)s;
    """
    
    cs = conn.cursor()
    try:
        cs.execute(delete_command, {'file_path': file_path})
        conn.commit()
        print(f"Deleted existing records for file: {file_path}")
    except Exception as e:
        print(f"Error during deletion for idempotency: {e}")
        raise
    finally:
        cs.close()


def refresh_snowflake_stage(
    conn: snowflake.connector.SnowflakeConnection,
    config: PipelineConfig = CONFIG
) -> None:
    """
    Refresh Snowflake stage metadata (required before COPY INTO).
    
    Args:
        conn: Snowflake connection
        config: Pipeline configuration
    """
    refresh_command = (
        f"ALTER STAGE {config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}."
        f"{config.SNOWFLAKE_STAGE} REFRESH;"
    )
    execute_snowflake_command(conn, refresh_command, "Stage metadata refresh")


def load_to_snowflake_from_s3(
    conn: snowflake.connector.SnowflakeConnection,
    file_path: str,
    config: PipelineConfig = CONFIG
) -> int:
    """
    Load data from S3 stage into Snowflake table using COPY INTO.
    
    Args:
        conn: Snowflake connection
        file_path: Path to file in S3 stage (relative to stage root)
        config: Pipeline configuration
    
    Returns:
        Number of rows loaded
    
    Raises:
        Exception: If COPY INTO fails
    """
    # Note: Snowflake parameterization doesn't work for table/schema names
    # but file_path comes from XCom (internal), not user input, so this is safe
    copy_command = f"""
    COPY INTO {config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}.{config.SNOWFLAKE_TABLE}(
        raw_data,
        loaded_at,
        source_file
    )
    FROM (
        SELECT
            $1,
            current_timestamp(),
            '{file_path}'
        FROM @{config.SNOWFLAKE_DATABASE}.{config.SNOWFLAKE_SCHEMA}.{config.SNOWFLAKE_STAGE}/{file_path}
    )
    FILE_FORMAT = (TYPE = 'JSON', STRIP_OUTER_ARRAY = TRUE);
    """
    
    cs = conn.cursor()
    try:
        cs.execute(copy_command)
        conn.commit()
        rows_loaded = cs.rowcount
        print(f"Events loaded into Snowflake: {rows_loaded}")
        return rows_loaded
    except Exception as e:
        print(f"Error COPY INTO SNOWFLAKE: {e}")
        raise
    finally:
        cs.close()


# ============================================================================
# AIRFLOW TASKS - Task functions that orchestrate the pipeline
# ============================================================================

def extract_and_save_task(product_code: str, **context: Any) -> bool:
    """
    Airflow task: Extract FDA events and upload to S3.
    
    This is the main extraction task that:
    1. Calculates date range from Airflow context
    2. Fetches all events from FDA API (with pagination)
    3. Uploads to S3
    4. Passes S3 path to next task via XCom
    
    Args:
        product_code: FDA product code to extract
        **context: Airflow task context (contains dates, task instance, etc.)
    
    Returns:
        True if successful, False if no data found
    
    Raises:
        AirflowSkipException: If no data exists (404 from API)
        Exception: If extraction or upload fails
    """
    # Extract date range from Airflow context
    start_date = context['data_interval_start'].date()
    end_date = context['data_interval_end'].date() - timedelta(days=1)
    
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    print(f"Extracting events for {product_code} from {start_date_str} to {end_date_str}")
    
    try:
        # Extract events from FDA API
        events = extract_fda_events(product_code, start_date_str, end_date_str)
        
        if not events:
            print(f"No records found for {product_code}. Skipping upload.")
            return False
        
        # Build S3 path
        s3_path, file_path_in_stage = build_s3_path(
            product_code, start_date_str, end_date_str
        )
        
        # Upload to S3
        upload_to_s3(events, s3_path)
        
        # Pass file path to next task via XCom
        context['ti'].xcom_push(key='file_path', value=file_path_in_stage)
        
        return True
        
    except NoDataFoundError as e:
        msg = (
            f"No data found for product_code={product_code} "
            f"between {start_date_str} and {end_date_str}. Skipping this run."
        )
        print(msg)
        raise AirflowSkipException(msg) from e
    except Exception as e:
        print(f"Extraction failed for {product_code}: {e}")
        raise


def load_to_snowflake_task(product_code: str, **context: Any) -> None:
    """
    Airflow task: Load data from S3 into Snowflake.
    
    This task:
    1. Retrieves S3 file path from previous task (XCom)
    2. Deletes existing records for idempotency
    3. Refreshes Snowflake stage metadata
    4. Executes COPY INTO to load data
    
    Args:
        product_code: FDA product code (used to identify source task)
        **context: Airflow task context
    
    Raises:
        Exception: If load operation fails
    """
    # Get file path from previous task
    ti = context['ti']
    file_path = ti.xcom_pull(
        key='file_path',
        task_ids=f'extract_and_save_{product_code}'
    )
    
    if not file_path:
        raise ValueError(f"No file path found in XCom for {product_code}")
    
    print(f"Loading file {file_path} into Snowflake")
    
    # Use context manager for proper resource cleanup
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    
    try:
        # Delete existing records for idempotency
        delete_existing_records(conn, file_path)
        
        # Refresh stage metadata (required before COPY INTO)
        refresh_snowflake_stage(conn)
        
        # Load data from S3
        rows_loaded = load_to_snowflake_from_s3(conn, file_path)
        print(f"Successfully loaded {rows_loaded} rows for {product_code}")
        
    finally:
        conn.close()


# ============================================================================
# DAG DEFINITION
# ============================================================================

with DAG(
    dag_id='extract_fda_events_v3',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@weekly',
    catchup=False,
    description='Extract FDA adverse events, load to Snowflake, transform with dbt'
) as dag:
    
    # Transform and test tasks (run once for all products)
    transform_dbt_task = BashOperator(
        task_id='transform_dbt',
        bash_command='cd /opt/airflow/dbt && dbt run --target prod --profiles-dir .'
    )
    
    test_dbt_task = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt && dbt test --target prod --profiles-dir .'
    )
    
    # Create tasks for each product code
    PRODUCT_CODES = ['DYE', 'MUD']
    
    for product_code in PRODUCT_CODES:
        extract_task = PythonOperator(
            task_id=f'extract_and_save_{product_code}',
            python_callable=extract_and_save_task,
            op_kwargs={'product_code': product_code},
            retries=2,
            retry_delay=timedelta(seconds=5),
            retry_exponential_backoff=True
        )
        
        load_task = PythonOperator(
            task_id=f'load_to_snowflake_{product_code}',
            python_callable=load_to_snowflake_task,
            op_kwargs={'product_code': product_code},
            retries=2,
            retry_delay=timedelta(seconds=5),
            retry_exponential_backoff=True
        )
        
        # Set task dependencies
        extract_task >> load_task >> transform_dbt_task >> test_dbt_task
