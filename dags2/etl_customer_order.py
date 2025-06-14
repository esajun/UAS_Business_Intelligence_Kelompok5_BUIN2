from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore
from datetime import datetime
import pandas as pd
import os

dag_path = os.path.dirname(__file__)

def extract():
    csv_path = os.path.join(dag_path, 'autosales_data.csv')
    df = pd.read_csv(csv_path)

    # Simpan hasil ekstraksi
    df.to_csv('/tmp/extracted_autosales.csv', index=False)

def transform():
    df = pd.read_csv('/tmp/extracted_autosales.csv')

    # Tabel fakta
    fact_df = df[['ORDERNUMBER', 'CUSTOMERNAME', 'SALES', 'DAYS_SINCE_LASTORDER']]
    fact_df = fact_df.drop_duplicates()
    fact_df.to_csv('/tmp/fact_customer_order.csv', index=False)

    # Tabel dimensi pelanggan
    dim_df = df[['CUSTOMERNAME', 'CONTACTFIRSTNAME', 'CONTACTLASTNAME',
                 'PHONE', 'ADDRESSLINE1', 'CITY', 'COUNTRY', 'DEALSIZE']]
    dim_df = dim_df.drop_duplicates(subset=['CUSTOMERNAME'])  # CUSTOMERNAME sebagai PK
    dim_df.to_csv('/tmp/dim_customer.csv', index=False)

def load():
    # Simpan ke direktori proyek DAG
    fact_df = pd.read_csv('/tmp/fact_customer_order.csv')
    dim_df = pd.read_csv('/tmp/dim_customer.csv')

    fact_df.to_csv(os.path.join(dag_path, 'fact_customer_order.csv'), index=False)
    dim_df.to_csv(os.path.join(dag_path, 'dim_customer.csv'), index=False)

with DAG(
    dag_id='etl_customer_order',
    start_date=datetime(2023, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['etl', 'star_schema']
) as dag:

    t1 = PythonOperator(
        task_id='extract',
        python_callable=extract
    )

    t2 = PythonOperator(
        task_id='transform',
        python_callable=transform
    )

    t3 = PythonOperator(
        task_id='load',
        python_callable=load
    )

    t1 >> t2 >> t3
