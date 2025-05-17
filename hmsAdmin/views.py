from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from users.models import CustomUser

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

# Create your views here.
@decorator.role_required('admin')
def home(request):
    users = CustomUser.objects.all()
    return render(request, "hmsAdmin/home.html", {"users": users})

@decorator.role_required('admin')
def messages(request):
    # For demo: get receiver_role from GET param, default to 'personnel' if not provided
    receiver_role = request.GET.get('receiver_role', 'Personnel')
    
    # Validate receiver role
    valid_roles = ['Personnel', 'Concierge', 'Laundry', 'Cafe', 'Room Service', 'Admin']
    if receiver_role not in valid_roles:
        receiver_role = 'Personnel'  # Default to Personnel if invalid role
    
    user_role = request.user.role
    
    # Create a consistent room name by sorting roles
    sorted_roles = sorted([user_role, receiver_role])
    room_name = f"chat_{'_'.join(sorted_roles)}".replace(' ', '_')
    
    # Get all related roles for both user and receiver
    user_roles = get_related_roles(user_role)
    receiver_roles = get_related_roles(receiver_role)
    
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

    return render(request, "hmsAdmin/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "receiver_username": receiver_username,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@decorator.role_required('admin')
def training(request):
    return render(request, "hmsAdmin/training.html")

@decorator.role_required('admin')
def analytics(request):
    return render(request, "hmsAdmin/analytics.html")

@decorator.role_required('admin')
def accounts(request):
    users = CustomUser.objects.all()
    return render(request, "hmsAdmin/accounts.html", {"users": users})

