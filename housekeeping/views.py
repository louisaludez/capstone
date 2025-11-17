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
from django.db.models import Q
from chat.models import Message
from users.models import CustomUser
from django.utils import timezone
def housekeeping_home(request):
    hk_list = Housekeeping.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(hk_list, 5)  # Show 5 requests per page
    page = request.GET.get('page')
    
    try:
        housekeeping = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        housekeeping = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        housekeeping = paginator.page(paginator.num_pages)
    
    rooms = []
    today = timezone.localdate()
    for i in range(1, 13):  # Rooms 1–12
        room_number = str(i)

        # Check for active booking today
        has_booking_today = Booking.objects.filter(
            room=room_number,
            status='Checked-in',
            check_in_date__lte=today,
            check_out_date__gte=today,
        ).exists()

        # Get the most recent housekeeping record for this room
        record = Housekeeping.objects.filter(room_number=room_number).order_by('-created_at').first()

        status_class = 'vacant'
        if record and record.status:
            s = record.status.strip().lower()
            print(f"Room {room_number}: record status='{record.status}', lowercase='{s}', has_booking={has_booking_today}")
            # Check for maintenance status first (applies regardless of booking)
            if 'maintenance' in s or 'under maintenance' in s:
                status_class = 'maintenance'
                print(f"  -> Setting status_class to 'maintenance'")
            elif 'no requests' in s or 'no request' in s:
                # "No requests" means room is vacant (no housekeeping needed)
                status_class = 'vacant'
                print(f"  -> Setting status_class to 'vacant' (no requests)")
            elif 'pending' in s:
                # Show pending regardless of booking status (persists after checkout)
                status_class = 'pending'
                print(f"  -> Setting status_class to 'pending' (persists regardless of booking)")
            elif 'progress' in s or 'in progress' in s:
                # Show progress regardless of booking status (persists after checkout)
                status_class = 'progress'
                print(f"  -> Setting status_class to 'progress' (persists regardless of booking)")
            else:
                # For other statuses or no specific status, check booking
                if has_booking_today:
                    status_class = 'vacant'
                    print(f"  -> Setting status_class to 'vacant' (has booking but no active housekeeping status)")
                else:
                    status_class = 'vacant'
                    print(f"  -> Setting status_class to 'vacant' (default)")
        else:
            # No housekeeping record - check if there's a booking
            if has_booking_today:
                status_class = 'vacant'
                print(f"Room {room_number}: No record but has booking -> 'vacant'")
            else:
                status_class = 'vacant'
                print(f"Room {room_number}: No record or no status -> 'vacant'")

        rooms.append({
            "number": room_number,
            "status_class": status_class,
            "has_booking_today": has_booking_today,
        })

    return render(request, 'housekeeping/housekeeping_home.html', {
        'housekeeping': housekeeping,
        'paginator': paginator,
        'rooms': rooms
    })
@csrf_exempt
def update_status(request):
    print("=" * 50)
    print("=== UPDATE_STATUS VIEW CALLED ===")
    print(f"Request method: {request.method}")
    print("=" * 50)

    if request.method == 'POST':
        room_number = request.POST.get('room_no')
        status = request.POST.get('status')
        request_type = request.POST.get('request_type')

        print(f"POST data received:")
        print(f"  - Room Number: {room_number}")
        print(f"  - Status: {status}")
        print(f"  - Request Type: {request_type}")
        print(f"  - All POST data: {dict(request.POST)}")

        # Check if status is "Under Maintenance" (case-insensitive)
        status_lower = status.lower() if status else ''
        is_under_maintenance = 'maintenance' in status_lower or 'under maintenance' in status_lower
        print(f"Status check:")
        print(f"  - Status (lowercase): '{status_lower}'")
        print(f"  - Is Under Maintenance: {is_under_maintenance}")

        # Check if there's a checked-in guest for this room today
        today = timezone.localdate()
        print(f"  - Today's date: {today}")
        
        booking = Booking.objects.filter(
            room=room_number,
            status='Checked-in',
            check_in_date__lte=today,
            check_out_date__gte=today,
        ).order_by('-booking_date').first()

        has_checked_in_guest = booking is not None
        print(f"Booking check:")
        print(f"  - Booking found: {booking}")
        print(f"  - Has checked-in guest: {has_checked_in_guest}")

        # If trying to set under-maintenance and there's a checked-in guest, prevent it
        if is_under_maintenance and has_checked_in_guest:
            print("❌ BLOCKED: Cannot set under-maintenance when guest is checked in")
            return JsonResponse({
                'error': 'Cannot set room to Under Maintenance when there is a checked-in guest.',
                'has_guest': True
            }, status=400)
        
        if is_under_maintenance and not has_checked_in_guest:
            print("✓ ALLOWED: Setting under-maintenance (no guest checked in)")

        # Get guest name if booking exists, otherwise use None
        # Allow status updates even when there's no guest (for under-maintenance and other statuses)
        guest_name = booking.guest.name if booking else None
        print(f"Guest name: {guest_name}")

        try:
            print("Attempting to update/create housekeeping record...")
            # Check if status is "No requests"
            is_no_requests = status and ('no requests' in status.lower() or 'no request' in status.lower())
            
            # For "Under Maintenance" and "No requests", use room_number and status as unique key
            # For other statuses, use room_number and request_type as unique key
            if is_under_maintenance or is_no_requests:
                # Use room_number and status as the key for maintenance/no requests status
                # This allows one maintenance or no-requests record per room
                # Delete any existing records for this room with different statuses first
                Housekeeping.objects.filter(room_number=room_number).exclude(status=status).delete()
                
                hk, created = Housekeeping.objects.update_or_create(
                    room_number=room_number,
                    status=status,
                    defaults={
                        'request_type': request_type or 'Room Status Update',
                        'guest_name': guest_name
                    }
                )
            else:
                # For other statuses, use room_number and request_type as unique keys
                # But first, delete any "No requests" or "Under Maintenance" records for this room
                Housekeeping.objects.filter(
                    room_number=room_number
                ).filter(
                    Q(status__icontains='no requests') | 
                    Q(status__icontains='no request') | 
                    Q(status__icontains='maintenance') | 
                    Q(status__icontains='under maintenance')
                ).delete()
                
                hk, created = Housekeeping.objects.update_or_create(
                    room_number=room_number,
                    request_type=request_type,
                    defaults={
                        'status': status,
                        'guest_name': guest_name
                    }
                )
            if created:
                print(f"✓ New Housekeeping record created: {hk}")
                message = f'New housekeeping record created for room {room_number}, service {request_type}, status {status}'
            else:
                print(f"✓ Housekeeping record updated: {hk}")
                message = f'Housekeeping record for room {room_number}, service {request_type} updated to {status}'

            response_data = {
                'message': message,
                'has_guest': has_checked_in_guest,
                'status': status
            }
            print(f"Response data: {response_data}")
            print("=" * 50)
            return JsonResponse(response_data, status=200)

        except Exception as e:
            print(f"❌ ERROR with update_or_create: {e}")
            import traceback
            print(traceback.format_exc())
            print("=" * 50)
            return JsonResponse({'error': str(e)}, status=500)

    print("❌ Request method was not POST.")
    print("=" * 50)
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
        # Update room_number if provided
        room_number = request.POST.get('room_number')
        if room_number:
            task.room_number = room_number
        
        # Preserve guest_name if empty string is submitted (don't overwrite existing value)
        guest_name = request.POST.get('guest_name', '').strip()
        if guest_name:
            task.guest_name = guest_name
        # If empty, preserve the existing guest_name (don't overwrite with empty string)
        # This prevents losing the customer name when only updating status
        
        # Update request_type if provided
        request_type = request.POST.get('request_type', '').strip()
        if request_type:
            task.request_type = request_type
        
        # Update status if provided
        status = request.POST.get('status')
        if status:
            task.status = status
        
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
    
    # Get the actual user's role (simplified) - messages are saved with the user's actual role
    from users.models import CustomUser
    user = request.user
    user_actual_role = user.role if hasattr(user, 'role') else None

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
    
    # Also get simplified roles for matching (messages are saved with simplified roles)
    simplified_user_role = simplify_role(current_service)
    simplified_receiver_role = simplify_role(receiver_role)
    
    # Get the user's actual simplified role (for matching messages they sent)
    simplified_user_actual_role = simplify_role(user_actual_role) if user_actual_role else None
    user_actual_roles = get_related_roles(user_actual_role) if user_actual_role else []
    
    # Build query conditions
    # Show messages in the conversation between current_service and receiver_role
    # Match on sender_service to find messages sent from this service/app context
    query_conditions = models.Q()
    
    # Primary match: Messages sent from this service context (e.g., Room Service -> Admin)
    query_conditions |= (models.Q(sender_service=simplified_user_role) & models.Q(receiver_role=simplified_receiver_role))
    query_conditions |= (models.Q(sender_service=simplified_user_role) & models.Q(receiver_role__in=receiver_roles))
    
    # Also match messages where receiver sent to this service (Admin -> Room Service)
    query_conditions |= (models.Q(sender_role=simplified_receiver_role) & models.Q(receiver_role=simplified_user_role))
    query_conditions |= (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role=simplified_user_role))
    query_conditions |= (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    
    # Match on expanded role lists (for backward compatibility with old messages without sender_service)
    query_conditions |= (models.Q(sender_role=simplified_user_role) & models.Q(receiver_role=simplified_receiver_role))
    query_conditions |= (models.Q(sender_role=simplified_receiver_role) & models.Q(receiver_role=simplified_user_role))
    query_conditions |= (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles))
    query_conditions |= (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    
    messages_qs = Message.objects.filter(query_conditions).order_by('created_at')
    
    print(f"[messenger] Querying messages:")
    print(f"  user_roles={user_roles}")
    print(f"  receiver_roles={receiver_roles}")
    print(f"  simplified_user_role='{simplified_user_role}'")
    print(f"  simplified_receiver_role='{simplified_receiver_role}'")
    print(f"  user_actual_role='{user_actual_role}'")
    print(f"  simplified_user_actual_role='{simplified_user_actual_role}'")
    print(f"  user_actual_roles={user_actual_roles}")
    print(f"  Found {messages_qs.count()} messages")
    
    # Debug: Print first few messages to see what's in the database
    all_messages = Message.objects.all().order_by('-created_at')[:5]
    print(f"[messenger] Recent messages in DB:")
    for m in all_messages:
        print(f"  ID={m.id}, sender_role='{m.sender_role}', receiver_role='{m.receiver_role}', body='{m.body[:30]}...'")

    # Convert queryset to list to ensure it's evaluated and messages are available
    messages_list = list(messages_qs)
    for msg in messages_list:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"
    
    print(f"[messenger] Passing {len(messages_list)} messages to template")

    return render(request, 'housekeeping/messenger.html', {
        'room_name': room_name,
        'receiver_role': receiver_role,
        'messages': messages_list,
        'current_user_id': request.user.id,
        'current_service': current_service,
    })