from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required

from globals import decorator
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

def login(request):
    # Check for error query parameters and display appropriate messages
    error_param = request.GET.get('error')
    if error_param == 'login_required':
        messages.error(request, "You must be logged in to access this page. Please log in to continue.")
    elif error_param == 'admin_required':
        messages.error(request, "You must be logged in as an admin or super admin to access this page. Please log in with appropriate credentials.")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, "registration/login.html")
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Debug logging
            print(f"=== USER LOGIN ===")
            print(f"Username: {user.username}")
            print(f"Role: {user.role}")
            print(f"Role Type: {type(user.role)}")
            print(f"Is Superuser: {user.is_superuser}")
            print(f"==================")
            
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            
            # Check if there's a 'next' parameter for redirect after login
            next_url = request.GET.get('next')
            if next_url:
                # Verify user has access to the requested page
                user_role = getattr(user, 'role', None)
                is_admin = user_role == 'admin'
                is_super_admin = getattr(user, 'is_superuser', False) or (user_role and str(user_role).upper() == 'SUPER_ADMIN')
                
                # Only allow redirect to admin pages if user is admin/super_admin
                if '/adminNew/' in next_url and not (is_admin or is_super_admin):
                    messages.error(request, "You do not have permission to access admin pages. Please contact an administrator.")
                    next_url = None
            
            if next_url:
                return redirect(next_url)
            
            # Redirect based on role
            if getattr(user, 'role', '').upper() == 'SUPER_ADMIN':
                return redirect('super_admin_portal')
            if user.role == 'admin':
                return redirect('admin_home')  
            elif user.role == 'personnel':
                return redirect('HomeStaff')
            elif user.role == 'staff':
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
            # Fallback redirect if role doesn't match any case
            return redirect('HomeStaff')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "registration/login.html")
            
    return render(request, "registration/login.html")

def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')


@decorator.role_required('SUPER_ADMIN')
def super_admin_portal(request):
    # Only SUPER_ADMIN can access this portal selection page
    if not hasattr(request.user, 'role') or str(request.user.role).upper() != 'SUPER_ADMIN':
        return redirect('login')
    return render(request, 'users/super_admin_portal.html')