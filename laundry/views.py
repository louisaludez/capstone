from django.shortcuts import render
from globals import decorator
from chat.models import Message
from django.db import models
from users.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from staff.models import Guest , Booking
from laundry.models import LaundryTransaction
from datetime import datetime
from django.db.models import Q
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

# Helper to map general and specific roles
def get_related_roles(role):
    role_mappings = {
        'Personnel': ['staff_personnel', 'manager_personnel', 'Personnel', 'personnel', 'staff', 'manager'],
        'Concierge': ['staff_concierge', 'manager_concierge', 'Concierge'],
        'Laundry': ['staff_laundry', 'manager_laundry', 'Laundry'],
        'Cafe': ['staff_cafe', 'manager_cafe', 'Cafe'],
        'Room Service': ['staff_room_service', 'manager_room_service', 'Room Service'],
        'Admin': ['admin', 'Admin']
    }
    for general_role, specific_roles in role_mappings.items():
        if role in specific_roles:
            return specific_roles
    return role_mappings.get(role, [role])


def staff_laundry_home(request):
    guests = Guest.objects.filter(booking__status='Checked-in').distinct().order_by('name')
    return render(request, 'laundry/home.html',{
        'guests': guests,                                     
    })


def staff_laundry_messages(request):
    receiver_role = request.GET.get('receiver_role', 'Admin')
    # Base on app service, not user role
    current_service = 'Laundry'

    user_roles = get_related_roles(current_service)
    receiver_roles = get_related_roles(receiver_role)

    # deterministic room with simplified roles
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

    messages_qs = Message.objects.filter(
        (models.Q(sender_role__in=user_roles) & models.Q(receiver_role__in=receiver_roles)) |
        (models.Q(sender_role__in=receiver_roles) & models.Q(receiver_role__in=user_roles))
    ).order_by('created_at')

    for message in messages_qs:
        try:
            sender = CustomUser.objects.get(id=message.sender_id)
            message.sender_username = sender.username
        except CustomUser.DoesNotExist:
            message.sender_username = "Unknown User"

    try:
        receiver = CustomUser.objects.filter(role__in=receiver_roles).first()
        receiver_username = receiver.username if receiver else "Unknown"
    except:
        receiver_username = "Unknown"

    return render(request, "laundry/messenger.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "receiver_username": receiver_username,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })


@login_required
def staff_laundry_orders(request):
    # Get query parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)
    
    # Base queryset
    orders = LaundryTransaction.objects.select_related('guest')
    
    # Apply search filter
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(guest__name__icontains=search_query) |
            Q(service_type__icontains=search_query) |
            Q(room_number__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Apply sorting
    if sort_by == 'created_at':
        orders = orders.order_by('created_at')
    elif sort_by == '-created_at':
        orders = orders.order_by('-created_at')
    elif sort_by == 'guest__name':
        orders = orders.order_by('guest__name')
    elif sort_by == '-guest__name':
        orders = orders.order_by('-guest__name')
    elif sort_by == 'status':
        orders = orders.order_by('status')
    elif sort_by == '-status':
        orders = orders.order_by('-status')
    else:
        orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 7)  # 7 items per page
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # AJAX response for dynamic updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string("includes/order_rows.html", {
            "orders": page_obj,
            "page_obj": page_obj,
            "paginator": paginator
        })
        return JsonResponse({
            'html': html,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'total_count': paginator.count
        })
    
    return render(request, "laundry/orders.html", {
        "orders": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "search_query": search_query,
        "status_filter": status_filter,
        "sort_by": sort_by
    })


@login_required
def view_laundry_order(request, order_id):
    """View a single laundry order"""
    order = get_object_or_404(LaundryTransaction, id=order_id)
    return JsonResponse({
        'id': order.id,
        'guest_name': order.guest.name,
        'room_number': order.room_number,
        'service_type': order.service_type,
        'no_of_bags': order.no_of_bags,
        'specifications': order.specifications or '',
        'date_time': order.date_time.strftime('%Y-%m-%d'),
        'payment_method': order.payment_method,
        'total_amount': float(order.total_amount),
        'status': order.status,
        'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
    })


@login_required
def edit_laundry_order(request, order_id):
    """Edit a laundry order"""
    order = get_object_or_404(LaundryTransaction, id=order_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Update order fields
            # Note: payment_method is not allowed to be changed
            order.service_type = data.get('service_type', order.service_type)
            order.no_of_bags = int(data.get('no_of_bags', order.no_of_bags))
            order.specifications = data.get('specifications', order.specifications)
            order.status = data.get('status', order.status)
            # payment_method remains unchanged - it cannot be modified after order creation
            
            # Recalculate total amount
            BASE_PRICE_PER_BAG = 75.00
            order.total_amount = BASE_PRICE_PER_BAG * order.no_of_bags
            
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Order updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'id': order.id,
        'guest_name': order.guest.name,
        'room_number': order.room_number,
        'service_type': order.service_type,
        'no_of_bags': order.no_of_bags,
        'specifications': order.specifications or '',
        'date_time': order.date_time.strftime('%Y-%m-%d'),
        'payment_method': order.payment_method,
        'total_amount': float(order.total_amount),
        'status': order.status
    })


@login_required
def delete_laundry_order(request, order_id):
    """Delete a laundry order"""
    order = get_object_or_404(LaundryTransaction, id=order_id)
    
    if request.method == 'POST':
        try:
            order.delete()
            return JsonResponse({
                'success': True,
                'message': 'Order deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)


@login_required
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(LaundryTransaction, id=order_id)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            if new_status in dict(LaundryTransaction.STATUS_CHOICES):
                order.status = new_status
                order.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Status updated successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)


def getGuest(request, guest_id):
    if request.method == 'GET':
        print(f"Fetching guest with ID: {guest_id}")
        try:
            latest_booking = Booking.objects.filter(guest_id=guest_id).latest('booking_date')
            response_data = {
                'guest_id': guest_id,
                'room': latest_booking.room,
            }
            print(f"Latest booking found: {response_data}")
            return JsonResponse(response_data)
        except Booking.DoesNotExist:
            return JsonResponse({'error': 'Guest has no booking'}, status=404)


def create_laundry_order(request):
    if request.method == 'POST':
        try:
            # Handle both JSON and form-encoded POSTs
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            print("✅ [DEBUG] Laundry order data received:", data)
            print("✅ [DEBUG] Request method:", request.method)
            print("✅ [DEBUG] Content type:", request.content_type)
            print("✅ [DEBUG] Path:", request.path)

            # Extract data
            guest_input = data.get('guest')  # just for logging
            guest_id = data.get('guest_id')  # new: used for lookup
            room_number = data.get('room_number')
            no_bags = int(data.get('no_bags', 1))
            service_type = data.get('service_type')
            specifications = data.get('specifications', '') or ''
            date_time = data.get('date_time')
            payment_method = data.get('payment_method', 'cash')  # 'room' or 'cash'

            # 💰 Pricing
            BASE_PRICE_PER_BAG = 75.00
            total_amount = BASE_PRICE_PER_BAG * no_bags

            print("📊 [DEBUG] Calculated total:", total_amount)

            # Booking lookup
            try:
                booking = Booking.objects.get(room=room_number, guest_id=guest_id)
                guest = booking.guest
                print("📘 [DEBUG] Booking found:", booking)
                print("👤 [DEBUG] Guest resolved:", guest)
            except Booking.DoesNotExist:
                print("❌ [ERROR] No active booking found for room:", room_number)
                return JsonResponse({'success': False, 'message': 'No active booking found for this room.'}, status=404)

            # Create LaundryTransaction
            transaction = LaundryTransaction.objects.create(
                guest=guest,
                booking=booking,
                room_number=room_number,
                service_type=service_type,
                no_of_bags=no_bags,
                specifications=specifications,
                date_time=datetime.strptime(date_time, '%Y-%m-%dT%H:%M') if 'T' in date_time else datetime.strptime(date_time, '%Y-%m-%d'),
                payment_method=payment_method,
                total_amount=total_amount,
            )

            print("✅ [DEBUG] LaundryTransaction created! ID:", transaction.id)
            print ("Payment method:", payment_method)
            # 💸 Update guest billing if charged to room
            if payment_method == 'Charge to room':
                print("💳 [DEBUG] Payment method is 'Charge to Room', updating guest billing.")
                try:
                    current_billing = float(guest.laundry_billing or 0)
                    print(f"💰 [DEBUG] Current guest billing: {current_billing}")
                except ValueError:
                    print("⚠️ [WARN] Guest billing value invalid, resetting to 0")
                    current_billing = 0

                new_billing = current_billing + total_amount
                guest.laundry_billing = str(new_billing)
                guest.save()
                print(f"💰 [DEBUG] Guest billing updated: {current_billing} → {new_billing}")

            return JsonResponse({
                'success': True,
                'message': 'Laundry transaction created successfully.',
                'order_number': transaction.id,
                'calculated_total': total_amount
            })

        except Exception as e:
            print("❌ [ERROR] Exception in laundry order creation:", str(e))
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'message': 'An error occurred while processing the order.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)