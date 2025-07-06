from django.shortcuts import render, redirect, get_object_or_404
from globals import decorator
from chat.models import Message
from django.db import models
from django.contrib import messages
from django.http import JsonResponse
from users.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import SpeechToTextActivity, MCQActivity
import locale

@decorator.role_required('admin')
def home(request):
    users = CustomUser.objects.all()

    # Placeholder metrics
    total_guests = 0
    peak_month = "-"
    formatted_revenue = "0.00"

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

            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

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

            if CustomUser.objects.exclude(id=user_id).filter(username=username).exists():
                return JsonResponse({'status': 'error', 'message': 'Username already exists'})
            if CustomUser.objects.exclude(id=user_id).filter(email=email).exists():
                return JsonResponse({'status': 'error', 'message': 'Email already exists'})

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
    return JsonResponse({
        'error': 'Forecasting disabled. No data available from updated models.'
    }, status=400)

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
