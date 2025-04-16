from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeLaundryStaff"),
    path("/orders",views.orders,name="OrdersLaundryStaff"),
    path("/messages",views.messages,name="MessagesLaundryStaff"),
]