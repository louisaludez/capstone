from urllib import request
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from globals import decorator
from django.contrib import messages
from datetime import datetime, date, time as dt_time
from django.utils import timezone
from django.db.models import Q
from chat.models import Message
from django.db import models
from users.models import CustomUser
from .models import *
from django.http import JsonResponse
from decimal import Decimal
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
import re
from datetime import timedelta
@decorator.role_required('staff', 'SUPER_ADMIN')
def home(request):
    # Only guests with at least one Checked-in booking should appear for checkout selection
    raw_guests = Guest.objects.filter(booking__status='Checked-in').distinct()
    guests = []

    for guest_obj in raw_guests:
        bookings_qs = guest_obj.booking_set.order_by('-booking_date')
        primary_booking = bookings_qs.filter(status='Checked-in').first() or bookings_qs.first()

        payment_record = None
        if primary_booking:
            try:
                payment_record = primary_booking.payment
            except Payment.DoesNotExist:
                payment_record = None

        # Map booking information
        guest_obj.check_in_date = primary_booking.check_in_date if primary_booking else None
        guest_obj.check_out_date = primary_booking.check_out_date if primary_booking else None
        guest_obj.room_type = primary_booking.room if primary_booking else ''
        guest_obj.total_guests = getattr(primary_booking, 'total_of_guests', '') if primary_booking else ''
        guest_obj.no_of_adults = getattr(primary_booking, 'num_of_adults', '') if primary_booking else ''
        guest_obj.no_of_children = getattr(primary_booking, 'num_of_children', '') if primary_booking else ''
        guest_obj.children_below_7 = getattr(primary_booking, 'no_of_children_below_7', '') if primary_booking else ''
        # Add booking source to identify walk-in vs reservation
        # Source can be 'walkin', 'reservation', or 'checkin'
        # 'checkin' means it was a reservation that was checked in
        # 'walkin' means it was a walk-in booking
        # 'reservation' means it's still a pending reservation
        booking_source = getattr(primary_booking, 'source', '') if primary_booking else ''
        guest_obj.booking_source = booking_source
        print(f"[home view] Guest {guest_obj.name}: booking_source = '{booking_source}'")

        # Map guest billing aliases for template compatibility
        guest_obj.room_service = getattr(guest_obj, 'room_service_billing', '') or ''
        guest_obj.laundry = getattr(guest_obj, 'laundry_billing', '') or ''
        guest_obj.cafe = getattr(guest_obj, 'cafe_billing', '') or ''
        guest_obj.excess_pax = getattr(guest_obj, 'excess_pax_billing', '') or ''
        guest_obj.additional_charges = getattr(guest_obj, 'additional_charge_billing', '') or ''

        # Map payment information
        if payment_record:
            guest_obj.payment_method = payment_record.method or ''
            guest_obj.billing_address = payment_record.billing_address or ''
            guest_obj.card_number = payment_record.card_number or ''
            guest_obj.card_exp = payment_record.exp_date or ''
            guest_obj.card_cvc = payment_record.cvc_code or ''
            guest_obj.total_balance = payment_record.total_balance or ''
        else:
            guest_obj.payment_method = ''
            guest_obj.billing_address = ''
            guest_obj.card_number = ''
            guest_obj.card_exp = ''
            guest_obj.card_cvc = ''
            guest_obj.total_balance = ''

        guests.append(guest_obj)

    booking = Booking.objects.all() 
    payment = Payment.objects.all()
    
    # Get all rooms for dynamic counts
    all_rooms = Room.objects.all().order_by('room_number')
    
    # Get individual rooms for specific room numbers (1-12)
    room_1 = Room.objects.filter(room_number='1').first()
    room_2 = Room.objects.filter(room_number='2').first()
    room_3 = Room.objects.filter(room_number='3').first()
    room_4 = Room.objects.filter(room_number='4').first()
    room_5 = Room.objects.filter(room_number='5').first()
    room_6 = Room.objects.filter(room_number='6').first()
    room_7 = Room.objects.filter(room_number='7').first()
    room_8 = Room.objects.filter(room_number='8').first()
    room_9 = Room.objects.filter(room_number='9').first()
    room_10 = Room.objects.filter(room_number='10').first()
    room_11 = Room.objects.filter(room_number='11').first()
    room_12 = Room.objects.filter(room_number='12').first()
    
    # Count rooms by status
    room_status_counts = {
        'available': all_rooms.filter(status='available').count(),
        'occupied': all_rooms.filter(status='occupied').count(),
        'maintenance': all_rooms.filter(status='maintenance').count(),
        'cleaning': all_rooms.filter(status='cleaning').count(),
        'reserved': all_rooms.filter(status='reserved').count(),
    }
    
    # Count rooms by type
    room_type_counts = {
        'deluxe': all_rooms.filter(room_type='deluxe').exclude(status='available').count(),
        'family': all_rooms.filter(room_type='family').exclude(status='available').count(),
        'standard': all_rooms.filter(room_type='standard').exclude(status='available').count(),
    }

    return render(request, "staff/home.html", {
        'guest': guests,
        'booking': booking,
        'payment': payment,
        'room_1': room_1,
        'room_2': room_2,
        'room_3': room_3,
        'room_4': room_4,
        'room_5': room_5,
        'room_6': room_6,
        'room_7': room_7,
        'room_8': room_8,
        'room_9': room_9,
        'room_10': room_10,
        'room_11': room_11,
        'room_12': room_12,
        'room_status_counts': room_status_counts,
        'room_type_counts': room_type_counts,
        'today': date.today().strftime('%Y-%m-%d')          
    })

def message(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')
    # Base on app service, not user role
    current_service = 'Personnel'

    # Deterministic room name with simplified roles
    def simplify_role(role):
        mapping = {
            'staff_personnel': 'Personnel', 'manager_personnel': 'Personnel', 'personnel': 'Personnel', 'staff': 'Personnel', 'manager': 'Personnel',
            'staff_concierge': 'Concierge', 'manager_concierge': 'Concierge',
            'staff_laundry': 'Laundry', 'manager_laundry': 'Laundry',
            'staff_cafe': 'Cafe', 'manager_cafe': 'Cafe',
            'staff_room_service': 'Room Service', 'manager_room_service': 'Room Service',
            'admin': 'Admin', 'Admin': 'Admin'
        }
        return mapping.get(role, role)

    simplified = sorted([simplify_role(current_service), simplify_role(receiver_role)])
    room_name = f"chat_{'_'.join([s.replace(' ', '_') for s in simplified])}"

    # Role groupings
    def get_related_roles(role):
        role_mappings = {
            'Personnel': ['staff_personnel', 'manager_personnel', 'Personnel', 'personnel', 'staff', 'manager'],
            'Concierge': ['staff_concierge', 'manager_concierge', 'Concierge'],
            'Laundry': ['staff_laundry', 'manager_laundry', 'Laundry'],
            'Cafe': ['staff_cafe', 'manager_cafe', 'Cafe'],
            'Room Service': ['staff_room_service', 'manager_room_service', 'Room Service'],
            'Admin': ['admin', 'Admin']
        }
        for general, specifics in role_mappings.items():
            if role in specifics:
                return specifics
        return role_mappings.get(role, [role])

    user_roles = get_related_roles(current_service)
    receiver_roles = get_related_roles(receiver_role)

    messages_qs = Message.objects.filter(
        (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles)) |
        (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    ).order_by('created_at')

    for msg in messages_qs:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"

    return render(request, "staff/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })



@decorator.role_required('staff', 'SUPER_ADMIN')
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

@decorator.role_required('staff', 'SUPER_ADMIN')
def book_room(request):
    if request.method == 'POST':
        try:
            print("[DEBUG] Received POST request for booking room")

            # Create guest
            print("[DEBUG] Creating guest")
            guest = Guest.objects.create(
                name=request.POST.get('guest_name'),
                address=request.POST.get('guest_address'),
                zip_code=request.POST.get('guest_zip_code'),
                email=request.POST.get('guest_email'),
                date_of_birth=request.POST.get('guest_birth')
            )
            print(f"[DEBUG] Guest created: {guest}")

            # Fetch room number and dates
            room_number = request.POST.get('room')
            check_in_date = request.POST.get('check_in')
            check_out_date = request.POST.get('check_out')
            print(f"[DEBUG] Room number: {room_number}, Check-in: {check_in_date}, Check-out: {check_out_date}")

            # Validate dates
            if not check_in_date or not check_out_date:
                print("[DEBUG] Missing check-in or check-out dates")
                return JsonResponse({'success': False, 'message': 'Check-in and check-out dates are required.'}, status=400)

            # Parse dates
            check_in_date = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out_date, '%Y-%m-%d').date()
            print(f"[DEBUG] Parsed dates - Check-in: {check_in_date}, Check-out: {check_out_date}")

            # Check if room is in housekeeping or under maintenance
            from housekeeping.models import Housekeeping
            import re as _re
            room_code_match = _re.search(r"\d+", str(room_number))
            room_code = room_code_match.group(0) if room_code_match else str(room_number)
            
            # Get the most recent housekeeping record for this room
            latest_hk = Housekeeping.objects.filter(room_number=room_code).order_by('-created_at').first()
            if latest_hk and latest_hk.status:
                status_lower = latest_hk.status.lower()
                if 'maintenance' in status_lower or 'under maintenance' in status_lower:
                    print(f"[DEBUG] Room {room_code} is under maintenance, cannot check in")
                    return JsonResponse({
                        'success': False, 
                        'message': f'Room {room_code} is currently under maintenance and cannot be checked in.'
                    }, status=400)
                elif 'progress' in status_lower or 'in progress' in status_lower:
                    print(f"[DEBUG] Room {room_code} is in housekeeping, cannot check in")
                    return JsonResponse({
                        'success': False, 
                        'message': f'Room {room_code} is currently in housekeeping and cannot be checked in.'
                    }, status=400)

            # Create booking
            print("[DEBUG] Creating booking")
            booking = Booking.objects.create(
                guest=guest,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                room=room_number,
                total_of_guests=request.POST.get('total_guests'),
                num_of_adults=request.POST.get('adults'),
                num_of_children=request.POST.get('children'),
                status='Checked-in',
                source='walkin'
            )
            print(f"[DEBUG] Booking created: {booking}")

            # Update room status to 'occupied'
            print(f"[DEBUG] Updating room {room_number} status to 'occupied'")
            room = Room.objects.get(room_number=room_number)
            room.status = 'occupied'
            room.save()
            print(f"[DEBUG] Room status updated: {room}")

            # Parse add-ons from POST and update guest additional charges
            def _safe_int(val):
                try:
                    return int(val)
                except Exception:
                    return 0

            bed_count = _safe_int(request.POST.get('add_ons[bed]', request.POST.get('add_ons.bed', request.POST.get('bed'))))
            pillow_count = _safe_int(request.POST.get('add_ons[pillow]', request.POST.get('add_ons.pillow', request.POST.get('pillow'))))
            towel_count = _safe_int(request.POST.get('add_ons[towel]', request.POST.get('add_ons.towel', request.POST.get('towel'))))

            bed_price = 200
            pillow_price = 50
            towel_price = 30
            addons_total = (bed_count * bed_price) + (pillow_count * pillow_price) + (towel_count * towel_price)
            print(f"[DEBUG] Add-ons -> bed={bed_count}, pillow={pillow_count}, towel={towel_count}, total={addons_total}")

            try:
                current_additional = float(guest.additional_charge_billing or 0)
            except Exception:
                current_additional = 0.0
            guest.additional_charge_billing = str(current_additional + addons_total)
            
            # Calculate billing based on room type and number of nights
            room_prices = {
                'standard': 1500,
                'family': 2500,
                'deluxe': 4500
            }
            
            # Get room type from room number
            room_obj = Room.objects.get(room_number=room_number)
            room_type = room_obj.room_type
            price_per_night = room_prices.get(room_type, 1500)
            
            # Calculate number of nights
            nights = (check_out_date - check_in_date).days
            if nights <= 0:
                nights = 1  # Minimum 1 night
            
            # Calculate total room cost
            total_room_cost = price_per_night * nights
            print(f"[DEBUG] Room type: {room_type}, Price per night: {price_per_night}, Nights: {nights}, Total room cost: {total_room_cost}")
            
            guest.billing = str(total_room_cost)
            
            guest.save(update_fields=['additional_charge_billing', 'billing'])
            print(f"[DEBUG] Updated guest.additional_charge_billing = {guest.additional_charge_billing}")
            print(f"[DEBUG] Updated guest.billing = {guest.billing}")

            # Create payment
            print("[DEBUG] Creating payment")
            exp_date_val = request.POST.get('exp_date', request.POST.get('card_expiry'))
            cvc_val = request.POST.get('cvv', request.POST.get('cvc'))
            total_balance_with_addons = total_room_cost + addons_total

            Payment.objects.create(
                booking=booking,
                method=request.POST.get('payment_method'),
                card_number=request.POST.get('card_number'),
                exp_date=exp_date_val,
                cvc_code=cvc_val,
                billing_address=request.POST.get('billing_address'),
                total_balance=total_balance_with_addons
            )
            print("[DEBUG] Payment created")

            return JsonResponse({'success': True, 'message': f'Room {room_number} successfully booked and checked in from {check_in_date} to {check_out_date}.'}, status=200)

        except Room.DoesNotExist:
            print(f"[DEBUG] Room {room_number} does not exist")
            return JsonResponse({'success': False, 'message': 'Room not found.'}, status=404)

        except Exception as e:
            print(f"[DEBUG] Unexpected error: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error: {str(e)}"}, status=500)

    print("[DEBUG] Invalid request method")
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)




def getGuest(request, guest_id):
    if request.method == 'GET':
        print(f"Fetching guest with ID: {guest_id}")
        try:
            guest = Guest.objects.get(id=guest_id)

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
                'payments': [],  # ← Add this to collect all payments
                'check_in_date': None,
                'check_out_date': None,
                'room': None,
                'booking_status': None
            }

            bookings = Booking.objects.filter(guest=guest).order_by('-booking_date')

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
                    payment_data = {
                        'id': payment.id,
                        'method': payment.method,
                        'card_number': payment.card_number,
                        'exp_date': payment.exp_date,
                        'cvc_code': payment.cvc_code,
                        'billing_address': payment.billing_address,
                        'total_balance': float(payment.total_balance),
                        'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    booking_data['payment'] = payment_data
                    guest_data['payments'].append(payment_data)  # ← Collect payment info here
                    print(f"Payment for booking {booking.id}: {payment_data}")  # ← Print it

                except Payment.DoesNotExist:
                    print(f"No payment found for booking {booking.id}")
                    booking_data['payment'] = None

                guest_data['bookings'].append(booking_data)

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
    Returns JSON with comprehensive room information based on actual Room model data
    """
    date_str = request.GET.get("date")
    print(f"[DEBUG] received date_str: {date_str!r}")

    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        print(f"[DEBUG] parsed date: {d!r}")
    except (ValueError, TypeError) as e:
        print(f"[DEBUG] date parsing error: {e}")
        return JsonResponse({"error": "invalid or missing date"}, status=400)

    # Auto-cancel no-shows: Pending bookings whose check-in date is past, or today after 09:00
    try:
        now = timezone.localtime()
        today = now.date()
        cutoff_reached = now.time() >= dt_time(9, 0)

        pending_qs = Booking.objects.filter(status='Pending')
        to_cancel = pending_qs.filter(check_in_date__lt=today)
        if cutoff_reached:
            to_cancel = to_cancel | pending_qs.filter(check_in_date=today)

        to_cancel = to_cancel.distinct()
        cancelled_ids = []
        for b in to_cancel:
            b.status = 'Cancelled'
            b.save()
            cancelled_ids.append(b.id)
            # Free up the room if possible
            try:
                # normalize room number to numeric string
                import re as _re
                m = _re.search(r"\d+", str(b.room))
                room_code = m.group(0) if m else str(b.room)
                room_obj = Room.objects.get(room_number=room_code)
                if room_obj.status == 'reserved':
                    room_obj.status = 'available'
                    room_obj.save()
            except Exception as _e:
                print(f"[DEBUG] while auto-cancelling booking {b.id}, room free-up error: {_e}")
        if cancelled_ids:
            print(f"[DEBUG] Auto-cancelled no-show bookings at room_status(): {cancelled_ids}")
    except Exception as auto_e:
        print(f"[DEBUG] auto-cancel pass failed: {auto_e}")

    # Get all rooms from the Room model
    all_rooms = Room.objects.all()
    total_rooms = all_rooms.count()
    print(f"[DEBUG] Total rooms: {total_rooms}")

    # Print all room statuses for debugging
    room_statuses = list(all_rooms.values('room_number', 'status'))
    print(f"[DEBUG] Room statuses: {room_statuses}")

    # Helper: normalize stored room string to plain numeric code matching data-room
    def normalize_room_code(room_str: str) -> str:
        if not room_str:
            return ""
        match = re.search(r"\d+", str(room_str))
        return match.group(0) if match else str(room_str)

    # Get occupied rooms for the selected date (normalized)
    try:
        occupied_qs = Booking.objects.filter(
            check_in_date__lte=d,
            check_out_date__gte=d,
            status='Checked-in'
        ).select_related('guest')
        occupied_rooms = [normalize_room_code(b.room) for b in occupied_qs]
        print(f"[DEBUG] occupied_qs raw: {[ (b.room, b.guest.name) for b in occupied_qs ]}")
    except Exception as e:
        print(f"[DEBUG] Error querying occupied 'room' field: {e}")
        occupied_rooms = []
    print(f"[DEBUG] Occupied rooms (normalized): {occupied_rooms}")

    # Get reserved rooms for the selected date (normalized)
    try:
        reserved_qs = Booking.objects.filter(
            check_in_date__lte=d,
            check_out_date__gte=d,
            status='Pending'
        ).select_related('guest')
        reserved_rooms = [normalize_room_code(b.room) for b in reserved_qs]
        print(f"[DEBUG] reserved_qs raw: {[ (b.room, b.guest.name) for b in reserved_qs ]}")
    except Exception as e:
        print(f"[DEBUG] Error querying reserved 'room' field: {e}")
        reserved_rooms = []
    print(f"[DEBUG] Reserved rooms (normalized): {reserved_rooms}")

    # Count rooms by status dynamically (date-aware for occupied and reserved)
    maintenance_count = all_rooms.filter(status='maintenance').count()
    cleaning_count = all_rooms.filter(status='cleaning').count()
    out_of_order_count = all_rooms.filter(status='out_of_order').count()

    occupied_set = set(occupied_rooms)
    reserved_set = set(reserved_rooms)

    # Available excludes occupied, reserved, maintenance, out_of_order
    available_count = total_rooms - len(occupied_set) - len(reserved_set) - maintenance_count - out_of_order_count
    if available_count < 0:
        available_count = 0

    room_status_counts = {
        'available': available_count,
        'occupied': len(occupied_set),
        'maintenance': maintenance_count,
        'cleaning': cleaning_count,
        'reserved': len(reserved_set),
        'out_of_order': out_of_order_count,
    }
    print(f"[DEBUG] Room status counts: {room_status_counts}")

    # Count rooms by type from the Room model
    room_type_counts = {
        'deluxe': all_rooms.filter(room_type='deluxe').count(),
        'family': all_rooms.filter(room_type='family').count(),
        'standard': all_rooms.filter(room_type='standard').count(),
    }

    # Count occupied rooms by type (based on actual room data)
    occupied_by_type = {
        'deluxe': 0,
        'family': 0,
        'standard': 0
    }

    # Get the actual room types for occupied rooms
    for room_number in occupied_rooms:
        room_num = room_number
        try:
            room = Room.objects.get(room_number=room_num)
            if room.room_type in occupied_by_type:
                occupied_by_type[room.room_type] += 1
        except Room.DoesNotExist:
            print(f"[DEBUG] Room {room_num} not found in Room model")
            continue

    print(f"[DEBUG] occupied rooms for {d}: {occupied_rooms}")
    print(f"[DEBUG] room counts: total={total_rooms}, available={room_status_counts['available']}, occupied={room_status_counts['occupied']}, maintenance={room_status_counts['maintenance']}")

    # Build details for tooltips
    occupied_details = {}
    try:
        for b in occupied_qs:
            rc = normalize_room_code(b.room)
            occupied_details[rc] = {
                'guest': b.guest.name,
                'check_in': b.check_in_date.strftime('%B %d, %Y'),
                'check_out': b.check_out_date.strftime('%B %d, %Y'),
            }
    except Exception:
        pass

    reserved_details = {}
    try:
        for b in reserved_qs:
            rc = normalize_room_code(b.room)
            reserved_details[rc] = {
                'guest': b.guest.name,
                'check_in': b.check_in_date.strftime('%B %d, %Y'),
                'check_out': b.check_out_date.strftime('%B %d, %Y'),
            }
    except Exception:
        pass

    # Get housekeeping status for all rooms
    from housekeeping.models import Housekeeping
    housekeeping_status = {}
    
    # Get all unique room numbers that have housekeeping records
    room_numbers = Housekeeping.objects.values_list('room_number', flat=True).distinct()
    print(f"[room_status] Checking housekeeping for {len(room_numbers)} rooms")
    
    for room_num in room_numbers:
        room_code = normalize_room_code(room_num)
        if room_code:
            # Get the most recent status for this room
            latest_hk = Housekeeping.objects.filter(
                room_number=room_num
            ).order_by('-created_at').first()
            if latest_hk and latest_hk.status:
                status_lower = latest_hk.status.lower()
                print(f"[room_status] Room {room_code}: status='{latest_hk.status}', lowercase='{status_lower}'")
                
                # Check maintenance FIRST (it should take priority)
                if 'maintenance' in status_lower or 'under maintenance' in status_lower:
                    housekeeping_status[room_code] = 'under_maintenance'
                    print(f"  -> Set to 'under_maintenance'")
                elif 'progress' in status_lower or 'in progress' in status_lower:
                    housekeeping_status[room_code] = 'in_progress'
                    print(f"  -> Set to 'in_progress'")
                elif 'pending' in status_lower:
                    housekeeping_status[room_code] = 'pending'
                    print(f"  -> Set to 'pending'")
                else:
                    print(f"  -> No match, skipping")
    
    print(f"[room_status] Final housekeeping_status: {housekeeping_status}")

    return JsonResponse({
        "occupied": list(occupied_set),
        "reserved": list(reserved_set),
        "occupied_details": occupied_details,
        "reserved_details": reserved_details,
        "housekeeping_status": housekeeping_status,  # Add housekeeping status
        "room_info": {
            "total": total_rooms,
            "vacant": room_status_counts['available'],
            "occupied": room_status_counts['occupied'],
            "maintenance": room_status_counts['maintenance'],
            "housekeeping": room_status_counts['cleaning'],
            "reserved": room_status_counts['reserved']
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

            # Set room status back to available
            try:
                import re as _re
                posted_room = request.POST.get('room') or booking.room
                m = _re.search(r"\d+", str(posted_room))
                room_code = m.group(0) if m else str(posted_room)
                room_obj = Room.objects.get(room_number=room_code)
                room_obj.status = 'available'
                room_obj.save()
                print(f"Room {room_code} set to available after checkout")
            except Exception as room_e:
                print("Room availability update failed:", room_e)

            # Guest billing
            # Sum existing additional charges into billing if provided
          

            # Payment
            payment, created = Payment.objects.get_or_create(booking=booking)
            payment.method = request.POST.get('payment_method')
            payment.card_number = request.POST.get('card_number')
            payment.exp_date = request.POST.get('exp_date', request.POST.get('card_expiry'))
            payment.cvc_code = request.POST.get('cvv', request.POST.get('card_cvc'))
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

@decorator.role_required('staff', 'SUPER_ADMIN')
def room_list(request):
    """Display all rooms with their current status"""
    rooms = Room.objects.all().order_by('room_number')
    
    return render(request, "staff/room_list.html", {
        'rooms': rooms,
        'today': date.today().strftime('%Y-%m-%d')
    })


@decorator.role_required('staff', 'SUPER_ADMIN')
def room_availability(request):
    """
    Returns blocked date ranges for a given room number.
    Query: ?room=<room_number>
    Considers bookings with status Pending and Checked-in.
    """
    room_num = request.GET.get('room')
    if not room_num:
        return JsonResponse({'error': 'room is required'}, status=400)

    # Collect all overlapping date ranges for this room (support multiple stored formats)
    room_num_str = str(room_num)
    alt_values = [
        room_num_str,
        f"R{room_num_str}",
        f"Room {room_num_str}",
        f"Room {room_num_str} : Standard",
        f"Room {room_num_str} : Family",
        f"Room {room_num_str} : Deluxe",
    ]
    bookings = Booking.objects.filter(
        Q(room__in=alt_values),
        status__in=['Pending', 'Checked-in']
    ).order_by('check_in_date')

    blocked = []
    for b in bookings:
        # Inclusive range [check_in_date, check_out_date]
        start = b.check_in_date
        end = b.check_out_date
        # Flatpickr expects strings; we will provide individual dates list too
        days = []
        d = start
        while d <= end:
            days.append(d.strftime('%Y-%m-%d'))
            d = d + timedelta(days=1)

        blocked.append({
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d'),
            'dates': days,
            'status': b.status,
            'ref': f"{b.id:05d}"
        })

    return JsonResponse({'blocked': blocked})