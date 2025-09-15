from django.db import models
from staff.models import Guest  # Link for room charges

class CafeCategory(models.Model):
    name = models.CharField(max_length=70)

    def __str__(self):
        return self.name


class CafeItem(models.Model):
    name = models.CharField(max_length=80)
    category = models.ForeignKey(CafeCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name


class CafeOrder(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash Cash Payment'),
        ('room', 'Charge to Room'),
        (
            'card', 'Card Payment'
        )
    ]
    SERVICE_CHOICES = [
        ('dine_in', 'Dine In'),
        ('take_out', 'Take Out'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('done', 'Done'),
    ]

    customer_name = models.CharField(max_length=100, blank=True, null=True)
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=100, choices=PAYMENT_CHOICES)
    service_type = models.CharField(max_length=100, choices=SERVICE_CHOICES)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    def __str__(self):
        return f"Order #{self.id}"


class CafeOrderItem(models.Model):
    order = models.ForeignKey(CafeOrder, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(CafeItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)  # Unit price
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # price * quantity

    def __str__(self):
        return f"{self.quantity}x {self.item.name}"
