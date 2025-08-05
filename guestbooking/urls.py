from django.urls import path
from .views import *
urlpatterns = [
    path('', guest_booking_home, name='guest_booking_home'),
]