from django.urls import path
from .views.staff_views import staff_laundry_home, staff_laundry_messages, staff_laundry_orders, create_laundry_order
from .views.supervisor_views import supervisor_laundry_home, supervisor_laundry_messages, supervisor_laundry_reports, send_message_view


urlpatterns = [
    path('staff/', staff_laundry_home, name='staff_laundry_home'),
    path('staff/messages', staff_laundry_messages, name='staff_laundry_messages'),
    path('staff/orders', staff_laundry_orders, name='staff_laundry_orders'),
    path('staff/create-order/', create_laundry_order, name='create_laundry_order'),
    path('supervisor/', supervisor_laundry_home, name='supervisor_laundry_home'),
    path('supervisor/messages', supervisor_laundry_messages, name='supervisor_laundry_messages'),
    path('supervisor/orders', supervisor_laundry_reports, name='supervisor_laundry_reports'),
    path('supervisor/messages/chat', send_message_view, name='send_message'),
    

]
