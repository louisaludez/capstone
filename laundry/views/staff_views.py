from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from users.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

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

@decorator.role_required('staff_laundry')
def staff_laundry_home(request):
    return render(request, 'staff_laundry/dd.html')

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

@csrf_exempt
def create_laundry_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # ⛔️ Removed Reservation and Room references
            # Placeholder logic here:
            # You should fetch Booking, then link LaundryOrder to it

            # Example placeholder:
            return JsonResponse({
                'success': True,
                'order_number': "TEMP123",
                'message': 'Laundry order created successfully (mock)'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)
