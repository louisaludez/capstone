from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='login')
def home(request):
    return render(request, "laundryStaff/home.html")
def orders(request):
    return render(request, "laundryStaff/orders.html")
def messages(request):
    return render(request, "laundryStaff/messages.html")