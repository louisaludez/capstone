from django.db import models

# Create your models here.
class Housekeeping(models.Model):
    room_number = models.CharField(max_length=10)
    guest_name = models.CharField(max_length=100, blank=True, null=True)
    request_type = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room {self.room_number} - {self.status}"