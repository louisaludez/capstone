from django.db import models
from django.conf import settings


class Activity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    scenario = models.TextField(blank=True)
    timer_seconds = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_adminnew_activities",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class ActivityItem(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="items")
    item_number = models.PositiveIntegerField(default=1)
    scenario = models.TextField(blank=True)
    timer_seconds = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["item_number"]
        unique_together = ['activity', 'item_number']

    def __str__(self) -> str:
        return f"{self.activity.title} - Item {self.item_number}"


class ActivityChoice(models.Model):
    activity_item = models.ForeignKey(ActivityItem, on_delete=models.CASCADE, related_name="choices", null=True, blank=True)
    # Keep old field temporarily for migration
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="old_choices", null=True, blank=True)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return f"{self.activity_item} - {self.text[:40]}"


class SpeechActivity(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    timer_seconds = models.PositiveIntegerField(default=0)
    reference_text = models.TextField(blank=True, help_text="Reference text for accuracy comparison")

    audio_file = models.FileField(upload_to='speech/audio/', null=True, blank=True)
    script_file = models.FileField(upload_to='speech/scripts/', null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_speech_activities",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

