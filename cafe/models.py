from django.db import models

    # Create your models here.
class Items(models.Model):
    item_name = models.CharField(max_length=80)
    item_category = models.CharField(max_length=70)
    item_price = models.CharField(max_length=70)

    def __str__(self):
        return self.item_name