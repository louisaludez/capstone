from .views import mcq_home, speech_home, mcq_start, mcq_take, mcq_submit, mcq_save, mcq_prev, mcq_results, speech_start, speech_take, speech_submit, speech_save, speech_results
from django.urls import path
# Create your views here.
urlpatterns  = [
  path('mcq/',mcq_home, name='mcq_home'),
  path('speech/',speech_home, name='speech_home'),
  path('mcq/start/<int:activity_id>/', mcq_start, name='mcq_start'),
  path('mcq/take/<int:attempt_id>/', mcq_take, name='mcq_take'),
  path('mcq/prev/<int:attempt_id>/', mcq_prev, name='mcq_prev'),
  path('mcq/submit/<int:attempt_id>/', mcq_submit, name='mcq_submit'),
  path('mcq/save/<int:attempt_id>/', mcq_save, name='mcq_save'),
  path('mcq/results/<int:attempt_id>/', mcq_results, name='mcq_results'),
  path('speech/start/<int:activity_id>/', speech_start, name='speech_start'),
  path('speech/take/<int:attempt_id>/', speech_take, name='speech_take'),
  path('speech/submit/<int:attempt_id>/', speech_submit, name='speech_submit'),
  path('speech/save/<int:attempt_id>/', speech_save, name='speech_save'),
  path('speech/results/<int:attempt_id>/', speech_results, name='speech_results'),

]