from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from chat.models import Message
from django.db import models

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'room_service/dashboard.html')

@login_required
def notifications(request):
    # For now, just render a simple notifications page
    return render(request, 'room_service/notifications.html', {
        'notifications': [
            {'message': 'New laundry request', 'is_read': False},
            {'message': 'Housekeeping task completed', 'is_read': True},
        ]
    })

@login_required
def tasks(request):
    # For now, just render a simple tasks page
    return render(request, 'room_service/tasks.html', {
        'tasks': [
            {'title': 'Clean room 301', 'status': 'pending'},
            {'title': 'Laundry pickup from room 205', 'status': 'in_progress'},
        ]
    })

@login_required
def timeline(request):
    return render(request, 'room_service/timeline.html')

def room_service_laundry(request):
    return render(request, 'room_service/room_service_laundry.html')

def room_service_housekeeping(request):
    return render(request, 'room_service/room_service_housekeeping.html')

def room_service_cafe(request):
    return render(request, 'room_service/room_service_cafe.html')

def messenger(request): 
    """
    Handle the messenger functionality for room service
    """
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "room_service/messenger.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })