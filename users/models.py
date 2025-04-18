from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('personnel', 'Personnel'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),

        # Supervisors
        ('supervisor_laundry', 'Supervisor - Laundry'),
        ('supervisor_concierge', 'Supervisor - Concierge'),
        ('supervisor_cafe', 'Supervisor - Cafe'),
        ('supervisor_restaurant', 'Supervisor - Restaurant'),
        ('supervisor_room_service', 'Supervisor - Room Service'),
        ('supervisor_fnb', 'Supervisor - Food and Beverages'),

        # Staff
        ('staff_laundry', 'Staff - Laundry'),
        ('staff_concierge', 'Staff - Concierge'),
        ('staff_cafe', 'Staff - Cafe'),
        ('staff_restaurant', 'Staff - Restaurant'),
        ('staff_room_service', 'Staff - Room Service'),
        ('staff_fnb', 'Staff - Food and Beverages'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='personnel')
