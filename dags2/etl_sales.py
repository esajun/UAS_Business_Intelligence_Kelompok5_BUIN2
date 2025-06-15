from airflow import DAG
from airflow.operators.python import PythonOperator  # type: ignore
from datetime import datetime
import pandas as pd
import os

dag_path = os.path.dirname(__file__)

def extract():
    csv_path = os.path.join(dag_path, 'autosales_data.csv')  # Ganti sesuai nama filemu
    df = pd.read_csv(csv_path)

    # Simpan hasil ekstraksi mentah
    df.to_csv('/tmp/extracted_sales.csv', index=False)

def transform():
    df = pd.read_csv('/tmp/extracted_sales.csv')

    # Pastikan kolom tanggal bertipe datetime
    df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])

    # ===== TABEL FAKTA =====
    fact_df = df[['ORDERNUMBER', 'PRODUCTCODE', 'ORDERDATE', 'QUANTITYORDERED', 'PRICEEACH']]
    fact_df['SALES'] = fact_df['QUANTITYORDERED'] * fact_df['PRICEEACH']
    fact_df = fact_df.drop_duplicates()
    fact_df.to_csv('/tmp/fact_sales.csv', index=False)

    # ===== DIMENSI PRODUK =====
    dim_product = df[['PRODUCTCODE', 'PRODUCTLINE', 'MSRP']]
    dim_product = dim_product.drop_duplicates(subset=['PRODUCTCODE'])  # PK: PRODUCTCODE
    dim_product.to_csv('/tmp/dim_product.csv', index=False)

    # ===== DIMENSI WAKTU =====
    dim_time = df[['ORDERDATE']].drop_duplicates()
    dim_time['MONTH'] = dim_time['ORDERDATE'].dt.month
    dim_time['YEAR'] = dim_time['ORDERDATE'].dt.year
    dim_time.to_csv('/tmp/dim_time.csv', index=False)

def load():
    # Baca hasil transform
    fact_df = pd.read_csv('/tmp/fact_sales.csv')
    dim_product = pd.read_csv('/tmp/dim_product.csv')
    dim_time = pd.read_csv('/tmp/dim_time.csv')

    # Simpan ke direktori proyek
    fact_df.to_csv(os.path.join(dag_path, 'fact_sales.csv'), index=False)
    dim_product.to_csv(os.path.join(dag_path, 'dim_product.csv'), index=False)
    dim_time.to_csv(os.path.join(dag_path, 'dim_time.csv'), index=False)

with DAG(
    dag_id='etl_sales',
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
