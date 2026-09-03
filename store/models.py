from django.db import models
import uuid
from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.IntegerField(help_text="Price in NGN (e.g. 35000)")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_filename = models.CharField(max_length=255, help_text="Filename in static/store/images/", blank=True, null=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    has_2xs = models.BooleanField(default=False)
    has_xs = models.BooleanField(default=False)
    has_s = models.BooleanField(default=False)
    has_m = models.BooleanField(default=False)
    has_l = models.BooleanField(default=True)
    has_xl = models.BooleanField(default=True)
    has_2xl = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='extra_images', on_delete=models.CASCADE)
    image_filename = models.CharField(max_length=255, help_text="Additional image filename in static/store/images/")
    alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} Extra Image ({self.image_filename})"



def generate_order_ref():
    return f"4TR-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reference = models.CharField(max_length=50, unique=True, default=generate_order_ref)
    
    # Customer Details
    full_name = models.CharField(max_length=255, default="")
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, default="")
    
    # Delivery Address
    street_address = models.CharField(max_length=255, default="")
    city = models.CharField(max_length=100, default="")
    state = models.CharField(max_length=100, default="")
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Financials & Status
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Includes items + shipping
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.reference} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    size = models.CharField(max_length=10, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.size})"