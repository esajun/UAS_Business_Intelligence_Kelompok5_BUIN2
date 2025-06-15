from django.db import models

from django.db import models

# === Dimensi Customer ===
class Customer(models.Model):
    customer_name = models.CharField(max_length=255, unique=True)
    contact_first_name = models.CharField(max_length=100)
    contact_last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    deal_size = models.CharField(max_length=50)

    def __str__(self):
        return self.customer_name


# === Fakta Customer Order ===
class CustomerOrder(models.Model):
    order_number = models.IntegerField(unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    sales = models.FloatField()
    days_since_last_order = models.IntegerField()

    def __str__(self):
        return f"Order #{self.order_number} for {self.customer.customer_name}"


# === Dimensi Produk ===
class Product(models.Model):
    product_code = models.CharField(max_length=50, primary_key=True)
    product_name = models.CharField(max_length=100)
    product_line = models.CharField(max_length=100)
    msrp = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.product_code


# === Dimensi Waktu ===
class Time(models.Model):
    order_date = models.DateField(primary_key=True)
    month = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return str(self.order_date)


# === Fakta Penjualan ===
class SalesFact(models.Model):
    order = models.ForeignKey(CustomerOrder, on_delete=models.CASCADE, related_name='sales_facts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sales_facts')
    order_date = models.ForeignKey(Time, on_delete=models.CASCADE, related_name='sales_facts')
    quantity_ordered = models.IntegerField()
    price_each = models.DecimalField(max_digits=10, decimal_places=2)
    sales = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ('order', 'product', 'order_date')

    def __str__(self):
        return f"{self.order.order_number} - {self.product.product_code} - {self.order_date}"

# === Dimensi Lokasi ===
class Location(models.Model):
    customer_name = models.CharField(max_length=255, unique=True)
    product_line = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.customer_name} - {self.country}"


# === Fakta Penjualan per Lokasi ===
class SalesByLocation(models.Model):
    order_number = models.IntegerField()
    customer_name = models.CharField(max_length=255)
    order_date = models.DateField()
    quantity_ordered = models.IntegerField()
    price_each = models.DecimalField(max_digits=10, decimal_places=2)
    sales = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        unique_together = ('order_number', 'customer_name', 'order_date')

    def __str__(self):
        return f"{self.order_number} - {self.customer_name} - {self.sales}"