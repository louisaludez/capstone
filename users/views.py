from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import CustomUserCreationForm

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # 👇 Check the role and redirect accordingly
            if user.role == 'admin':
                return redirect('HomeAdmin')  
            elif user.role == 'personnel':
                return redirect('HomeStaff')
            elif user.role == 'supervisor_laundry':
                return redirect('supervisor_laundry_home')
            
            elif user.role == 'staff_laundry':
                return redirect('staff_laundry_home')
             # fallback
            elif user.role == 'supervisor_concierge':
                return redirect('supervisor_concierge_home')
            elif user.role == 'supervisor_cafe':
                return redirect('supervisor_cafe_home')
            elif user.role == 'supervisor_room_service':
                return redirect('supervisor_home_service_home')
            elif user.role == 'supervisor_fnb':
                return redirect('supervisor_fnb_home')
            elif user.role == 'staff_concierge':
                return redirect('staff_concierge_home')
            elif user.role == 'staff_cafe':
                return redirect('staff_cafe_home')
            elif user.role == 'staff_restaurant':
                return redirect('staff_restaurant_home')
            elif user.role == 'staff_room_servie':
                return redirect('staff_room_service_home')
            elif user.role == 'staff_fnb':
                return redirect('staff_fnb_home')
        else:
            return render(request, "registration/login.html", {"error": "Invalid credentials"}) 
    return render(request, "registration/login.html")
def logout_view(request):
    auth_logout(request)
    return redirect('login')