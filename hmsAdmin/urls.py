from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeAdmin"),
    path("messages/",views.messages,name="MessagesAdmin"), 
    path("training/",views.training,name="TrainingAdmin"),
    path("analytics/",views.analytics,name="AnalyticsAdmin"),
    path("accountsAdmin/",views.accounts,name="AccountsAdmin"),
    path("accountsAdmin/add-user/", views.add_user, name="add_user"),
    path("accountsAdmin/view-user/<int:user_id>/", views.view_user, name="view_user"),
    path("accountsAdmin/edit-user/<int:user_id>/", views.edit_user, name="edit_user"),
    path("accountsAdmin/delete-user/<int:user_id>/", views.delete_user, name="delete_user"),
]
