from django.db import models

# Create your models here.
class Chat(models.Model):
    sender = models.CharField(max_length=50)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=True)

    