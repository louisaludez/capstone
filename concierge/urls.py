from django.urls import path
from . import views

app_name = 'concierge'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('book-tours/', views.book_tours, name='book_tours'),
    path('book-reservations/', views.book_reservations, name='book_reservations'),
] 