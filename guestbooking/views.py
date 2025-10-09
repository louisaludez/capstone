from django.shortcuts import render
from staff.models import Room, Guest, Booking, Payment  # Import models from staff app
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from datetime import datetime, timedelta
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
    checkin_str = request.GET.get('checkin')
    checkout_str = request.GET.get('checkout')
    rooms_param = request.GET.get('rooms')
    adults_param = request.GET.get('adults')
    children_param = request.GET.get('children')
    child_ages = request.GET.get('childAges', '')

    # Parse counts safely
    try:
        adults = int(adults_param or 2)
    except Exception:
        adults = 2
    try:
        children = int(children_param or 0)
    except Exception:
        children = 0

    # Parse dates; ensure checkout set correctly for dayuse/overnight
    try:
        checkin = datetime.strptime(str(checkin_str), '%Y-%m-%d').date()
    except Exception:
        checkin = timezone.localdate()

    try:
        checkout = datetime.strptime(str(checkout_str), '%Y-%m-%d').date() if checkout_str else None
    except Exception:
        checkout = None

    if stay_type == 'dayuse':
        # Same-day use
        checkout = checkin
    else:
        # Overnight requires at least one night
        if not checkout or checkout <= checkin:
            checkout = checkin + timedelta(days=1)

    logger.debug(f"Search Parameters - Stay Type: {stay_type}, Check-in: {checkin}, Check-out: {checkout}, Rooms: {rooms_param}, Adults: {adults}, Children: {children}, Child Ages: {child_ages}")
    print(f"[guest_booking_results] stay_type={stay_type} checkin={checkin} checkout={checkout} rooms={rooms_param} adults={adults} children={children}")

    # Collect rooms blocked by overlapping bookings within selected range
    # A booking overlaps if: booking.check_in_date <= checkout and booking.check_out_date >= checkin
    overlapping = Booking.objects.filter(
        status__in=['Pending', 'Checked-in'],
        check_in_date__lte=checkout,
        check_out_date__gte=checkin,
    )

    # Normalize room codes to plain numeric strings (e.g., "Room 11 : Deluxe" -> "11")
    import re as _re
    blocked_numbers = set()
    for b in overlapping:
        m = _re.search(r"\d+", str(b.room))
        code = m.group(0) if m else str(b.room)
        blocked_numbers.add(code)

    print(f"[guest_booking_results] blocked room_numbers due to overlap: {sorted(blocked_numbers)}")

    # Start from all rooms that meet capacity, then exclude blocked
    candidate_rooms = Room.objects.filter(capacity__gte=(adults + children))
    available_rooms = candidate_rooms.exclude(room_number__in=blocked_numbers).order_by('room_number')
    blocked_among_candidates = candidate_rooms.filter(room_number__in=blocked_numbers).count()
    candidate_count = candidate_rooms.count()
    available_count = available_rooms.count()

    print(f"[guest_booking_results] total candidates={candidate_count} available_after_block={available_count} blocked={blocked_among_candidates}")

    context = {
        'stay_type': stay_type,
        'checkin': checkin.strftime('%Y-%m-%d'),
        'checkout': checkout.strftime('%Y-%m-%d'),
        'num_rooms': rooms_param,
        'adults': adults,
        'children': children,
        'child_ages': child_ages,
        'rooms': available_rooms,
        'unavailable_count': blocked_among_candidates,
        'available_count': available_count,
        'candidate_count': candidate_count,
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
            children_below_7 = data.get('children_below_7', 0)

            # Debug log incoming reservation payload
            try:
                logger.info("[save_reservation] payload: %s", data)
                print("[save_reservation] payload:", data)
            except Exception:
                pass
            
            # Create or get guest
            guest, created = Guest.objects.get_or_create(
                email=guest_data.get('email'),
                defaults={
                    'name': f"{guest_data.get('firstName', '')} {guest_data.get('lastName', '')}".strip(),
                    'address': guest_data.get('country', ''),
                    'email': guest_data.get('email'),
                    'mobile': guest_data.get('phone') or None,
                    'date_of_birth': timezone.now().date(),  # Default date
                }
            )

            # If guest existed already, update mobile if provided
            try:
                incoming_mobile = guest_data.get('phone')
                if incoming_mobile and getattr(guest, 'mobile', None) != incoming_mobile:
                    guest.mobile = incoming_mobile
                    guest.save(update_fields=['mobile'])
            except Exception:
                pass
            
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
                no_of_children_below_7=children_below_7,
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
            
            # Debug log saved entities
            try:
                logger.info("[save_reservation] saved: guest=%s booking=%s payment=%s", guest.id, booking.id, payment.id)
                print("[save_reservation] saved guest:", {
                    'id': guest.id,
                    'name': guest.name,
                    'email': guest.email,
                })
                print("[save_reservation] saved booking:", {
                    'id': booking.id,
                    'room': booking.room,
                    'check_in_date': str(booking.check_in_date),
                    'check_out_date': str(booking.check_out_date),
                    'total_of_guests': booking.total_of_guests,
                    'num_of_adults': booking.num_of_adults,
                    'num_of_children': booking.num_of_children,
                    'no_of_children_below_7': booking.no_of_children_below_7,
                    'status': booking.status,
                })
                print("[save_reservation] saved payment:", {
                    'id': payment.id,
                    'method': payment.method,
                    'total_balance': float(payment.total_balance),
                })
            except Exception:
                pass

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
            'guest_mobile': getattr(b.guest, 'mobile', None),
            'check_in_date': b.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': b.check_out_date.strftime('%Y-%m-%d'),
            'room': b.room,
            'status': b.status,
            'total_of_guests': getattr(b, 'total_of_guests', None),
            'num_of_adults': getattr(b, 'num_of_adults', None),
            'num_of_children': getattr(b, 'num_of_children', None),
            'children_below_7': getattr(b, 'no_of_children_below_7', None),
            'payment_method': getattr(payment, 'method', None),
            'billing_address': getattr(payment, 'billing_address', None),
            'total_balance': float(getattr(payment, 'total_balance', 0) or 0),
        })

    # Debug log the results count and sample
    try:
        logger.info("[list_pending_reservations] count=%d", len(results))
        print("[list_pending_reservations] first item:", results[0] if results else None)
    except Exception:
        pass

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

        # Compute and store additional charges from add-ons on the Guest record
        try:
            def _safe_int(val):
                try:
                    return int(val)
                except Exception:
                    return 0

            bed_count = _safe_int(request.POST.get('add_ons[bed]') or request.POST.get('add_ons.bed'))
            pillow_count = _safe_int(request.POST.get('add_ons[pillow]') or request.POST.get('add_ons.pillow'))
            towel_count = _safe_int(request.POST.get('add_ons[towel]') or request.POST.get('add_ons.towel'))

            bed_price = 200
            pillow_price = 50
            towel_price = 30
            addons_total = (bed_count * bed_price) + (pillow_count * pillow_price) + (towel_count * towel_price)

            # Accumulate on guest.additional_charge_billing (string field)
            current_additional_raw = getattr(booking.guest, 'additional_charge_billing', '0') or '0'
            try:
                current_additional = float(current_additional_raw)
            except Exception:
                current_additional = 0.0
            booking.guest.additional_charge_billing = str(current_additional + addons_total)
            booking.guest.save(update_fields=['additional_charge_billing'])

            # Debug log
            try:
                logger.info("[checkin_reservation] addons: bed=%d pillow=%d towel=%d total=%.2f -> guest.additional_charge_billing=%s",
                            bed_count, pillow_count, towel_count, addons_total, booking.guest.additional_charge_billing)
                print("[checkin_reservation] addons computed:", {
                    'bed': bed_count, 'pillow': pillow_count, 'towel': towel_count, 'total': addons_total,
                    'guest_additional_charge_billing': booking.guest.additional_charge_billing
                })
            except Exception:
                pass
        except Exception:
            # Do not fail check-in if addons parse fails
            pass

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