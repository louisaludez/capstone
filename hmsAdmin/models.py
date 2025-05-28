from django.db import models

class SpeechToTextActivity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    audio_file = models.FileField(upload_to='speech_to_text/')
    created_at = models.DateTimeField(auto_now_add=True)

class MCQActivity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    scenario = models.TextField()
    timer = models.CharField(max_length=20, blank=True)
    choice1 = models.CharField(max_length=255)
    choice2 = models.CharField(max_length=255)
    choice3 = models.CharField(max_length=255)
    choice4 = models.CharField(max_length=255)
    action_block = models.BooleanField(default=False)
    action_reserve = models.BooleanField(default=False)
    action_cash_payment = models.BooleanField(default=False)
    action_customization = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
