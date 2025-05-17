from django.db import models
from staff.models import Room

class ConciergeRequestTour(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('wash', 'Wash'),
        ('wash_fold', 'Wash and Fold'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In progress'),
        ('finished', 'Finished'),
    ]
    customer = models.CharField(max_length=100) 
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='concierge_requests_tour')
    reservation = models.CharField(max_length=100)

    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"

class ConciergeRequestCafe(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('coffee', 'Coffee'),
        ('snack', 'Snack'),
        ('meal', 'Meal'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In progress'),
        ('finished', 'Finished'),
    ]
    
    customer = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='concierge_requests_cafe')
    reservation = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"

class ConciergeRequestSpa(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('cleaning', 'Cleaning'),
        ('towel_replacement', 'Towel Replacement'),
        ('linen_change', 'Linen Change'),
        ('amenities', 'Amenities Restock'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In progress'),
        ('finished', 'Finished'),
    ]

    customer = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='concierge_spa_requests')
    reservation = models.CharField(max_length=100)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"