from django.shortcuts import render

# Create your views here.
def guest_booking_home(request):
    return render(request, 'guestbooking/home.html')


def guest_booking_results(request):
    # Read query params
    stay_type = request.GET.get('stayType', 'overnight')
    checkin = request.GET.get('checkin')
    checkout = request.GET.get('checkout')
    rooms = request.GET.get('rooms')
    adults = request.GET.get('adults')
    children = request.GET.get('children')
    child_ages = request.GET.get('childAges', '')

    context = {
        'stay_type': stay_type,
        'checkin': checkin,
        'checkout': checkout,
        'rooms': rooms,
        'adults': adults,
        'children': children,
        'child_ages': child_ages,
    }

    return render(request, 'guestbooking/results.html', context)