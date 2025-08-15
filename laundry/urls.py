from django.urls import path
from .views import *


urlpatterns = [
    path('', staff_laundry_home, name='staff_laundry_home'),
    path('staff/<int:guest_id>',getGuest, name='get_guest'),
    path('messages/', staff_laundry_messages, name='staff_laundry_messages'),
    path('orders/', staff_laundry_orders, name='staff_laundry_orders'),
    path('orders/<int:order_id>/view/', view_laundry_order, name='view_laundry_order'),
    path('orders/<int:order_id>/edit/', edit_laundry_order, name='edit_laundry_order'),
    path('orders/<int:order_id>/delete/', delete_laundry_order, name='delete_laundry_order'),
    path('orders/<int:order_id>/status/', update_order_status, name='update_order_status'),
    path('staff/create-order/', create_laundry_order, name='create_laundry_order'),
    #path('supervisor/messages/chat', send_message_view, name='send_message'),
    

]
