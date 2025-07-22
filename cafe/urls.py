from django.urls import path
from .views.staff import *

urlpatterns = [
    path('staff/home/', staff_cafe_home, name='staff_cafe_home'),
]