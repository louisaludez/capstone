from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models

from users.models import CustomUser  # Replace 'your_app' with the actual app name where CustomUser is defined
# Create your views here.
@decorator.role_required('admin')
def home(request):
    users = CustomUser.objects.all()  # Assuming you have a User model
    # Print the username of each user

    return render(request, "hmsAdmin/home.html", {"users": users})

@decorator.role_required('admin')
def messages(request):
    
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "hmsAdmin/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
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

