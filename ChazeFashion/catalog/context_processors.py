# ChazeFashion/catalog/context_processors.py

from .models import Cart, CartItem
from django.db.models import Sum

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            total_quantity = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            total_quantity = 0
    else:
        total_quantity = 0

    return {'cart_item_count': total_quantity}