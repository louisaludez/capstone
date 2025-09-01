from .views import mcq_home, speech_home, mcq_start, mcq_take, mcq_submit
from django.urls import path
# Create your views here.
urlpatterns  = [
  path('mcq/',mcq_home, name='mcq_home'),
  path('speech/',speech_home, name='speech_home'),
  path('mcq/start/<int:activity_id>/', mcq_start, name='mcq_start'),
  path('mcq/take/<int:attempt_id>/', mcq_take, name='mcq_take'),
  path('mcq/submit/<int:attempt_id>/', mcq_submit, name='mcq_submit'),

]