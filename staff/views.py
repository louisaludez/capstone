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
from django.utils.dateparse import parse_date
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

            # Prepare guest base data
            guest_data = {
                'id': guest.id,
                'name': guest.name,
                'address': guest.address,
                'zip_code': guest.zip_code,
                'email': guest.email,
                'date_of_birth': guest.date_of_birth.strftime('%Y-%m-%d'),
                'billing': guest.billing,
                'room_service_billing': guest.room_service_billing,
                'laundry_billing': guest.laundry_billing,
                'cafe_billing': guest.cafe_billing,
                'excess_pax_billing': guest.excess_pax_billing,
                'additional_charge_billing': guest.additional_charge_billing,
                'created_at': guest.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'bookings': [],
                'check_in_date': None,
                'check_out_date': None,
                'room': None,
                'booking_status': None
            }

            bookings = Booking.objects.filter(guest=guest)

            for index, booking in enumerate(bookings):
                booking_data = {
                    'id': booking.id,
                    'booking_date': booking.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'check_in_date': booking.check_in_date.strftime('%Y-%m-%d'),
                    'check_out_date': booking.check_out_date.strftime('%Y-%m-%d'),
                    'room': booking.room,
                    'total_of_guests': booking.total_of_guests,
                    'num_of_adults': booking.num_of_adults,
                    'num_of_children': booking.num_of_children,
                    'status': booking.status,
                    'payment': None
                }

                try:
                    payment = Payment.objects.get(booking=booking)
                    booking_data['payment'] = {
                        'id': payment.id,
                        'method': payment.method,
                        'card_number': payment.card_number,
                        'exp_date': payment.exp_date,
                        'cvc_code': payment.cvc_code,
                        'billing_address': payment.billing_address,
                        'total_balance': float(payment.total_balance),
                        'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                except Payment.DoesNotExist:
                    booking_data['payment'] = None

                guest_data['bookings'].append(booking_data)

                # Flatten only the first booking into root-level fields
                if index == 0:
                    guest_data['check_in_date'] = booking.check_in_date.strftime('%Y-%m-%d')
                    guest_data['check_out_date'] = booking.check_out_date.strftime('%Y-%m-%d')
                    guest_data['room'] = booking.room
                    guest_data['booking_status'] = booking.status
                    guest_data['num_of_adults'] = booking.num_of_adults
                    guest_data['num_of_children'] = booking.num_of_children
                    guest_data['total_of_guests'] = booking.total_of_guests
                    guest_data['no_of_children_below_7'] = booking.no_of_children_below_7 

            print(f"Guest data: {guest_data}")
            return JsonResponse(guest_data, safe=False)

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
            "timein": "9:00AM", 
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



def room_status(request):
    """
    Expects ?date=YYYY-MM-DD
    Returns JSON with comprehensive room information
    """
    date_str = request.GET.get("date")
    print(f"[DEBUG] received date_str: {date_str!r}")

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        print(f"[DEBUG] parsed date: {d!r}")
    except (ValueError, TypeError) as e:
        print(f"[DEBUG] date parsing error: {e}")
        return JsonResponse({"error": "invalid or missing date"}, status=400)

    # Get occupied rooms for the selected date
    occupied_qs = Booking.objects.filter(
        check_in_date__lte=d,
        check_out_date__gte=d
    ).values_list("room", flat=True)

    occupied_rooms = list(occupied_qs)
    occupied_rooms = [
        f"R{room}" if not str(room).startswith("R") else str(room)
        for room in occupied_rooms
    ]

    # Calculate actual total rooms based on what exists in the system
    # Based on your template, you have rooms R1-R12 (12 rooms total)
    total_rooms = 12
    
    # Count rooms by type based on your actual room layout
    # Adjust these ranges based on your actual room numbering
    room_types = {
        'deluxe': 4,      # R1, R2, R3, R4
        'family': 4,      # R5, R6, R7, R8  
        'standard': 4     # R9, R10, R11, R12
    }
    
    # Count occupied rooms by type (adjust ranges based on your actual room layout)
    occupied_by_type = {
        'deluxe': len([r for r in occupied_rooms if r in ['R1', 'R2', 'R3', 'R4']]),
        'family': len([r for r in occupied_rooms if r in ['R5', 'R6', 'R7', 'R8']]),
        'standard': len([r for r in occupied_rooms if r in ['R9', 'R10', 'R11', 'R12']])
    }
    
    # Calculate other statuses
    vacant_count = total_rooms - len(occupied_rooms)
    maintenance_count = 2  # R6, R11 (based on your template)
    housekeeping_count = 0  # You can make this dynamic based on your housekeeping system
    reserved_count = 0  # You can make this dynamic based on your reservation system

    print(f"[DEBUG] occupied rooms for {d}: {occupied_rooms}")
    print(f"[DEBUG] room counts: total={total_rooms}, vacant={vacant_count}, occupied={len(occupied_rooms)}, maintenance={maintenance_count}")

    return JsonResponse({
        "occupied": occupied_rooms,
        "room_info": {
            "total": total_rooms,
            "vacant": vacant_count,
            "occupied": len(occupied_rooms),
            "maintenance": maintenance_count,
            "housekeeping": housekeeping_count,
            "reserved": reserved_count
        },
        "rooms_occupied": {
            "deluxe": occupied_by_type['deluxe'],
            "family": occupied_by_type['family'],
            "standard": occupied_by_type['standard']
        }
    })




def perform_checkout(request):
    if request.method == 'POST':
        print("=== Starting CHECKOUT process ===")
        print("Incoming POST data:", request.POST)

        try:
            guest_id = request.POST.get('guest_id')
            print("Guest ID:", guest_id)
            guest = Guest.objects.get(id=guest_id)
            print("Fetched Guest:", guest)

            # Get most recent booking
            booking = Booking.objects.filter(guest=guest).order_by('-booking_date').first()
            print("Latest Booking:", booking)
            if not booking:
                print("No active booking found.")
                return JsonResponse({'success': False, 'message': 'No active booking found for this guest.'}, status=404)

            # Dates
            check_in_raw = request.POST.get('check_in')
            check_out_raw = request.POST.get('check_out')
            print("Check-in:", check_in_raw, "Check-out:", check_out_raw)

            if not check_in_raw or not check_out_raw:
                print("Missing check-in or check-out date.")
                return JsonResponse({'success': False, 'message': 'Missing check-in or check-out date.'}, status=400)

            try:
                booking.check_in_date = parse_date(str(check_in_raw))
                booking.check_out_date = parse_date(str(check_out_raw))
                print("Parsed check-in date:", booking.check_in_date)
                print("Parsed check-out date:", booking.check_out_date)
            except Exception as date_error:
                print("Date parsing error:", date_error)
                return JsonResponse({'success': False, 'message': f"Date parsing error: {date_error}"}, status=400)

            # Booking details
            booking.room = request.POST.get('room')
            booking.total_of_guests = int(request.POST.get('total_guests') or 0)
            booking.num_of_adults = int(request.POST.get('adults') or 0)
            booking.num_of_children = int(request.POST.get('children') or 0)
            booking.no_of_children_below_7 = int(request.POST.get('below_7') or 0)
            booking.status = 'Checked-out'
            booking.save()
            print("Booking updated:", booking)

            # Guest billing
            guest.billing = request.POST.get('room_charges') or '0'
            guest.room_service_billing = request.POST.get('room_service') or '0'
            guest.laundry_billing = request.POST.get('laundry') or '0'
            guest.cafe_billing = request.POST.get('cafe') or '0'
            guest.excess_pax_billing = request.POST.get('excess_pax') or '0'
            guest.additional_charge_billing = request.POST.get('additional_charges') or '0'
            guest.save()
            print("Guest billing updated:", {
                'billing': guest.billing,
                'room_service_billing': guest.room_service_billing,
                'laundry_billing': guest.laundry_billing,
                'cafe_billing': guest.cafe_billing,
                'excess_pax_billing': guest.excess_pax_billing,
                'additional_charge_billing': guest.additional_charge_billing,
            })

            # Payment
            payment, created = Payment.objects.get_or_create(booking=booking)
            payment.method = request.POST.get('payment_method')
            payment.card_number = request.POST.get('card_number')
            payment.exp_date = request.POST.get('exp_date')
            payment.cvc_code = request.POST.get('cvv')
            payment.billing_address = request.POST.get('billing_address')
            payment.total_balance = Decimal(request.POST.get('balance') or 0)
            print('total balance : ' + str(payment.total_balance))
            payment.save()
            print("Payment saved:", {
                'method': payment.method,
                'card_number': payment.card_number,
                'exp_date': payment.exp_date,
                'cvc_code': payment.cvc_code,
                'billing_address': payment.billing_address,
                'total_balance': payment.total_balance,
            })

            print("=== CHECKOUT SUCCESSFUL ===")
            return JsonResponse({'success': True, 'message': 'Guest successfully checked out.'}, status=200)

        except Guest.DoesNotExist:
            print("Error: Guest not found.")
            return JsonResponse({'success': False, 'message': 'Guest not found.'}, status=404)

        except Exception as e:
            print("Unexpected error during checkout:", e)
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    print("Invalid request method (not POST).")
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)