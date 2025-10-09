from django.urls import path
from .views import RegisterView
from . import views
urlpatterns = [
     path('signup/', RegisterView.as_view(), name='signup'),
     path('login/',views.login, name="login"),
     path('logout/',views.logout_view, name="logout"),
     path('super-admin-portal/', views.super_admin_portal, name='super_admin_portal'),
]
