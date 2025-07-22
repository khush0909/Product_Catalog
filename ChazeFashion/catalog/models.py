from django.db import models
from django.contrib.auth.models import User

# Product Model
class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Boys", "Boys"),
        ("Girls", "Girls"),
        ("Men", "Men"),
        ("Women", "Women"),
        ("Toddler", "Toddler"),
    ]
    SEASON_CHOICES = [
        ("Summer", "Summer"),
        ("Winter", "Winter"),
        ("All Season", "All Season"),
    ]
    pr_id = models.AutoField(primary_key=True)
    pr_cate = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    pr_name = models.CharField(max_length=100)
    pr_price = models.DecimalField(max_digits=10, decimal_places=2)
    pr_reviews = models.FloatField(default=0)
    pr_buy_quant = models.PositiveIntegerField(default=0)
    pr_stk_quant = models.PositiveIntegerField(default=0)
    pr_dimensions = models.CharField(max_length=100, blank=True)
    pr_weights = models.CharField(max_length=50, blank=True)
    pr_offers = models.CharField(max_length=100, blank=True)
    pr_images = models.ImageField(upload_to='product_images/', blank=True, null=True)
    pr_season = models.CharField(max_length=20, choices=SEASON_CHOICES, default="All Season")
    pr_fabric = models.CharField(max_length=50, blank=True)
    pr_texture = models.CharField(max_length=50, blank=True)
    pr_brand = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.pr_name

    # You might want to add a get_absolute_url method here for consistency
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('product_detail', kwargs={'product_id': self.pr_id})


# Seller Model
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    shop_name = models.CharField(max_length=100)
    shop_address = models.TextField()
    contact = models.CharField(max_length=20)

    def __str__(self):
        return self.shop_name

# User Profile Extension
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # The 'cart' field here should ideally link to a Cart model instance
    # that is associated with this UserProfile, or directly to the User.
    # Given the Cart model below, linking directly to User in Cart is more common.
    # This field might be redundant if Cart has a OneToOneField to User.
    cart = models.OneToOneField('Cart', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

# Cart Model
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

# CartItem Model (moved here to be near Cart)
class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

    @property
    def subtotal(self):
        return self.quantity * self.product.pr_price


# Wishlist Model (updated to ManyToMany as per your input)
class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return f"Wishlist of {self.user.username}"

# Ordered Item Model
class OrderedItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of order

    def __str__(self):
        return f"{self.quantity} x {self.product.pr_name}"

    @property
    def item_total(self):
        return self.quantity * self.price

# Order Model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(OrderedItem) # Many-to-many relationship with OrderedItem
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

# Review Model
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5) # Assuming 1-5 rating
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.pr_name}"

# Payment Model
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"Payment {self.id} for Order {self.order.id}"
