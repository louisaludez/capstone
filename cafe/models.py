from django.db import models
from django.conf import settings
from staff.models import Room, Reservation
from django.utils import timezone

class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('pasta', 'Pasta'),
        ('pastry', 'Pastry'),
        ('hot_drinks', 'Hot Drinks'),
        ('cold_drinks', 'Cold Drinks'),
        ('sandwich', 'Sandwich'),
        ('salad', 'Salad'),
        ('dessert', 'Dessert'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_items/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.get_category_display()}"

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash Payment'),
        ('room', 'Charge to Room'),
        ('credit_card', 'Credit Card'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # Order Information
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='cafe_orders', null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # Order Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    cash_tendered = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: CAF-YYYYMMDD-XXXX
            date_prefix = self.created_at.strftime('%Y%m%d')
            last_order = Order.objects.filter(
                order_number__startswith=f'CAF-{date_prefix}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.order_number = f'CAF-{date_prefix}-{new_number:04d}'
        
        if self.status == 'delivered' and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)

    def total_amount(self):
        return sum(item.subtotal() for item in self.items.all())

    def __str__(self):
        return f"Order #{self.order_number} - {self.customer.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = models.TextField(blank=True)

    def subtotal(self):
        return self.quantity * self.price_at_time

    def save(self, *args, **kwargs):
        if not self.price_at_time:
            self.price_at_time = self.menu_item.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Order Status History'

    def __str__(self):
        return f"{self.order.order_number} - {self.status} at {self.created_at}"
