from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from globals import decorator
from django.contrib import messages
from datetime import datetime, date
from django.utils import timezone
from django.db.models import Q
from chat.models import Message
from .models import *
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator
@decorator.role_required('personnel')
def home(request):
    guest = Guest.objects.all()
    booking = Booking.objects.all() 
    payment = Payment.objects.all()

    return render(request, "staff/home.html", {
        
       'guest': guest,
       'booking': booking,
       'payment': payment,
       'today': date.today().strftime('%Y-%m-%d')          
        
    })

def message(request):
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        Q(sender_role=user_role, receiver_role=receiver_role) |
        Q(sender_role=receiver_role, receiver_role=user_role)
    ).order_by('created_at')
    return render(request, "staff/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@decorator.role_required('personnel')
def check_in(request):
    if request.method == 'POST':
        # You'll plug in Guest, Booking, Payment creation here
        messages.success(request, "Check-in functionality is under development.")
        return redirect('HomeStaff')
    
    return render(request, "staff/check_in.html", {
        'available_rooms': Room.objects.filter(status='available'),
        'today': date.today().strftime('%Y-%m-%d')
    })

@decorator.role_required('personnel')
def check_out(request, booking_id):
    # Booking checkout logic goes here
    messages.success(request, "Check-out functionality is under development.")
    return redirect('view_reservations')

@decorator.role_required('personnel')
def view_reservations(request):
    selected_date = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    # Replace this with your Booking model filtering
    bookings = []

    return render(request, "staff/view_reservations.html", {
        'reservations': bookings,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'today': date.today().strftime('%Y-%m-%d')
    })

@decorator.role_required('personnel')
def book_room(request):
    if request.method == 'POST':
        try:
            print("Booking request received")
            for key, value in request.POST.items():
                print(f"{key}: {value}")

            # Create guest
            guest = Guest.objects.create(
                name=request.POST.get('guest_name'),
                address=request.POST.get('guest_address'),
                zip_code=request.POST.get('guest_zip_code'),
                email=request.POST.get('guest_email'),
                date_of_birth=request.POST.get('guest_birth')
            )

            # Create booking
            booking = Booking.objects.create(
                guest=guest,
                check_in_date=request.POST.get('check_in'),
                check_out_date=request.POST.get('check_out'),
                room=request.POST.get('room'),
                total_of_guests=request.POST.get('total_guests'),
                num_of_adults=request.POST.get('adults'),
                num_of_children=request.POST.get('children'),
            )

            # Create payment
            Payment.objects.create(
                booking=booking,
                method=request.POST.get('payment_method'),
                card_number=request.POST.get('card_number'),
                exp_date=request.POST.get('exp_date'),
                cvc_code=request.POST.get('cvv'),
                billing_address=request.POST.get('billing_address'),
                total_balance=Decimal(request.POST.get('current_balance') or 0)
            )

            return JsonResponse({'success': True, 'message': 'Room successfully booked!'}, status=200)

        except Exception as e:
            print(f"Error booking room: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)


def getGuest(request, guest_id):
    if request.method == 'GET':
     print(f"Fetching guest with ID: {guest_id}")
     try:
        guest = Guest.objects.get(id=guest_id)
        data = {
            'name': guest.name,
            'address': guest.address,
            'zip_code': guest.zip_code,
            'email': guest.email,
            'date_of_birth': guest.date_of_birth.strftime('%Y-%m-%d'),
        }
        print(f"Guest data: {data}")
        return JsonResponse(data)
     except Guest.DoesNotExist:
        return JsonResponse({'error': 'Guest not found'}, status=404)


def get_reservations_ajax(request):
    page_number = request.GET.get("page", 1)

    # Get all bookings, newest first
    bookings = Booking.objects.select_related("guest").order_by("-booking_date")

    # Paginate bookings (10 per page)
    paginator = Paginator(bookings, 5)
    page = paginator.get_page(page_number)

    # Prepare JSON-friendly data
    data = [
        {
            "ref": f"{b.id:05d}",  # Padded ID like 00001
            "name": b.guest.name,
            "service": "Reservation",  # Static label
            "reservation_date": b.booking_date.strftime("%m/%d/%Y"),
            "checkin_date": b.check_in_date.strftime("%m/%d/%Y"),
            "timein": "9:00AM",  # Optional: Replace if you have a real field
            "status": b.status,
        }
        for b in page.object_list
    ]

    return JsonResponse({
        "reservations": data,
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "num_pages": paginator.num_pages,
        "current_page": page.number,
    })
    