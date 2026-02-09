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
        # Support multiple request types (checkboxes) or single (legacy)
        request_types = request.POST.getlist('request_types')
        if not request_types and request.POST.get('request_type'):
            request_types = [request.POST.get('request_type')]
        if not request_types:
            request_types = ['Room Status Update']

        print(f"POST data received:")
        print(f"  - Room Number: {room_number}")
        print(f"  - Status: {status}")
        print(f"  - Request Types: {request_types}")
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
            print("Attempting to update/create housekeeping record(s)...")
            # Check if status is "No requests"
            is_no_requests = status and ('no requests' in status.lower() or 'no request' in status.lower())
            
            # For "Under Maintenance" and "No requests", one record per room (single status)
            if is_under_maintenance or is_no_requests:
                Housekeeping.objects.filter(room_number=room_number).exclude(status=status).delete()
                request_type_display = request_types[0] if request_types else 'Room Status Update'
                hk, created = Housekeeping.objects.update_or_create(
                    room_number=room_number,
                    status=status,
                    defaults={
                        'request_type': request_type_display,
                        'guest_name': guest_name
                    }
                )
                message = f'Room {room_number} status updated to {status}.'
            else:
                # For other statuses: create/update one record per selected request type
                Housekeeping.objects.filter(
                    room_number=room_number
                ).filter(
                    Q(status__icontains='no requests') |
                    Q(status__icontains='no request') |
                    Q(status__icontains='maintenance') |
                    Q(status__icontains='under maintenance')
                ).delete()

                created_count = 0
                updated_count = 0
                for request_type in request_types:
                    hk, created = Housekeeping.objects.update_or_create(
                        room_number=room_number,
                        request_type=request_type,
                        defaults={
                            'status': status,
                            'guest_name': guest_name
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                if created_count + updated_count == 1:
                    message = f'Room {room_number}, {request_types[0]}: {status}'
                else:
                    message = f'Room {room_number}: {created_count + updated_count} request(s) set to {status}.'

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

    # ULTRA-SIMPLE: ONLY filter by conversation_room - nothing else!
    # This ensures each chatbox ONLY shows messages for that specific conversation
    try:
        # Check if conversation_room field exists
        Message._meta.get_field('conversation_room')
        field_exists = True
    except:
        field_exists = False
    
    if field_exists:
        # ONLY show messages with the exact conversation_room - no fallback, no exceptions!
        messages_qs = Message.objects.filter(conversation_room=room_name).order_by('created_at')
    else:
        # If field doesn't exist (migration not run), compute room on-the-fly for each message
        all_messages = Message.objects.all()
        matching_messages = []
        
        for msg in all_messages:
            # Compute room for this message the same way it's computed when saving
            sender_context = simplify_role(msg.sender_service) if msg.sender_service else simplify_role(msg.sender_role)
            receiver_context = simplify_role(msg.receiver_role)
            conv_roles = sorted([sender_context, receiver_context])
            msg_room = f"chat_{'_'.join([r.replace(' ', '_') for r in conv_roles])}"
            
            if msg_room == room_name:
                matching_messages.append(msg.id)
        
        messages_qs = Message.objects.filter(id__in=matching_messages).order_by('created_at')
    
    # Debug logging
    print(f"\n[HOUSEKEEPING MESSENGER] ========================================")
    print(f"[HOUSEKEEPING MESSENGER] Viewing chat with: {receiver_role}")
    print(f"[HOUSEKEEPING MESSENGER] Current service: {current_service}")
    print(f"[HOUSEKEEPING MESSENGER] Conversation room: {room_name}")
    print(f"[HOUSEKEEPING MESSENGER] Field exists: {field_exists}")
    print(f"[HOUSEKEEPING MESSENGER] Found {messages_qs.count()} messages in this room")
    print(f"[HOUSEKEEPING MESSENGER] ========================================\n")

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