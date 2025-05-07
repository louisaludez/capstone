from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import *
# Create your views here.
@login_required(login_url='login')
def home(request):
    
    return render(request, "home.html")
