from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "laundryStaff/home.html")
def orders(request):
    return render(request, "laundryStaff/orders.html")
def messages(request):
    return render(request, "laundryStaff/messages.html")