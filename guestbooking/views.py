from django.shortcuts import render
from staff.models import Room, Guest, Booking, Payment  # Import models from staff app
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def guest_booking_home(request):
    return render(request, 'guestbooking/home.html')


def guest_booking_results(request):
    # Read query params
    stay_type = request.GET.get('stayType', 'overnight')
    checkin = request.GET.get('checkin')
    checkout = request.GET.get('checkout')
    rooms = request.GET.get('rooms')
    adults = request.GET.get('adults')
    children = request.GET.get('children')
    child_ages = request.GET.get('childAges', '')

    # Debug: Log query parameters
    logger.debug(f"Search Parameters - Stay Type: {stay_type}, Check-in: {checkin}, Check-out: {checkout}, Rooms: {rooms}, Adults: {adults}, Children: {children}, Child Ages: {child_ages}")
    print(f"DEBUG: Stay Type: {stay_type}, Check-in: {checkin}, Check-out: {checkout}, Rooms: {rooms}, Adults: {adults}, Children: {children}, Child Ages: {child_ages}")

    # Query the database for available rooms
    available_rooms = Room.objects.filter(
        capacity__gte=int(adults) + int(children),
        status='available'  # Check if the room status is available
    )

    # Debug: Log the number of available rooms
    logger.debug(f"Number of available rooms: {available_rooms.count()}")
    print(f"DEBUG: Number of available rooms: {available_rooms.count()}")

    # Print available room information
    for room in available_rooms:
        print(f"Room Number: {room.room_number}")
        print(f"Room Type: {room.get_room_type_display()}")
        print(f"Status: {room.get_status_display()}")
        print(f"Capacity: {room.capacity}")
        print(f"Price per Night: {room.price_per_night}")
        print(f"Description: {room.description}")
        print(f"Amenities: {room.amenities}")
        print(f"Accessible: {room.is_accessible}")
        print(f"Balcony: {room.has_balcony}")
        print(f"Ocean View: {room.has_ocean_view}")
        print(f"Created At: {room.created_at}")
        print(f"Updated At: {room.updated_at}")
        print("-" * 40)

    context = {
        'stay_type': stay_type,
        'checkin': checkin,
        'checkout': checkout,
        'rooms': rooms,
        'adults': adults,
        'children': children,
        'child_ages': child_ages,
        'rooms': available_rooms,  # Pass the rooms to the template
    }

    return render(request, 'guestbooking/results.html', context)


def book_reservation(request):
    """Display the book reservation page with guest information form"""
    return render(request, 'guestbooking/book_reservation.html')


def payment(request):
    """Display the payment page (placeholder for now)"""
    return render(request, 'guestbooking/payment.html')


def confirmation(request):
    """Display the confirmation page after successful reservation"""
    return render(request, 'guestbooking/confirmation.html')


@csrf_exempt
def save_reservation(request):
    """Save reservation data to database"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract data
            guest_data = data.get('guest', {})
            payment_data = data.get('payment', {})
            room_id = data.get('room_id')
            check_in_date = data.get('check_in_date')
            check_out_date = data.get('check_out_date')
            num_of_adults = data.get('num_of_adults', 2)
            num_of_children = data.get('num_of_children', 0)
            
            # Create or get guest
            guest, created = Guest.objects.get_or_create(
                email=guest_data.get('email'),
                defaults={
                    'name': f"{guest_data.get('firstName', '')} {guest_data.get('lastName', '')}".strip(),
                    'address': guest_data.get('country', ''),
                    'email': guest_data.get('email'),
                    'date_of_birth': timezone.now().date(),  # Default date
                }
            )
            
            # Get room
            try:
                room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                return JsonResponse({'error': 'Room not found'}, status=400)
            
            # Create booking
            booking = Booking.objects.create(
                guest=guest,
                room=room.room_number,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                total_of_guests=num_of_adults + num_of_children,
                num_of_adults=num_of_adults,
                num_of_children=num_of_children,
                status='Pending'
            )
            
            # Create payment
            payment = Payment.objects.create(
                booking=booking,
                method='card',
                card_number=payment_data.get('cardNumber', ''),
                exp_date=payment_data.get('expiryDate', ''),
                cvc_code=payment_data.get('cvc', ''),
                total_balance=room.price_per_night
            )
            
            # Update room status
            room.status = 'reserved'
            room.save()
            
            # Generate reference number
            reference_number = f"{booking.id:05d}"
            
            return JsonResponse({
                'success': True,
                'guest_name': guest.name,
                'room_number': room.room_number,
                'reference_number': reference_number,
                'booking_id': booking.id
            })
            
        except Exception as e:
            logger.error(f"Error saving reservation: {str(e)}")
            return JsonResponse({'error': 'Failed to save reservation'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def list_pending_reservations(request):
    """Return all pending reservations for use in check-in modal (searchable list)."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    query = request.GET.get('q', '').strip().lower()

    bookings_qs = Booking.objects.select_related('guest').filter(status='Pending').order_by('-booking_date')

    if query:
        bookings_qs = bookings_qs.filter(
            Q(guest__name__icontains=query) |
            Q(room__icontains=query)
        )

    results = []
    for b in bookings_qs:
        payment = None
        try:
            payment = Payment.objects.get(booking=b)
        except Payment.DoesNotExist:
            payment = None

        results.append({
            'id': b.id,
            'ref': f"{b.id:05d}",
            'guest_name': b.guest.name,
            'guest_email': b.guest.email,
            'guest_address': b.guest.address,
            'check_in_date': b.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': b.check_out_date.strftime('%Y-%m-%d'),
            'room': b.room,
            'status': b.status,
            'payment_method': getattr(payment, 'method', None),
            'billing_address': getattr(payment, 'billing_address', None),
            'total_balance': float(getattr(payment, 'total_balance', 0) or 0),
        })

    return JsonResponse({'reservations': results})


def checkin_reservation(request):
    """Check in an existing reservation (must be status Pending)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

    try:
        booking_id = request.POST.get('booking_id')
        if not booking_id:
            return JsonResponse({'success': False, 'message': 'Reservation is required for check-in.'}, status=400)

        # Fetch booking and validate status
        booking = Booking.objects.select_related('guest').get(id=booking_id)
        if booking.status != 'Pending':
            return JsonResponse({'success': False, 'message': 'Only pending reservations can be checked in.'}, status=400)

        # Parse dates (fallback to existing if not provided)
        raw_check_in = request.POST.get('check_in')
        raw_check_out = request.POST.get('check_out')
        if raw_check_in:
            booking.check_in_date = parse_date(str(raw_check_in))
        if raw_check_out:
            booking.check_out_date = parse_date(str(raw_check_out))

        # Room (keep reserved room if not provided)
        room_number = request.POST.get('room') or booking.room
        booking.room = room_number

        # Guest counts
        if request.POST.get('total_guests') is not None:
            booking.total_of_guests = int(request.POST.get('total_guests') or 0)
        if request.POST.get('adults') is not None:
            booking.num_of_adults = int(request.POST.get('adults') or 0)
        if request.POST.get('children') is not None:
            booking.num_of_children = int(request.POST.get('children') or 0)
        if request.POST.get('children_7_years') is not None:
            booking.no_of_children_below_7 = int(request.POST.get('children_7_years') or 0)

        booking.status = 'Checked-in'
        booking.save()

        # Update room status to occupied
        try:
            room_obj = Room.objects.get(room_number=room_number)
            room_obj.status = 'occupied'
            room_obj.save()
        except Room.DoesNotExist:
            # If room record not found, continue; front-end still succeeds but logs warning
            pass

        # Payment handling: update existing or create if missing
        payment_method = request.POST.get('payment_method')
        card_number = request.POST.get('card_number')
        exp_date = request.POST.get('exp_date')
        cvc = request.POST.get('cvv')
        billing_address = request.POST.get('billing_address')
        balance_raw = request.POST.get('current_balance') or request.POST.get('balance')

        try:
            payment = Payment.objects.get(booking=booking)
        except Payment.DoesNotExist:
            payment = Payment(booking=booking)

        if payment_method:
            payment.method = payment_method
        if card_number is not None:
            payment.card_number = card_number
        if exp_date is not None:
            payment.exp_date = exp_date
        if cvc is not None:
            payment.cvc_code = cvc
        if billing_address is not None:
            payment.billing_address = billing_address
        if balance_raw is not None:
            try:
                payment.total_balance = Decimal(str(balance_raw))
            except Exception:
                pass

        payment.save()

        return JsonResponse({'success': True, 'message': f'Reservation {booking_id} checked in successfully.'})

    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Reservation not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)
def reservation_details(request):
    """Display a paginated list of reservations similar to the provided UI."""
    bookings = (
        Booking.objects.select_related('guest')
        .order_by('-booking_date')
    )

    page_number = request.GET.get('page', 1)
    paginator = Paginator(bookings, 5)  # Show 5 rows per page to match the screenshot
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'paginator': paginator,
    }
    return render(request, 'guestbooking/reservation_details.html', context)