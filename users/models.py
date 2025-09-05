from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Additional student-related fields
    course = models.CharField(max_length=100, blank=True, null=True)
    set = models.CharField(max_length=50, blank=True, null=True)
    year_level = models.PositiveSmallIntegerField(blank=True, null=True)
    
    # Additional fields for MCQ activities
    section = models.CharField(max_length=50, blank=True, null=True, help_text="Student section (e.g., 3A, 2B)")
    middle_initial = models.CharField(max_length=5, blank=True, null=True, help_text="Middle initial")
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
    
    def get_participant_info(self):
        """Generate participant info string for MCQ activities"""
        parts = []
        if self.last_name:
            parts.append(self.last_name)
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_initial:
            parts.append(self.middle_initial)
        
        name_part = ', '.join(parts) if parts else self.username
        
        # Add course and section info
        course_info = []
        if self.course:
            course_info.append(self.course)
        if self.year_level:
            course_info.append(str(self.year_level))
        if self.section:
            course_info.append(self.section)
        
        if course_info:
            return f"{name_part}, {' '.join(course_info)}"
        return name_part
