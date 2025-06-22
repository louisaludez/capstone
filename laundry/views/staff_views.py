from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from users.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import LaundryOrder, LaundryItem
from staff.models import Room, Reservation
from django.utils import timezone
import json

def get_related_roles(role):
    role_mappings = {
        'Personnel': ['staff_personnel', 'manager_personnel', 'Personnel'],
        'Concierge': ['staff_concierge', 'manager_concierge', 'Concierge'],
        'Laundry': ['staff_laundry', 'manager_laundry', 'Laundry'],
        'Cafe': ['staff_cafe', 'manager_cafe', 'Cafe'],
        'Room Service': ['staff_room_service', 'manager_room_service', 'Room Service'],
        'Admin': ['admin', 'Admin']
    }
    # If the role is a specific role (e.g., staff_laundry), find its general role
    for general_role, specific_roles in role_mappings.items():
        if role in specific_roles:
            return specific_roles
    return role_mappings.get(role, [role])

def staff_laundry_home(request):
    return render(request, 'staff_laundry/dd.html')

def staff_laundry_messages(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')  # Default to Admin for staff
    user_role = request.user.role  # Get user_role first
    
    # Get all related roles for both user and receiver
    user_roles = get_related_roles(user_role)
    receiver_roles = get_related_roles(receiver_role)
    
    # Create a consistent room name by sorting roles
    sorted_roles = sorted([user_role, receiver_role])
    room_name = f"chat_{'_'.join(sorted_roles)}".replace(' ', '_')
    
    # Get messages
    messages_qs = Message.objects.filter(
        (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles)) |
        (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    ).order_by('created_at')

    # Fetch usernames for each message
    for message in messages_qs:
        try:
            sender = CustomUser.objects.get(id=message.sender_id)
            message.sender_username = sender.username
        except CustomUser.DoesNotExist:
            message.sender_username = "Unknown User"

    # Get receiver information
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

def staff_laundry_orders(request):
    return render(request,"staff_laundry/orders.html")

@csrf_exempt
def create_laundry_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get or create reservation and room
            reservation = Reservation.objects.get(id=data.get('customer_id'))
            room = Room.objects.get(id=data.get('room_id'))
            
            # Create the laundry order
            order = LaundryOrder.objects.create(
                customer=reservation,
                room=room,
                service_type=data.get('service_type'),
                item_type=data.get('item_type'),
                quantity=data.get('quantity'),
                weight=data.get('weight'),
                special_instructions=data.get('special_instructions', ''),
                payment_method='cash',
                total_amount=data.get('total_amount'),
                is_paid=True,
                status='pending'
            )
            
            # Create laundry items
            for item in data.get('items', []):
                LaundryItem.objects.create(
                    order=order,
                    category=item.get('category'),
                    description=item.get('description'),
                    quantity=item.get('quantity'),
                    price_per_item=item.get('price_per_item'),
                    special_instructions=item.get('special_instructions', '')
                )
            
            return JsonResponse({
                'success': True,
                'order_number': order.order_number,
                'message': 'Laundry order created successfully'
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

