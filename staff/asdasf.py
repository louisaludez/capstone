from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from globals import decorator
from .models import *
from django.contrib import messages
from decimal import Decimal
from datetime import datetime, date
from django.db import models
from django.utils import timezone
from chat.models import Message
from django.db.models import Q
# Create your views here.
@decorator.role_required('staff')
def home(request):
    # Get selected date from request, default to today
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    # Get all rooms
    rooms = Room.objects.all()
    
    # Get rooms that have reservations for the selected date
    reserved_rooms = Reservation.objects.filter(
        Q(checkin_date__lte=selected_date, checkout_date__gt=selected_date),
        status__in=['confirmed', 'checked_in']
    ).values_list('room_id', flat=True)
    
    # Create a list to store room statuses
    room_statuses = {}
    
    # Update room status based on reservations
    for room in rooms:
        # Only update status if room is not under maintenance or cleaning
        if room.status not in ['maintenance', 'cleaning']:
            if room.id in reserved_rooms:
                room_statuses[room.id] = 'occupied'
            else:
                room_statuses[room.id] = 'available'
        else:
            room_statuses[room.id] = room.status
    
    # Count rooms by status
    available_rooms = sum(1 for status in room_statuses.values() if status == 'available')
    occupied_rooms = sum(1 for status in room_statuses.values() if status == 'occupied')
    under_maintenance_rooms = sum(1 for status in room_statuses.values() if status == 'maintenance')
    housekeeping_rooms = sum(1 for status in room_statuses.values() if status == 'cleaning')
    room_count = len(rooms)

    # Add status to each room object
    for room in rooms:
        room.status = room_statuses[room.id]

    # Get available rooms for the check-in modal
    available_rooms_list = Room.objects.filter(status='available')

    return render(request, "staff/home.html", {
        'rooms': rooms,
        'available_rooms_count': available_rooms,
        'occupied_rooms_count': occupied_rooms,
        'under_maintenance_rooms_count': under_maintenance_rooms,
        'housekeeping_rooms_count': housekeeping_rooms,
        'room_count': room_count,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'available_rooms': available_rooms_list
    })
def message(request):
    
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "staff/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@decorator.role_required('staff')
def check_in(request):
    if request.method == 'POST':
        try:
            # Get form data
            customer_name = request.POST.get('customer_name')
            customer_address = request.POST.get('customer_address')
            customer_zipCode = request.POST.get('customer_zipCode')
            customer_dateOfBirth = request.POST.get('customer_dateOfBirth')
            customer_email = request.POST.get('customer_email')
            checkin_date = request.POST.get('checkin_date')
            checkout_date = request.POST.get('checkout_date')
            room_number_id = int(request.POST.get('room_number'))
            special_requests = request.POST.get('special_requests')
            number_of_guests = request.POST.get('number_of_guests')
            payment_method = request.POST.get('payment_method')
            credit_card_number = request.POST.get('credit_card_number')
            credit_card_expiry = request.POST.get('credit_card_expiry')
            cvc_code = request.POST.get('cvc_code')
            billing_address = request.POST.get('billing_address')
            total_balance = request.POST.get('total_balance')

            # Validate dates
            checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()
            
            if checkin_date < date.today():
                messages.add_message(request, messages.ERROR, 'Check-in date cannot be in the past.')
                return redirect('check_in')
            
            if checkout_date <= checkin_date:
                messages.add_message(request, messages.ERROR, 'Check-out date must be after check-in date.')
                return redirect('check_in')

            # Get room and check availability
            room = get_object_or_404(Room, room_number=room_number_id)
            
            if room.status != 'available':
                messages.add_message(request, messages.ERROR, f'Room {room.room_number} is not available.')
                return redirect('check_in')

            # Check for overlapping reservations
            overlapping_reservations = Reservation.objects.filter(
                room=room,
                status__in=['confirmed', 'checked_in'],
                checkin_date__lt=checkout_date,
                checkout_date__gt=checkin_date
            )
            
            if overlapping_reservations.exists():
                messages.add_message(request, messages.ERROR, 'Room is already booked for these dates.')
                return redirect('check_in')

            # Create reservation
            reservation = Reservation.objects.create(
                customer_name=customer_name,
                customer_address=customer_address,
                customer_zipCode=customer_zipCode,
                customer_dateOfBirth=customer_dateOfBirth,
                customer_email=customer_email,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                room=room,
                special_requests=special_requests,
                number_of_guests=number_of_guests,
                payment_method=payment_method,
                credit_card_number=credit_card_number,
                credit_card_expiry=credit_card_expiry or None,
                cvc_code=cvc_code,
                billing_address=billing_address,
                total_balance=Decimal(total_balance) if total_balance else None,
                status='checked_in'
            )

            # Update room status
            room.status = 'occupied'
            room.save()

            messages.add_message(request, messages.SUCCESS, f'Guest {customer_name} checked in successfully to Room {room.room_number}.')
            return redirect('view_reservations')

        except Room.DoesNotExist:
            messages.add_message(request, messages.ERROR, 'Selected room does not exist.')
        except ValueError as e:
            messages.add_message(request, messages.ERROR, f'Invalid date format: {str(e)}')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'An error occurred: {str(e)}')

    # GET request - show available rooms
    available_rooms = Room.objects.filter(status='available')
    return render(request, "staff/check_in.html", {
        'available_rooms': available_rooms,
        'today': date.today().strftime('%Y-%m-%d')
    })

@decorator.role_required('staff')
def check_out(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        
        if reservation.status != 'checked_in':
            messages.add_message(request, messages.ERROR, 'This reservation is not checked in.')
            return redirect('view_reservations')

        # Update reservation status
        reservation.status = 'checked_out'
        reservation.save()

        # Update room status
        room = reservation.room
        room.status = 'available'
        room.save()

        messages.add_message(request, messages.SUCCESS, f'Guest {reservation.customer_name} checked out successfully from Room {room.room_number}.')
        return redirect('view_reservations')

    except Exception as e:
        messages.add_message(request, messages.ERROR, f'An error occurred during check-out: {str(e)}')
        return redirect('view_reservations')

@decorator.role_required('staff')
def view_reservations(request):
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    # Get reservations for the selected date
    reservations = Reservation.objects.filter(
        Q(checkin_date=selected_date) | Q(checkout_date=selected_date)
    ).order_by('checkin_date')

    return render(request, "staff/view_reservations.html", {
        'reservations': reservations,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'today': date.today().strftime('%Y-%m-%d')
    })

@decorator.role_required('staff')
def book_room(request):
    if request.method == 'POST':
        try:
            # Get form data
            customer_name = request.POST.get('customer_name')
            customer_address = request.POST.get('customer_address')
            customer_zipCode = request.POST.get('customer_zipCode')
            customer_dateOfBirth = request.POST.get('customer_dateOfBirth')
            customer_email = request.POST.get('customer_email')
            checkin_date = request.POST.get('checkin_date')
            checkout_date = request.POST.get('checkout_date')
            room_number_id = int(request.POST.get('room_number'))
            special_requests = request.POST.get('special_requests')
            number_of_guests = request.POST.get('number_of_guests')
            payment_method = request.POST.get('payment_method')
            credit_card_number = request.POST.get('credit_card_number')
            credit_card_expiry = request.POST.get('credit_card_expiry')
            cvc_code = request.POST.get('cvc_code')
            billing_address = request.POST.get('billing_address')
            total_balance = request.POST.get('total_balance')

            # Validate required fields
            required_fields = {
                'customer_name': 'Name',
                'customer_address': 'Address',
                'customer_zipCode': 'ZIP Code',
                'customer_dateOfBirth': 'Date of Birth',
                'customer_email': 'Email',
                'checkin_date': 'Check-in Date',
                'checkout_date': 'Check-out Date',
                'room_number': 'Room Number',
                'number_of_guests': 'Number of Guests',
                'payment_method': 'Payment Method',
                'billing_address': 'Billing Address',
                'total_balance': 'Total Balance'
            }

            for field, label in required_fields.items():
                if not request.POST.get(field):
                    messages.add_message(request, messages.ERROR, f'{label} is required.')
                    return redirect('HomeStaff')

            # Validate dates
            try:
                checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d').date()
                checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()
            except ValueError:
                messages.add_message(request, messages.ERROR, 'Invalid date format.')
                return redirect('HomeStaff')
            
            if checkin_date < date.today():
                messages.add_message(request, messages.ERROR, 'Check-in date cannot be in the past.')
                return redirect('HomeStaff')
            
            if checkout_date <= checkin_date:
                messages.add_message(request, messages.ERROR, 'Check-out date must be after check-in date.')
                return redirect('HomeStaff')

            # Get room and check availability
            try:
                room = Room.objects.get(room_number=room_number_id)
            except Room.DoesNotExist:
                messages.add_message(request, messages.ERROR, 'Selected room does not exist.')
                return redirect('HomeStaff')
            
            if room.status != 'available':
                messages.add_message(request, messages.ERROR, f'Room {room.room_number} is not available.')
                return redirect('HomeStaff')

            # Check for overlapping reservations
            overlapping_reservations = Reservation.objects.filter(
                room=room,
                status__in=['confirmed', 'checked_in'],
                checkin_date__lt=checkout_date,
                checkout_date__gt=checkin_date
            )
            
            if overlapping_reservations.exists():
                messages.add_message(request, messages.ERROR, 'Room is already booked for these dates.')
                return redirect('HomeStaff')

            # Create reservation
            try:
                # Determine if this is a check-in or booking based on the form submission
                is_checkin = request.POST.get('is_checkin', False)
                
                reservation = Reservation.objects.create(
                    customer_name=customer_name,
                    customer_address=customer_address,
                    customer_zipCode=customer_zipCode,
                    customer_dateOfBirth=customer_dateOfBirth,
                    customer_email=customer_email,
                    checkin_date=checkin_date,
                    checkout_date=checkout_date,
                    room=room,
                    special_requests=special_requests,
                    number_of_guests=number_of_guests,
                    payment_method=payment_method,
                    credit_card_number=credit_card_number,
                    credit_card_expiry=credit_card_expiry or None,
                    cvc_code=cvc_code,
                    billing_address=billing_address,
                    total_balance=Decimal(total_balance) if total_balance else None,
                    status='checked_in' if is_checkin else 'confirmed'  # Set status based on form type
                )
                
                # Update room status
                room.status = 'occupied'
                room.save()
                
                messages.add_message(request, messages.SUCCESS, f'Room {room.room_number} {"checked in" if is_checkin else "booked"} successfully for {customer_name}.')
            except Exception as e:
                messages.add_message(request, messages.ERROR, f'Error creating reservation: {str(e)}')
                return redirect('HomeStaff')

            return redirect('HomeStaff')

        except Exception as e:
            messages.add_message(request, messages.ERROR, f'An error occurred: {str(e)}')
            return redirect('HomeStaff')

    # GET request - show available rooms
    available_rooms = Room.objects.filter(status='available')
    return render(request, "staff/home.html", {
        'available_rooms': available_rooms,
        'today': date.today().strftime('%Y-%m-%d')
    })

