from django.urls import path
from . import views

app_name = 'concierge'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('timeline/', views.timeline, name='timeline'),
    path('messenger/', views.messenger, name='messenger'),
    path('book-reservations/', views.book_reservations, name='book_reservations'),
    path('book-tours/', views.book_tours, name='book_tours'),
] 