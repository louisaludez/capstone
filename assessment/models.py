from django.db import models
from django.conf import settings


class McqAttempt(models.Model):
  STATUS_IN_PROGRESS = 'in_progress'
  STATUS_SUBMITTED = 'submitted'
  STATUS_ABANDONED = 'abandoned'
  STATUS_CHOICES = [
    (STATUS_IN_PROGRESS, 'In Progress'),
    (STATUS_SUBMITTED, 'Submitted'),
    (STATUS_ABANDONED, 'Abandoned'),
  ]

  activity = models.ForeignKey('adminNew.Activity', on_delete=models.CASCADE, related_name='mcq_attempts')
  participant_info = models.CharField(max_length=255)
  participant_key = models.CharField(max_length=255, db_index=True, default='', blank=True)

  attempt_number = models.PositiveIntegerField(default=1)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
  
  # Track current item in the activity
  current_item_number = models.PositiveIntegerField(default=1)

  started_at = models.DateTimeField(auto_now_add=True)
  finished_at = models.DateTimeField(null=True, blank=True)

  score = models.FloatField(null=True, blank=True)
  duration_seconds = models.PositiveIntegerField(default=0)

  # Optional: who triggered it if authenticated
  started_by = models.ForeignKey(getattr(settings, 'AUTH_USER_MODEL', 'auth.User'), null=True, blank=True, on_delete=models.SET_NULL)

  def __str__(self) -> str:
    return f"Attempt #{self.id} for {self.activity_id}: {self.participant_info[:40]}"


class McqAnswer(models.Model):
  attempt = models.ForeignKey(McqAttempt, on_delete=models.CASCADE, related_name='answers')
  activity_item = models.ForeignKey('adminNew.ActivityItem', on_delete=models.CASCADE, null=True, blank=True)
  choice = models.ForeignKey('adminNew.ActivityChoice', on_delete=models.CASCADE)
  is_correct = models.BooleanField(default=False)
  selected_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    indexes = [
      models.Index(fields=["attempt"]),
      models.Index(fields=["attempt", "activity_item"]),
    ]

  def __str__(self) -> str:
    return f"Answer for attempt {self.attempt_id}, item {self.activity_item.item_number}: {'correct' if self.is_correct else 'wrong'}"