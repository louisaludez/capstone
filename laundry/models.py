from django.db import models
from staff.models import Room, Reservation
from django.utils import timezone

class LaundryOrder(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('room', 'Charge to Room'),
        ('credit_card', 'Credit Card'),
    ]

    SERVICE_TYPE_CHOICES = [
        ('wash_fold', 'Wash and Fold'),
        ('dry_clean', 'Dry Cleaning'),
        ('iron', 'Iron Only'),
        ('express', 'Express Service'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Pickup'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # Order Information
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='laundry_orders')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='laundry_orders')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Item Details
    item_type = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    special_instructions = models.TextField(blank=True)

    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: LAU-YYYYMMDD-XXXX
            date_prefix = timezone.now().strftime('%Y%m%d')
            last_order = LaundryOrder.objects.filter(
                order_number__startswith=f'LAU-{date_prefix}'
            ).order_by('-order_number').first()
            
            if last_order:
                last_number = int(last_order.order_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.order_number = f'LAU-{date_prefix}-{new_number:04d}'
        
        if self.status == 'delivered' and not self.completed_at:
            self.completed_at = timezone.now()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer.customer_name} - {self.get_service_type_display()}"

class LaundryItem(models.Model):
    CATEGORY_CHOICES = [
        ('shirts', 'Shirts'),
        ('pants', 'Pants'),
        ('dresses', 'Dresses'),
        ('suits', 'Suits'),
        ('bedding', 'Bedding'),
        ('towels', 'Towels'),
        ('other', 'Other'),
    ]

    order = models.ForeignKey(LaundryOrder, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = models.TextField(blank=True)

    def subtotal(self):
        return self.quantity * self.price_per_item

    def __str__(self):
        return f"{self.quantity}x {self.get_category_display()} - {self.description}"
