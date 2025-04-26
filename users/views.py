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
            elif user.role == 'staff':
                return redirect('HomeStaff')
            elif user.role == 'supervisor_laundry':
                return redirect('supervisor_laundry_home')
           
             # fallback
        else:
            return render(request, "registration/login.html", {"error": "Invalid credentials"}) 
    return render(request, "registration/login.html")
def logout_view(request):
    auth_logout(request)
    return redirect('login')