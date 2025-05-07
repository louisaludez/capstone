from django.db import models

# Create your models here.
class Room(models.Model):
    room_number = models.IntegerField()
    status = models.CharField(max_length=100)
    

    def __str__(self):
        return str(self.room_number)