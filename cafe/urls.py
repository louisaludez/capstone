from django.urls import path
from .views.staff_views import *
from .views.supervisor_views import *
urlpatterns = [
    path('staff/', staff_cafe_home, name='staff_cafe_home'),
    path('staff/messages', staff_cafe_messages, name='staff_cafe_messages'),
    path('staff/orders', staff_cafe_orders, name='staff_cafe_orders'),
    path('staff/place_order/', place_order, name='place_order'),
    path('supervisor/', supervisor_cafe_home, name='supervisor_cafe_home'),
    path('supervisor/messages', supervisor_cafe_messages, name='supervisor_cafe_messages'),
    path('supervisor/orders', supervisor_cafe_orders, name='supervisor_cafe_orders'),

]
