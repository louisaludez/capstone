from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from staff.models import Booking
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from chat.models import Message
from users.models import CustomUser
def housekeeping_home(request):
    hk = Housekeeping.objects.all()[:3]
    rooms = []
    for i in range(1, 13):  # Rooms 1–12
        room_number = str(i)
        record = Housekeeping.objects.filter(room_number=room_number).order_by('-created_at').first()
        status = record.status if record else "Vacant"
        rooms.append({
            "number": room_number,
            "status": status
        })
    return render(request, 'housekeeping/housekeeping_home.html', {'housekeeping': hk, 'rooms': rooms})
@csrf_exempt
def update_status(request):
    print("update_status view called")  # Debug
    print(f"Request method: {request.method}")  # Debug

    if request.method == 'POST':
        room_number = request.POST.get('room_no')
        status = request.POST.get('status')
        request_type = request.POST.get('request_type')

        print(f"POST data received - Room Number: {room_number}, Status: {status}, Request Type: {request_type}")  # Debug

        try:
            booking = Booking.objects.get(room=room_number)
            print(f"Booking found: {booking}")  # Debug
            guest = booking.guest.name
            print(f"Guest name: {guest}")  # Debug
        except Booking.DoesNotExist:
            print("No booking found for that room number.")  # Debug
            return JsonResponse({'error': 'Room not found'}, status=404)

        try:
            hk, created = Housekeeping.objects.update_or_create(
                room_number=room_number,
                guest_name=guest,
                request_type=request_type,   # key field for uniqueness
                defaults={
                    'status': status
                }
            )
            if created:
                print(f"New Housekeeping record created: {hk}")  # Debug
                message = f'New housekeeping record created for room {room_number}, service {request_type}, status {status}'
            else:
                print(f"Housekeeping record updated: {hk}")  # Debug
                message = f'Housekeeping record for room {room_number}, service {request_type} updated to {status}'

            return JsonResponse({'message': message}, status=200)

        except Exception as e:
            print(f"Error with update_or_create: {e}")  # Debug
            return JsonResponse({'error': str(e)}, status=500)

    print("Request method was not POST.")  # Debug
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def timeline(request):
    hk_list = Housekeeping.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(hk_list, 5)  # Show 5 tasks per page
    page = request.GET.get('page')
    
    try:
        housekeeping_tasks = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        housekeeping_tasks = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        housekeeping_tasks = paginator.page(paginator.num_pages)
    
    context = {
        'housekeeping_tasks': housekeeping_tasks,
        'paginator': paginator,
    }
    
    return render(request, 'housekeeping/timeline.html', context)

@login_required
def view_task(request, task_id):
    task = get_object_or_404(Housekeeping, id=task_id)
    return JsonResponse({
        'id': task.id,
        'room_number': task.room_number,
        'guest_name': task.guest_name,
        'request_type': task.request_type,
        'status': task.status,
        'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Housekeeping, id=task_id)
    
    if request.method == 'POST':
        task.room_number = request.POST.get('room_number')
        task.guest_name = request.POST.get('guest_name')
        task.request_type = request.POST.get('request_type')
        task.status = request.POST.get('status')
        task.save()
        
        messages.success(request, 'Task updated successfully!')
        return JsonResponse({'success': True, 'message': 'Task updated successfully!'})
    
    return JsonResponse({
        'id': task.id,
        'room_number': task.room_number,
        'guest_name': task.guest_name,
        'request_type': task.request_type,
        'status': task.status
    })

@login_required
@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Housekeeping, id=task_id)
    task.delete()
    messages.success(request, 'Task deleted successfully!')
    return JsonResponse({'success': True, 'message': 'Task deleted successfully!'})

@login_required
def messenger(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')
    # Base on app service, not user role
    current_service = 'Room Service'

    # room name deterministic ordering with simplified roles
    def simplify_role(role):
        mapping = {
            'staff_personnel': 'Personnel', 'manager_personnel': 'Personnel', 'personnel': 'Personnel', 'staff': 'Personnel', 'manager': 'Personnel',
            'staff_concierge': 'Concierge', 'manager_concierge': 'Concierge',
            'staff_laundry': 'Laundry', 'manager_laundry': 'Laundry',
            'staff_cafe': 'Cafe', 'manager_cafe': 'Cafe',
            'staff_room_service': 'Room Service', 'manager_room_service': 'Room Service',
            'admin': 'Admin', 'Admin': 'Admin'
        }
        return mapping.get(role, role)

    simplified = sorted([simplify_role(current_service), simplify_role(receiver_role)])
    room_name = f"chat_{'_'.join([s.replace(' ', '_') for s in simplified])}"

    def get_related_roles(role):
        role_mappings = {
            'Personnel': ['staff_personnel', 'manager_personnel', 'Personnel', 'personnel', 'staff', 'manager'],
            'Concierge': ['staff_concierge', 'manager_concierge', 'Concierge'],
            'Laundry': ['staff_laundry', 'manager_laundry', 'Laundry'],
            'Cafe': ['staff_cafe', 'manager_cafe', 'Cafe'],
            'Room Service': ['staff_room_service', 'manager_room_service', 'Room Service'],
            'Admin': ['admin', 'Admin']
        }
        for general, specifics in role_mappings.items():
            if role in specifics:
                return specifics
        return role_mappings.get(role, [role])

    user_roles = get_related_roles(current_service)
    receiver_roles = get_related_roles(receiver_role)

    messages_qs = Message.objects.filter(
        (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles)) |
        (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    ).order_by('created_at')

    for msg in messages_qs:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"

    return render(request, 'housekeeping/messenger.html', {
        'room_name': room_name,
        'receiver_role': receiver_role,
        'messages': messages_qs,
        'current_user_id': request.user.id,
    })