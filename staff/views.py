from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from globals import decorator
from .models import *
# Create your views here.
@decorator.role_required('personnel')
def home(request):
    rooms = Room.objects.all()
    available_rooms = rooms.filter(status='available').count()
    occupied_rooms = rooms.filter(status='occupied').count()
    room_count = rooms.count()
    under_maintenance_rooms = rooms.filter(status='under_maintenance').count()
    housekeeping_rooms = rooms.filter(status='house_keeping').count()
    return render(request, "staff/home.html", {'rooms': rooms,'available_rooms_count': available_rooms,
                                               'occupied_rooms_count': occupied_rooms, 'under_maintenance_rooms_count': under_maintenance_rooms,
            'housekeeping_rooms_count': housekeeping_rooms
                                               ,'room_count': room_count})
def message(request):
    return render(request, "staff/messages.html")