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
    path('api/occupancy-forecast/', views.occupancy_forecast, name='occupancy_forecast'),
    path("training/mcq/", views.mcq_page, name="mcq_page"),
    path("training/speech-to-text/", views.speech_to_text_page, name="speech_to_text_page"),
    path("training/speech-to-text/add/", views.add_speech_to_text_activity, name="add_speech_to_text_activity"),
    path("training/mcq/add/", views.add_mcq_activity, name="add_mcq_activity"),
    path("training/mcq/delete/<int:activity_id>/", views.delete_mcq_activity, name="delete_mcq_activity"),
    path("training/mcq/edit/<int:activity_id>/", views.edit_mcq_activity, name="edit_mcq_activity"),
    path("training/mcq/simulate/<int:activity_id>/", views.simulate_mcq_activity, name="simulate_mcq_activity"),
    path("training/speech-to-text/delete/<int:activity_id>/", views.delete_speech_to_text_activity, name="delete_speech_to_text_activity"),
    path("training/speech-to-text/edit/<int:activity_id>/", views.edit_speech_to_text_activity, name="edit_speech_to_text_activity"),
    path("training/speech-to-text/simulate/<int:activity_id>/", views.simulate_speech_to_text_activity, name="simulate_speech_to_text_activity"),
]
