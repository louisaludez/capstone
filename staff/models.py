from django.db import models

class Guest(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField()
    mobile = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField() 
  #  billing = models.TextField(blank=True, null=True, default='1000')
    billing = models.TextField(blank=True, null=True, default='1000')
    room_service_billing = models.TextField(blank=True, null=True, default='0')
    laundry_billing = models.TextField(blank=True, null=True, default='0')
    cafe_billing = models.TextField(blank=True, null=True, default='0')
    excess_pax_billing = models.TextField(blank=True, null=True, default='0')
    additional_charge_billing = models.TextField(blank=True, null=True, default='0')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPES = [
        ('standard', 'Standard'),
        ('family', 'Family'),
        ('deluxe', 'Deluxe'),
    ]
    
    ROOM_STATUS = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('cleaning', 'Being Cleaned'),
        ('reserved', 'Reserved'),
        ('out_of_order', 'Out of Order'),
    ]
    
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    status = models.CharField(max_length=20, choices=ROOM_STATUS, default='available')
    capacity = models.PositiveIntegerField(default=2)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    amenities = models.JSONField(default=dict, blank=True)
    is_accessible = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_ocean_view = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['room_number']
    
    def __str__(self):
        return f"Room {self.room_number} - {self.get_room_type_display()}"
    
    def is_available(self):
        return self.status == 'available'
    
    def get_current_booking(self):
        """Get the current active booking for this room"""
        return self.booking_set.filter(status='Checked-in').first()

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Checked-in', 'Checked-in'),
        ('Checked-out', 'Checked-out'),
        ('Cancelled', 'Cancelled'),
    ]
    
    SOURCE_CHOICES = [
        ('walkin', 'Walk-in'),
        ('reservation', 'Reservation'),
        ('checkin', 'Check-in'),
    ]
    
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room= models.CharField(max_length=50)  # Keep as CharField for now
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_of_guests =    models.PositiveIntegerField()
    num_of_adults = models.PositiveIntegerField()
    num_of_children = models.PositiveIntegerField(default=0)
    no_of_children_below_7 = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='reservation')

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