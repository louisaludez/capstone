from django.db import models
from django.conf import settings
from staff.models import Room

class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    PAYMENT_CHOICES = [
        ('cash', 'Cash Payment'),
        ('room', 'Charge to Room'),
    ]
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    cash_tendered = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def total_amount(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name}"

class OrderItem(models.Model):
    CATEGORY_CHOICES = [
        ('pasta', 'Pasta'),
        ('pastry', 'Pastry'),
        ('hot_drinks', 'Hot Drinks'),
        ('cold_drinks', 'Cold Drinks'),
        ('sandwich', 'Sandwich'),
    ]

    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.name}"
