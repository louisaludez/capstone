from django.urls import path
from .views import *
urlpatterns = [
    path('', housekeeping_home, name='housekeeping_home'),
    path('update_status/', update_status, name='update_status'),
    path('timeline/', timeline, name='timeline'),
]