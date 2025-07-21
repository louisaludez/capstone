from django.db import models

class Guest(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField()
    date_of_birth = models.DateField()
    billing = models.TextField(blank=True, null=True, default='1000')
    room_service_billing = models.TextField(blank=True, null=True, default='0')
    laundry_billing = models.TextField(blank=True, null=True, default='0')
    cafe_billing = models.TextField(blank=True, null=True, default='0')
    excess_pax_billing = models.TextField(blank=True, null=True, default='0')
    additional_charge_billing = models.TextField(blank=True, null=True, default='0')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Checked-in', 'Checked-in'),
        ('Cancelled', 'Cancelled'),
    ]
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    room = models.CharField(max_length=50)
    total_of_guests = models.PositiveIntegerField()
    num_of_adults = models.PositiveIntegerField()
    num_of_children = models.PositiveIntegerField(default=0)
    no_of_children_below_7 = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Booking for {self.guest.name} from {self.check_in_date} to {self.check_out_date}"
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('card', 'Card Payment'),
        ('cash', 'Cash'),
       
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    card_number = models.CharField(max_length=20, blank=True, null=True)
    exp_date = models.CharField(max_length=50, blank=True, null=True)
    cvc_code = models.CharField(max_length=4, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Payment for Booking {self.booking.id} - {self.method}"