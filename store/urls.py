from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<str:cart_key>/', views.remove_from_cart, name='remove_from_cart'),
    path('contact/', views.contact, name='contact'),
    path('shop/<int:item_id>/', views.product_detail, name='product_detail'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-checkout/', views.process_checkout, name='process_checkout'),
    path('order-success/', views.order_success, name='order_success'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('merchant/dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
]