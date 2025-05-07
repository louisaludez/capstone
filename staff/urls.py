from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeStaff"),
    path("message/",views.message,name="MessageStaff"),
    path("check-in",views.check_in,name="check_in"),
]