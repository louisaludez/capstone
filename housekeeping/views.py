from django.shortcuts import render
from .models import *
from staff.models import Booking
from django.http import JsonResponse
def housekeeping_home(request):
    hk = Housekeeping.objects.all()[:3]
    rooms = []
    for i in range(1, 13):  # Rooms 1–12
        room_number = str(i)
        record = Housekeeping.objects.filter(room_number=room_number).order_by('-created_at').first()
        status = record.status if record else "Vacant"
        rooms.append({
            "number": room_number,
            "status": status
        })
    return render(request, 'housekeeping/housekeeping_home.html', {'housekeeping': hk, 'rooms': rooms})
def update_status(request):
    print("update_status view called")  # Debug
    print(f"Request method: {request.method}")  # Debug

    if request.method == 'POST':
        room_number = request.POST.get('room_no')
        status = request.POST.get('status')
        request_type = request.POST.get('request_type')

        print(f"POST data received - Room Number: {room_number}, Status: {status}, Request Type: {request_type}")  # Debug

        try:
            booking = Booking.objects.get(room=room_number)
            print(f"Booking found: {booking}")  # Debug
            guest = booking.guest.name
            print(f"Guest name: {guest}")  # Debug
        except Booking.DoesNotExist:
            print("No booking found for that room number.")  # Debug
            return JsonResponse({'error': 'Room not found'}, status=404)

        try:
            hk, created = Housekeeping.objects.update_or_create(
                room_number=room_number,
                guest_name=guest,
                request_type=request_type,   # key field for uniqueness
                defaults={
                    'status': status
                }
            )
            if created:
                print(f"New Housekeeping record created: {hk}")  # Debug
                message = f'New housekeeping record created for room {room_number}, service {request_type}, status {status}'
            else:
                print(f"Housekeeping record updated: {hk}")  # Debug
                message = f'Housekeeping record for room {room_number}, service {request_type} updated to {status}'

            return JsonResponse({'message': message}, status=200)

        except Exception as e:
            print(f"Error with update_or_create: {e}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)

    print("Request method was not POST.")  # Debug
    return JsonResponse({'error': 'Invalid request method'}, status=405)
def timeline(request):
    hk = Housekeeping.objects.all()
    return render(request, 'housekeeping/timeline.html', {'housekeeping_tasks': hk})