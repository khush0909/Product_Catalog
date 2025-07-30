from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cart URLs
    path('cart/', views.cart_view, name='cart'), # Main cart view
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),

    # Wishlist URLs (Updated based on views.py)
    path('wishlist/', views.wishlist_view, name='wishlist'), # Main wishlist view
    # This view now handles both adding and removing from wishlist
    path('wishlist/toggle/<int:product_id>/', views.add_remove_wishlist, name='add_remove_wishlist'),
    path('wishlist/add_to_cart/<int:product_id>/', views.add_to_cart_from_wishlist, name='add_to_cart_from_wishlist'),

    # User Profile & Orders URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password_change/', views.password_change, name='password_change'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Checkout URL
    path('checkout/', views.checkout, name='checkout'),
]