from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from catalog.models import Product, Cart, CartItem
from django.http import JsonResponse
from decimal import Decimal

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    messages.success(request, f"{product.pr_name} added to cart.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'quantity': cart_item.quantity})
    return redirect('cart')

@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    total_price = sum(item.subtotal for item in cart_items)
    shipping_cost = Decimal('5.00')
    grand_total = total_price + shipping_cost
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
    }
    return render(request, 'catalog/cart.html', context)

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.pr_name
    cart_item.delete()
    messages.info(request, f"{product_name} removed from cart.")
    return redirect('cart')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
            else:
                product_name = cart_item.product.pr_name
                cart_item.delete()
                messages.info(request, f"{product_name} removed from cart.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")
    return redirect('cart')

