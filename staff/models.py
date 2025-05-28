from django.db import models

# Create your models here.
class Room(models.Model):
    ROOM_STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
        ('cleaning', 'Cleaning'),
    ]
    
    ROOM_TYPE_CHOICES = [
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('suite', 'Suite'),
        ('presidential', 'Presidential Suite'),
    ]

    room_number = models.IntegerField(unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=ROOM_STATUS_CHOICES, default='available')
    floor = models.IntegerField()
    capacity = models.PositiveIntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room_number']

    def __str__(self):
        return f"Room {self.room_number} - {self.get_room_type_display()}"

class Reservation(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    # Guest Information
    customer_name = models.CharField(max_length=100)
    customer_address = models.CharField(max_length=200)
    customer_zipCode = models.CharField(max_length=20)
    customer_dateOfBirth = models.DateField()
    customer_email = models.EmailField()

    # Booking Information
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reservations')
    number_of_guests = models.PositiveSmallIntegerField()
    special_requests = models.TextField(blank=True)
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    total_nights = models.PositiveIntegerField(editable=False)

    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    credit_card_number = models.CharField(max_length=20, blank=True, null=True)
    credit_card_expiry = models.DateField(blank=True, null=True)
    cvc_code = models.CharField(max_length=3, blank=True, null=True)
    billing_address = models.CharField(max_length=200, blank=True, null=True)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    # Status and Timestamps
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Calculate total nights
        if self.checkin_date and self.checkout_date:
            self.total_nights = (self.checkout_date - self.checkin_date).days
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - Room {self.room.room_number} ({self.checkin_date} → {self.checkout_date})"
