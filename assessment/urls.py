from .views import *
from django.urls import path
# Create your views here.
urlpatterns  = [
  path('mcq/',mcq_home, name='mcq_home'),
  path('speech/',speech_home, name='speech_home')
]