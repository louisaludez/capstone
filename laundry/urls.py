from django.urls import path
from .views import *


urlpatterns = [
    path('', staff_laundry_home, name='staff_laundry_home'),
    path('staff/<int:guest_id>',getGuest, name='get_guest'),
    path('messages/', staff_laundry_messages, name='staff_laundry_messages'),
    path('orders/', staff_laundry_orders, name='staff_laundry_orders'),
    path('staff/create-order/', create_laundry_order, name='create_laundry_order'),
    #path('supervisor/messages/chat', send_message_view, name='send_message'),
    

]
