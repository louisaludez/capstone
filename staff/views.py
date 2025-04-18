from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from globals import decorator
# Create your views here.
@decorator.role_required('staff')
def home(request):
    return render(request, "staff/home.html")
def message(request):
    return render(request, "staff/messages.html")