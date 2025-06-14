# Tugas 3: Data Warehouse Penjualan dengan Star Schema, ETL, dan Django Dashboard

## 📚 Sumber Dataset
Dataset yang digunakan diperoleh dari Kaggle:

> 🚗 **[Automobile Sales | Visual EDA 📊](https://www.kaggle.com/datasets/deepla/automobile-sales)**  
> oleh **dee dee**, dipublikasikan sekitar 1 tahun yang lalu dengan lebih dari **19.000 views** dan **500+ salinan**.

## 📦 Struktur Star Schema

### 📌 Star Schema 1 – Penjualan per Produk dan Waktu

#### Fakta: `fact_sales`
| Kolom | Deskripsi |
|-------|-----------|
| ORDERNUMBER | ID unik transaksi |
| PRODUCTCODE | Kode produk |
| ORDERDATE | Tanggal pemesanan |
| QUANTITYORDERED | Jumlah unit terjual |
| PRICEEACH | Harga per unit |
| SALES | Total pendapatan transaksi |

#### Dimensi:
- `dim_product`
  - PRODUCTCODE (PK)
  - PRODUCTLINE
  - MSRP (Harga eceran)
- `dim_time`
  - ORDERDATE (PK)
  - MONTH, YEAR (dihasilkan dari ORDERDATE)

---

### 📌 Star Schema 2 – Segmentasi Pelanggan dan Order

#### Fakta: `fact_customer_order`
| Kolom | Deskripsi |
|-------|-----------|
| ORDERNUMBER | ID transaksi |
| CUSTOMERNAME | Nama pelanggan |
| SALES | Nilai transaksi |
| DAYS_SINCE_LASTORDER | Selisih hari dari transaksi sebelumnya |

#### Dimensi:
- `dim_customer`
  - CUSTOMERNAME (PK)
  - CONTACTFIRSTNAME, CONTACTLASTNAME
  - PHONE, ADDRESSLINE1, CITY, COUNTRY
  - DEALSIZE (ukuran transaksi)

---

### 📌 Star Schema 3 – Penjualan per Lokasi

#### Fakta: `fact_sales_by_location`
| Kolom | Deskripsi |
|-------|-----------|
| ORDERNUMBER | ID transaksi |
| CUSTOMERNAME | Nama pelanggan |
| ORDERDATE | Tanggal transaksi |
| SALES | Total pendapatan |

#### Dimensi:
- `dim_location`
  - CUSTOMERNAME (PK)
  - PRODUCTLINE
  - COUNTRY
  - ADDRESSLINE1
- `dim_time`
  - ORDERDATE (PK)
  - MONTH, YEAR

---

## 🌐 Dashboard Django
Dashboard dibangun menggunakan Django dan Bootstrap 5. Fitur yang tersedia antara lain:
1. **Penjualan Berdasarkan Produk**
2. **Penjualan Berdasarkan Customer**
3. **Penjualan Berdasarkan Lokasi**
4. **Penjualan Berdasarkan Negara dan Waktu**
5. **Prediksi Penjualan per Bulan**
6. **Prediksi Penjualan per Produk**

Visualisasi menggunakan **Chart.js** untuk tampilan grafik yang interaktif.

---
