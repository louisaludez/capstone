from django.urls import path
from .views import send_message
app_name = 'chat'
urlpatterns = [
    path('send-message/', send_message, name='send_message'),
]
