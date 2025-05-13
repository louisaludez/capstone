from django.db import models
from staff.models import Room
from staff.models import Reservation
class LaundryOrder(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Pay Cash'),
        ('ROOM', 'Charge to Room'),
    ]

    # If you already have a Customer or Reservation model you want to link to,
    # swap these out for ForeignKey fields.
    customer_name    = models.CharField(max_length=100)
    room             = models.ForeignKey(
                         Room,
                         on_delete=models.CASCADE,
                         related_name='laundry_orders'
                       )

    service_type     = models.CharField(
                         max_length=50,
                         help_text="e.g. 'Wash & Fold', 'Dry Cleaning'"
                       )
    # Two mutually exclusive metrics—either hours or kilograms:
    hours            = models.DecimalField(
                         max_digits=5, decimal_places=2,
                         blank=True, null=True,
                         help_text="If billed by the hour"
                       )
    weight_kg        = models.DecimalField(
                         max_digits=6, decimal_places=2,
                         blank=True, null=True,
                         help_text="If billed by weight (kg)"
                       )

    item_type        = models.CharField(
                         max_length=50,
                         help_text="e.g. 'Shirts', 'Bedsheets', 'Socks'"
                       )
    quantity         = models.PositiveIntegerField(
                         help_text="Number of items"
                       )

    created_at       = models.DateTimeField(auto_now_add=True)
    notes            = models.TextField(
                         blank=True,
                         help_text="Add-ons, special requests, etc."
                       )

    payment_method   = models.CharField(
                         max_length=10,
                         choices=PAYMENT_METHODS,
                         default='CASH'
                       )

    def __str__(self):
        return (
            f"Laundry #{self.pk} – {self.customer_name} "
            f"(Room {self.room}) on {self.created_at:%Y-%m-%d %H:%M}"
        )

from datetime import date
from django.db import models, transaction

class Order(models.Model):
    # ——— Receipt Number ———
    receipt_no = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated as YYYYMMDD-#####"
    )

   
    customer = models.ForeignKey(
        Reservation,          
        on_delete=models.CASCADE,
        related_name='orders'
    )

    # ——— Service Type ———
    SERVICE_CHOICES = [
        ('WASH_FOLD',   'Wash and Fold'),
        ('DRY_CLEAN',   'Dry Cleaning'),
        ('IRON_ONLY',   'Iron Only'),
        # …add more as needed
    ]
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_CHOICES
    )

    # ——— Timestamps & Status ———
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('PENDING',     'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('FINISHED',    'Finished'),
        ('CANCELLED',   'Cancelled'),
    ]
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receipt_no']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        creating = self.pk is None
        # First save to get a PK and created_at timestamp
        super().save(*args, **kwargs)
        if creating and not self.receipt_no:
            # Build date prefix (YYYYMMDD) + zero-padded PK
            date_prefix = self.created_at.date().strftime("%Y%m%d")
            self.receipt_no = f"{date_prefix}-{self.pk:05d}"
            # Update only the receipt_no field to avoid recursion
            super().save(update_fields=['receipt_no'])

    def __str__(self):
        return f"{self.receipt_no} – {self.customer} ({self.get_status_display()})"
