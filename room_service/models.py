from django.db import models
from staff.models import Room

class RoomServiceLaundryRequest(models.Model):
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
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_service_laundry_requests')
    reservation = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"

class RoomServiceCafeRequest(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('coffee', 'Coffee'),
        ('snack', 'Snack'),
        ('meal', 'Meal'),
    ]
    STATUS_CHOICES = RoomServiceLaundryRequest.STATUS_CHOICES
    customer = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_service_cafe_requests')
    reservation = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"

class RoomServiceHousekeepingRequest(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('cleaning', 'Cleaning'),
        ('towel_replacement', 'Towel Replacement'),
        ('linen_change', 'Linen Change'),
        ('amenities', 'Amenities Restock'),
    ]
    STATUS_CHOICES = RoomServiceLaundryRequest.STATUS_CHOICES
    customer = models.CharField(max_length=100)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='room_service_housekeeping_requests')
    reservation = models.CharField(max_length=100)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.reservation.customer_name} - {self.get_service_type_display()} ({self.get_status_display()})"