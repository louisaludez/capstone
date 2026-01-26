from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from globals import decorator
from chat.models import Message
from django.db import models
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from users.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from staff.models import *
from .models import Activity, ActivityItem, ActivityChoice, SpeechActivity
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
import locale
from decimal import Decimal
from django.views.decorators.http import require_GET
from cafe.models import CafeOrder
from laundry.models import LaundryTransaction
from .sarima_forecast import get_reservation_forecast
from django.db.models import Sum
from datetime import datetime, timedelta
import calendar
    
# Create your views here.
@decorator.admin_required
def admin_home(request):
    
    users = CustomUser.objects.all()
    # Sum total_of_guests from all bookings with Checked-in or Checked-out status
    total_guests = Booking.objects.filter(
        status__in=['Checked-in', 'Checked-out']
    ).aggregate(total=Sum('total_of_guests'))['total'] or 0
    
    # Calculate total revenue from all billing fields
    total_revenue = 0.0
    room_service_revenue = 0.0
    laundry_revenue = 0.0
    cafe_revenue = 0.0
    excess_pax_revenue = 0.0
    additional_charge_revenue = 0.0
    front_office_revenue = 0.0
    total_cafe = CafeOrder.objects.exclude(payment_method='room').aggregate(
        total_sum=Sum('total')
    )['total_sum'] or 0
    total_laundry = LaundryTransaction.objects.exclude(payment_method='Charge to room').aggregate(
        total_sum=Sum('total_amount')
    )['total_sum'] or 0
    
    valid_guests = Guest.objects.filter(
        booking__status__in=['Checked-in', 'Checked-out']
    ).distinct()


    for guest_obj in valid_guests:
        try:
            front_office_revenue += float(guest_obj.billing or 0)
            room_service_revenue += float(guest_obj.room_service_billing or 0)
            laundry_revenue += float(guest_obj.laundry_billing or 0)
            cafe_revenue += float(guest_obj.cafe_billing or 0)
            excess_pax_revenue += float(guest_obj.excess_pax_billing or 0)
            additional_charge_revenue += float(guest_obj.additional_charge_billing or 0)
            total_revenue += (
              float(guest_obj.billing or 0)
            + float(guest_obj.room_service_billing or 0)
            + float(guest_obj.laundry_billing or 0)
            + float(guest_obj.cafe_billing or 0)
            + float(guest_obj.excess_pax_billing or 0)
            + float(guest_obj.additional_charge_billing or 0)
        )
        except (ValueError, TypeError):
            continue
    total_revenue += float(total_cafe)
    total_revenue += float(total_laundry)
    print(f"Front Office Revenue: {front_office_revenue}")
    print(f"Room Service Revenue: {room_service_revenue}")
    print(f"Laundry Revenue: {laundry_revenue}")
    print(f"Cafe Revenue: {cafe_revenue}")
    print(f"Excess Pax Revenue: {excess_pax_revenue}")
    print(f"Additional Charge Revenue: {additional_charge_revenue}")
    
    # Find peak month and calculate growth based on booking counts
    monthly_bookings = {}
    for booking in Booking.objects.all():
        month_key = booking.booking_date.strftime('%Y-%m')
        monthly_bookings[month_key] = monthly_bookings.get(month_key, 0) + 1
    
    peak_month = "No data"
    growth_percentage = 0.0
    
    if monthly_bookings:
        # Find peak month
        peak_month_key = max(monthly_bookings, key=monthly_bookings.get)
        peak_month = datetime.strptime(peak_month_key, '%Y-%m').strftime('%B %Y')
        
        # Calculate growth percentage (comparing last 2 months)
        sorted_months = sorted(monthly_bookings.keys())
        if len(sorted_months) >= 2:
            current_month = monthly_bookings[sorted_months[-1]]
            previous_month = monthly_bookings[sorted_months[-2]]
            if previous_month > 0:
                growth_percentage = ((current_month - previous_month) / previous_month) * 100
            else:
                growth_percentage = 100.0 if current_month > 0 else 0.0
    
    # Defer forecast computation to an async JSON endpoint to speed up initial page load
    return render(request, "adminNew/home.html", {
        "users": users,
        "total_guests": total_guests,
        "peak_month": peak_month,
        "total_revenue": f"{total_revenue:.2f}",
        "growth_percentage": f"{growth_percentage:.1f}",
    })

@require_GET
@decorator.admin_required
def admin_home_forecast_json(request):
    from .sarima_forecast import get_reservation_forecast
    import json
    # Check if force_retrain parameter is provided
    force_retrain = request.GET.get('force_retrain', 'false').lower() == 'true'
    data = get_reservation_forecast(force_retrain=force_retrain) or {}
    return JsonResponse(data, safe=False)

@require_GET
@decorator.admin_required
def admin_home_monthly_data(request):
    """Get monthly guest and revenue data for a specific month"""
    from datetime import datetime
    from django.db.models import Q, Sum

    month_str = request.GET.get('month')
    if not month_str:
        return JsonResponse({'error': 'Month parameter required'}, status=400)

    try:
        # Parse month string (format: YYYY-MM)
        year, month = map(int, month_str.split('-'))
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
    except (ValueError, IndexError):
        return JsonResponse({'error': 'Invalid month format. Use YYYY-MM'}, status=400)

    # Sum total_of_guests from bookings that checked in during the selected month
    # Count guests based on when they checked in, not when they checked out
    monthly_guests = Booking.objects.filter(
        status__in=['Checked-in', 'Checked-out'],
        check_in_date__gte=start_date.date(),
        check_in_date__lt=end_date.date()
    ).aggregate(total=Sum('total_of_guests'))['total'] or 0

    # Include only guests with Checked-in or Checked-out bookings
    valid_guests = Guest.objects.filter(
        Q(booking__status__in=['Checked-in', 'Checked-out']),
        Q(booking__check_in_date__gte=start_date, booking__check_in_date__lt=end_date) |
        Q(booking__check_out_date__gte=start_date, booking__check_out_date__lt=end_date)
    ).distinct()

    # Guest-based revenue
    monthly_revenue = 0.0
    for guest_obj in valid_guests:
        try:
            monthly_revenue += float(guest_obj.billing or 0)
            monthly_revenue += float(guest_obj.room_service_billing or 0)
            monthly_revenue += float(guest_obj.laundry_billing or 0)
            monthly_revenue += float(guest_obj.cafe_billing or 0)
            monthly_revenue += float(guest_obj.excess_pax_billing or 0)
            monthly_revenue += float(guest_obj.additional_charge_billing or 0)
        except (ValueError, TypeError):
            continue

    # CafeOrder revenue (exclude room charges)
    cafe_revenue = CafeOrder.objects.filter(
        order_date__gte=start_date,
        order_date__lt=end_date
    ).exclude(payment_method='room').aggregate(
        total_sum=Sum('total')
    )['total_sum'] or 0.0

    # Laundry revenue (exclude room charges)
    laundry_revenue = LaundryTransaction.objects.filter(
        date_time__gte=start_date,
        date_time__lt=end_date
    ).exclude(payment_method='Charge to room').aggregate(
        total=Sum('total_amount')
    )['total'] or 0.0

    # Add Cafe and Laundry revenue
    monthly_revenue += float(cafe_revenue)
    monthly_revenue += float(laundry_revenue)

    return JsonResponse({
        'month': month_str,
        'month_display': start_date.strftime('%B %Y'),
        'guests': monthly_guests,
        'revenue': f"{monthly_revenue:.2f}",
        'cafe_revenue': f"{float(cafe_revenue):.2f}",
        'laundry_revenue': f"{float(laundry_revenue):.2f}",
    })

@decorator.admin_required
def admin_account(request):
    users = CustomUser.objects.all()
    return render(request, "adminNew/accounts.html", {"users": users})

@decorator.admin_required
def add_user(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            course = request.POST.get('course')
            student_set = request.POST.get('set')
            year_level_raw = request.POST.get('year_level')
            try:
                year_level = int(year_level_raw) if year_level_raw is not None and year_level_raw != '' else None
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Year level must be a number'})

            # Restrict roles to only 'staff' or 'admin'
            if role not in ['staff', 'admin']:
                return JsonResponse({'status': 'error', 'message': 'Invalid role. Allowed roles are Staff or Admin.'})

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

            user = CustomUser.objects.create(
                username=username,
                email=email,
                first_name=first_name or '',
                last_name=last_name or '',
                course=course or None,
                set=student_set or None,
                year_level=year_level,
                password=make_password(password),
                role=role
            )

            return JsonResponse({'status': 'success', 'message': 'User created successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@decorator.admin_required
def view_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
    }
    return JsonResponse(data)

@decorator.admin_required
def delete_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            username = user.username
            user.delete()
            return JsonResponse({
                'status': 'success',
                'message': f'User {username} has been deleted successfully'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
@decorator.admin_required
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            password = request.POST.get('password')

            if CustomUser.objects.exclude(id=user_id).filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.exclude(id=user_id).filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

            # Restrict roles to only 'staff' or 'admin'
            if role not in ['staff', 'admin']:
                return JsonResponse({'status': 'error', 'message': 'Invalid role. Allowed roles are Staff or Admin.'})

            user.username = username
            user.email = email
            user.role = role
            if password:
                user.password = make_password(password)
            user.save()

            return JsonResponse({
                'status': 'success',
                'message': 'User updated successfully',
                'user_data': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'date_joined': user.date_joined.strftime('%d/%m/%Y %H:%M')
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }
    return JsonResponse(data)
@decorator.admin_required
def admin_reports(request):
    return render(request, "adminNew/reports.html")
@decorator.admin_required
def admin_messenger(request):
    receiver_role = request.GET.get('receiver_role', 'Personnel')
    # Base on app service, not user role
    current_service = 'Admin'

    # Build deterministic room with simplified roles
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
        simplified_receiver_role = simplify_role(receiver_role)
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
    print(f"\n[ADMIN MESSENGER] ========================================")
    print(f"[ADMIN MESSENGER] Viewing chat with: {receiver_role}")
    print(f"[ADMIN MESSENGER] Current service: {current_service}")
    print(f"[ADMIN MESSENGER] Conversation room: {room_name}")
    print(f"[ADMIN MESSENGER] Field exists: {field_exists}")
    print(f"[ADMIN MESSENGER] Found {messages_qs.count()} messages in this room")
    
    # Show sample messages
    for msg in messages_qs[:5]:
        print(f"  - ID={msg.id}, conversation_room='{getattr(msg, 'conversation_room', 'N/A')}', sender_service='{msg.sender_service}', sender_role='{msg.sender_role}', receiver_role='{msg.receiver_role}'")
    print(f"[ADMIN MESSENGER] ========================================\n")
    
    # Convert queryset to list to ensure it's evaluated
    messages_list = list(messages_qs)
    for msg in messages_list:
        try:
            sender = CustomUser.objects.get(id=msg.sender_id)
            msg.sender_username = sender.username
        except CustomUser.DoesNotExist:
            msg.sender_username = "Unknown User"

    return render(request, "adminNew/messenger.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_list,
        "current_user_id": request.user.id,
        "current_service": current_service,
    })
@decorator.admin_required
def admin_front_office_reports(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    from staff.models import Room

    # Calculate total revenue - match admin_home calculation
    # Only include guests with Checked-in or Checked-out bookings
    total_revenue = 0.0
    valid_guests = Guest.objects.filter(
        booking__status__in=['Checked-in', 'Checked-out']
    ).distinct()

    for guest_obj in valid_guests:
        try:
            total_revenue += (
                float(guest_obj.billing or 0) +
                float(guest_obj.room_service_billing or 0) +
                float(guest_obj.laundry_billing or 0) +
                float(guest_obj.cafe_billing or 0) +
                float(guest_obj.excess_pax_billing or 0) +
                float(guest_obj.additional_charge_billing or 0)
            )
        except (ValueError, TypeError):
            continue
    
    # Add cafe and laundry revenue (excluding room charges) - match admin_home
    total_cafe = CafeOrder.objects.exclude(payment_method='room').aggregate(
        total_sum=Sum('total')
    )['total_sum'] or 0
    total_laundry = LaundryTransaction.objects.exclude(payment_method='Charge to room').aggregate(
        total_sum=Sum('total_amount')
    )['total_sum'] or 0
    
    total_revenue += float(total_cafe)
    total_revenue += float(total_laundry)

    # FO metrics
    # Total check-ins: bookings with source='checkin' OR source='reservation' (merged)
    total_checkins = Booking.objects.filter(source__in=['checkin', 'reservation']).count()
    total_checkouts = Booking.objects.filter(status='Checked-out').count()
    # Walk-ins: bookings with source='walkin'
    walkins = Booking.objects.filter(source='walkin').count()
    # Total reservations (for reference, but check-ins includes reservations)
    total_reservations = Booking.objects.filter(source='reservation').count()

    # Search, filter, and sort functionality
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'date_desc')
    orders_query = Booking.objects.select_related('guest')
    
    # Create a mapping of room numbers to room types
    room_mapping = {}
    for room in Room.objects.all():
        room_mapping[room.room_number] = room.get_room_type_display()
    
    # Apply filters based on guest cycle
    if filter_type == 'walkins':
        # Walk-ins: bookings with source='walkin'
        orders_query = orders_query.filter(source='walkin')
    elif filter_type == 'checkins':
        # Check-ins: checked-in bookings that are NOT walk-ins
        orders_query = orders_query.filter(status='Checked-in').exclude(source='walkin')
    elif filter_type == 'checkouts':
        # Check-outs: all checked-out bookings
        orders_query = orders_query.filter(status='Checked-out')
    # 'all' shows all bookings regardless of status
    
    if search_query:
        orders_query = orders_query.filter(
            Q(guest__name__icontains=search_query) |
            Q(guest__email__icontains=search_query) |
            Q(room__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply sorting
    if sort_by == 'date_asc':
        orders_query = orders_query.order_by('booking_date')
    elif sort_by == 'date_desc':
        orders_query = orders_query.order_by('-booking_date')
    elif sort_by == 'guest_asc':
        orders_query = orders_query.order_by('guest__name')
    elif sort_by == 'guest_desc':
        orders_query = orders_query.order_by('-guest__name')
    elif sort_by == 'room_asc':
        orders_query = orders_query.order_by('room')
    elif sort_by == 'room_desc':
        orders_query = orders_query.order_by('-room')
    else:
        orders_query = orders_query.order_by('-booking_date')

    # Pagination with 7 rows per page
    paginator = Paginator(orders_query, 7)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'total_revenue': f"{total_revenue:.2f}",
        'total_walkins': walkins,
        'total_reservations': total_reservations,
        'total_checkins': total_checkins,
        'total_checkouts': total_checkouts,
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'filter_type': filter_type,
        'room_mapping': room_mapping,
        'current_sort': sort_by,
    }
    return render(request, "adminNew/front_office_reports.html", context)

@require_GET
@decorator.admin_required
def admin_front_office_reports_export(request):
    """Export Front Office reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from staff.models import Room, Payment

    # Base queryset similar to admin_front_office_reports
    orders_query = Booking.objects.select_related('guest')

    # Filters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'date_desc')

    # Apply filter type
    if filter_type == 'walkins':
        orders_query = orders_query.filter(source='walkin')
    elif filter_type == 'checkins':
        orders_query = orders_query.filter(status='Checked-in').exclude(source='walkin')
    elif filter_type == 'checkouts':
        orders_query = orders_query.filter(status='Checked-out')

    # Apply search
    if search_query:
        orders_query = orders_query.filter(
            models.Q(guest__name__icontains=search_query) |
            models.Q(guest__email__icontains=search_query) |
            models.Q(room__icontains=search_query) |
            models.Q(id__icontains=search_query)
        )

    # Sort
    if sort_by == 'date_asc':
        orders_query = orders_query.order_by('booking_date')
    elif sort_by == 'date_desc':
        orders_query = orders_query.order_by('-booking_date')
    elif sort_by == 'guest_asc':
        orders_query = orders_query.order_by('guest__name')
    elif sort_by == 'guest_desc':
        orders_query = orders_query.order_by('-guest__name')
    elif sort_by == 'room_asc':
        orders_query = orders_query.order_by('room')
    elif sort_by == 'room_desc':
        orders_query = orders_query.order_by('-room')
    else:
        orders_query = orders_query.order_by('-booking_date')

    # Room mapping for type labels
    room_mapping = {r.room_number: r.get_room_type_display() for r in Room.objects.all()}

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Receipt #', 'Room No.', 'Room Type', 'Guest Name', 'Booking Date', 'Check-in', 'Check-out',
        'Status', 'Adults', 'Children', 'Total Guests', 'Room Charges', 'Other Charges', 'Payment Method', 'Total Balance'
    ])

    for b in orders_query:
        guest = b.guest
        room_type = room_mapping.get(str(b.room), '')
        # Compute charges
        def _to_float(v):
            try:
                return float(v or 0)
            except Exception:
                return 0.0
        room_charges = _to_float(guest.billing)
        other_charges = _to_float(guest.room_service_billing) + _to_float(guest.laundry_billing) + _to_float(guest.cafe_billing) + _to_float(guest.excess_pax_billing) + _to_float(guest.additional_charge_billing)
        # Payment
        pay = Payment.objects.filter(booking=b).first()
        payment_method = getattr(pay, 'method', '')
        total_balance = getattr(pay, 'total_balance', '')

        writer.writerow([
            f"{b.id:05d}", str(b.room), room_type, guest.name,
            b.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
            b.check_in_date.strftime('%Y-%m-%d'),
            b.check_out_date.strftime('%Y-%m-%d'),
            b.status, b.num_of_adults, b.num_of_children, b.total_of_guests,
            f"{room_charges:.2f}", f"{other_charges:.2f}", payment_method, str(total_balance)
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="front_office_report.csv"'
    return response
@decorator.admin_required
def admin_cafe_reports(request):
    from cafe.models import CafeOrder, CafeOrderItem

    from django.core.paginator import Paginator
    from django.db.models import Q

    # Totals
    transactions = CafeOrder.objects.count()
    items_sold = CafeOrderItem.objects.aggregate(n=Sum('quantity'))['n'] or 0
    top = (
        CafeOrderItem.objects
        .values('item__name')
        .annotate(q=Sum('quantity'))
        .order_by('-q')
        .first()
    )
    most_sold_item = top['item__name'] if top else '—'
    total_revenue = CafeOrder.objects.aggregate(s=Sum('total'))['s'] or 0

    # Search, filter, sort
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')  # cash, card, all
    sort_by = request.GET.get('sort', 'date_desc')

    orders_qs = CafeOrder.objects.select_related('guest')

    if filter_type == 'cash':
        orders_qs = orders_qs.filter(payment_method='cash')
    elif filter_type == 'card':
        orders_qs = orders_qs.filter(payment_method='card')

    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )

    if sort_by == 'date_asc':
        orders_qs = orders_qs.order_by('order_date')
    elif sort_by == 'date_desc':
        orders_qs = orders_qs.order_by('-order_date')
    elif sort_by == 'total_asc':
        orders_qs = orders_qs.order_by('total')
    elif sort_by == 'total_desc':
        orders_qs = orders_qs.order_by('-total')
    elif sort_by == 'receipt_asc':
        orders_qs = orders_qs.order_by('id')
    elif sort_by == 'receipt_desc':
        orders_qs = orders_qs.order_by('-id')
    else:
        orders_qs = orders_qs.order_by('-order_date')

    paginator = Paginator(orders_qs, 7)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions_count': transactions,
        'items_sold': items_sold,
        'most_sold_item': most_sold_item,
        'total_revenue': total_revenue,
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'filter_type': filter_type,
        'current_sort': sort_by,
    }
    return render(request, "adminNew/cafe_reports.html", context)

@require_GET
@decorator.admin_required
def admin_cafe_reports_export(request):
    """Export Cafe reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from cafe.models import CafeOrder, CafeOrderItem
    from django.db.models import Q, Sum

    # Base queryset similar to admin_cafe_reports
    orders_qs = CafeOrder.objects.select_related('guest')

    # Filters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'date_desc')

    # Apply filter type
    if filter_type == 'cash':
        orders_qs = orders_qs.filter(payment_method='cash')
    elif filter_type == 'card':
        orders_qs = orders_qs.filter(payment_method='card')

    # Apply search
    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )

    # Sort
    if sort_by == 'date_asc':
        orders_qs = orders_qs.order_by('order_date')
    elif sort_by == 'date_desc':
        orders_qs = orders_qs.order_by('-order_date')
    elif sort_by == 'total_asc':
        orders_qs = orders_qs.order_by('total')
    elif sort_by == 'total_desc':
        orders_qs = orders_qs.order_by('-total')
    elif sort_by == 'receipt_asc':
        orders_qs = orders_qs.order_by('id')
    elif sort_by == 'receipt_desc':
        orders_qs = orders_qs.order_by('-id')
    else:
        orders_qs = orders_qs.order_by('-order_date')

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Receipt No.', 'Date and Time', 'Items Sold', 'Qty', 'Total', 
        'Cash Tendered', 'Change', 'Payment Method'
    ])

    for order in orders_qs:
        # Get items for this order
        items = CafeOrderItem.objects.filter(order=order)
        items_text = ', '.join([f"{item.item.name} (x{item.quantity})" for item in items])
        total_qty = sum([item.quantity for item in items])
        
        # Handle None values safely
        total = order.total if order.total is not None else 0.0
        cash_tendered = order.cash_tendered if order.cash_tendered is not None else 0.0
        change = order.change if order.change is not None else 0.0
        payment_method = order.payment_method if order.payment_method is not None else 'N/A'
        
        writer.writerow([
            f"{order.id:05d}",
            order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            items_text,
            total_qty,
            f"{total:.2f}",
            f"{cash_tendered:.2f}",
            f"{change:.2f}",
            payment_method
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cafe_report.csv"'
    return response

@decorator.admin_required
def admin_housekeeping_reports(request):
    from housekeeping.models import Housekeeping
    from django.core.paginator import Paginator
    from django.db.models import Q

    hk_pending = Housekeeping.objects.filter(status__iexact='pending').count()
    hk_in_progress = Housekeeping.objects.filter(status__iexact='in progress').count()
    hk_finished = Housekeeping.objects.filter(status__iexact='finished').count()

    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')  # pending, in_progress, finished, all
    sort_by = request.GET.get('sort', 'date_desc')

    qs = Housekeeping.objects.all()

    # Normalize status mapping for filter values
    if filter_type == 'pending':
        qs = qs.filter(status__iexact='pending')
    elif filter_type == 'in_progress':
        qs = qs.filter(status__iexact='in progress')
    elif filter_type == 'finished':
        qs = qs.filter(status__iexact='finished')

    if search_query:
        qs = qs.filter(
            Q(room_number__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(request_type__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    if sort_by == 'date_asc':
        qs = qs.order_by('created_at')
    elif sort_by == 'date_desc':
        qs = qs.order_by('-created_at')
    elif sort_by == 'room_asc':
        qs = qs.order_by('room_number')
    elif sort_by == 'room_desc':
        qs = qs.order_by('-room_number')
    elif sort_by == 'status_asc':
        qs = qs.order_by('status')
    elif sort_by == 'status_desc':
        qs = qs.order_by('-status')
    else:
        qs = qs.order_by('-created_at')

    paginator = Paginator(qs, 7)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'hk_pending': hk_pending,
        'hk_in_progress': hk_in_progress,
        'hk_finished': hk_finished,
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'filter_type': filter_type,
        'current_sort': sort_by,
    }
    return render(request, "adminNew/housekeeping_reports.html", context)

@require_GET
@decorator.admin_required
def admin_housekeeping_reports_export(request):
    """Export Housekeeping reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from housekeeping.models import Housekeeping
    from django.db.models import Q

    # Base queryset similar to admin_housekeeping_reports
    qs = Housekeeping.objects.all()

    # Filters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'date_desc')

    # Apply filter type
    if filter_type == 'pending':
        qs = qs.filter(status__iexact='pending')
    elif filter_type == 'in_progress':
        qs = qs.filter(status__iexact='in progress')
    elif filter_type == 'finished':
        qs = qs.filter(status__iexact='finished')

    # Apply search
    if search_query:
        qs = qs.filter(
            Q(room_number__icontains=search_query) |
            Q(guest_name__icontains=search_query) |
            Q(request_type__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Sort
    if sort_by == 'date_asc':
        qs = qs.order_by('created_at')
    elif sort_by == 'date_desc':
        qs = qs.order_by('-created_at')
    elif sort_by == 'room_asc':
        qs = qs.order_by('room_number')
    elif sort_by == 'room_desc':
        qs = qs.order_by('-room_number')
    elif sort_by == 'status_asc':
        qs = qs.order_by('status')
    elif sort_by == 'status_desc':
        qs = qs.order_by('-status')
    else:
        qs = qs.order_by('-created_at')

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Room No.', 'Guest Name', 'Service Type', 'Date', 'Time', 'Status'
    ])

    for hk in qs:
        # Handle None values safely
        room_number = hk.room_number if hk.room_number is not None else 'N/A'
        guest_name = hk.guest_name if hk.guest_name is not None else 'N/A'
        request_type = hk.request_type if hk.request_type is not None else 'N/A'
        status = hk.status if hk.status is not None else 'N/A'
        
        writer.writerow([
            room_number,
            guest_name,
            request_type,
            hk.created_at.strftime('%Y-%m-%d'),
            hk.created_at.strftime('%H:%M:%S'),
            status
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="housekeeping_report.csv"'
    return response

@decorator.admin_required
def admin_laundry_reports(request):
    from laundry.models import LaundryTransaction

    from django.core.paginator import Paginator
    from django.db.models import Q

    qs = LaundryTransaction.objects.all()
    # Count completed transactions (case-insensitive to handle any variations)
    completed_count = qs.filter(status__iexact='completed').count()
    room_charges = qs.filter(payment_method='room').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    cash_payments = qs.filter(payment_method='cash').aggregate(s=Sum('total_amount'))['s'] or Decimal('0')
    total_revenue = qs.aggregate(s=Sum('total_amount'))['s'] or Decimal('0')

    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')  # pending, in_progress, completed, cancelled, all
    sort_by = request.GET.get('sort', 'date_desc')

    orders_qs = LaundryTransaction.objects.select_related('guest')

    # Status filter
    if filter_type == 'pending':
        orders_qs = orders_qs.filter(status='pending')
    elif filter_type == 'in_progress':
        orders_qs = orders_qs.filter(status='in_progress')
    elif filter_type == 'completed':
        orders_qs = orders_qs.filter(status='completed')
    elif filter_type == 'cancelled':
        orders_qs = orders_qs.filter(status='cancelled')

    # Search
    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(guest__name__icontains=search_query) |
            Q(service_type__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )

    # Sort
    if sort_by == 'date_asc':
        orders_qs = orders_qs.order_by('date_time', 'created_at')
    elif sort_by == 'date_desc':
        orders_qs = orders_qs.order_by('-date_time', '-created_at')
    elif sort_by == 'amount_asc':
        orders_qs = orders_qs.order_by('total_amount')
    elif sort_by == 'amount_desc':
        orders_qs = orders_qs.order_by('-total_amount')
    elif sort_by == 'receipt_asc':
        orders_qs = orders_qs.order_by('id')
    elif sort_by == 'receipt_desc':
        orders_qs = orders_qs.order_by('-id')
    else:
        orders_qs = orders_qs.order_by('-date_time', '-created_at')

    paginator = Paginator(orders_qs, 7)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'completed_count': completed_count,
        'room_charges': room_charges,
        'cash_payments': cash_payments,
        'total_revenue': total_revenue,
        'orders': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'filter_type': filter_type,
        'current_sort': sort_by,
    }
    return render(request, "adminNew/laundry_reports.html", context)

@require_GET
@decorator.admin_required
def admin_laundry_reports_export(request):
    """Export Laundry reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from laundry.models import LaundryTransaction
    from django.db.models import Q, Sum
    from decimal import Decimal

    # Base queryset similar to admin_laundry_reports
    orders_qs = LaundryTransaction.objects.select_related('guest')

    # Filters
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', 'date_desc')

    # Apply filter type
    if filter_type == 'pending':
        orders_qs = orders_qs.filter(status='pending')
    elif filter_type == 'in_progress':
        orders_qs = orders_qs.filter(status='in_progress')
    elif filter_type == 'completed':
        orders_qs = orders_qs.filter(status='completed')
    elif filter_type == 'cancelled':
        orders_qs = orders_qs.filter(status='cancelled')

    # Apply search
    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(guest__name__icontains=search_query) |
            Q(service_type__icontains=search_query) |
            Q(payment_method__icontains=search_query)
        )

    # Sort
    if sort_by == 'date_asc':
        orders_qs = orders_qs.order_by('date_time', 'created_at')
    elif sort_by == 'date_desc':
        orders_qs = orders_qs.order_by('-date_time', '-created_at')
    elif sort_by == 'amount_asc':
        orders_qs = orders_qs.order_by('total_amount')
    elif sort_by == 'amount_desc':
        orders_qs = orders_qs.order_by('-total_amount')
    elif sort_by == 'receipt_asc':
        orders_qs = orders_qs.order_by('id')
    elif sort_by == 'receipt_desc':
        orders_qs = orders_qs.order_by('-id')
    else:
        orders_qs = orders_qs.order_by('-date_time', '-created_at')

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Receipt No.', 'Customer', 'Service Type', 'Date and Time', 
        'Amount', 'Status', 'Payment Method'
    ])

    for transaction in orders_qs:
        # Handle None values safely
        total_amount = transaction.total_amount if transaction.total_amount is not None else 0.0
        service_type = transaction.service_type if transaction.service_type is not None else 'N/A'
        status = transaction.status if transaction.status is not None else 'N/A'
        payment_method = transaction.payment_method if transaction.payment_method is not None else 'N/A'
        
        writer.writerow([
            f"{transaction.id:05d}",
            transaction.guest.name if transaction.guest else 'N/A',
            service_type,
            transaction.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            f"{total_amount:.2f}",
            status,
            payment_method
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="laundry_report.csv"'
    return response

@decorator.admin_required
def admin_mcq_reports(request):
    from assessment.models import McqAttempt
    from django.core.paginator import Paginator
    
    # Get all MCQ attempts
    attempts = McqAttempt.objects.select_related('activity', 'started_by').order_by('-started_at')
    
    # Apply filters
    filter_status = request.GET.get('filter', '')
    if filter_status == 'passed':
        attempts = attempts.filter(passed=True, status=McqAttempt.STATUS_SUBMITTED)
    elif filter_status == 'failed':
        attempts = attempts.filter(passed=False, status=McqAttempt.STATUS_SUBMITTED)
    elif filter_status == 'in_progress':
        attempts = attempts.filter(status=McqAttempt.STATUS_IN_PROGRESS)
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'date_desc')
    if sort_by == 'date_asc':
        attempts = attempts.order_by('started_at')
    elif sort_by == 'date_desc':
        attempts = attempts.order_by('-started_at')
    elif sort_by == 'score_asc':
        attempts = attempts.order_by('score')
    elif sort_by == 'score_desc':
        attempts = attempts.order_by('-score')
    elif sort_by == 'participant_asc':
        attempts = attempts.order_by('participant_info')
    elif sort_by == 'participant_desc':
        attempts = attempts.order_by('-participant_info')
    
    # Calculate statistics (always show total stats, not filtered)
    all_attempts = McqAttempt.objects.select_related('activity', 'started_by')
    total_tests = all_attempts.count()
    passed_tests = all_attempts.filter(passed=True, status=McqAttempt.STATUS_SUBMITTED).count()
    failed_tests = all_attempts.filter(passed=False, status=McqAttempt.STATUS_SUBMITTED).count()
    
    # Add answer counts to each attempt
    for attempt in attempts:
        attempt.correct_count = attempt.answers.filter(is_correct=True).count()
        attempt.incorrect_count = attempt.answers.filter(is_correct=False).count()
        attempt.total_items = attempt.activity.items.count()
    
    # Pagination
    paginator = Paginator(attempts, 5)  # Show 5 attempts per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'attempts': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'current_filter': filter_status,
        'current_sort': sort_by,
    }
    
    return render(request, "adminNew/mcq_reports.html", context)

@require_GET
@decorator.admin_required
def admin_mcq_reports_export(request):
    """Export MCQ reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from assessment.models import McqAttempt

    # Base queryset similar to admin_mcq_reports
    attempts = McqAttempt.objects.select_related('activity', 'started_by').order_by('-started_at')

    # Apply filters
    filter_status = request.GET.get('filter', '')
    if filter_status == 'passed':
        attempts = attempts.filter(passed=True, status=McqAttempt.STATUS_SUBMITTED)
    elif filter_status == 'failed':
        attempts = attempts.filter(passed=False, status=McqAttempt.STATUS_SUBMITTED)
    elif filter_status == 'in_progress':
        attempts = attempts.filter(status=McqAttempt.STATUS_IN_PROGRESS)

    # Apply sorting
    sort_by = request.GET.get('sort', 'date_desc')
    if sort_by == 'date_asc':
        attempts = attempts.order_by('started_at')
    elif sort_by == 'date_desc':
        attempts = attempts.order_by('-started_at')
    elif sort_by == 'score_asc':
        attempts = attempts.order_by('score')
    elif sort_by == 'score_desc':
        attempts = attempts.order_by('-score')
    elif sort_by == 'participant_asc':
        attempts = attempts.order_by('participant_info')
    elif sort_by == 'participant_desc':
        attempts = attempts.order_by('-participant_info')

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Test No.', 'Name', 'Test Type', 'Date and Time', 'No. of Items', 
        'No. of Corrects', 'No. of Mistakes', 'Score', 'Status'
    ])

    for attempt in attempts:
        correct_count = attempt.answers.filter(is_correct=True).count()
        incorrect_count = attempt.answers.filter(is_correct=False).count()
        total_items = attempt.activity.items.count()
        
        # Determine status
        if attempt.status == McqAttempt.STATUS_SUBMITTED:
            if attempt.passed:
                status = 'Passed'
            else:
                status = 'Failed'
        elif attempt.status == McqAttempt.STATUS_IN_PROGRESS:
            status = 'In Progress'
        else:
            status = attempt.status.title()

        writer.writerow([
            f"#{attempt.id}",
            attempt.participant_info,
            'MCQ',
            attempt.started_at.strftime('%b %d, %Y %H:%M'),
            total_items,
            correct_count,
            incorrect_count,
            f"{attempt.score:.1f}%" if attempt.score is not None else 'N/A',
            status
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mcq_report.csv"'
    return response

@decorator.admin_required
def admin_speech_reports(request):
    from assessment.models import SpeechAttempt
    from django.core.paginator import Paginator
    
    # Get all Speech attempts
    attempts = SpeechAttempt.objects.select_related('activity', 'started_by').order_by('-started_at')
    
    # Apply filters
    filter_status = request.GET.get('filter', '')
    if filter_status == 'passed':
        attempts = attempts.filter(passed=True, status=SpeechAttempt.STATUS_SUBMITTED)
    elif filter_status == 'failed':
        attempts = attempts.filter(passed=False, status=SpeechAttempt.STATUS_SUBMITTED)
    elif filter_status == 'in_progress':
        attempts = attempts.filter(status=SpeechAttempt.STATUS_IN_PROGRESS)
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'date_desc')
    if sort_by == 'date_asc':
        attempts = attempts.order_by('started_at')
    elif sort_by == 'date_desc':
        attempts = attempts.order_by('-started_at')
    elif sort_by == 'score_asc':
        attempts = attempts.order_by('score')
    elif sort_by == 'score_desc':
        attempts = attempts.order_by('-score')
    elif sort_by == 'participant_asc':
        attempts = attempts.order_by('participant_info')
    elif sort_by == 'participant_desc':
        attempts = attempts.order_by('-participant_info')
    
    # Calculate statistics (always show total stats, not filtered)
    all_attempts = SpeechAttempt.objects.select_related('activity', 'started_by')
    total_tests = all_attempts.count()
    passed_tests = all_attempts.filter(passed=True, status=SpeechAttempt.STATUS_SUBMITTED).count()
    failed_tests = all_attempts.filter(passed=False, status=SpeechAttempt.STATUS_SUBMITTED).count()
    
    # Add answer counts to each attempt (for speech, we'll use accuracy-based logic)
    for attempt in attempts:
        if attempt.status == SpeechAttempt.STATUS_SUBMITTED and attempt.score is not None:
            # For speech, we consider it "correct" if score >= 70%, "incorrect" otherwise
            if attempt.score >= 70:
                attempt.correct_count = 1
                attempt.incorrect_count = 0
            else:
                attempt.correct_count = 0
                attempt.incorrect_count = 1
        else:
            attempt.correct_count = 0
            attempt.incorrect_count = 0
        attempt.total_items = 1  # Speech tests have 1 item
    
    # Pagination
    paginator = Paginator(attempts, 5)  # Show 5 attempts per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': failed_tests,
        'attempts': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'current_filter': filter_status,
        'current_sort': sort_by,
    }
    
    return render(request, "adminNew/speech_reports.html", context)

@require_GET
@decorator.admin_required
def admin_speech_reports_export(request):
    """Export Speech reports as CSV using current filters and sort."""
    import csv
    from io import StringIO
    from assessment.models import SpeechAttempt

    # Base queryset similar to admin_speech_reports
    attempts = SpeechAttempt.objects.select_related('activity', 'started_by').order_by('-started_at')

    # Apply filters
    filter_status = request.GET.get('filter', '')
    if filter_status == 'passed':
        attempts = attempts.filter(passed=True, status=SpeechAttempt.STATUS_SUBMITTED)
    elif filter_status == 'failed':
        attempts = attempts.filter(passed=False, status=SpeechAttempt.STATUS_SUBMITTED)
    elif filter_status == 'in_progress':
        attempts = attempts.filter(status=SpeechAttempt.STATUS_IN_PROGRESS)

    # Apply sorting
    sort_by = request.GET.get('sort', 'date_desc')
    if sort_by == 'date_asc':
        attempts = attempts.order_by('started_at')
    elif sort_by == 'date_desc':
        attempts = attempts.order_by('-started_at')
    elif sort_by == 'score_asc':
        attempts = attempts.order_by('score')
    elif sort_by == 'score_desc':
        attempts = attempts.order_by('-score')
    elif sort_by == 'participant_asc':
        attempts = attempts.order_by('participant_info')
    elif sort_by == 'participant_desc':
        attempts = attempts.order_by('-participant_info')

    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Test No.', 'Name', 'Test Type', 'Date and Time', 'No. of Items', 
        'No. of Corrects', 'No. of Mistakes', 'Score', 'Status'
    ])

    for attempt in attempts:
        # For speech, we consider it "correct" if score >= 70%, "incorrect" otherwise
        if attempt.status == SpeechAttempt.STATUS_SUBMITTED and attempt.score is not None:
            if attempt.score >= 70:
                correct_count = 1
                incorrect_count = 0
            else:
                correct_count = 0
                incorrect_count = 1
        else:
            correct_count = 0
            incorrect_count = 0
        
        # Determine status
        if attempt.status == SpeechAttempt.STATUS_SUBMITTED:
            if attempt.passed:
                status = 'Passed'
            else:
                status = 'Failed'
        elif attempt.status == SpeechAttempt.STATUS_IN_PROGRESS:
            status = 'In Progress'
        else:
            status = attempt.status.title()

        writer.writerow([
            f"#{attempt.id}",
            attempt.participant_info,
            'Speech',
            attempt.started_at.strftime('%b %d, %Y %H:%M'),
            1,  # Speech tests have 1 item
            correct_count,
            incorrect_count,
            f"{attempt.score:.1f}%" if attempt.score is not None else 'N/A',
            status
        ])

    csv_content = buffer.getvalue()
    buffer.close()

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="speech_report.csv"'
    return response

@decorator.admin_required
def admin_training(request):
    return render(request, "adminNew/training.html")


   
@decorator.admin_required
def add_activity_mcq(request):
    print("[add_activity] method=", request.method)
    if request.method == "POST":
        try:
            import json
            data = request.POST or {}
            if not data:
                data = json.loads(request.body.decode("utf-8")) if request.body else {}
            print("[add_activity][POST] payload_keys=", list(data.keys()))
            
            activity_id = data.get("id") or request.GET.get("id")
            item_number = int(data.get("item_number", 1))
            action = data.get("action", "save")  # save, add_next
            
            if activity_id:
                activity = get_object_or_404(Activity, id=activity_id)
            else:
                # Create new activity
                initial_timer = data.get("timer_seconds")
                if initial_timer is not None:
                    try:
                        initial_timer = int(initial_timer)
                    except (ValueError, TypeError):
                        initial_timer = 0
                else:
                    initial_timer = 0
                
                activity = Activity.objects.create(
                    title=data.get("title", "New Activity"),
                    description=data.get("description", ""),
                    timer_seconds=initial_timer,
                    created_by=request.user if request.user.is_authenticated else None
                )
            
            print(f"[add_activity][POST] target_activity_id={activity.id}, item_number={item_number}")
            
            # Update activity basic info (including timer - applies to all items)
            activity.title = data.get("title", activity.title)
            activity.description = data.get("description", activity.description)
            # Timer is set once for the entire activity, applies to all items
            # Always save timer_seconds (even if 0) so it can be updated/cleared
            timer_seconds = data.get("timer_seconds")
            if timer_seconds is not None:
                try:
                    timer_seconds = int(timer_seconds)
                except (ValueError, TypeError):
                    timer_seconds = activity.timer_seconds if activity.timer_seconds else 0
            else:
                # If timer_seconds is not provided, keep existing value
                timer_seconds = activity.timer_seconds if activity.timer_seconds else 0
            
            print(f"[add_activity][POST] timer_seconds received: {data.get('timer_seconds')}, parsed: {timer_seconds}, existing: {activity.timer_seconds}")
            activity.timer_seconds = timer_seconds
            activity.save(update_fields=['title', 'description', 'timer_seconds'])
            print(f"[add_activity][POST] timer_seconds saved: {activity.timer_seconds}")
            
            # Handle current item
            if action == "save" or action == "add_next":
                scenario = data.get("scenario", "").strip()
                
                # For "add_next" action, require scenario
                if action == "add_next" and not scenario:
                    return JsonResponse({
                        "ok": False, 
                        "error": "Scenario is required. Please enter a scenario before adding the next item."
                    }, status=400)
                
                # For "save" action, skip items without scenario
                if action == "save" and not scenario:
                    return JsonResponse({
                        "ok": True, 
                        "message": "Item skipped - no scenario provided",
                        "redirect_to_view": f"/adminNew/activity-materials/view-mcq-activity/?id={activity.id}"
                    })
                
                # Get or create activity item (timer is not stored per item anymore)
                activity_item, created = ActivityItem.objects.get_or_create(
                    activity=activity,
                    item_number=item_number,
                    defaults={
                        'scenario': scenario
                    }
                )
                
                if not created:
                    activity_item.scenario = scenario
                    activity_item.save()
                
                # Update choices for this item
                choices = data.get("choices", [])
                if isinstance(choices, str):
                    try:
                        choices = json.loads(choices)
                    except Exception:
                        choices = []
                
                print(f"[add_activity][POST] incoming_choices_count={len(choices) if isinstance(choices, list) else 'n/a'}")
                
                # Delete existing choices for this item
                activity_item.choices.all().delete()
                
                # Create new choices
                bulk = []
                for order, text in enumerate(choices[:4]):
                    text_str = (text or "").strip()
                    if not text_str:
                        continue
                    # First choice is correct answer
                    is_correct = (order == 0)
                    bulk.append(ActivityChoice(
                        activity_item=activity_item,
                        text=text_str,
                        display_order=order,
                        is_correct=is_correct
                    ))
                
                if bulk:
                    ActivityChoice.objects.bulk_create(bulk)
                print(f"[add_activity][POST] saved_choices_count={len(bulk)}")
            
            # If adding next item, increment item number
            if action == "add_next":
                next_item_number = item_number + 1
                return JsonResponse({
                    "ok": True, 
                    "id": activity.id, 
                    "next_item_number": next_item_number,
                    "redirect": f"?id={activity.id}&item={next_item_number}"
                })
            else:
                # For "save" action, redirect to separate MCQ view page
                return JsonResponse({
                    "ok": True, 
                    "id": activity.id,
                    "redirect_to_view": f"/adminNew/activity-materials/view-mcq-activity/?id={activity.id}"
                })
                
        except Exception as e:
            print("[add_activity][POST][error]", e)
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    # GET: render activity details from DB
    activity = None
    activity_id = request.GET.get("id") or request.GET.get("activity_id")
    item_number = int(request.GET.get("item", 1))
    is_new_item = request.GET.get("new_item", "false").lower() == "true"
    
    if activity_id:
        activity = get_object_or_404(Activity, id=activity_id)
        print(f"[add_activity][GET] load_by_id id={activity_id}")
        
        # If adding a new item, find the next available item number
        if is_new_item:
            last_item = ActivityItem.objects.filter(activity=activity).order_by('-item_number').first()
            item_number = (last_item.item_number + 1) if last_item else 1
            print(f"[add_activity][GET] new_item, next_item_number={item_number}")
    else:
        # Don't load any activity - start with blank form
        activity = None
        print("[add_activity][GET] starting with blank form")

    # Get current item data
    current_item = None
    choices = []
    if activity is not None and not is_new_item:
        # Only load existing item data if we're not explicitly adding a new item
        try:
            current_item = ActivityItem.objects.get(activity=activity, item_number=item_number)
            choices = list(current_item.choices.order_by("display_order", "id").values_list("text", flat=True))
        except ActivityItem.DoesNotExist:
            # Item doesn't exist yet, use empty choices
            choices = ["", "", "", ""]
    else:
        # No activity loaded or adding new item, use empty choices for new form
        choices = ["", "", "", ""]
    
    print(f"[add_activity][GET] choices_count={len(choices)}, item_number={item_number}")

    context = {
        "activity": activity,
        "current_item": current_item,
        "choices": choices,
        "item_number": item_number,
    }
    return render(request, "adminNew/add_activity_mcq.html", context)


@decorator.admin_required
def view_mcq_activity(request):
    """View for displaying MCQ activity items in a separate page"""
    activity_id = request.GET.get("id")
    
    if not activity_id:
        return JsonResponse({"error": "Activity ID required"}, status=400)
    
    try:
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Get all items for this activity
        all_items = ActivityItem.objects.filter(activity=activity).order_by("item_number")
        
        context = {
            "activity": activity,
            "all_items": all_items,
        }
        
        return render(request, "adminNew/view_mcq_activity.html", context)
        
    except Exception as e:
        print(f"[view_mcq_activity] error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@decorator.admin_required
def add_activity_speech(request):
    print("[add_activity_speech] method=", request.method)
    if request.method == "POST":
        try:
            import json
            data = request.POST or {}
            if not data:
                data = json.loads(request.body.decode("utf-8")) if request.body else {}
            print("[add_activity_speech][POST] payload_keys=", list(data.keys()))
            
            activity_id = data.get("id") or request.GET.get("id")
            item_number = int(data.get("item_number", 1))
            action = data.get("action", "save")  # save, add_next
            
            if activity_id:
                activity = get_object_or_404(SpeechActivity, id=activity_id)
            else:
                # Create new speech activity
                activity = SpeechActivity.objects.create(
                    title=data.get("title", "New Speech Activity"),
                    description=data.get("description", ""),
                    timer_seconds=int(data.get("timer_seconds", 0)),
                    created_by=request.user if request.user.is_authenticated else None
                )
            
            print(f"[add_activity_speech][POST] target_activity_id={activity.id}, item_number={item_number}")
            
            # Update activity basic info
            activity.title = data.get("title", activity.title)
            activity.description = data.get("description", activity.description)
            activity.timer_seconds = int(data.get("timer_seconds", activity.timer_seconds))
            
            # Handle reference text
            reference_text = data.get("reference_text", "").strip()
            if reference_text:
                activity.reference_text = reference_text
            
            # Handle file uploads
            if 'audio_file' in request.FILES:
                activity.audio_file = request.FILES['audio_file']
            if 'script_file' in request.FILES:
                activity.script_file = request.FILES['script_file']
                # Extract text from script file if it's a .txt file
                if activity.script_file.name.lower().endswith('.txt'):
                    try:
                        activity.script_file.seek(0)
                        script_content = activity.script_file.read().decode('utf-8')
                        activity.reference_text = script_content
                    except Exception as e:
                        print(f"Error reading script file: {e}")
            
            activity.save()
            
            # If adding next item, increment item number
            if action == "add_next":
                next_item_number = item_number + 1
                return JsonResponse({
                    "ok": True, 
                    "id": activity.id, 
                    "next_item_number": next_item_number,
                    "redirect": f"?id={activity.id}&item={next_item_number}"
                })
            else:
                # For "save" action, redirect to speech activity view page
                return JsonResponse({
                    "ok": True, 
                    "id": activity.id,
                    "redirect_to_view": f"/adminNew/activity-materials/view-speech-activity/?id={activity.id}"
                })
                
        except Exception as e:
            print("[add_activity_speech][POST][error]", e)
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    # GET: render activity details from DB
    activity = None
    activity_id = request.GET.get("id") or request.GET.get("activity_id")
    item_number = int(request.GET.get("item", 1))
    
    if activity_id:
        activity = get_object_or_404(SpeechActivity, id=activity_id)
        print(f"[add_activity_speech][GET] load_by_id id={activity_id}")
    else:
        activity = SpeechActivity.objects.order_by("-created_at").first()
        print("[add_activity_speech][GET] load_latest id=", getattr(activity, "id", None))

    context = {
        "activity": activity,
        "item_number": item_number,
    }
    return render(request, "adminNew/add_activity_speech.html", context)


@decorator.admin_required
def view_speech_activity(request):
    """View for displaying speech activity items similar to MCQ page layout"""
    activity_id = request.GET.get("id")
    
    if not activity_id:
        return JsonResponse({"error": "Activity ID required"}, status=400)
    
    try:
        activity = get_object_or_404(SpeechActivity, id=activity_id)
        
        # For speech activities, we'll treat each activity as a single "item"
        # since speech activities don't have multiple items like MCQ activities
        context = {
            "activity": activity,
            "item_number": 1,  # Speech activities are single items
            "current_item": {
                "scenario": getattr(activity, 'scenario', ''),
                "timer_seconds": activity.timer_seconds,
            },
            "choices": [],  # Speech activities don't have choices
        }
        
        return render(request, "adminNew/view_speech_activity.html", context)
        
    except Exception as e:
        print(f"[view_speech_activity] error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@decorator.admin_required
def save_activities(request):
    print("[save_activities] method=", request.method)
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Invalid method"}, status=405)

    try:
        # Expect JSON payload: { activities: [{title, description}], delete_ids: [] }
        import json
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        items = data.get("activities", [])
        delete_ids = data.get("delete_ids", [])
        print(f"[save_activities] payload activities={len(items)} delete_ids={len(delete_ids)} user={'auth' if request.user.is_authenticated else 'anon'}")

        # Optionally delete
        if delete_ids:
            Activity.objects.filter(id__in=delete_ids).delete()
            print(f"[save_activities] deleted_count={len(delete_ids)}")

        saved = []
        for item in items:
            act_id = item.get("id")
            title = (item.get("title") or "").strip()
            description = (item.get("description") or "").strip()
            if not description:
                print("[save_activities] skip: empty description")
                continue
            # Create new or update existing
            if act_id:
                act = Activity.objects.filter(id=act_id).first() or Activity(id=act_id)
            else:
                act = Activity()
            act.title = title or (act.title or "Activity Title")
            act.description = description
            if request.user.is_authenticated:
                act.created_by = request.user
            act.save()
            saved.append({"id": act.id, "title": act.title})
            print(f"[save_activities] saved id={act.id} title='{act.title}'")

        return JsonResponse({"ok": True, "saved": saved})
    except Exception as e:
        print("[save_activities][error]", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

@decorator.admin_required
def addmt_mcq(request):
    print("[admin_activity_materials] method=GET user=", request.user if request.user.is_authenticated else "anonymous")
    activities = Activity.objects.order_by("created_at")
    try:
        count = activities.count()
    except Exception:
        count = len(list(activities))
    print(f"[admin_activity_materials] activities_count={count}")
    return render(request, "adminNew/addmt_mcq.html", {"activities": activities})
@csrf_exempt
@decorator.admin_required
def delete_activity_items(request):
    """Delete selected activity items"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)
    
    try:
        import json
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
        
        activity_id = data.get("activity_id")
        item_numbers = data.get("item_numbers", [])
        
        if not activity_id:
            return JsonResponse({"ok": False, "error": "Activity ID is required"}, status=400)
        
        if not item_numbers:
            return JsonResponse({"ok": False, "error": "No items selected for deletion"}, status=400)
        
        # Get the activity
        activity = get_object_or_404(Activity, id=activity_id)
        
        # Delete the selected items
        deleted_count = 0
        for item_number in item_numbers:
            try:
                activity_item = ActivityItem.objects.get(activity=activity, item_number=item_number)
                activity_item.delete()
                deleted_count += 1
            except ActivityItem.DoesNotExist:
                continue
        
        print(f"[delete_activity_items] deleted {deleted_count} items from activity {activity_id}")
        
        return JsonResponse({
            "ok": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} item(s)"
        })
        
    except Exception as e:
        print("[delete_activity_items][error]", e)
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

@decorator.admin_required
def addmt_speech_to_text(request):
    print("[addmt_speech_to_text] method=", request.method)
    if request.method == "POST":
        action = request.POST.get('action', 'save')
        
        # Handle delete action
        if action == 'delete':
            item_id = request.POST.get('id')
            if item_id:
                try:
                    speech = SpeechActivity.objects.get(id=item_id)
                    speech.delete()
                    print(f"Deleted SpeechActivity with id: {item_id}")
                    return JsonResponse({"ok": True, "deleted": True, "id": item_id})
                except SpeechActivity.DoesNotExist:
                    print(f"SpeechActivity with id {item_id} not found")
                    return JsonResponse({"ok": False, "error": "Activity not found"})
            else:
                return JsonResponse({"ok": False, "error": "No ID provided for deletion"})
        
        # Handle save action (create or update)
        item_id = request.POST.get('id')
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        reference_text = (request.POST.get('reference_text') or '').strip()
        timer = request.POST.get('timer_seconds', '0')
        try:
            timer_seconds = int(timer or 0)
        except ValueError:
            timer_seconds = 0

        if item_id:
            speech = SpeechActivity.objects.filter(id=item_id).first() or SpeechActivity(id=item_id)
            if title:
                speech.title = title
            if description:
                speech.description = description
            if reference_text:
                speech.reference_text = reference_text
            speech.timer_seconds = timer_seconds
        else:
            speech = SpeechActivity(
                title=title or 'Activity Title',
                description=description,
                reference_text=reference_text,
                timer_seconds=timer_seconds,
            )
        if request.user.is_authenticated:
            speech.created_by = request.user
        if 'audio_file' in request.FILES:
            speech.audio_file = request.FILES['audio_file']
        if 'script_file' in request.FILES:
            speech.script_file = request.FILES['script_file']
            # Extract text from script file if it's a .txt file
            if speech.script_file.name.lower().endswith('.txt'):
                try:
                    speech.script_file.seek(0)
                    script_content = speech.script_file.read().decode('utf-8')
                    speech.reference_text = script_content
                except Exception as e:
                    print(f"Error reading script file: {e}")
        speech.save()
        return JsonResponse({"ok": True, "id": speech.id})
    else:
        # Render the form for adding a new Speech-to-Text activity
        activities = SpeechActivity.objects.order_by("created_at")
        return render(request, "adminNew/addmt_speech.html", {"activities": activities})

@decorator.admin_required
def admin_sales_reports(request):
    """Sales Reports with daily/weekly/monthly filtering"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.utils import timezone
    
    # Get filter type (daily, weekly, monthly, or all)
    period = request.GET.get('period', 'all')  # daily, weekly, monthly, all
    search_query = request.GET.get('search', '')
    
    # Calculate date range based on period
    today = timezone.now().date()
    start_date = None
    end_date = today
    
    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        # Start of current week (Monday)
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == 'monthly':
        # Start of current month
        start_date = today.replace(day=1)
        end_date = today
    
    # Initialize revenue totals
    front_office_revenue = 0.0
    room_service_revenue = 0.0
    laundry_revenue = 0.0
    cafe_revenue = 0.0
    excess_pax_revenue = 0.0
    additional_charge_revenue = 0.0
    total_revenue = 0.0
    
    # Calculate revenue based on actual transaction dates, not guest billing totals
    
    # Front office revenue - only from bookings in the period
    # For front office, we need to calculate based on booking dates
    if start_date:
        # Get bookings in the period and sum their billing amounts
        # Note: We'll approximate by getting guests with bookings in period
        # and using a portion of their billing, but this is complex
        # For now, let's get all guests with active bookings and sum their billing
        # but only if they have bookings in the period
        bookings_in_period = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out'],
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        )
        guest_ids_in_period = bookings_in_period.values_list('guest_id', flat=True).distinct()
        front_office_revenue = Guest.objects.filter(
            id__in=guest_ids_in_period
        ).aggregate(total=Sum('billing'))['total'] or 0
        front_office_revenue = float(front_office_revenue) if front_office_revenue else 0.0
    else:
        # All time - get all guests with active bookings
        all_guest_ids = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out']
        ).values_list('guest_id', flat=True).distinct()
        front_office_revenue = Guest.objects.filter(
            id__in=all_guest_ids
        ).aggregate(total=Sum('billing'))['total'] or 0
        front_office_revenue = float(front_office_revenue) if front_office_revenue else 0.0
    
    # Get all guests with active bookings (for room service, excess pax, additional charges)
    all_guest_ids = Booking.objects.filter(
        status__in=['Checked-in', 'Checked-out']
    ).values_list('guest_id', flat=True).distinct()
    
    # Room service revenue - only count if guest has booking in period (if period specified)
    if start_date:
        guest_ids_in_period = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out'],
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        ).values_list('guest_id', flat=True).distinct()
        room_service_revenue = Guest.objects.filter(
            id__in=guest_ids_in_period
        ).aggregate(total=Sum('room_service_billing'))['total'] or 0
    else:
        room_service_revenue = Guest.objects.filter(
            id__in=all_guest_ids
        ).aggregate(total=Sum('room_service_billing'))['total'] or 0
    room_service_revenue = float(room_service_revenue) if room_service_revenue else 0.0
    
    # Laundry revenue from room charges - filter by transaction date
    # Payment method stored value is 'room' (not 'Charge to room')
    laundry_room_qs = LaundryTransaction.objects.filter(
        payment_method='room'
    )
    if start_date:
        # Use date range filtering - convert date to datetime range
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        laundry_room_qs = laundry_room_qs.filter(
            date_time__gte=start_datetime,
            date_time__lte=end_datetime
        )
    laundry_revenue = laundry_room_qs.aggregate(total_sum=Sum('total_amount'))['total_sum'] or 0
    laundry_revenue = float(laundry_revenue) if laundry_revenue else 0.0
    
    # Cafe revenue from room charges - filter by order date
    # Payment method stored value is 'room'
    cafe_room_qs = CafeOrder.objects.filter(
        payment_method='room'
    )
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        cafe_room_qs = cafe_room_qs.filter(
            order_date__gte=start_datetime,
            order_date__lte=end_datetime
        )
    cafe_revenue = cafe_room_qs.aggregate(total_sum=Sum('total'))['total_sum'] or 0
    cafe_revenue = float(cafe_revenue) if cafe_revenue else 0.0
    
    # Add cafe revenue from cash/card payments - filter by order date
    cafe_qs = CafeOrder.objects.exclude(payment_method='room')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        cafe_qs = cafe_qs.filter(
            order_date__gte=start_datetime,
            order_date__lte=end_datetime
        )
    total_cafe = cafe_qs.aggregate(total_sum=Sum('total'))['total_sum'] or 0
    cafe_revenue += float(total_cafe) if total_cafe else 0.0
    
    # Add laundry revenue from cash payments - filter by transaction date
    laundry_qs = LaundryTransaction.objects.exclude(payment_method='room')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        laundry_qs = laundry_qs.filter(
            date_time__gte=start_datetime,
            date_time__lte=end_datetime
        )
    total_laundry = laundry_qs.aggregate(total_sum=Sum('total_amount'))['total_sum'] or 0
    laundry_revenue += float(total_laundry) if total_laundry else 0.0
    
    # Excess pax and additional charges - only count if guest has booking in period (if period specified)
    if start_date:
        guest_ids_in_period = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out'],
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        ).values_list('guest_id', flat=True).distinct()
        excess_pax_revenue = Guest.objects.filter(
            id__in=guest_ids_in_period
        ).aggregate(total=Sum('excess_pax_billing'))['total'] or 0
        additional_charge_revenue = Guest.objects.filter(
            id__in=guest_ids_in_period
        ).aggregate(total=Sum('additional_charge_billing'))['total'] or 0
    else:
        excess_pax_revenue = Guest.objects.filter(
            id__in=all_guest_ids
        ).aggregate(total=Sum('excess_pax_billing'))['total'] or 0
        additional_charge_revenue = Guest.objects.filter(
            id__in=all_guest_ids
        ).aggregate(total=Sum('additional_charge_billing'))['total'] or 0
    excess_pax_revenue = float(excess_pax_revenue) if excess_pax_revenue else 0.0
    additional_charge_revenue = float(additional_charge_revenue) if additional_charge_revenue else 0.0
    
    # Calculate total revenue
    total_revenue = (
        front_office_revenue +
        room_service_revenue +
        laundry_revenue +
        cafe_revenue +
        excess_pax_revenue +
        additional_charge_revenue
    )
    
    # Get transaction counts - count all transactions (bookings, cafe orders, laundry) in period
    booking_count = 0
    cafe_count = 0
    laundry_count = 0
    
    if start_date:
        # Count bookings in period
        booking_count = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out'],
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        ).count()
        
        # Count cafe orders in period
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        cafe_count = CafeOrder.objects.filter(
            order_date__gte=start_datetime,
            order_date__lte=end_datetime
        ).count()
        
        # Count laundry transactions in period
        laundry_count = LaundryTransaction.objects.filter(
            date_time__gte=start_datetime,
            date_time__lte=end_datetime
        ).count()
    else:
        # All time counts
        booking_count = Booking.objects.filter(
            status__in=['Checked-in', 'Checked-out']
        ).count()
        cafe_count = CafeOrder.objects.count()
        laundry_count = LaundryTransaction.objects.count()
    
    total_transactions = booking_count + cafe_count + laundry_count
    
    # Prepare sales data for display - include bookings, cafe orders, and laundry transactions
    sales_data = []
    
    # Get bookings
    bookings = Booking.objects.filter(
        status__in=['Checked-in', 'Checked-out']
    ).select_related('guest')
    
    if start_date:
        bookings = bookings.filter(
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        )
    
    if search_query:
        bookings = bookings.filter(
            Q(guest__name__icontains=search_query) |
            Q(room__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Add bookings to sales_data
    for booking in bookings:
        guest = booking.guest
        try:
            fo = float(guest.billing or 0)
            rs = float(guest.room_service_billing or 0)
            la = float(guest.laundry_billing or 0)
            ca = float(guest.cafe_billing or 0)
            ep = float(guest.excess_pax_billing or 0)
            ad = float(guest.additional_charge_billing or 0)
            other = ep + ad
            total = fo + rs + la + ca + ep + ad
        except (ValueError, TypeError):
            fo = rs = la = ca = ep = ad = other = total = 0.0
        
        sales_data.append({
            'type': 'booking',
            'booking': booking,
            'date': booking.booking_date,
            'front_office': fo,
            'room_service': rs,
            'laundry': la,
            'cafe': ca,
            'other': other,
            'total': total
        })
    
    # Get cafe orders
    cafe_orders = CafeOrder.objects.select_related('guest')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        cafe_orders = cafe_orders.filter(
            order_date__gte=start_datetime,
            order_date__lte=end_datetime
        )
    
    if search_query:
        cafe_orders = cafe_orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(guest__name__icontains=search_query)
        )
    
    # Add cafe orders to sales_data
    for order in cafe_orders:
        sales_data.append({
            'type': 'cafe',
            'cafe_order': order,
            'date': order.order_date,
            'front_office': 0.0,
            'room_service': 0.0,
            'laundry': 0.0,
            'cafe': float(order.total),
            'other': 0.0,
            'total': float(order.total)
        })
    
    # Get laundry transactions
    laundry_trans = LaundryTransaction.objects.select_related('guest')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        laundry_trans = laundry_trans.filter(
            date_time__gte=start_datetime,
            date_time__lte=end_datetime
        )
    
    if search_query:
        laundry_trans = laundry_trans.filter(
            Q(guest__name__icontains=search_query) |
            Q(room_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Add laundry transactions to sales_data
    for trans in laundry_trans:
        sales_data.append({
            'type': 'laundry',
            'laundry_trans': trans,
            'date': trans.date_time,
            'front_office': 0.0,
            'room_service': 0.0,
            'laundry': float(trans.total_amount),
            'cafe': 0.0,
            'other': 0.0,
            'total': float(trans.total_amount)
        })
    
    # Sort all sales data by date (newest first)
    sales_data.sort(key=lambda x: x['date'], reverse=True)
    
    # Paginate the combined sales_data
    paginator = Paginator(sales_data, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Create a wrapper class to make sales_data work with pagination template tags
    class SalesDataPage:
        def __init__(self, sales_data_list, original_page_obj):
            self._sales_data = sales_data_list
            self.number = original_page_obj.number
            self.paginator = original_page_obj.paginator
            self.has_previous = original_page_obj.has_previous
            self.has_next = original_page_obj.has_next
            self.previous_page_number = original_page_obj.previous_page_number
            self.next_page_number = original_page_obj.next_page_number
        
        def __iter__(self):
            return iter(self._sales_data)
        
        def __len__(self):
            return len(self._sales_data)
    
    sales_page = SalesDataPage(list(page_obj), page_obj)
    
    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'front_office_revenue': front_office_revenue,
        'room_service_revenue': room_service_revenue,
        'laundry_revenue': laundry_revenue,
        'cafe_revenue': cafe_revenue,
        'excess_pax_revenue': excess_pax_revenue,
        'additional_charge_revenue': additional_charge_revenue,
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'page_obj': sales_page,
        'paginator': paginator,
        'search_query': search_query,
    }
    return render(request, "adminNew/sales_reports.html", context)

@require_GET
@decorator.admin_required
def admin_sales_reports_export(request):
    """Export Sales Reports as CSV"""
    import csv
    from io import StringIO
    from django.utils import timezone
    from django.db.models import Q
    
    # Get filter type
    period = request.GET.get('period', 'all')
    search_query = request.GET.get('search', '')
    
    # Calculate date range
    today = timezone.now().date()
    start_date = None
    end_date = today
    
    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    
    # Prepare CSV
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'Transaction Type', 'ID', 'Guest Name', 'Room', 'Date', 'Payment Method',
        'Front Office', 'Room Service', 'Laundry', 'Cafe', 'Excess Pax', 'Additional Charges', 'Total'
    ])
    
    # Export bookings with their guest billing
    bookings = Booking.objects.filter(
        status__in=['Checked-in', 'Checked-out']
    ).select_related('guest')
    
    if start_date:
        bookings = bookings.filter(
            booking_date__date__gte=start_date,
            booking_date__date__lte=end_date
        )
    
    if search_query:
        bookings = bookings.filter(
            Q(guest__name__icontains=search_query) |
            Q(room__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    bookings = bookings.order_by('-booking_date')
    
    for booking in bookings:
        guest = booking.guest
        if not guest:
            # Skip bookings without guests (shouldn't happen, but be safe)
            continue
        try:
            fo = float(guest.billing or 0)
            rs = float(guest.room_service_billing or 0)
            la = float(guest.laundry_billing or 0)
            ca = float(guest.cafe_billing or 0)
            ep = float(guest.excess_pax_billing or 0)
            ad = float(guest.additional_charge_billing or 0)
            total = fo + rs + la + ca + ep + ad
        except (ValueError, TypeError):
            fo = rs = la = ca = ep = ad = total = 0.0
        
        writer.writerow([
            'Booking',
            f"BK{booking.id:05d}",
            guest.name if guest else 'N/A',
            booking.room,
            booking.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
            'N/A',
            f"{fo:.2f}",
            f"{rs:.2f}",
            f"{la:.2f}",
            f"{ca:.2f}",
            f"{ep:.2f}",
            f"{ad:.2f}",
            f"{total:.2f}"
        ])
    
    # Export cafe orders
    cafe_orders = CafeOrder.objects.select_related('guest')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        cafe_orders = cafe_orders.filter(
            order_date__gte=start_datetime,
            order_date__lte=end_datetime
        )
    
    if search_query:
        cafe_orders = cafe_orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(id__icontains=search_query) |
            Q(guest__name__icontains=search_query)
        )
    
    cafe_orders = cafe_orders.order_by('-order_date')
    
    for order in cafe_orders:
        # Safely get guest name
        guest_name = order.customer_name or 'Walk-in'
        try:
            if order.guest_id:
                guest_name = order.guest.name if order.guest else 'Walk-in'
        except Exception:
            guest_name = 'Walk-in'
        
        # Safely get room number
        room_number = 'N/A'
        try:
            if order.guest_id and order.guest:
                first_booking = order.guest.booking_set.first()
                if first_booking:
                    room_number = first_booking.room
        except Exception:
            room_number = 'N/A'
        
        writer.writerow([
            'Cafe Order',
            f"CF{order.id:05d}",
            guest_name,
            room_number,
            order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            order.get_payment_method_display(),
            '0.00',
            '0.00',
            '0.00',
            f"{float(order.total):.2f}",
            '0.00',
            '0.00',
            f"{float(order.total):.2f}"
        ])
    
    # Export laundry transactions
    laundry_trans = LaundryTransaction.objects.select_related('guest')
    if start_date:
        from datetime import datetime as dt
        start_datetime = timezone.make_aware(dt.combine(start_date, dt.min.time()))
        end_datetime = timezone.make_aware(dt.combine(end_date, dt.max.time()))
        laundry_trans = laundry_trans.filter(
            date_time__gte=start_datetime,
            date_time__lte=end_datetime
        )
    
    if search_query:
        laundry_trans = laundry_trans.filter(
            Q(guest__name__icontains=search_query) |
            Q(room_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    laundry_trans = laundry_trans.order_by('-date_time')
    
    for trans in laundry_trans:
        # Safely get guest name
        guest_name = 'N/A'
        try:
            if trans.guest_id:
                guest_name = trans.guest.name if trans.guest else 'N/A'
        except Exception:
            guest_name = 'N/A'
        
        writer.writerow([
            'Laundry',
            f"LD{trans.id:05d}",
            guest_name,
            trans.room_number or 'N/A',
            trans.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            trans.get_payment_method_display(),
            '0.00',
            '0.00',
            f"{float(trans.total_amount):.2f}",
            '0.00',
            '0.00',
            '0.00',
            f"{float(trans.total_amount):.2f}"
        ])
    
    csv_content = buffer.getvalue()
    buffer.close()
    
    period_label = period.capitalize() if period != 'all' else 'All'
    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{period_label}_{today.strftime("%Y%m%d")}.csv"'
    return response