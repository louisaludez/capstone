from django.db import models
from staff.models import Room, Reservation

class BaseServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='%(class)s_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='%(class)s_requests')
    service_type = models.CharField(max_length=50)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.room} - {self.customer.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"

class RoomServiceLaundryRequest(BaseServiceRequest):
    SERVICE_TYPE_CHOICES = [
        ('wash', 'Wash'),
        ('wash_fold', 'Wash and Fold'),
        ('dry_clean', 'Dry Cleaning'),
        ('iron', 'Iron Only'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    special_instructions = models.TextField(blank=True)

class RoomServiceCafeRequest(BaseServiceRequest):
    SERVICE_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('coffee', 'Coffee'),
        ('tea', 'Tea'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    items = models.JSONField(help_text="List of ordered items with quantities")
    delivery_time = models.DateTimeField()
    special_instructions = models.TextField(blank=True)

class RoomServiceHousekeepingRequest(BaseServiceRequest):
    SERVICE_TYPE_CHOICES = [
        ('cleaning', 'Cleaning'),
        ('towel_replacement', 'Towel Replacement'),
        ('linen_change', 'Linen Change'),
        ('amenities', 'Amenities Restock'),
        ('deep_cleaning', 'Deep Cleaning'),
    ]

    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    special_instructions = models.TextField(blank=True)