from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, "registration/login.html")
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Redirect based on role
            if user.role == 'admin':
                return redirect('HomeAdmin')  
            elif user.role == 'personnel':
                return redirect('HomeStaff')
            elif user.role == 'supervisor_laundry':
                return redirect('supervisor_laundry_home')          
            elif user.role == 'staff_laundry':
                return redirect('staff_laundry_home')
            elif user.role == 'supervisor_concierge':
                return redirect('concierge:dashboard')
            elif user.role == 'supervisor_cafe':
                return redirect('supervisor_cafe_home')
            elif user.role == 'supervisor_room_service':
                return redirect('supervisor_home_service_home')
            elif user.role == 'supervisor_fnb':
                return redirect('supervisor_fnb_home')
            elif user.role == 'staff_concierge':
                return redirect('concierge:dashboard')
            elif user.role == 'staff_cafe':
                return redirect('staff_cafe_home')
            elif user.role == 'staff_restaurant':
                return redirect('staff_restaurant_home')
            elif user.role == 'staff_room_service':
                return redirect('room_service:dashboardrm')
            elif user.role == 'staff_fnb':
                return redirect('staff_fnb_home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "registration/login.html")
            
    return render(request, "registration/login.html")

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')