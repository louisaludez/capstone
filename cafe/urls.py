from django.urls import path
from .views.staff_views import *
from .views.supervisor_views import *
urlpatterns = [  
    path('staff/home/',staff_cafe_home, name='staff_cafe_home'),
 
]
