import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from decimal import Decimal # Import Decimal for precise calculations

# Import all your models from catalog.models
from .models import Product, Seller, UserProfile, Cart, CartItem, Wishlist, OrderedItem, Order, Review, Payment

# --- Authentication Views ---

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a UserProfile, Cart, and Wishlist for the new user
            UserProfile.objects.create(user=user)
            Cart.objects.create(user=user)
            Wishlist.objects.create(user=user)
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('home') # Redirect to home page after successful signup
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserCreationForm()
    return render(request, 'catalog/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home') # Redirect to home page after successful login
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'catalog/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# --- Product & Catalog Views ---

def home(request):
    # Fetch some featured products for the homepage
    featured_products = Product.objects.all().order_by('-pr_id')[:8]
    # Categories are now directly from Product.CATEGORY_CHOICES
    categories = [choice[0] for choice in Product.CATEGORY_CHOICES]

    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'catalog/home.html', context)

def product_list(request):
    products = Product.objects.all()
    category_name = request.GET.get('category')
    sort_by = request.GET.get('sort')

    if category_name and category_name != 'All Products':
        products = products.filter(pr_cate__iexact=category_name)
    
    if sort_by == 'price_asc':
        products = products.order_by('pr_price')
    elif sort_by == 'price_desc':
        products = products.order_by('-pr_price')
    elif sort_by == 'newest':
        products = products.order_by('-pr_id')

    context = {
        'products': products,
        'current_category': category_name,
        'current_sort': sort_by,
        'categories': [choice[0] for choice in Product.CATEGORY_CHOICES],
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    
    related_products = Product.objects.filter(pr_cate=product.pr_cate).exclude(pr_id=product.pr_id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)

# --- Cart Views ---

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.pr_name} added to cart.")
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
            else:
                cart_item.delete() # Remove if quantity is 0
                messages.info(request, "Item removed from cart.")
        except ValueError:
            messages.error(request, "Invalid quantity.")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        cart_item.delete()
        messages.info(request, "Item removed from cart.")
    return redirect('cart')

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all().order_by('product__pr_name')
    
    total_price = sum(item.subtotal for item in cart_items)
    shipping_cost = Decimal('5.00') # Corrected: Converted to Decimal
    grand_total = total_price + shipping_cost # Add tax if applicable
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    return render(request, 'catalog/cart.html', context)

# --- Wishlist Views ---

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    if product not in wishlist.products.all():
        wishlist.products.add(product)
        messages.success(request, f"{product.pr_name} added to your wishlist.")
    else:
        messages.info(request, f"{product.pr_name} is already in your wishlist.")
    return redirect('wishlist')

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    
    if request.method == 'POST':
        if product in wishlist.products.all():
            wishlist.products.remove(product)
            messages.info(request, "Item removed from wishlist.")
        else:
            messages.error(request, "Item not found in your wishlist.")
    return redirect('wishlist')

@login_required
def add_to_cart_from_wishlist(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    
    # Add to cart logic
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f"{product.pr_name} moved to cart.")
    
    # Remove from wishlist after moving to cart
    wishlist = get_object_or_404(Wishlist, user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
    
    return redirect('cart')

@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_items = wishlist.products.all().order_by('-pr_id')
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'catalog/wishlist.html', context)

# --- Profile View ---
@login_required
def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]

    context = {
        'user_profile': user_profile,
        'orders': orders,
    }
    return render(request, 'catalog/profile.html', context)

# --- Placeholder for profile_edit and password_change ---
@login_required
def profile_edit(request):
    messages.info(request, "Profile edit functionality not yet implemented.")
    return redirect('profile')

@login_required
def password_change(request):
    messages.info(request, "Password change functionality not yet implemented.")
    return redirect('profile')

# --- Placeholder for order_detail ---
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    ordered_items = order.items.all()

    context = {
        'order': order,
        'ordered_items': ordered_items,
    }
    return render(request, 'catalog/order_detail.html', context)
