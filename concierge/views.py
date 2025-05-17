from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    """
    Display the main concierge dashboard with service options
    """
    context = {
        'active_page': 'concierge'
    }
    return render(request, 'concierge/dashboard.html', context)

@login_required
def book_tours(request):
    """
    Handle tour booking operations
    """
    context = {
        'active_page': 'concierge'
    }
    return render(request, 'concierge/book_tours.html', context)

@login_required
def book_reservations(request):
    """
    Handle restaurant/venue reservations
    """
    context = {
        'active_page': 'concierge'
    }
    return render(request, 'concierge/book_reservations.html', context)
