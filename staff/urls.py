from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="HomeStaff"),
    path("message/",views.message,name="MessageStaff"),
    path("check-in/",views.check_in,name="check_in"),
    path("checkout/<int:reservation_id>/", views.check_out, name="check_out"),
    path("view-reservations/", views.view_reservations, name="view_reservations"),
    path("book-room/", views.book_room, name="book_room"),
]