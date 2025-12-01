from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test_snowflake_connection():
    import snowflake.connector
    from config import SNOWFLAKE_CONFIG
    
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_USER(), CURRENT_ROLE()")
    result = cursor.fetchone()
    print(f"Connected as: {result}")
    cursor.close()
    conn.close()

with DAG(
    dag_id='test_snowflake',
    start_date=datetime(2024, 11, 11),
    schedule_interval=None,
    catchup=False,
    tags=['test']
) as dag:
    
    test_task = PythonOperator(
        task_id='test_connection',
        python_callable=test_snowflake_connection
    )
