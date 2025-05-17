from django.urls import path
from . import views

app_name = 'room_service'

urlpatterns = [
    path('', views.dashboard, name='dashboardrm'),
    path('notifications/', views.notifications, name='notifications'),
    path('tasks/', views.tasks, name='tasks'),
    path('laundry/', views.room_service_laundry, name='room_service_laundry'),
    path('housekeeping/', views.room_service_housekeeping, name='room_service_housekeeping'),
    path('cafe/', views.room_service_cafe, name='room_service_cafe'),
] 