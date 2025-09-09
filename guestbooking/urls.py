from django.urls import path
from .views import *
urlpatterns = [
    path('', guest_booking_home, name='guest_booking_home'),
    path('results/', guest_booking_results, name='guest_booking_results'),
    path('book-reservation/', book_reservation, name='book_reservation'),
    path('payment/', payment, name='payment'),
    path('confirmation/', confirmation, name='confirmation'),
    path('save-reservation/', save_reservation, name='save_reservation'),
    # APIs used by staff check-in modal
    path('api/list-pending-reservations/', list_pending_reservations, name='list_pending_reservations'),
    path('api/checkin-reservation/', checkin_reservation, name='checkin_reservation'),
]