from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeStaff"),
    path("message/",views.message,name="MessageStaff"),
     
    path("view-reservations/", views.view_reservations, name="view_reservations"),
    path("book-room/", views.book_room, name="book_room"),
    path("rooms/", views.room_list, name="room_list"),
    path("get-guest/<int:guest_id>/", views.getGuest, name="get_guest"),
    path("ajax/get-reservations/", views.get_reservations_ajax, name="get_reservations_ajax"),
    path("api/room-status/", views.room_status, name="room_status"),
    path("api/checkout/",views.perform_checkout, name="perform_checkout"),
    path("api/room-availability/", views.room_availability, name="room_availability"),
    path("statement-of-account/<int:guest_id>/", views.statement_of_account, name="statement_of_account"),
    path("statement-of-account/<int:guest_id>/pdf/", views.statement_of_account_pdf, name="statement_of_account_pdf"),
]