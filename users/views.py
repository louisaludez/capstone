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
            auth_login(request, user)
           
            
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
            
            # Redirect based on role (system has 3 roles: SUPER_ADMIN, admin, staff)
            user_role = getattr(user, 'role', None)
            role_upper = str(user_role).upper() if user_role else ''
            is_super_admin = getattr(user, 'is_superuser', False) or role_upper == 'SUPER_ADMIN'
            
            if is_super_admin:
                return redirect('super_admin_portal')
            if user_role == 'admin':
                return redirect('admin_home')
            # staff or any other role → staff home
            return redirect('HomeStaff')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return render(request, "registration/login.html")
            
    return render(request, "registration/login.html")

def logout_view(request):
    auth_logout(request)
   
    return redirect('login')


@decorator.role_required('SUPER_ADMIN')
def super_admin_portal(request):
    # SUPER_ADMIN or Django is_superuser can access this portal
    user_role = getattr(request.user, 'role', None)
    role_upper = str(user_role).upper() if user_role else ''
    is_super_admin = getattr(request.user, 'is_superuser', False) or role_upper == 'SUPER_ADMIN'
    if not is_super_admin:
        return redirect('login')
    return render(request, 'users/super_admin_portal.html')