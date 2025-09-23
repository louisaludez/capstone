from django.urls import path
from .views import *
urlpatterns = [
    path('', housekeeping_home, name='housekeeping_home'),
    path('update_status/', update_status, name='update_status'),
    path('timeline/', timeline, name='timeline'),
    path('messenger/', messenger, name='housekeeping_messenger'),
    path('task/<int:task_id>/view/', view_task, name='view_task'),
    path('task/<int:task_id>/edit/', edit_task, name='edit_task'),
    path('task/<int:task_id>/delete/', delete_task, name='delete_task'),
]