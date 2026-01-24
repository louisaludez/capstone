# messaging/models.py
from django.db import models
from django.conf import settings  # 👈 this is the key part

class Message(models.Model):
    sender_role = models.CharField(max_length=30, blank=True)
    receiver_role = models.CharField(max_length=30, blank=True)
    sender_service = models.CharField(max_length=30, blank=True, help_text="Service/app context where message was sent from (e.g., 'Room Service', 'Cafe')")
    conversation_room = models.CharField(max_length=100, blank=True, db_index=True, help_text="Room identifier for this conversation (e.g., 'chat_Admin_Cafe')")
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sender_id = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"From {self.sender_role} to {self.receiver_role}: {self.subject}"
