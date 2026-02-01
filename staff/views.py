from urllib import request
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.clickjacking import xframe_options_exempt, xframe_options_sameorigin
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
from io import BytesIO
from django.template.loader import get_template
import os
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
    print("[INIT] xhtml2pdf library loaded successfully")
except ImportError as e:
    XHTML2PDF_AVAILABLE = False
    print(f"[INIT] xhtml2pdf library not available: {e}")
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
    total_rooms = all_rooms.count()
    
    # Helper: normalize room string to numeric code
    def normalize_room_code(room_str):
        if not room_str:
            return ""
        import re
        match = re.search(r"\d+", str(room_str))
        return match.group(0) if match else str(room_str)
    
    # Get today's date
    today = timezone.localdate()
    
    # Get housekeeping statuses (matching housekeeping_home logic exactly)
    from housekeeping.models import Housekeeping
    
    # Debug: Check all housekeeping records to see what statuses exist
    # all_hk = Housekeeping.objects.all().values('room_number', 'status').distinct()
    # print("All housekeeping records:", list(all_hk))
    
    # Function to determine room status (matching template display logic)
    def get_room_status_class(room_number):
        """Determine room status class matching the template display"""
        room_code = str(room_number)
        
        # Room field might be stored in different formats, so we need to check multiple formats
        room_alt_values = [
            room_code,
            f"R{room_code}",
            f"Room {room_code}",
            f"Room {room_code} : Standard",
            f"Room {room_code} : Family",
            f"Room {room_code} : Deluxe",
        ]
        
        # Check for active booking today
        has_booking_today = Booking.objects.filter(
            room__in=room_alt_values,
            status='Checked-in',
            check_in_date__lte=today,
            check_out_date__gte=today,
        ).exists()
        
        # Check for pending booking today
        has_pending_booking = Booking.objects.filter(
            room__in=room_alt_values,
            status='Pending',
            check_in_date__lte=today,
            check_out_date__gte=today,
        ).exists()
        
        # Get the most recent housekeeping record for this room
        # Try exact match first
        record = Housekeeping.objects.filter(
            room_number=room_code
        ).order_by('-created_at').first()
        
        # If not found with exact match, try to find by extracting number from room_number
        if not record:
            # Try to find records where room_number contains the room code
            all_records = Housekeeping.objects.filter(
                room_number__icontains=room_code
            ).order_by('-created_at')
            # Filter to get the one that matches the room number exactly (extract number from room_number)
            for rec in all_records:
                # Extract numeric part from room_number (re is already imported at top)
                rec_num = re.search(r'\d+', str(rec.room_number))
                if rec_num and rec_num.group(0) == room_code:
                    record = rec
                    break
        
        status_class = 'vacant'
        if record and record.status:
            s = record.status.strip().lower()
            # Replace underscores with spaces for matching
            s_normalized = s.replace('_', ' ').replace('-', ' ')
            # Check for maintenance status first (applies regardless of booking)
            if 'maintenance' in s_normalized or 'under maintenance' in s_normalized:
                status_class = 'maintenance'
            elif 'no requests' in s_normalized or 'no request' in s_normalized:
                # "No requests" means room is vacant (no housekeeping needed)
                status_class = 'vacant'
            elif 'pending' in s_normalized:
                # Show pending regardless of booking status (persists after checkout)
                status_class = 'pending'
            elif 'progress' in s_normalized or 'in progress' in s_normalized:
                # Show progress regardless of booking status (persists after checkout)
                status_class = 'progress'
            else:
                # For other statuses, check booking
                if has_booking_today:
                    status_class = 'occupied'
                elif has_pending_booking:
                    status_class = 'reserved'
                else:
                    status_class = 'vacant'
        else:
            # No housekeeping record - check booking
            if has_booking_today:
                status_class = 'occupied'
            elif has_pending_booking:
                status_class = 'reserved'
            else:
                status_class = 'vacant'
        
        # Map to CSS class names used in template (matching template default and CSS classes)
        status_mapping = {
            'vacant': 'vacant',  # matches template default
            'occupied': 'occupied',
            'maintenance': 'maintenance',
            'pending': 'housekeeping',  # pending housekeeping = housekeeping CSS class
            'progress': 'housekeeping',  # in progress housekeeping = housekeeping CSS class
            'reserved': 'reserved',
        }
        return status_mapping.get(status_class, 'vacant')  # default matches template default
    
    # Get individual rooms and update their status dynamically
    room_1 = Room.objects.filter(room_number='1').first()
    if room_1:
        room_1.status = get_room_status_class('1')
    room_2 = Room.objects.filter(room_number='2').first()
    if room_2:
        room_2.status = get_room_status_class('2')
    room_3 = Room.objects.filter(room_number='3').first()
    if room_3:
        room_3.status = get_room_status_class('3')
    room_4 = Room.objects.filter(room_number='4').first()
    if room_4:
        room_4.status = get_room_status_class('4')
    room_5 = Room.objects.filter(room_number='5').first()
    if room_5:
        room_5.status = get_room_status_class('5')
    room_6 = Room.objects.filter(room_number='6').first()
    if room_6:
        room_6.status = get_room_status_class('6')
    room_7 = Room.objects.filter(room_number='7').first()
    if room_7:
        room_7.status = get_room_status_class('7')
    room_8 = Room.objects.filter(room_number='8').first()
    if room_8:
        room_8.status = get_room_status_class('8')
    room_9 = Room.objects.filter(room_number='9').first()
    if room_9:
        room_9.status = get_room_status_class('9')
    room_10 = Room.objects.filter(room_number='10').first()
    if room_10:
        room_10.status = get_room_status_class('10')
    room_11 = Room.objects.filter(room_number='11').first()
    if room_11:
        room_11.status = get_room_status_class('11')
    room_12 = Room.objects.filter(room_number='12').first()
    if room_12:
        room_12.status = get_room_status_class('12')
    
    # Count rooms by actual displayed status (based on room.status CSS class that will be shown in template)
    # Count based on the actual room objects that are displayed in the template
    status_counts = {
        'vacant': 0,
        'occupied': 0,
        'maintenance': 0,
        'housekeeping': 0,  # housekeeping class (pending/progress)
        'reserved': 0,
    }
    
    # Count each room's actual displayed status (CSS class) from the room objects
    room_list = [room_1, room_2, room_3, room_4, room_5, room_6, room_7, room_8, room_9, room_10, room_11, room_12]
    for i, room in enumerate(room_list, 1):
        if room and hasattr(room, 'status'):
            status = room.status  # This is the CSS class name (vacant, occupied, maintenance, housekeeping, reserved)
            # Debug: print status for each room
            print(f"Room {i}: status = '{status}'")
            if status in status_counts:
                status_counts[status] += 1
            else:
                # Default to vacant if status is not recognized
                print(f"  -> Room {i}: Unrecognized status '{status}', defaulting to vacant")
                status_counts['vacant'] += 1
        else:
            # If room doesn't exist, count as vacant
            print(f"Room {i}: room object doesn't exist, counting as vacant")
            status_counts['vacant'] += 1
    
    # Debug: Print final counts
    print(f"Final status_counts: {status_counts}")
    
    # Map to template keys (based on actual displayed room status classes)
    room_status_counts = {
        'available': status_counts['vacant'],  # vacant = available in the counts display
        'occupied': status_counts['occupied'],
        'maintenance': status_counts['maintenance'],
        'cleaning': status_counts['housekeeping'],  # housekeeping = cleaning (housekeeping class)
        'reserved': status_counts['reserved'],
    }
    
    # Debug output (uncomment to see counts)
    # print(f"Status counts: {status_counts}")
    # print(f"Room status counts: {room_status_counts}")
    
    # Count rooms by type (only occupied rooms - matching displayed status)
    occupied_by_type = {
        'deluxe': 0,
        'family': 0,
        'standard': 0
    }
    
    # Count occupied rooms by type based on actual displayed status
    for i in range(1, 13):  # Rooms 1-12
        status_class = get_room_status_class(i)
        if status_class == 'occupied':
            try:
                room = Room.objects.get(room_number=str(i))
                if room.room_type in occupied_by_type:
                    occupied_by_type[room.room_type] += 1
            except Room.DoesNotExist:
                continue
    
    room_type_counts = {
        'deluxe': occupied_by_type['deluxe'],
        'family': occupied_by_type['family'],
        'standard': occupied_by_type['standard'],
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
            
            # Collect validation errors
            errors = []
            
            # Validate required fields
            guest_name = request.POST.get('guest_name', '').strip()
            if not guest_name:
                errors.append('Name is required')
            
            guest_email = request.POST.get('guest_email', '').strip()
            if not guest_email:
                errors.append('Email is required')
            elif '@' not in guest_email:
                errors.append('Please enter a valid email address')
            
            guest_mobile = request.POST.get('guest_mobile', '').strip()
            if not guest_mobile:
                errors.append('Mobile number is required')
            
            room_number = request.POST.get('room', '').strip()
            if not room_number:
                errors.append('Room selection is required')
            
            check_in_date = request.POST.get('check_in', '').strip()
            if not check_in_date:
                errors.append('Check-in date is required')
            
            check_out_date = request.POST.get('check_out', '').strip()
            if not check_out_date:
                errors.append('Check-out date is required')
            
            adults = request.POST.get('adults', '').strip()
            if not adults:
                errors.append('Number of adults is required')
            else:
                try:
                    adults_int = int(adults)
                    if adults_int < 1:
                        errors.append('At least 1 adult is required')
                except ValueError:
                    errors.append('Number of adults must be a valid number')
            
            # Validate dates format and order
            if check_in_date and check_out_date:
                try:
                    check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
                    check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
                    
                    if check_out <= check_in:
                        errors.append('Check-out date must be after check-in date')
                    
                    if check_in < datetime.now().date():
                        errors.append('Check-in date cannot be in the past')
                except ValueError:
                    errors.append('Invalid date format. Please use YYYY-MM-DD format')
            
            # Validate payment method and card fields if card payment
            payment_method = request.POST.get('payment_method', '').strip()
            if payment_method == 'card':
                card_number = request.POST.get('card_number', '').strip()
                exp_date = request.POST.get('exp_date', '').strip()
                cvc = request.POST.get('cvc', '').strip()
                
                if not card_number:
                    errors.append('Card number is required for card payment')
                elif len(card_number.replace(' ', '').replace('-', '')) < 13:
                    errors.append('Card number must be at least 13 digits')
                
                if not exp_date:
                    errors.append('Expiration date is required for card payment')
                elif not re.match(r'^\d{2}/\d{2}$', exp_date):
                    errors.append('Expiration date must be in MM/YY format')
                
                if not cvc:
                    errors.append('CVC is required for card payment')
                elif len(cvc) < 3:
                    errors.append('CVC must be at least 3 digits')
            
            # Return validation errors if any
            if errors:
                return JsonResponse({
                    'success': False,
                    'message': 'Please fix the validation errors below.',
                    'errors': errors
                }, status=400)

            # Create guest
            print("[DEBUG] Creating guest")
            guest = Guest.objects.create(
                name=guest_name,
                address=request.POST.get('guest_address', ''),
                zip_code=request.POST.get('guest_zip_code', ''),
                email=guest_email,
                date_of_birth=request.POST.get('guest_birth') or None
            )
            print(f"[DEBUG] Guest created: {guest}")

            print(f"[DEBUG] Room number: {room_number}, Check-in: {check_in_date}, Check-out: {check_out_date}")

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

    # Get housekeeping statuses (matching home view logic)
    from housekeeping.models import Housekeeping
    
    # Function to determine room status (matching home view logic)
    def get_room_status_class_api(room_number, target_date):
        """Determine room status class matching the template display"""
        room_code = str(room_number)
        
        # Check for active booking on target date
        # Room field might be stored in different formats, so we need to check multiple formats
        room_alt_values = [
            room_code,
            f"R{room_code}",
            f"Room {room_code}",
            f"Room {room_code} : Standard",
            f"Room {room_code} : Family",
            f"Room {room_code} : Deluxe",
        ]
        has_booking = Booking.objects.filter(
            room__in=room_alt_values,
            status='Checked-in',
            check_in_date__lte=target_date,
            check_out_date__gte=target_date,
        ).exists()
        
        # Check for pending booking on target date
        has_pending_booking = Booking.objects.filter(
            room__in=room_alt_values,
            status='Pending',
            check_in_date__lte=target_date,
            check_out_date__gte=target_date,
        ).exists()
        
        # Get the most recent housekeeping record for this room
        record = Housekeeping.objects.filter(room_number=room_code).order_by('-created_at').first()
        
        # If not found with exact match, try to find by extracting number from room_number
        if not record:
            all_records = Housekeeping.objects.filter(room_number__icontains=room_code).order_by('-created_at')
            for rec in all_records:
                rec_num = re.search(r'\d+', str(rec.room_number))
                if rec_num and rec_num.group(0) == room_code:
                    record = rec
                    break
        
        status_class = 'vacant'
        if record and record.status:
            s = record.status.strip().lower()
            # Replace underscores with spaces for matching
            s_normalized = s.replace('_', ' ').replace('-', ' ')
            # Check for maintenance status first (applies regardless of booking)
            if 'maintenance' in s_normalized or 'under maintenance' in s_normalized:
                status_class = 'maintenance'
            elif 'no requests' in s_normalized or 'no request' in s_normalized:
                status_class = 'vacant'
            elif 'pending' in s_normalized:
                status_class = 'pending'
            elif 'progress' in s_normalized or 'in progress' in s_normalized:
                status_class = 'progress'
            else:
                if has_booking:
                    status_class = 'occupied'
                elif has_pending_booking:
                    status_class = 'reserved'
                else:
                    status_class = 'vacant'
        else:
            if has_booking:
                status_class = 'occupied'
            elif has_pending_booking:
                status_class = 'reserved'
            else:
                status_class = 'vacant'
        
        # Map to CSS class names
        status_mapping = {
            'vacant': 'vacant',
            'occupied': 'occupied',
            'maintenance': 'maintenance',
            'pending': 'housekeeping',
            'progress': 'housekeeping',
            'reserved': 'reserved',
        }
        return status_mapping.get(status_class, 'vacant')
    
    # Count rooms by actual displayed status
    # First, count occupied and reserved from the actual booking data
    occupied_count = len(occupied_rooms)
    reserved_count = len(reserved_rooms)
    
    # Count maintenance and housekeeping from housekeeping records
    maintenance_count = 0
    housekeeping_count = 0
    
    # Get housekeeping status for all rooms to count maintenance and housekeeping
    from housekeeping.models import Housekeeping
    for i in range(1, 13):  # Rooms 1-12
        room_code = str(i)
        # Get the most recent housekeeping record for this room
        record = Housekeeping.objects.filter(room_number=room_code).order_by('-created_at').first()
        if not record:
            # Try to find by extracting number from room_number
            all_records = Housekeeping.objects.filter(room_number__icontains=room_code).order_by('-created_at')
            for rec in all_records:
                rec_num = re.search(r'\d+', str(rec.room_number))
                if rec_num and rec_num.group(0) == room_code:
                    record = rec
                    break
        
        if record and record.status:
            status_lower = record.status.strip().lower().replace('_', ' ').replace('-', ' ')
            # Only count if room is not already occupied or reserved
            if room_code not in occupied_rooms and room_code not in reserved_rooms:
                if 'maintenance' in status_lower or 'under maintenance' in status_lower:
                    maintenance_count += 1
                elif 'progress' in status_lower or 'in progress' in status_lower or 'pending' in status_lower:
                    housekeeping_count += 1
    
    # Calculate vacant: total rooms minus all other statuses
    vacant_count = total_rooms - occupied_count - reserved_count - maintenance_count - housekeeping_count
    if vacant_count < 0:
        vacant_count = 0
    
    room_status_counts = {
        'available': vacant_count,
        'occupied': occupied_count,
        'maintenance': maintenance_count,
        'cleaning': housekeeping_count,
        'reserved': reserved_count,
    }
    print(f"[DEBUG] Room status counts: {room_status_counts}")
    print(f"[DEBUG] Breakdown: occupied={occupied_count}, reserved={reserved_count}, maintenance={maintenance_count}, housekeeping={housekeeping_count}, vacant={vacant_count}, total={total_rooms}")

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

    # Create sets for occupied and reserved rooms
    occupied_set = set(occupied_rooms)
    reserved_set = set(reserved_rooms)

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

@xframe_options_exempt
@decorator.role_required('staff', 'SUPER_ADMIN')
def statement_of_account(request, guest_id):
    """Generate and display statement of account for a guest"""
    # Check if it's an AJAX request and handle errors appropriately
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    print(f"[STATEMENT] View called with guest_id={guest_id}, is_ajax={is_ajax}, user={request.user}, role={getattr(request.user, 'role', None)}")
    
    try:
        guest = get_object_or_404(Guest, id=guest_id)
        print(f"[STATEMENT] Guest found: {guest.name}")
        
        # Get the most recent booking
        booking = Booking.objects.filter(guest=guest).order_by('-booking_date').first()
        
        # Get all payments
        payments = []
        if booking:
            try:
                payment = Payment.objects.get(booking=booking)
                # Get payment method display name
                method_display = dict(Payment.PAYMENT_METHODS).get(payment.method, payment.method.title())
                payments.append({
                    'date': payment.created_at,
                    'method': method_display,
                    'amount': payment.total_balance,
                    'description': f'Payment for Booking #{booking.id}'
                })
            except Payment.DoesNotExist:
                pass
        
        # Get laundry transactions
        from laundry.models import LaundryTransaction
        laundry_transactions = LaundryTransaction.objects.filter(guest=guest).order_by('-created_at')
        
        # Get cafe orders
        from cafe.models import CafeOrder
        cafe_orders = CafeOrder.objects.filter(guest=guest).order_by('-order_date')
        
        # Calculate billing totals
        def safe_float(value):
            try:
                return float(value) if value else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        room_charges = safe_float(guest.billing)
        room_service = safe_float(guest.room_service_billing)
        laundry_total = safe_float(guest.laundry_billing)
        cafe_total = safe_float(guest.cafe_billing)
        excess_pax = safe_float(guest.excess_pax_billing)
        additional_charges = safe_float(guest.additional_charge_billing)
        
        # Calculate total charges
        total_charges = room_charges + room_service + laundry_total + cafe_total + excess_pax + additional_charges
        
        # Calculate total payments - convert Decimal to float
        total_payments = sum(float(p['amount']) for p in payments)
        
        # Calculate outstanding balance - ensure both are floats
        outstanding_balance = float(total_charges) - float(total_payments)
        
        # Prepare transaction history
        transactions = []
        
        # Helper function to normalize dates to timezone-aware datetime for consistent sorting
        def normalize_date(dt):
            """Convert to timezone-aware datetime so naive/aware comparison doesn't fail."""
            if dt is None:
                return timezone.now()
            if isinstance(dt, datetime):
                if timezone.is_naive(dt):
                    return timezone.make_aware(dt)
                return dt
            if isinstance(dt, date) and not isinstance(dt, datetime):
                naive_dt = datetime.combine(dt, dt_time.min)
                return timezone.make_aware(naive_dt)
            return timezone.now()
        
        # Add room charges if exists
        if room_charges > 0 and booking:
            transactions.append({
                'date': normalize_date(booking.check_in_date),
                'description': f'Room Charges - {booking.room}',
                'type': 'Charge',
                'amount': room_charges,
                'category': 'Room'
            })
        
        # Add laundry transactions
        print(f"[STATEMENT HTML] Processing {len(laundry_transactions)} laundry transactions")
        for lt in laundry_transactions:
            print(f"[STATEMENT HTML] Laundry transaction: payment_method={lt.payment_method}, amount={lt.total_amount}")
            if lt.payment_method == 'room':  # Charge to room
                transactions.append({
                    'date': normalize_date(lt.date_time),
                    'description': f'Laundry - {lt.service_type} ({lt.no_of_bags} bag{"s" if lt.no_of_bags > 1 else ""})',
                    'type': 'Charge',
                    'amount': float(lt.total_amount),
                    'category': 'Laundry'
                })
            elif lt.payment_method == 'cash':  # Cash payment
                transactions.append({
                    'date': normalize_date(lt.date_time),
                    'description': f'Laundry Payment - {lt.service_type} ({lt.no_of_bags} bag{"s" if lt.no_of_bags > 1 else ""})',
                    'type': 'Payment',
                    'amount': float(lt.total_amount),
                    'category': 'Laundry'
                })
        
        # Add cafe orders
        print(f"[STATEMENT HTML] Processing {len(cafe_orders)} cafe orders")
        for co in cafe_orders:
            print(f"[STATEMENT HTML] Cafe order: payment_method={co.payment_method}, amount={co.total}")
            if co.payment_method == 'room':  # Charge to room
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Order #{co.id}',
                    'type': 'Charge',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
            elif co.payment_method == 'cash':  # Cash payment
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Payment - Order #{co.id}',
                    'type': 'Payment',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
            elif co.payment_method == 'card':  # Card payment
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Payment - Order #{co.id}',
                    'type': 'Payment',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
        
        # Add room service if exists
        if room_service > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Room Service',
                'type': 'Charge',
                'amount': room_service,
                'category': 'Room Service'
            })
        
        # Add excess pax if exists
        if excess_pax > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Excess Pax Charges',
                'type': 'Charge',
                'amount': excess_pax,
                'category': 'Excess Pax'
            })
        
        # Add additional charges if exists
        if additional_charges > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Additional Charges',
                'type': 'Charge',
                'amount': additional_charges,
                'category': 'Additional'
            })
        
        # Add payments to transactions
        for payment in payments:
            transactions.append({
                'date': normalize_date(payment['date']),
                'description': payment['description'],
                'type': 'Payment',
                'amount': float(payment['amount']),
                'category': 'Payment'
            })
        
        # Sort by timestamp to avoid comparing naive vs aware datetimes
        def _txn_sort_key(t):
            d = t.get('date')
            if d is None:
                return 0.0
            if isinstance(d, datetime) and timezone.is_naive(d):
                d = timezone.make_aware(d)
            elif isinstance(d, date) and not isinstance(d, datetime):
                d = timezone.make_aware(datetime.combine(d, dt_time.min))
            return d.timestamp() if hasattr(d, 'timestamp') else 0.0
        transactions.sort(key=_txn_sort_key, reverse=True)
        
        print(f"[STATEMENT HTML] Total transactions: {len(transactions)}")
        for i, txn in enumerate(transactions):
            print(f"[STATEMENT] Transaction {i+1}: type={txn['type']}, category={txn['category']}, amount={txn['amount']}, desc={txn['description']}")
        
        context = {
            'guest': guest,
            'booking': booking,
            'room_charges': room_charges,
            'room_service': room_service,
            'laundry_total': laundry_total,
            'cafe_total': cafe_total,
            'excess_pax': excess_pax,
            'additional_charges': additional_charges,
            'total_charges': total_charges,
            'total_payments': total_payments,
            'outstanding_balance': outstanding_balance,
            'transactions': transactions,
            'statement_date': timezone.now().date(),
            'statement_number': f"SOA-{guest.id:05d}-{timezone.now().strftime('%Y%m%d')}"
        }
        
        response = render(request, 'staff/statement_of_account.html', context)
        # The @xframe_options_exempt decorator should prevent middleware from adding X-Frame-Options
        # But we'll also explicitly ensure it's removed as a fallback
        # Set the xframe_options_exempt attribute to ensure middleware respects it
        response.xframe_options_exempt = True
        return response
        
    except Guest.DoesNotExist:
        error_msg = f'Guest with ID {guest_id} not found'
        print(f"Error generating statement of account: {error_msg}")
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({
                'error': True,
                'message': error_msg
            }, status=404)
        messages.error(request, error_msg)
        return redirect('HomeStaff')
    except Exception as e:
        print(f"Error generating statement of account: {e}")
        import traceback
        traceback.print_exc()
        
        # If it's an AJAX request, return JSON error instead of redirecting
        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({
                'error': True,
                'message': f'Error generating statement: {str(e)}'
            }, status=500)
        
        messages.error(request, f'Error generating statement: {str(e)}')
        return redirect('HomeStaff')

@decorator.role_required('staff', 'SUPER_ADMIN')
def statement_of_account_pdf(request, guest_id):
    """Generate and download statement of account as PDF"""
    print(f"[PDF] ====== PDF REQUEST RECEIVED ======")
    print(f"[PDF] Method: {request.method}")
    print(f"[PDF] Path: {request.path}")
    print(f"[PDF] User: {request.user}")
    print(f"[PDF] User role: {getattr(request.user, 'role', None)}")
    print(f"[PDF] Guest ID: {guest_id}")
    print(f"[PDF] XHTML2PDF_AVAILABLE: {XHTML2PDF_AVAILABLE}")
    try:
        guest = get_object_or_404(Guest, id=guest_id)
        
        # Get the most recent booking
        booking = Booking.objects.filter(guest=guest).order_by('-booking_date').first()
        
        # Get all payments
        payments = []
        if booking:
            try:
                payment = Payment.objects.get(booking=booking)
                # Get payment method display name
                method_display = dict(Payment.PAYMENT_METHODS).get(payment.method, payment.method.title())
                payments.append({
                    'date': payment.created_at,
                    'method': method_display,
                    'amount': payment.total_balance,
                    'description': f'Payment for Booking #{booking.id}'
                })
            except Payment.DoesNotExist:
                pass
        
        # Get laundry transactions
        from laundry.models import LaundryTransaction
        laundry_transactions = LaundryTransaction.objects.filter(guest=guest).order_by('-created_at')
        
        # Get cafe orders
        from cafe.models import CafeOrder
        cafe_orders = CafeOrder.objects.filter(guest=guest).order_by('-order_date')
        
        # Calculate billing totals
        def safe_float(value):
            try:
                return float(value) if value else 0.0
            except (ValueError, TypeError):
                return 0.0
        
        room_charges = safe_float(guest.billing)
        room_service = safe_float(guest.room_service_billing)
        laundry_total = safe_float(guest.laundry_billing)
        cafe_total = safe_float(guest.cafe_billing)
        excess_pax = safe_float(guest.excess_pax_billing)
        additional_charges = safe_float(guest.additional_charge_billing)
        
        # Calculate total charges
        total_charges = room_charges + room_service + laundry_total + cafe_total + excess_pax + additional_charges
        
        # Calculate total payments - convert Decimal to float
        total_payments = sum(float(p['amount']) for p in payments)
        
        # Calculate outstanding balance - ensure both are floats
        outstanding_balance = float(total_charges) - float(total_payments)
        
        # Prepare transaction history
        transactions = []
        
        # Helper function to normalize dates to timezone-aware datetime for consistent sorting
        def normalize_date(dt):
            """Convert to timezone-aware datetime so naive/aware comparison doesn't fail."""
            if dt is None:
                return timezone.now()
            if isinstance(dt, datetime):
                if timezone.is_naive(dt):
                    return timezone.make_aware(dt)
                return dt
            if isinstance(dt, date) and not isinstance(dt, datetime):
                naive_dt = datetime.combine(dt, dt_time.min)
                return timezone.make_aware(naive_dt)
            return timezone.now()
        
        # Add room charges if exists
        if room_charges > 0 and booking:
            transactions.append({
                'date': normalize_date(booking.check_in_date),
                'description': f'Room Charges - {booking.room}',
                'type': 'Charge',
                'amount': room_charges,
                'category': 'Room'
            })
        
        # Add laundry transactions
        for lt in laundry_transactions:
            if lt.payment_method == 'room':  # Charge to room
                transactions.append({
                    'date': normalize_date(lt.date_time),
                    'description': f'Laundry - {lt.service_type} ({lt.no_of_bags} bag{"s" if lt.no_of_bags > 1 else ""})',
                    'type': 'Charge',
                    'amount': float(lt.total_amount),
                    'category': 'Laundry'
                })
            elif lt.payment_method == 'cash':  # Cash payment
                transactions.append({
                    'date': normalize_date(lt.date_time),
                    'description': f'Laundry Payment - {lt.service_type} ({lt.no_of_bags} bag{"s" if lt.no_of_bags > 1 else ""})',
                    'type': 'Payment',
                    'amount': float(lt.total_amount),
                    'category': 'Laundry'
                })
        
        # Add cafe orders
        for co in cafe_orders:
            if co.payment_method == 'room':  # Charge to room
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Order #{co.id}',
                    'type': 'Charge',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
            elif co.payment_method == 'cash':  # Cash payment
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Payment - Order #{co.id}',
                    'type': 'Payment',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
            elif co.payment_method == 'card':  # Card payment
                transactions.append({
                    'date': normalize_date(co.order_date),
                    'description': f'Cafe Payment - Order #{co.id}',
                    'type': 'Payment',
                    'amount': float(co.total),
                    'category': 'Cafe'
                })
        
        # Add room service if exists
        if room_service > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Room Service',
                'type': 'Charge',
                'amount': room_service,
                'category': 'Room Service'
            })
        
        # Add excess pax if exists
        if excess_pax > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Excess Pax Charges',
                'type': 'Charge',
                'amount': excess_pax,
                'category': 'Excess Pax'
            })
        
        # Add additional charges if exists
        if additional_charges > 0:
            transactions.append({
                'date': normalize_date(booking.check_in_date if booking else guest.created_at.date()),
                'description': 'Additional Charges',
                'type': 'Charge',
                'amount': additional_charges,
                'category': 'Additional'
            })
        
        # Add payments to transactions
        for payment in payments:
            transactions.append({
                'date': normalize_date(payment['date']),
                'description': payment['description'],
                'type': 'Payment',
                'amount': float(payment['amount']),
                'category': 'Payment'
            })
        
        # Sort by timestamp to avoid comparing naive vs aware datetimes
        def _txn_sort_key(t):
            d = t.get('date')
            if d is None:
                return 0.0
            if isinstance(d, datetime) and timezone.is_naive(d):
                d = timezone.make_aware(d)
            elif isinstance(d, date) and not isinstance(d, datetime):
                d = timezone.make_aware(datetime.combine(d, dt_time.min))
            return d.timestamp() if hasattr(d, 'timestamp') else 0.0
        transactions.sort(key=_txn_sort_key, reverse=True)
        
        context = {
            'guest': guest,
            'booking': booking,
            'room_charges': room_charges,
            'room_service': room_service,
            'laundry_total': laundry_total,
            'cafe_total': cafe_total,
            'excess_pax': excess_pax,
            'additional_charges': additional_charges,
            'total_charges': total_charges,
            'total_payments': total_payments,
            'outstanding_balance': outstanding_balance,
            'transactions': transactions,
            'statement_date': timezone.now().date(),
            'statement_number': f"SOA-{guest.id:05d}-{timezone.now().strftime('%Y%m%d')}"
        }
        
        # Generate PDF
        print(f"[PDF] XHTML2PDF_AVAILABLE check: {XHTML2PDF_AVAILABLE}")
        if XHTML2PDF_AVAILABLE:
            print("[PDF] Generating PDF...")
            template = get_template('staff/statement_of_account_pdf.html')
            html = template.render(context)
            result = BytesIO()
            
            # Generate PDF
            try:
                print("[PDF] Calling pisa.pisaDocument...")
                html_bytes = html.encode("UTF-8")
                pdf = pisa.pisaDocument(BytesIO(html_bytes), result)
                
                print(f"[PDF] PDF generation result - err: {pdf.err}")
                if not pdf.err:
                    # Get PDF data from BytesIO
                    result.seek(0)
                    pdf_data = result.getvalue()
                    
                    print(f"[PDF] PDF data size: {len(pdf_data)} bytes")
                    if len(pdf_data) > 0:
                        print(f"[PDF] First 20 bytes: {pdf_data[:20]}")
                    
                    # Verify it's actually PDF (starts with %PDF)
                    if len(pdf_data) == 0:
                        print(f"[PDF] ERROR: PDF data is empty!")
                        return HttpResponse(
                            'Error: Generated PDF is empty',
                            content_type='text/plain',
                            status=500
                        )
                    elif pdf_data.startswith(b'%PDF'):
                        response = HttpResponse(pdf_data, content_type='application/pdf')
                        # Clean filename - remove special characters
                        safe_name = "".join(c for c in guest.name if c.isalnum() or c in (' ', '-', '_')).strip()
                        safe_name = safe_name.replace(' ', '_')
                        filename = f"Statement_of_Account_{safe_name}_{timezone.now().strftime('%Y%m%d')}.pdf"
                        response['Content-Disposition'] = f'attachment; filename="{filename}"'
                        response['Content-Length'] = str(len(pdf_data))
                        print(f"[PDF] Returning PDF response with filename: {filename}, size: {len(pdf_data)} bytes")
                        return response
                    else:
                        print(f"[PDF] ERROR: Generated data is not a valid PDF! First bytes: {pdf_data[:50]}")
                        return HttpResponse(
                            f'Error: Generated file is not a valid PDF. Size: {len(pdf_data)} bytes',
                            content_type='text/plain',
                            status=500
                        )
                else:
                    # If PDF generation fails, return error response
                    print(f"[PDF] PDF generation error: {pdf.err}")
                    return HttpResponse(
                        f'Error generating PDF: {pdf.err}',
                        content_type='text/plain',
                        status=500
                    )
            except Exception as pdf_error:
                import traceback
                print(f"[PDF] PDF generation exception: {pdf_error}")
                print(f"[PDF] Traceback: {traceback.format_exc()}")
                return HttpResponse(
                    f'Error generating PDF: {str(pdf_error)}',
                    content_type='text/plain',
                    status=500
                )
        else:
            # If xhtml2pdf is not available, return error
            print("[PDF] ERROR: xhtml2pdf library not available!")
            return HttpResponse(
                'PDF generation library (xhtml2pdf) is not installed. Please install it using: pip install xhtml2pdf',
                content_type='text/plain',
                status=500
            )
        
    except Exception as e:
        import traceback
        print(f"[PDF] Error generating PDF statement: {e}")
        print(f"[PDF] Traceback: {traceback.format_exc()}")
        # Return error as plain text instead of redirecting
        return HttpResponse(
            f'Error generating PDF: {str(e)}\n\nTraceback:\n{traceback.format_exc()}',
            content_type='text/plain',
            status=500
        )

@decorator.role_required('staff', 'SUPER_ADMIN')
def message(request):
    """Front Office/Personnel messenger view"""
    receiver_role = request.GET.get('receiver_role', 'Admin')
    # Base on app service, not user role
    current_service = 'Personnel'

    # Build a deterministic room name based on simplified roles (order-insensitive)
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

    # ULTRA-SIMPLE: ONLY filter by conversation_room - nothing else!
    # This ensures each chatbox ONLY shows messages for that specific conversation
    try:
        # Check if conversation_room field exists
        Message._meta.get_field('conversation_room')
        field_exists = True
    except:
        field_exists = False
    
    if field_exists:
        # ONLY show messages with the exact conversation_room - no fallback, no exceptions!
        messages_qs = Message.objects.filter(conversation_room=room_name).order_by('created_at')
    else:
        # If field doesn't exist (migration not run), compute room on-the-fly for each message
        all_messages = Message.objects.all()
        matching_messages = []
        
        for msg in all_messages:
            # Compute room for this message the same way it's computed when saving
            sender_context = simplify_role(msg.sender_service) if msg.sender_service else simplify_role(msg.sender_role)
            receiver_context = simplify_role(msg.receiver_role)
            conv_roles = sorted([sender_context, receiver_context])
            msg_room = f"chat_{'_'.join([r.replace(' ', '_') for r in conv_roles])}"
            
            if msg_room == room_name:
                matching_messages.append(msg.id)
        
        messages_qs = Message.objects.filter(id__in=matching_messages).order_by('created_at')
    
    # Debug logging
    print(f"\n[PERSONNEL MESSENGER] ========================================")
    print(f"[PERSONNEL MESSENGER] Viewing chat with: {receiver_role}")
    print(f"[PERSONNEL MESSENGER] Conversation room: {room_name}")
    print(f"[PERSONNEL MESSENGER] Found {messages_qs.count()} messages in this room")
    print(f"[PERSONNEL MESSENGER] ========================================\n")

    # Attach sender usernames for display consistency
    for msg in messages_qs:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"

    return render(request, 'staff/messages.html', {
        'room_name': room_name,
        'receiver_role': receiver_role,
        'messages': messages_qs,
        'current_user_id': request.user.id,
        'current_service': current_service,
    })