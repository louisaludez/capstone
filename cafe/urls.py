from django.urls import path
from .views.staff import *

urlpatterns = [
    path('staff/home/', staff_cafe_home, name='staff_cafe_home'),
    path('search-items-ajax/',search_items_ajax, name='search_items_ajax'),
]