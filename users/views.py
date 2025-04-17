from urllib import request
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login as auth_login
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
                return redirect('admin_dashboard')  # or your actual url name
            elif user.role == 'personnel':
                return redirect('personnel_dashboard')
            else:
                return redirect('default_dashboard')  # fallback
        else:
            return render(request, "registration/login.html", {"error": "Invalid credentials"}) 
    return render(request, "registration/login.html")
