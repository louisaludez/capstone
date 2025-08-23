from django.db import models

class Ffsdf(models.Model):
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