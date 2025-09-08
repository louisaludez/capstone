from django.shortcuts import render
from staff.models import Room, Guest, Booking, Payment  # Import models from staff app
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
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