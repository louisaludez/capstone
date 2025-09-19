from django.urls import path
from .views import *
urlpatterns = [
    path('',admin_home, name='admin_home'),
    path('home/forecast.json', admin_home_forecast_json, name='admin_home_forecast_json'),
    path('accounts/',admin_account,name='admin_accounts'),
    path("accounts/add-user/",add_user, name="add_user"),
    path("accounts/view-user/<int:user_id>/",view_user, name="view_user"),
    path("accounts/edit-user/<int:user_id>/", edit_user, name="edit_user"),
    path("accounts/delete-user/<int:user_id>/", delete_user, name="delete_user"),
    path('reports/', admin_reports, name='admin_reports'),
    path('messenger/', admin_messenger, name='admin_messenger'),
    path('reports/front-office/', admin_front_office_reports, name='admin_front_office_reports'),
    path('reports/cafe/', admin_cafe_reports, name='admin_cafe_reports'),
    path('reports/laundry/', admin_laundry_reports, name='admin_laundry_reports'),
    path('reports/housekeeping/', admin_housekeeping_reports, name='admin_housekeeping_reports'),
    path('reports/speech/', admin_speech_reports, name='admin_speech_reports'),
    path('reports/mcq/', admin_mcq_reports, name='admin_mcq_reports'),
    path('training/', admin_training, name='admin_training'),
   
    path('activity-materials/add-activity-mcq/', add_activity_mcq, name='add_activity_mcq'),
    path('activity-materials/add-activity-speech/', add_activity_speech, name='add_activity_speech'),
    path('activity-materials/view-mcq-activity/', view_mcq_activity, name='view_mcq_activity'),
    path('activity-materials/view-speech-activity/', view_speech_activity, name='view_speech_activity'),
    path('activity-materials/save/', save_activities, name='save_activities'),
    path('activity-materials/delete-items/', delete_activity_items, name='delete_activity_items'),
    path('addmt-speech-to-text/', addmt_speech_to_text, name='addmt_speech_to_text'),
    path('addmt-mcq/', addmt_mcq, name='addmt_mcq')
]