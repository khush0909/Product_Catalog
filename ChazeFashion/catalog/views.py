import csv
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from decimal import Decimal # Import Decimal for precise calculations
from django.db.models import Sum, F
from django.core.paginator import Paginator # Import Paginator
from django.http import JsonResponse

# Import all your models from catalog.models
from .models import Product, Seller, UserProfile, Cart, CartItem, Wishlist, OrderedItem, Order, Review, Payment

# --- Authentication Views ---
# ChazeFashion/catalog/views.py

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # ...
            login(request, user)
            messages.success(request, "Account created successfully!") # This message
            return redirect('home') # Redirects to home, not login
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
            messages.success(request, f"Welcome back, {user.username}!") # This message
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.") # This message
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
    
    # --- Filtering Logic ---
    # Category Filter
    category_name = request.GET.get('category')
    if category_name and category_name != 'All Products':
        products = products.filter(pr_cate__iexact=category_name)
    
    # Price Range Filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(pr_price__gte=Decimal(min_price))
        except ValueError:
            messages.error(request, "Invalid minimum price.")
    if max_price:
        try:
            products = products.filter(pr_price__lte=Decimal(max_price))
        except ValueError:
            messages.error(request, "Invalid maximum price.")

    # Brand Filter
    selected_brands = request.GET.getlist('brand') # Use getlist for multiple selections
    if selected_brands:
        products = products.filter(pr_brand__in=selected_brands) # Filter by selected brands

    # --- Sorting Logic ---
    sort_by = request.GET.get('sort_by')
    if sort_by == 'name':
        products = products.order_by('pr_name')
    elif sort_by == '-name':
        products = products.order_by('-pr_name')
    elif sort_by == 'price':
        products = products.order_by('pr_price')
    elif sort_by == '-price':
        products = products.order_by('-pr_price')
    elif sort_by == '-pr_id': # Using pr_id for "newest" as per your model
        products = products.order_by('-pr_id')
    else:
        products = products.order_by('pr_name')

    products = products.distinct()

    # --- Data for Filters in Template ---
    # Get all unique categories from your Product model
    all_categories = sorted([choice[0] for choice in Product.CATEGORY_CHOICES])
    # Get all unique brands from products currently in the database
    all_brands = sorted(Product.objects.values_list('pr_brand', flat=True).distinct().exclude(pr_brand=''))

    context = {
        'products': products,
        'selected_category': category_name,
        'selected_sort': sort_by,
        'categories': all_categories, # Pass unique categories
        'brands': all_brands,         # Pass unique brands
        'selected_min_price': min_price,
        'selected_max_price': max_price,
        'selected_brands': selected_brands, # Pass selected brands back to template
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    # Use pr_id as the primary key
    product = get_object_or_404(Product, pr_id=product_id)
    
    # Filter related products by 'pr_cate' and exclude the current product
    related_products = Product.objects.filter(pr_cate=product.pr_cate).exclude(pr_id=product.pr_id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)

# --- Cart Views ---

@login_required
def add_to_cart(request, product_id):
    # Use pr_id as the primary key
    product = get_object_or_404(Product, pr_id=product_id)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            quantity = 1 # Ensure quantity is at least 1
    except ValueError:
        quantity = 1 # Default to 1 if not a valid number

    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = quantity # If it's a new item, set the initial quantity
    cart_item.save()

    # Calculate current total cart items and total price for AJAX response
    total_items = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 # Use related_name 'items'
    total_price = cart.items.aggregate(total_price=Sum(F('quantity') * F('product__pr_price')))['total_price'] or Decimal('0.00')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.pr_name} added to cart!', # Use pr_name
            'cart_item_count': total_items,
            'cart_total_price': float(total_price), # Convert Decimal to float for JSON
            'product_id': product_id,
            'new_item_quantity': cart_item.quantity,
        })
    else:
        messages.success(request, f"{product.pr_name} added to cart.") # Use pr_name
        return redirect('product_detail', product_id=product_id)


@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    success = False
    message = ""

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                message = "Cart updated successfully."
                success = True
            else:
                cart_item.delete()
                message = "Item removed from cart."
                success = True
        except ValueError:
            message = "Invalid quantity."
            success = False
        
        # Recalculate cart totals for AJAX response
        cart = cart_item.cart # Get the cart after potential deletion of item
        total_items = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 # Use related_name 'items'
        total_price = cart.items.aggregate(total_price=Sum(F('quantity') * F('product__pr_price')))['total_price'] or Decimal('0.00')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'cart_item_count': total_items,
                'cart_total_price': float(total_price),
                'item_id': item_id,
                'new_item_quantity': cart_item.quantity if success and quantity > 0 else 0,
                'new_item_subtotal': float(cart_item.quantity * cart_item.product.pr_price) if success and quantity > 0 else 0.0,
            })
    
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    return redirect('cart_view')


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    message = "Item removed from cart."
    success = True
    
    if request.method == 'POST':
        cart = cart_item.cart # Get cart before deleting item
        cart_item.delete()
        
        # Recalculate cart totals for AJAX response
        total_items = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 # Use related_name 'items'
        total_price = cart.items.aggregate(total_price=Sum(F('quantity') * F('product__pr_price')))['total_price'] or Decimal('0.00')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'cart_item_count': total_items,
                'cart_total_price': float(total_price),
                'item_id': item_id,
            })
    
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        messages.info(request, message)
    return redirect('cart_view')


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    # Use select_related to get product details in one query for efficiency
    cart_items = cart.items.select_related('product').all().order_by('product__pr_name')
    
    # Calculate subtotal for each item on the fly if no property exists
    # For total price calculation, use aggregation for database efficiency
    total_price = cart_items.aggregate(
        total=Sum(F('quantity') * F('product__pr_price'))
    )['total'] or Decimal('0.00')

    shipping_cost = Decimal('5.00')
    grand_total = total_price + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    return render(request, 'catalog/cart.html', context)

# --- Wishlist Views ---

@login_required
def add_remove_wishlist(request, product_id):
    # This view toggles an item's presence in the wishlist and handles AJAX
    product = get_object_or_404(Product, pr_id=product_id) # Use pr_id
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    added = False
    message = ""

    # Check if product is in the wishlist's many-to-many relationship
    if wishlist.products.filter(pr_id=product_id).exists():
        # If it exists, remove it
        wishlist.products.remove(product)
        message = f'{product.pr_name} removed from wishlist.'
        added = False
    else:
        # If it does not exist, add it
        wishlist.products.add(product)
        message = f'{product.pr_name} added to your wishlist.'
        added = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': message,
            'added': added, # Indicates if the product was added or removed
            'product_id': product_id,
        })
    else:
        messages.success(request, message)
        return redirect('wishlist_view')


@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    # Access products through the ManyToMany field
    wishlist_items = wishlist.products.all().order_by('-pr_id')
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'catalog/wishlist.html', context)


@login_required
def add_to_cart_from_wishlist(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id) # Use pr_id

    # Add to cart logic (similar to the main add_to_cart view)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()

    # Remove from wishlist after adding to cart
    wishlist_removed = False
    try:
        wishlist = Wishlist.objects.get(user=request.user)
        if wishlist.products.filter(pr_id=product_id).exists(): # Check if it's actually in the wishlist
            wishlist.products.remove(product)
            wishlist_removed = True
    except Wishlist.DoesNotExist:
        pass # Wishlist doesn't exist for the user, so nothing to remove

    # Calculate current total cart items and total price for AJAX response
    total_items = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 # Use related_name 'items'
    total_price = cart.items.aggregate(total_price=Sum(F('quantity') * F('product__pr_price')))['total_price']  # Use related_name 'items'

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.pr_name} moved to cart!', # Use pr_name
            'cart_item_count': total_items,
            'cart_total_price': float(total_price),
            'product_id': product_id, # Pass product_id to remove from wishlist in DOM
            'wishlist_removed': wishlist_removed,
        })
    
    messages.success(request, f"{product.pr_name} moved from wishlist to cart.")
    return redirect('cart_view')


# --- Profile View ---
@login_required
def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    # Assuming Order has a default ordering or you want to order by created_at
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
    return redirect('profile_view') # Corrected redirect name

@login_required
def password_change(request):
    messages.info(request, "Password change functionality not yet implemented.")
    return redirect('profile_view') # Corrected redirect name

# --- Placeholder for order_detail ---
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # Access ordered items through the ManyToMany field
    ordered_items = order.items.all().select_related('product') # Use select_related for efficiency

    context = {
        'order': order,
        'ordered_items': ordered_items,
    }
    return render(request, 'catalog/order_detail.html', context)


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all() # Use related_name 'items'
    
    # Calculate total using aggregation for more precise Decimal arithmetic
    total = cart_items.aggregate(
        total_sum=Sum(F('quantity') * F('product__pr_price'))
    )['total_sum'] or Decimal('0.00')
    
    shipping_cost = Decimal('5.00')
    grand_total = total + shipping_cost

    if request.method == 'POST':
        if not cart_items.exists():
            messages.error(request, "Your cart is empty. Please add items before checking out.")
            return redirect('cart_view')

        try:
            # Create an Order instance
            order = Order.objects.create(user=request.user, total_price=grand_total) # Use total_price field

            # Move items from cart to ordered items and add to the order's ManyToMany field
            for cart_item in cart_items:
                ordered_item = OrderedItem.objects.create(
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.pr_price # Store price at time of order
                )
                order.items.add(ordered_item) # Add to the ManyToMany field

            # Clear the cart after moving items to order
            cart.items.all().delete()
            messages.success(request, "Thank you for your purchase! Your order has been placed.")
            return redirect('order_detail', order_id=order.id) # Redirect to the newly created order detail page
        except Exception as e:
            messages.error(request, f"An error occurred during checkout: {e}")
            return redirect('cart_view') # Redirect back to cart on error

    return render(request, 'catalog/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    })