from django.urls import path
from . import views
urlpatterns = [
    path('', views.housekeeping_home, name='housekeeping_home'),
]