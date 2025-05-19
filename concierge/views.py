from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    """
    Display the main concierge dashboard with service options
    """
    
    return render(request, 'concierge/dashboard.html' )

@login_required
def book_tours(request):
    """
    Handle tour booking operations
    """
    {
        'active_page': 'concierge'
    }
    return render(request, 'concierge/book_tours.html' )

@login_required
def book_reservations(request):
    """
    Handle restaurant/venue reservations
    """
    {
        'active_page': 'concierge'
    }
    return render(request, 'concierge/book_reservations.html' )

def messenger(request):
    """
    Handle the messenger functionality for concierge
    """
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "concierge/messenger.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@login_required
def timeline(request):
    return render(request, 'concierge/timeline.html')