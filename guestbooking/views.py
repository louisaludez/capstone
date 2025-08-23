from django.shortcuts import render
from staff.models import Room  # Import Room model from staff app
from django.db.models import Q
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