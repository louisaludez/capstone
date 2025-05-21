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
     
        
       

        # Staff
        ('staff_laundry', 'Staff - Laundry'),
        ('staff_concierge', 'Staff - Concierge'),
        ('staff_cafe', 'Staff - Cafe'),
      
        ('staff_room_service', 'Staff - Room Service'),
 
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='personnel')
