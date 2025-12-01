from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def test():
    print('Hello MedTech Sentinel!')

with DAG(
    dag_id='test_dag',
    start_date=datetime(2024, 11, 11),
    schedule_interval=None,
    catchup=False,
    tags=['test']
) as dag:
    
    say_hello_task = PythonOperator(
        task_id='say_hello',
        python_callable=test
    )
