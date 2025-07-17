from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from users.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from staff.models import Guest , Booking
from laundry.models import LaundryTransaction
from datetime import datetime

# Helper to map general and specific roles
def get_related_roles(role):
    role_mappings = {
        'Personnel': ['staff_personnel', 'manager_personnel', 'Personnel'],
        'Concierge': ['staff_concierge', 'manager_concierge', 'Concierge'],
        'Laundry': ['staff_laundry', 'manager_laundry', 'Laundry'],
        'Cafe': ['staff_cafe', 'manager_cafe', 'Cafe'],
        'Room Service': ['staff_room_service', 'manager_room_service', 'Room Service'],
        'Admin': ['admin', 'Admin']
    }
    for general_role, specific_roles in role_mappings.items():
        if role in specific_roles:
            return specific_roles
    return role_mappings.get(role, [role])


def staff_laundry_home(request):
    guests = Guest.objects.all()
    return render(request, 'staff_laundry/dd.html',{
        'guests': guests,                                     
    })

@decorator.role_required('staff_laundry')
def staff_laundry_messages(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')
    user_role = request.user.role

    user_roles = get_related_roles(user_role)
    receiver_roles = get_related_roles(receiver_role)

    sorted_roles = sorted([user_role, receiver_role])
    room_name = f"chat_{'_'.join(sorted_roles)}".replace(' ', '_')

    messages_qs = Message.objects.filter(
        (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles)) |
        (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    ).order_by('created_at')

    for message in messages_qs:
        try:
            sender = CustomUser.objects.get(id=message.sender_id)
            message.sender_username = sender.username
        except CustomUser.DoesNotExist:
            message.sender_username = "Unknown User"

    try:
        receiver = CustomUser.objects.filter(role__in=receiver_roles).first()
        receiver_username = receiver.username if receiver else "Unknown"
    except:
        receiver_username = "Unknown"

    return render(request, "staff_laundry/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "receiver_username": receiver_username,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@decorator.role_required('staff_laundry')
def staff_laundry_orders(request):
    # You’ll eventually load laundry orders from your new model here
    return render(request, "staff_laundry/orders.html")


def getGuest(request, guest_id):
    if request.method == 'GET':
        print(f"Fetching guest with ID: {guest_id}")
        try:
            latest_booking = Booking.objects.filter(guest_id=guest_id).latest('booking_date')
            response_data = {
                'guest_id': guest_id,
                'room': latest_booking.room,
            }
            print(f"Latest booking found: {response_data}")
            return JsonResponse(response_data)
        except Booking.DoesNotExist:
            return JsonResponse({'error': 'Guest has no booking'}, status=404)


def create_laundry_order(request):
    if request.method == 'POST':
        try:
            # Handle both JSON and form-encoded POSTs
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            print("✅ [DEBUG] Laundry order data received:", data)
            print("✅ [DEBUG] Request method:", request.method)
            print("✅ [DEBUG] Content type:", request.content_type)
            print("✅ [DEBUG] Path:", request.path)

            # Extract data
            guest_input = data.get('guest')  # just for logging
            guest_id = data.get('guest_id')  # new: used for lookup
            room_number = data.get('room_number')
            no_bags = int(data.get('no_bags', 1))
            service_type = data.get('service_type')
            specifications = data.get('specifications', '') or ''
            date_time = data.get('date_time')
            payment_method = data.get('payment_method', 'cash')  # 'room' or 'cash'

            # 💰 Pricing
            BASE_PRICE_PER_BAG = 75.00
            total_amount = BASE_PRICE_PER_BAG * no_bags

            print("📊 [DEBUG] Calculated total:", total_amount)

            # Booking lookup
            try:
                booking = Booking.objects.get(room=room_number, guest_id=guest_id)
                guest = booking.guest
                print("📘 [DEBUG] Booking found:", booking)
                print("👤 [DEBUG] Guest resolved:", guest)
            except Booking.DoesNotExist:
                print("❌ [ERROR] No active booking found for room:", room_number)
                return JsonResponse({'success': False, 'message': 'No active booking found for this room.'}, status=404)

            # Create LaundryTransaction
            transaction = LaundryTransaction.objects.create(
                guest=guest,
                booking=booking,
                room_number=room_number,
                service_type=service_type,
                no_of_bags=no_bags,
                specifications=specifications,
                date_time=datetime.strptime(date_time, '%Y-%m-%d'),
                payment_method=payment_method,
                total_amount=total_amount,
            )

            print("✅ [DEBUG] LaundryTransaction created! ID:", transaction.id)
            print ("Payment method:", payment_method)
            # 💸 Update guest billing if charged to room
            if payment_method == 'Charge to room':
                print("💳 [DEBUG] Payment method is 'Charge to Room', updating guest billing.")
                try:
                    current_billing = float(guest.laundry_billing or 0)
                    print(f"💰 [DEBUG] Current guest billing: {current_billing}")
                except ValueError:
                    print("⚠️ [WARN] Guest billing value invalid, resetting to 0")
                    current_billing = 0

                new_billing = current_billing + total_amount
                guest.laundry_billing = str(new_billing)
                guest.save()
                print(f"💰 [DEBUG] Guest billing updated: {current_billing} → {new_billing}")

            return JsonResponse({
                'success': True,
                'message': 'Laundry transaction created successfully.',
                'order_number': transaction.id,
                'calculated_total': total_amount
            })

        except Exception as e:
            print("❌ [ERROR] Exception in laundry order creation:", str(e))
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': 'An error occurred while processing the order.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)