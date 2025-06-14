from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import os

dag_path = os.path.dirname(__file__)

def extract():
    csv_path = os.path.join(dag_path, 'autosales_data.csv')  # File sumber
    df = pd.read_csv(csv_path)
    df.to_csv('/tmp/extracted_sales_by_location.csv', index=False)

def transform():
    df = pd.read_csv('/tmp/extracted_sales_by_location.csv')
    df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])

    # ===== TABEL FAKTA =====
    fact_df = df[['ORDERNUMBER', 'CUSTOMERNAME', 'ORDERDATE', 'QUANTITYORDERED', 'PRICEEACH']]
    fact_df['SALES'] = fact_df['QUANTITYORDERED'] * fact_df['PRICEEACH']
    fact_df = fact_df.drop_duplicates()
    fact_df.to_csv('/tmp/fact_sales_by_location.csv', index=False)

    # ===== DIMENSI LOCATION =====
    dim_location = df[['CUSTOMERNAME', 'PRODUCTLINE', 'COUNTRY', 'ADDRESSLINE1']]
    dim_location = dim_location.drop_duplicates(subset=['CUSTOMERNAME'])  # PK: CUSTOMERNAME
    dim_location.to_csv('/tmp/dim_location.csv', index=False)

    # ===== DIMENSI WAKTU (GANTI NAMA JADI dim_time_loc) =====
    dim_time_loc = df[['ORDERDATE']].drop_duplicates()
    dim_time_loc['MONTH'] = dim_time_loc['ORDERDATE'].dt.month
    dim_time_loc['YEAR'] = dim_time_loc['ORDERDATE'].dt.year
    dim_time_loc.to_csv('/tmp/dim_time_loc.csv', index=False)

def load():
    fact_df = pd.read_csv('/tmp/fact_sales_by_location.csv')
    dim_location = pd.read_csv('/tmp/dim_location.csv')
    dim_time_loc = pd.read_csv('/tmp/dim_time_loc.csv')

    fact_df.to_csv(os.path.join(dag_path, 'fact_sales_by_location.csv'), index=False)
    dim_location.to_csv(os.path.join(dag_path, 'dim_location.csv'), index=False)
    dim_time_loc.to_csv(os.path.join(dag_path, 'dim_time_loc.csv'), index=False)

with DAG(
    dag_id='etl_sales_by_location',
    start_date=datetime(2023, 1, 1),
    schedule='@daily',
    catchup=False,
    tags=['etl', 'star_schema', 'sales']
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
