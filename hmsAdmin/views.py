from django.shortcuts import render, redirect, get_object_or_404
from globals import decorator
from chat.models import Message
from django.db import models
from django.contrib import messages
from django.http import JsonResponse
from users.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from staff.models import Reservation, Room
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from .models import SpeechToTextActivity, MCQActivity
from django.views.decorators.csrf import csrf_exempt
import calendar
import locale

from users.models import CustomUser  
# Create your views here.
@decorator.role_required('admin')
def home(request):
    users = CustomUser.objects.all()
    # --- Total number of guests ---
    guest_qs = Reservation.objects.filter(status__in=["confirmed", "checked_in", "checked_out"])
    
    # Calculate total guests by summing number_of_guests
    total_guests = guest_qs.aggregate(total=Sum('number_of_guests'))['total'] or 0

    # --- Peak month (by guest count) ---
    monthly_guests = guest_qs.annotate(month=TruncMonth('checkin_date')).values('month').annotate(guest_count=Sum('number_of_guests')).order_by('-guest_count')
    if monthly_guests and len(monthly_guests) > 0 and monthly_guests[0]['month']:
        peak_month_date = monthly_guests[0]['month']
        peak_month = calendar.month_name[peak_month_date.month]
    else:
        peak_month = "-"

    # --- Overall Revenue (current month) ---
    current_month = timezone.now().month
    current_year = timezone.now().year
    current_month_revenue = guest_qs.filter(
        checkin_date__month=current_month,
        checkin_date__year=current_year
    ).aggregate(total=Sum('total_balance'))['total'] or 0

    # Format revenue with thousands separator and two decimals
    try:
        locale.setlocale(locale.LC_ALL, '')
        formatted_revenue = locale.format_string('%.2f', current_month_revenue, grouping=True)
    except Exception:
        formatted_revenue = f"{current_month_revenue:,.2f}"

    # Print debug information
    print(f"Total Guests: {total_guests}")
    print(f"Peak Month: {peak_month}")
    print(f"Current Month Revenue: {current_month_revenue}")

    return render(request, "hmsAdmin/home.html", {
        "users": users,
        "total_guests": total_guests,
        "peak_month": peak_month,
        "total_revenue": formatted_revenue,
    })

@decorator.role_required('admin')
def messages(request):
    
    receiver_role = request.GET.get('receiver_role', 'personnel')
    room_name = f"chat_{receiver_role}"
    user_role = request.user.role
    messages_qs = Message.objects.filter(
        (models.Q(sender_role=user_role, receiver_role=receiver_role)) |
        (models.Q(sender_role=receiver_role, receiver_role=user_role))
    ).order_by('created_at')
    return render(request, "hmsAdmin/messages.html", {
        "room_name": room_name,
        "receiver_role": receiver_role,
        "messages": messages_qs,
        "current_user_id": request.user.id,
    })

@decorator.role_required('admin')
def training(request):
    return render(request, "hmsAdmin/training.html")

@decorator.role_required('admin')
def analytics(request):
    return render(request, "hmsAdmin/analytics.html")

@decorator.role_required('admin')
def accounts(request):
    users = CustomUser.objects.all()
    return render(request, "hmsAdmin/accounts.html", {"users": users})

@decorator.role_required('admin')
def add_user(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            role = request.POST.get('role')

            # Check if username or email already exists
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

            # Create new user
            user = CustomUser.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role=role
            )

            return JsonResponse({'status': 'success', 'message': 'User created successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@decorator.role_required('admin')
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

@decorator.role_required('admin')
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            password = request.POST.get('password')

            # Check if username or email already exists (excluding current user)
            if CustomUser.objects.exclude(id=user_id).filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.exclude(id=user_id).filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

            # Update user
            user.username = username
            user.email = email
            user.role = role
            if password:  # Only update password if provided
                user.password = make_password(password)
            user.save()

            # Return updated user data
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
    
    # GET request - return user data
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }
    return JsonResponse(data)

@decorator.role_required('admin')
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

@decorator.role_required('admin')
def occupancy_forecast(request):
    # Calculate monthly occupancy rates
    total_rooms = Room.objects.count()
    monthly_occupancy = Reservation.objects.annotate(month=TruncMonth('checkin_date')).values('month').annotate(count=Count('id')).order_by('month')
    print(monthly_occupancy)
    # Convert to DataFrame
    df = pd.DataFrame(list(monthly_occupancy))
    if df.empty:
        return JsonResponse({'error': 'No data available'}, status=400)
    
    df['occupancy_rate'] = df['count'] / total_rooms
    
    # Fit SARIMA model
    model = SARIMAX(df['occupancy_rate'], order=(1,1,1), seasonal_order=(1,1,1,12))
    results = model.fit()   

    # --- Accuracy metrics (in-sample) ---
    y_true = df['occupancy_rate']
    y_pred = results.fittedvalues
    mae = (abs(y_true - y_pred)).mean()
    rmse = ((y_true - y_pred) ** 2).mean() ** 0.5
    mape = (abs((y_true - y_pred) / y_true).replace([float('inf'), -float('inf')], 0).dropna()).mean() * 100
    print("\nSARIMA Forecast Accuracy (in-sample):")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.2f}%\n")
    
    # Forecast next 12 months
    forecast = results.get_forecast(steps=12)
    forecast_index = pd.date_range(df['month'].iloc[-1] + pd.offsets.MonthEnd(1), periods=12, freq='M')
    forecast_series = pd.Series(forecast.predicted_mean.values, index=forecast_index)
    
    # Prepare response data
    historical_data = df[['month', 'occupancy_rate']].rename(columns={'month': 'date'}).to_dict('records')
    forecast_data = [{'date': date.strftime('%Y-%m-%d'), 'occupancy_rate': rate} for date, rate in zip(forecast_series.index, forecast_series.values)]
    
    return JsonResponse({
        'historical': historical_data,
        'forecast': forecast_data
    })

@decorator.role_required('admin')
def mcq_page(request):
    activities = MCQActivity.objects.all().order_by('-created_at')
    return render(request, 'hmsAdmin/mcq.html', {'activities': activities})

@decorator.role_required('admin')
def speech_to_text_page(request):
    activities = SpeechToTextActivity.objects.all().order_by('-created_at')
    return render(request, 'hmsAdmin/speech_to_text.html', {'activities': activities})

@decorator.role_required('admin')
def add_speech_to_text_activity(request):
    if request.method == 'POST':
        title = request.POST.get('activityTitle1')
        description = request.POST.get('activityDesc1')
        audio_file = request.FILES.get('audioFile1')
        if title and description and audio_file:
            SpeechToTextActivity.objects.create(
                title=title,
                description=description,
                audio_file=audio_file
            )
            return redirect('speech_to_text_page')
    return render(request, 'hmsAdmin/add_speech_to_text_activity.html')

@decorator.role_required('admin')
def add_mcq_activity(request):
    if request.method == 'POST':
        print("ad mcg")
        title = request.POST.get('testTitle')
        description = request.POST.get('testDesc')
        scenario = request.POST.get('scenario')
        timer = request.POST.get('timer', '')
        choices = [
            request.POST.get('choice1'),
            request.POST.get('choice2'),
            request.POST.get('choice3'),
            request.POST.get('choice4'),
        ]
        action_block = bool(request.POST.get('action_block'))
        action_reserve = bool(request.POST.get('action_reserve'))
        action_cash_payment = bool(request.POST.get('action_cash_payment'))
        action_customization = bool(request.POST.get('action_customization'))
        if title and description and scenario and all(choices):
            MCQActivity.objects.create(
                title=title,
                description=description,
                scenario=scenario,
                timer=timer,
                choice1=choices[0],
                choice2=choices[1],
                choice3=choices[2],
                choice4=choices[3],
                action_block=action_block,
                action_reserve=action_reserve,
                action_cash_payment=action_cash_payment,
                action_customization=action_customization
            )
            return redirect('mcq_page')
    return render(request, 'hmsAdmin/add_mcq.html')

@decorator.role_required('admin')
@csrf_exempt
def delete_mcq_activity(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(MCQActivity, id=activity_id)
        activity.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@decorator.role_required('admin')
def edit_mcq_activity(request, activity_id):
    activity = get_object_or_404(MCQActivity, id=activity_id)
    if request.method == 'POST':
        activity.title = request.POST.get('testTitle')
        activity.description = request.POST.get('testDesc')
        activity.scenario = request.POST.get('scenario')
        activity.timer = request.POST.get('timer', '')
        activity.choice1 = request.POST.get('choice1')
        activity.choice2 = request.POST.get('choice2')
        activity.choice3 = request.POST.get('choice3')
        activity.choice4 = request.POST.get('choice4')
        activity.action_block = bool(request.POST.get('action_block'))
        activity.action_reserve = bool(request.POST.get('action_reserve'))
        activity.action_cash_payment = bool(request.POST.get('action_cash_payment'))
        activity.action_customization = bool(request.POST.get('action_customization'))
        activity.save()
        return redirect('mcq_page')
    return render(request, 'hmsAdmin/edit_mcq.html', {'activity': activity})

@decorator.role_required('admin')
def simulate_mcq_activity(request, activity_id):
    activity = get_object_or_404(MCQActivity, id=activity_id)
    return render(request, 'hmsAdmin/simulate_mcq.html', {'activity': activity})

@decorator.role_required('admin')
@csrf_exempt
def delete_speech_to_text_activity(request, activity_id):
    if request.method == 'POST':
        activity = get_object_or_404(SpeechToTextActivity, id=activity_id)
        activity.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@decorator.role_required('admin')
def edit_speech_to_text_activity(request, activity_id):
    activity = get_object_or_404(SpeechToTextActivity, id=activity_id)
    if request.method == 'POST':
        activity.title = request.POST.get('activityTitle1')
        activity.description = request.POST.get('activityDesc1')
        if request.FILES.get('audioFile1'):
            activity.audio_file = request.FILES.get('audioFile1')
        activity.save()
        return redirect('speech_to_text_page')
    return render(request, 'hmsAdmin/edit_speech_to_text.html', {'activity': activity})

@decorator.role_required('admin')
def simulate_speech_to_text_activity(request, activity_id):
    activity = get_object_or_404(SpeechToTextActivity, id=activity_id)
    return render(request, 'hmsAdmin/simulate_speech_to_text.html', {'activity': activity})

