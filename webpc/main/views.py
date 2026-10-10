from django.shortcuts import render, get_object_or_404, redirect

# Create your views here.
from .cart import Cart
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Category, Product
from .models import Cart as DBCart, CartItem, Product
from .forms import CartAddProductForm
from django.urls import reverse
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from decimal import Decimal
from django.conf import settings

@receiver(user_logged_in)
def merge_carts(sender, request, user, **kwargs):
    session_cart = request.session.get(settings.CART_SESSION_ID)
    if not session_cart:
        return

    db_cart, _ = DBCart.objects.get_or_create(user=user)

    for product_id, item_data in session_cart.items():
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            continue

        cart_item, created = CartItem.objects.get_or_create(
            cart=db_cart,
            product=product,
            defaults={
                'price': Decimal(item_data['price']),
                'quantity': item_data['quantity'],
            }
        )
        if not created:
            cart_item.quantity += item_data['quantity']
            cart_item.save()
    
    if settings.CART_SESSION_ID in request.session:
        del request.session[settings.CART_SESSION_ID]

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'main/product/list.html', {
        'category': category,
        'products': products,
        'categories': categories
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, available=True, slug=slug)
    return render(request, 'main/product/detail.html', {
        'product': product
    })

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(
            product= product,
            quantity=cd['quantity'],
            override_quantity=cd['override']
        )
    return redirect('main:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('main:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'main/cart/detail.html', {'cart': cart})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('main:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'main/registration/register.html', {'form': form})
