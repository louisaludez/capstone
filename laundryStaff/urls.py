from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="Home"),
    path("/orders",views.orders,name="Orders"),
    path("/messages",views.messages,name="Messages"),
]