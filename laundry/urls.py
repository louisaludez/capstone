from django.urls import path
from .views.staff_views import *
from .views.supervisor_views import *


urlpatterns = [
    path('staff/', staff_laundry_home, name='staff_laundry_home'),
    path('staff/messages',staff_laundry_messages,name='staff_laundry_messages'),
    path('staff/orders',staff_laundry_orders,name='staff_laundry_orders'),
    path('supervisor/', supervisor_laundry_home, name='supervisor_laundry_home'),
    path('supervisor/messages',supervisor_laundry_messages,name='supervisor_laundry_messages'),
    path('supervisor/orders',supervisor_laundry_reports,name='supervisor_laundry_reports'),
    path('supervisor/messages/chat', send_message_view, name='send_message'),
    

]
