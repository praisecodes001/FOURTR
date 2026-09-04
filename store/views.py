from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, Http404
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
import requests
from django.shortcuts import render, get_object_or_404
from .models import Product
from django.conf import settings
from django.shortcuts import render, redirect
from urllib.parse import quote
from django.shortcuts import render
from .models import Order
from decimal import Decimal
from django.core.mail import send_mail
import uuid
from django.core.mail import EmailMessage
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem
from django.db.models import Sum, Count

def home(request):
    return render(request, 'store/home.html')

def shop(request):
    return render(request, 'store/shop.html')

def cart(request):
    return render(request, 'store/cart.html')


def about(request):
    return render(request, 'store/about.html')
    
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        sender_email = request.POST.get('email')
        message_text = request.POST.get('message')

        subject = f"[FOURTR INQUIRY] Message from {name}"
        
        body = f"""
NEW CONTACT FORM TRANSMISSION

Name: {name}
Customer Email: {sender_email}

Message:
{message_text}
"""

        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.BRAND_NOTIFICATION_EMAIL],
                reply_to=[sender_email]  # Clicking 'Reply' in Gmail replies to the customer
            )
            email.send(fail_silently=False)
            
            messages.success(request, "Your transmission has been received. We will respond shortly.")
        except Exception as e:
            print(f"CONTACT EMAIL ERROR: {str(e)}")
            messages.error(request, "Unable to send message right now. Please try again later.")

        return redirect('contact')

    return render(request, 'store/contact.html')

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

def user_signup(request):
    if request.method == 'POST':
        fname = request.POST.get('first_name')
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pwd = request.POST.get('password')

        # Check if username already exists
        if User.objects.filter(username=uname).exists():
            messages.error(request, 'Username is already taken.')
            return render(request, 'store/signup.html')

        # Create user with raw template input values
        user = User.objects.create_user(
            username=uname, 
            email=email, 
            password=pwd, 
            first_name=fname
        )
        
        # Log user in and redirect to home page
        login(request, user)
        return redirect('home')
        
    return render(request, 'store/signup.html')


def user_logout(request):
    logout(request)
    return redirect('home')





@login_required(login_url='login')
def shop(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'store/shop.html', {'products': products}) # Capitalization fixed

def product_detail(request, item_id):
    item = get_object_or_404(Product.objects.prefetch_related('extra_images'), id=item_id)
    return render(request, 'store/product_detail.html', {'item': item})


def add_to_cart(request, item_id):
    if request.method == 'POST':
        # Fetch item directly from live database
        product = get_object_or_404(Product, id=item_id)
        size = request.POST.get('size', 'M')
        cart = request.session.get('cart', {})
        
        cart_key = f"{item_id}_{size}"
        
        if cart_key in cart:
            cart[cart_key]['quantity'] += 1
        else:
            cart[cart_key] = {
                'product_id': item_id,
                'name': product.name,
                'price': float(product.price),
                'image': product.image_filename,  # Uses your database field
                'size': size,
                'quantity': 1
            }
            
        request.session['cart'] = cart
        return redirect('cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    total = 0
    
    for item in cart.values():
        raw_price = str(item['price']).replace(',', '').replace('₦', '').strip()
        price = int(float(raw_price))
        quantity = int(item['quantity'])
        
        item['price'] = price
        item['subtotal'] = price * quantity
        total += item['subtotal']
        
    return render(request, 'store/cart.html', {'cart': cart.values(), 'total': total})

def remove_from_cart(request, cart_key):
    cart = request.session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]
        request.session['cart'] = cart
    return redirect('cart')

def checkout(request):
    cart = request.session.get('cart', {})
    
    # Cast via float first to safely convert strings like '35000.0' into ints
    total = sum(int(float(str(item['price']).replace(',', '').replace('₦', '').strip())) * int(item['quantity']) for item in cart.values())
    
    # Paystack works in kobo (multiply Naira by 100)
    paystack_amount = total * 100 
    
    context = {
        'cart': cart.values(),
        'total': total,
        'paystack_amount': paystack_amount,
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'user_email': request.user.email if request.user.is_authenticated else ''
    }
    return render(request, 'store/checkout.html', context)

# store/views.py
@csrf_exempt
def verify_payment(request):
    # Extract params sent by Paystack callback URL
    reference = request.GET.get('reference')
    order_id = request.GET.get('order_id')

    if not reference or not order_id:
        messages.error(request, "Invalid payment verification parameters.")
        return redirect('checkout')

    order = get_object_or_404(Order, id=order_id)

    # Paystack verification API
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    try:
        response = requests.get(url, headers=headers)
        res_data = response.json()

        if res_data.get('status') and res_data['data']['status'] == 'success':
            # Update order state in database
            order.paid = True
            order.status = 'Paid'
            order.save()

            # Save reference to session for the order success page
            request.session['last_order_ref'] = order.reference

            # Clear cart from session
            if 'cart' in request.session:
                del request.session['cart']

            # Redirect to order_success page
            return redirect('order_success')
        else:
            messages.error(request, "Payment verification failed or was declined.")
            return redirect('checkout')

    except requests.exceptions.RequestException as e:
        print(f"VERIFICATION ERROR: {str(e)}")
        messages.error(request, "Could not verify payment with Paystack.")
        return redirect('checkout')




def order_success(request):
    last_ref = request.session.get('last_order_ref')
    order = None

    if last_ref:
        order = Order.objects.filter(reference=last_ref).first()

    context = {
        'order': order,
    }
    return render(request, 'store/order_success.html', context)


@staff_member_required(login_url='login')
def merchant_dashboard(request):
    total_revenue = Order.objects.filter(status='Paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.filter(status='Paid').count()
    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:15]
    
    # Top selling breakdown
    top_items = OrderItem.objects.values('product_name').annotate(total_sold=Sum('quantity')).order_by('-total_sold')[:5]

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
        'top_items': top_items,
    }
    return render(request, 'store/merchant_dashboard.html', context)    



def process_checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('cart')

        # 1. Calculate Items Subtotal
        items_subtotal = Decimal('0.00')
        for cart_key, item_data in cart.items():
            items_subtotal += Decimal(str(item_data['price'])) * item_data['quantity']

        # 2. Extract State & Determine Server-Side Shipping Fee
        state = request.POST.get('state', '').strip()
        
        if state.lower() == 'lagos':
            shipping_fee = Decimal('5000.00')
        else:
            shipping_fee = Decimal('10000.00')

        # 3. Calculate Final Grand Total
        grand_total = items_subtotal + shipping_fee

        # 4. Save Order with Shipping Details
        reference = f"4TR-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"

        order = Order.objects.create(
            reference=reference,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone_number'),
            street_address=request.POST.get('street_address'),
            city=request.POST.get('city'),
            state=state,
            postal_code=request.POST.get('postal_code', ''),
            shipping_fee=shipping_fee,
            total_amount=grand_total,  # Includes shipping
            paid=False
        )

        # 5. Create Order Items
        for cart_key, item_data in cart.items():
            real_product_id = cart_key.split('_')[0] if '_' in str(cart_key) else cart_key
            product = get_object_or_404(Product, id=int(real_product_id))

            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                price=Decimal(str(item_data['price'])),
                quantity=item_data['quantity'],
                size=item_data.get('size', '')
            )

        # 6. Initialize Paystack using the Grand Total (Converted to Kobo)
        amount_in_kobo = int(grand_total * 100)
        callback_url = request.build_absolute_uri(f'/verify-payment/?order_id={order.id}')

        paystack_url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "email": order.email,
            "amount": amount_in_kobo,
            "reference": order.reference,
            "callback_url": callback_url,
        }

        try:
            response = requests.post(paystack_url, json=payload, headers=headers)
            res_data = response.json()

            if res_data.get('status'):
                return redirect(res_data['data']['authorization_url'])
            else:
                messages.error(request, f"Paystack error: {res_data.get('message')}")
                return redirect('checkout')

        except requests.exceptions.RequestException:
            messages.error(request, "Unable to connect to Paystack.")
            return redirect('checkout')

    return redirect('checkout')
