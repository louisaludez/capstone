from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    return render(request, 'room_service/dashboard.html')

@login_required
def notifications(request):
    # For now, just render a simple notifications page
    return render(request, 'room_service/notifications.html', {
        'notifications': [
            {'message': 'New laundry request', 'is_read': False},
            {'message': 'Housekeeping task completed', 'is_read': True},
        ]
    })

@login_required
def tasks(request):
    # For now, just render a simple tasks page
    return render(request, 'room_service/tasks.html', {
        'tasks': [
            {'title': 'Clean room 301', 'status': 'pending'},
            {'title': 'Laundry pickup from room 205', 'status': 'in_progress'},
        ]
    })
def room_service_laundry(request):
    return render(request, 'room_service/room_service_laundry.html')
def room_service_housekeeping(request):
    return render(request, 'room_service/room_service_housekeeping.html')
def room_service_cafe(request):
    return render(request, 'room_service/room_service_cafe.html')

