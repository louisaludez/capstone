from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from globals import decorator
from .models import *
from django.contrib import messages
from decimal import Decimal
from datetime import datetime

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


def check_in(request):
    if request.method == 'POST':
        print(request)
        customer_name = request.POST.get('customer_name')
        customer_address = request.POST.get('customer_address')
        customer_zipCode = request.POST.get('customer_zipCode')
        customer_dateOfBirth = request.POST.get('customer_dateOfBirth')
        customer_email = request.POST.get('customer_email')
        checkin_date = request.POST.get('checkin_date')
        checkout_date = request.POST.get('checkout_date')
        room_type = request.POST.get('room_type')
        room_number_id = int(request.POST.get('room_number'))
        special_requests = request.POST.get('special_requests')
        number_of_guests = request.POST.get('number_of_guests')
        payment_method = request.POST.get('payment_method')
        credit_card_number = request.POST.get('credit_card_number')
        credit_card_expiry = request.POST.get('credit_card_expiry')
        cvc_code = request.POST.get('cvc_code')
        billing_address = request.POST.get('billing_address')
        total_balance = request.POST.get('total_balance')

        try:
            room = Room.objects.get(room_number=room_number_id)
            
            checkin = Reservation.objects.create(
                customer_name=customer_name,
                customer_address=customer_address,
                customer_zipCode=customer_zipCode,
                customer_dateOfBirth=customer_dateOfBirth,
                customer_email=customer_email,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                room_type=room_type,
                room_number=room,
                special_requests=special_requests,
                number_of_guests=number_of_guests,
                payment_method=payment_method,
                credit_card_number=credit_card_number,
                credit_card_expiry=credit_card_expiry or None,
                cvc_code=cvc_code,
                billing_address=billing_address,
                total_balance=Decimal(total_balance) if total_balance else None,
            )
            Room.objects.filter(room_number=room_number_id).update(status='occupied')
            messages.success(request, 'Guest checked in successfully.')
            return redirect('HomeStaff') 

        except Room.DoesNotExist:
            messages.error(request, 'Selected room does not exist.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')

        rooms = Room.objects.all()
        available_rooms = rooms.filter(status='available').count()
        occupied_rooms = rooms.filter(status='occupied').count()
        room_count = rooms.count()
        under_maintenance_rooms = rooms.filter(status='under_maintenance').count()
        housekeeping_rooms = rooms.filter(status='house_keeping').count()
    return render(request, "staff/home.html", {'rooms': rooms,
                                               'available_rooms_count': available_rooms,
                                               'occupied_rooms_count': occupied_rooms, 
                                               'under_maintenance_rooms_count': under_maintenance_rooms,
                                               'housekeeping_rooms_count': housekeeping_rooms,
                                               'room_count': room_count})  

