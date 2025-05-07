from django.db import models

# Create your models here.
class Room(models.Model):
    room_number = models.IntegerField()
    status = models.CharField(max_length=100)
    

    def __str__(self):
        return str(self.room_number)
class Checkin(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_address = models.CharField(max_length=200)
    customer_zipCode = models.CharField(max_length=20)
    customer_dateOfBirth = models.DateField()
    customer_email = models.EmailField()
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    room_type = models.CharField(max_length=100)
    room_number = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='checkin_room')
    special_requests = models.TextField(blank=True, null=True)
    number_of_guests = models.IntegerField()
    payment_method= models.CharField(max_length=100)
    credit_card_number = models.CharField(max_length=20, blank=True, null=True)
    credit_card_expiry = models.DateField(blank=True, null=True)
    cvc_code = models.CharField(max_length=3, blank=True, null=True)
    billing_address = models.CharField(max_length=200, blank=True, null=True)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)





    def __str__(self):
        return f"{self.customer_name} - {self.room_number}"