from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeAdmin"),
    path("messages/",views.messages,name="MessagesAdmin"), 
    path("training/",views.training,name="TrainingAdmin"),
    path("analytics/",views.analytics,name="AnalyticsAdmin"),
    path("accountsAdmin/",views.accounts,name="AccountsAdmin"),

]
