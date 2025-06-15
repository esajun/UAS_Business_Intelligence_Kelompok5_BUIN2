from django.shortcuts import render
from django.db.models import Sum
from .models import Customer, CustomerOrder, Product, Time, SalesFact
from sklearn.linear_model import LinearRegression
import pandas as pd
import os
import json 

# Path file
BASE_DIR = '/root/airflow'
FACT_PATH1 = os.path.join(BASE_DIR, 'dags2/fact_customer_order.csv')
DIM_PATH = os.path.join(BASE_DIR, 'dags2/dim_customer.csv')
FACT_PATH = os.path.join(BASE_DIR, 'dags2/fact_sales.csv')
PRODUCT_DIM_PATH = os.path.join(BASE_DIR, 'dags2/dim_product.csv')
TIME_DIM_PATH = os.path.join(BASE_DIR, 'dags2/dim_time.csv')

def dashboard_view(request):
    return render(request, 'dashboard.html')

def load_etl_data(request):
    # Load dim_customer
    dim_df = pd.read_csv(DIM_PATH)
    for _, row in dim_df.iterrows():
        Customer.objects.update_or_create(
            customer_name=row['CUSTOMERNAME'],
            defaults={
                'contact_first_name': row['CONTACTFIRSTNAME'],
                'contact_last_name': row['CONTACTLASTNAME'],
                'phone': row['PHONE'],
                'address': row['ADDRESSLINE1'],
                'city': row['CITY'],
                'country': row['COUNTRY'],
                'deal_size': row['DEALSIZE'],
            }
        )

    # Load fact_customer_order
    fact_df = pd.read_csv(FACT_PATH1)
    for _, row in fact_df.iterrows():
        try:
            customer = Customer.objects.get(customer_name=row['CUSTOMERNAME'])
            CustomerOrder.objects.update_or_create(
                order_number=row['ORDERNUMBER'],
                customer=customer,
                defaults={
                    'sales': row['SALES'],
                    'days_since_last_order': row['DAYS_SINCE_LASTORDER'],
                }
            )
        except Customer.DoesNotExist:
            print(f"Customer {row['CUSTOMERNAME']} not found, skipping...")

    return render(request, 'load_success.html')

# PREDIKSI PENJUALAN PER BULAN
def predict_sales_month(request):
    # Agregat total sales dari model SalesFact
    total_sales = SalesFact.objects.aggregate(total=Sum('sales'))['total'] or 0

    # Total sales per product line
    product_data = SalesFact.objects.values('product__product_line')\
        .annotate(total=Sum('sales')).order_by('-total')

    # Monthly sales dari tabel fakta
    monthly_sales = SalesFact.objects.values(
        'order_date__month', 'order_date__year'
    ).annotate(total=Sum('sales')).order_by('order_date__year', 'order_date__month')

    try:
        # Load data CSV
        fact_df = pd.read_csv(FACT_PATH)
        time_df = pd.read_csv(TIME_DIM_PATH)

        # ✅ Samakan format ORDERDATE: convert ke datetime.date
        fact_df['ORDERDATE'] = pd.to_datetime(fact_df['ORDERDATE']).dt.date
        time_df['ORDERDATE'] = pd.to_datetime(time_df['ORDERDATE']).dt.date

        # ✅ Merge setelah tanggal sama
        df = pd.merge(fact_df, time_df, how='left', on='ORDERDATE')

        if 'SALES' not in df.columns or 'MONTH' not in df.columns or 'YEAR' not in df.columns:
            raise ValueError("Kolom yang diperlukan tidak ditemukan dalam CSV")

        df = df[['MONTH', 'YEAR', 'SALES']].dropna()

        df['SALES'] = pd.to_numeric(df['SALES'], errors='coerce').fillna(0)

        df_grouped = df.groupby(['YEAR', 'MONTH'], as_index=False)['SALES'].sum()
        df_grouped['time_index'] = df_grouped['YEAR'] * 12 + df_grouped['MONTH']
        df_grouped = df_grouped.sort_values('time_index')

        X = df_grouped[['time_index']]
        y = df_grouped['SALES']
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)

        labels = (df_grouped['YEAR'].astype(str) + '-' + df_grouped['MONTH'].astype(str).str.zfill(2)).tolist()
        actual_values = y.round(2).tolist()
        predicted_values = [round(val, 2) for val in y_pred]

    except Exception as e:
        print("Error saat memproses data prediksi sales:", e)
        labels, actual_values, predicted_values = [], [], []

    context = {
    'total_sales': float(total_sales),
    'product_data': product_data,
    'monthly_sales': monthly_sales,
    'labels': json.dumps(labels),
    'values': json.dumps(actual_values),
    'predictions': json.dumps(predicted_values),
    }

    return render(request, 'predict_sales_month.html', context)

# PENJUALAN BERDASARKAN CUSTOMER
def order_summary(request):
    df = pd.DataFrame(list(CustomerOrder.objects.all().values(
        'customer__customer_name', 'sales'
    )))

    if df.empty:
        return render(request, 'order_summary.html', {'labels': [], 'values': []})

    summary = df.groupby('customer__customer_name')['sales'].sum().reset_index()

    labels = summary['customer__customer_name'].tolist()
    values = summary['sales'].tolist()

    return render(request, 'order_summary.html', {
        'labels': labels,
        'values': values,
    })

# PENJUALAN BERDASARKAN NEGARA
def sales_by_country_view(request):
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, 'dags2/fact_sales_by_location.csv'))
        location_df = pd.read_csv(os.path.join(BASE_DIR, 'dags2/dim_location.csv'))

        merged_df = pd.merge(df, location_df, how='left', on='CUSTOMERNAME')
        merged_df = merged_df[['COUNTRY', 'SALES']].dropna()

        summary = merged_df.groupby('COUNTRY')['SALES'].sum().reset_index()

        labels = summary['COUNTRY'].tolist()
        values = summary['SALES'].round(2).tolist()

    except Exception as e:
        print("Error saat memproses data penjualan per negara:", e)
        labels, values = [], []

    return render(request, 'sales_by_country.html', {
        'labels': labels,
        'values': values,
    })

# PENJUALAN BERDASARKAN NEGARA DAN WAKTU
def sales_by_location_over_time(request):
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, 'dags2/fact_sales_by_location.csv'))
        location_df = pd.read_csv(os.path.join(BASE_DIR, 'dags2/dim_location.csv'))
        df = pd.merge(df, location_df, how='left', on='CUSTOMERNAME')  # Tambahkan ini


        # Pastikan kolom yang dibutuhkan ada
        for col in ['ORDERDATE', 'SALES', 'COUNTRY']:
            if col not in df.columns:
                raise ValueError(f"Kolom {col} tidak ditemukan")

        df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'])
        df['MONTH'] = df['ORDERDATE'].dt.month
        df['YEAR'] = df['ORDERDATE'].dt.year
        df['PERIOD'] = df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str).str.zfill(2)

        # Kelompokkan berdasarkan lokasi & waktu
        grouped = df.groupby(['COUNTRY', 'PERIOD'])['SALES'].sum().reset_index()

        # Buat list semua periode unik (untuk x-axis konsisten)
        periods = sorted(grouped['PERIOD'].unique().tolist())

        # Ambil semua lokasi unik
        countries = grouped['COUNTRY'].unique()

        # Siapkan data untuk Chart.js
        datasets = []
        for country in countries:
            data_per_period = []
            for period in periods:
                val = grouped[(grouped['COUNTRY'] == country) & (grouped['PERIOD'] == period)]['SALES']
                data_per_period.append(round(val.values[0], 2) if not val.empty else 0)
            datasets.append({
                'label': country,
                'data': data_per_period
            })

    except Exception as e:
        print("Gagal proses data:", e)
        periods, datasets = [], []

    return render(request, 'sales_by_location_over_time.html', {
        'labels': periods,
        'datasets': json.dumps(datasets)
    })

# PENJUALAN SELURUH PRODUK
def sales_by_product_view(request):
    try:
        fact_df = pd.read_csv(FACT_PATH)
        product_df = pd.read_csv(PRODUCT_DIM_PATH)

        # Merge fact dan dimensi produk
        df = pd.merge(fact_df, product_df, how='left', on='PRODUCTCODE')
        df = df[['PRODUCTLINE', 'SALES', 'QUANTITYORDERED']].dropna()

        # Group by PRODUCTLINE, hitung total SALES dan jumlah produk
        summary = df.groupby('PRODUCTLINE').agg({
            'SALES': 'sum',
            'QUANTITYORDERED': 'sum'
        }).reset_index()

        labels = summary['PRODUCTLINE'].tolist()
        sales_values = summary['SALES'].round(2).tolist()
        quantity_values = summary['QUANTITYORDERED'].astype(int).tolist()

    except Exception as e:
        print("Gagal memproses data penjualan produk:", e)
        labels, sales_values, quantity_values = [], [], []

    return render(request, 'sales_by_product.html', {
        'labels': labels,
        'sales_values': sales_values,
        'quantity_values': quantity_values,
    })

# PENJUALAN PRODUK PER BULAN
def sales_by_product_month(request):
    try:
        fact_df = pd.read_csv(FACT_PATH)
        product_df = pd.read_csv(PRODUCT_DIM_PATH)
        time_df = pd.read_csv(TIME_DIM_PATH)

        # Join
        df = pd.merge(fact_df, product_df, on='PRODUCTCODE', how='left')
        df = pd.merge(df, time_df, on='ORDERDATE', how='left')

        # Pilihan unik productline
        productlines = sorted(df['PRODUCTLINE'].dropna().unique().tolist())

        # Ambil productline dari request
        selected_line = request.GET.get('productline', productlines[0])

        df_filtered = df[df['PRODUCTLINE'] == selected_line]

        df_filtered['PERIOD'] = df_filtered['YEAR'].astype(str) + '-' + df_filtered['MONTH'].astype(str).str.zfill(2)
        summary = df_filtered.groupby('PERIOD')['SALES'].sum().reset_index()

        labels = summary['PERIOD'].tolist()
        values = summary['SALES'].round(2).tolist()

    except Exception as e:
        print("Error:", e)
        labels, values, productlines, selected_line = [], [], [], ''

    return render(request, 'sales_by_product_month.html', {
        'productlines': productlines,
        'selected': selected_line,
        'labels': json.dumps(labels),
        'values': json.dumps(values),
    })

# PREDIKSI PENJUALAN PER PRODUK
def predict_sales_by_product_month(request):
    try:
        fact_df = pd.read_csv(FACT_PATH)
        product_df = pd.read_csv(PRODUCT_DIM_PATH)
        time_df = pd.read_csv(TIME_DIM_PATH)

        # Join
        df = pd.merge(fact_df, product_df, on='PRODUCTCODE', how='left')
        df = pd.merge(df, time_df, on='ORDERDATE', how='left')

        productlines = sorted(df['PRODUCTLINE'].dropna().unique().tolist())
        selected_line = request.GET.get('productline', productlines[0])

        df_filtered = df[df['PRODUCTLINE'] == selected_line]

        # Gabungkan YEAR dan MONTH jadi period
        df_filtered = df_filtered.dropna(subset=['YEAR', 'MONTH', 'SALES'])
        df_filtered['YEAR'] = df_filtered['YEAR'].astype(int)
        df_filtered['MONTH'] = df_filtered['MONTH'].astype(int)
        df_filtered['SALES'] = pd.to_numeric(df_filtered['SALES'], errors='coerce').fillna(0)
        df_filtered['PERIOD'] = df_filtered['YEAR'].astype(str) + '-' + df_filtered['MONTH'].astype(str).str.zfill(2)
        df_filtered['time_index'] = df_filtered['YEAR'] * 12 + df_filtered['MONTH']

        summary = df_filtered.groupby(['PERIOD', 'time_index'])['SALES'].sum().reset_index()
        summary = summary.sort_values('time_index')

        X = summary[['time_index']]
        y = summary['SALES']
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)

        labels = summary['PERIOD'].tolist()
        actual_values = y.round(2).tolist()
        predicted_values = [round(val, 2) for val in y_pred]

    except Exception as e:
        print("Error:", e)
        labels, actual_values, predicted_values, productlines, selected_line = [], [], [], [], ''

    return render(request, 'predict_sales_by_product_month.html', {
        'productlines': productlines,
        'selected': selected_line,
        'labels': json.dumps(labels),
        'values': json.dumps(actual_values),
        'predictions': json.dumps(predicted_values),
    })

# SEGMENTASI CUSTOMER
from sklearn.cluster import KMeans
def customer_segmentation(request):
    # Ambil data customer dan total sales mereka
    df = pd.DataFrame(list(CustomerOrder.objects.values(
        'customer__customer_name', 'sales'
    )))
    
    if df.empty:
        return render(request, 'customer_segment.html', {
            'labels': json.dumps([]),
            'values': json.dumps([]),
            'customer_segments': []
        })
    
    # Hitung total sales per customer
    grouped = df.groupby('customer__customer_name')['sales'].sum().reset_index()
    
    # Terapkan KMeans clustering
    kmeans = KMeans(n_clusters=3, random_state=42)
    grouped['segment'] = kmeans.fit_predict(grouped[['sales']])
    
    # Mapping label berdasarkan nilai centroid (Low, Medium, High)
    centroids = kmeans.cluster_centers_.flatten()
    sorted_idx = centroids.argsort()
    label_map = {
        sorted_idx[0]: 'Low Value',
        sorted_idx[1]: 'Medium Value',
        sorted_idx[2]: 'High Value'
    }
    grouped['segment_label'] = grouped['segment'].map(label_map)
    
    # Untuk grafik: jumlah customer per segment
    segment_counts = grouped['segment_label'].value_counts().sort_index()
    labels = segment_counts.index.tolist()
    values = segment_counts.values.tolist()

    # Untuk tabel
    customer_segments = grouped[['customer__customer_name', 'segment_label']].to_dict(orient='records')

    return render(request, 'customer_segment.html', {
        'labels': json.dumps(labels),
        'values': json.dumps(values),
        'customer_segments': customer_segments
    })