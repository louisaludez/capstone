from django.shortcuts import render
from globals import decorator

from users.models import CustomUser  # Replace 'your_app' with the actual app name where CustomUser is defined
# Create your views here.
@decorator.role_required('admin')
def home(request):
    users = CustomUser.objects.all()  # Assuming you have a User model
    # Print the username of each user

    return render(request, "hmsAdmin/home.html", {"users": users})

@decorator.role_required('admin')
def messages(request):
    return render(request, "hmsAdmin/messages.html")

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

