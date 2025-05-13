from django.db import models

# Create your models here.
class Room(models.Model):
    room_number = models.IntegerField()
    status = models.CharField(max_length=100)
    

    def __str__(self):
        return str(self.room_number)
class Reservation(models.Model):
    # guest info
    customer_name         = models.CharField(max_length=100)
    customer_address      = models.CharField(max_length=200)
    customer_zipCode      = models.CharField(max_length=20)
    customer_dateOfBirth  = models.DateField()
    customer_email        = models.EmailField()

    # booking info
    room                  = models.ForeignKey(Room, on_delete=models.CASCADE)
    room_type             = models.CharField(max_length=100)
    number_of_guests      = models.PositiveSmallIntegerField()
    special_requests      = models.TextField(blank=True)

    checkin_date          = models.DateField()
    checkout_date         = models.DateField()

    # payment info
    payment_method        = models.CharField(max_length=100)
    credit_card_number    = models.CharField(max_length=20, blank=True, null=True)
    credit_card_expiry    = models.DateField(blank=True, null=True)
    cvc_code              = models.CharField(max_length=3, blank=True, null=True)
    billing_address       = models.CharField(max_length=200, blank=True, null=True)
    total_balance         = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.customer_name} ({self.checkin_date} → {self.checkout_date})"
