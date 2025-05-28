from django.db import models
from staff.models import Room, Reservation

class BaseConciergeRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Request Information
    request_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='%(class)s_requests')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='%(class)s_requests')
    service_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Request Details
    date_time = models.DateTimeField()
    special_instructions = models.TextField(blank=True)
    assigned_to = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.request_number} - {self.customer.customer_name} - {self.get_service_type_display()}"

class ConciergeRequestTour(BaseConciergeRequest):
    SERVICE_TYPE_CHOICES = [
        ('city_tour', 'City Tour'),
        ('museum_tour', 'Museum Tour'),
        ('shopping_tour', 'Shopping Tour'),
        ('historical_tour', 'Historical Tour'),
        ('custom_tour', 'Custom Tour'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    number_of_guests = models.PositiveIntegerField()
    tour_date = models.DateField()
    tour_duration = models.DurationField()
    pickup_location = models.CharField(max_length=200)
    dropoff_location = models.CharField(max_length=200)
    tour_guide_required = models.BooleanField(default=True)
    transportation_required = models.BooleanField(default=True)

class ConciergeRequestCafe(BaseConciergeRequest):
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
    delivery_location = models.CharField(max_length=200)
    special_dietary_requirements = models.TextField(blank=True)

class ConciergeRequestSpa(BaseConciergeRequest):
    SERVICE_TYPE_CHOICES = [
        ('massage', 'Massage'),
        ('facial', 'Facial'),
        ('body_treatment', 'Body Treatment'),
        ('manicure', 'Manicure'),
        ('pedicure', 'Pedicure'),
        ('hair_treatment', 'Hair Treatment'),
    ]

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.DurationField()
    number_of_guests = models.PositiveIntegerField()
    special_requirements = models.TextField(blank=True)
    therapist_preference = models.CharField(max_length=100, blank=True)