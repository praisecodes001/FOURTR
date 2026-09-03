from django.contrib import admin
from .models import Product, ProductImage, Order, OrderItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'is_active']
    fieldsets = (
        (None, {'fields': ('name', 'price', 'image_filename', 'description', 'is_active')}),
        ('Available Sizes', {'fields': ('has_2xs', 'has_xs', 'has_s', 'has_m', 'has_l', 'has_xl', 'has_2xl')}),
    )
    inlines = [ProductImageInline]

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_filename', 'alt_text']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone_number', 'city', 'state', 'paid', 'created_at']
    list_filter = ['paid', 'state', 'created_at']
    search_fields = ['full_name', 'email', 'phone_number', 'street_address']
    
    fieldsets = (
        ('Customer & Payment', {
            'fields': ('full_name', 'email', 'phone_number', 'paid')
        }),
        ('Shipping Address', {
            'fields': ('street_address', 'city', 'state', 'postal_code')
        }),
    )
    inlines = [OrderItemInline]