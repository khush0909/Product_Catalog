from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from catalog.models import Product, Cart, CartItem
from django.http import JsonResponse
from django.db.models import Sum, F
from decimal import Decimal


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pr_id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'quantity': cart_item.quantity})
    return redirect('cart')

@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        cart_items = cart.items.select_related('product').all()
        for item in cart_items:
            quantity_str = request.POST.get(f'quantity_{item.id}')
            if quantity_str:
                try:
                    quantity = int(quantity_str)
                    if quantity > 0:
                        item.quantity = quantity
                        item.save()
                except ValueError:
                    pass  # Ignore invalid input, keep old quantity
    cart_items = cart.items.select_related('product').all()
    total = sum(item.product.pr_price * item.quantity for item in cart_items)
    total_items = cart.items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    total_price = cart.items.aggregate(total_price=Sum(F('quantity') * F('product__pr_price')))['total_price'] or Decimal('0.00')
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total, 'total_items': total_items, 'total_price': total_price})
@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart')

@login_required
def clear_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    return redirect('cart')



