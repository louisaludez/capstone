from django.db import models
from staff.models import Guest, Booking

class LaundryTransaction(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('room', 'Charge to Room'),
    ]

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True)
    room_number = models.CharField(max_length=20)
    service_type = models.CharField(max_length=50)
    no_of_bags = models.PositiveIntegerField(default=1)
    specifications = models.TextField(blank=True, null=True)  # Detergent, Bleach, etc.
    date_time = models.DateTimeField()
    payment_method = models.CharField(max_length=255, choices=PAYMENT_METHODS)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest.name} - {self.service_type} - {self.payment_method.upper()}"

    def save(self, *args, **kwargs):
        # Auto-charge to guest billing if method is 'room'
        if self.payment_method == 'room':
            self.guest.billing = str(float(self.guest.billing or 0) + float(self.total_amount))
            self.guest.save()
        super().save(*args, **kwargs)
