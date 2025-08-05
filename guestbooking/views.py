from django.shortcuts import render

# Create your views here.
def guest_booking_home(request):
    return render(request, 'guestbooking/home.html')