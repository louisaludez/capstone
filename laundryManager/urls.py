from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeLaundryManager"),
    path("/reports",views.reports,name="ReportsLaundryManager"),
    path("/messages",views.messages,name="MessagesLaundryManager"),
]