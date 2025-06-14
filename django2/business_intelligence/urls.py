from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('summary/', views.order_summary, name='order_summary'),
    path('load_etl_data/', views.load_etl_data, name='load_etl_data'),  
    path('predict_sales_month/', views.predict_sales_month, name='predict_sales_month'),  
    path('product_trend/', views.product_sales_trend, name='product_sales_trend'),  
    path('sales_by_country/', views.sales_by_country_view, name='sales_by_country'),
    path('sales_location_time/', views.sales_by_location_over_time, name='sales_location_time'),
    path('sales_by_product/', views.sales_by_product_view, name='sales_by_product'),
    path('sales_by_product_month/', views.sales_by_product_month, name='sales_by_product_month'),
    path('predict_sales_by_product_month/', views.predict_sales_by_product_month, name='predict_sales_by_product_month'),
]

