from django.urls import path
from .views import *
urlpatterns = [
    path('',admin_home, name='admin_home'),
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
]