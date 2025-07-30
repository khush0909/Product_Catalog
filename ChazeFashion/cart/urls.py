from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='cart_add_to_cart'),
    path('', views.cart_detail, name='cart_detail'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='cart_remove_from_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='cart_update_cart_item'),
]
