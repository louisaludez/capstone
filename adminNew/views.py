from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from globals import decorator
from chat.models import Message
from django.db import models
from django.contrib import messages
from django.http import JsonResponse
from users.models import CustomUser
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from staff.models import *
import locale

# Create your views here.
def admin_home(request):
    users = CustomUser.objects.all()
    guest = Guest.objects.all().count()
    # Placeholder metrics
    total_guests = guest
    peak_month = "alaws"
    formatted_revenue = "0.00"

    return render(request, "adminNew/home.html", {
        "users": users,
        "total_guests": total_guests,
        "peak_month": peak_month,
        "total_revenue": formatted_revenue,
    })
def admin_account(request):
    users = CustomUser.objects.all()
    return render(request, "adminNew/accounts.html", {"users": users})

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
def admin_reports(request):
    return render(request, "adminNew/reports.html")
def admin_messenger(request):
    return render(request, "adminNew/messenger.html")
def admin_front_office_reports(request):
    return render(request, "adminNew/front_office_reports.html")
def admin_cafe_reports(request):
    return render(request, "adminNew/cafe_reports.html")
def admin_housekeeping_reports(request):
    return render(request, "adminNew/housekeeping_reports.html")
def admin_laundry_reports(request):
    return render(request, "adminNew/laundry_reports.html")
def admin_mcq_reports(request):
    return render(request, "adminNew/mcq_reports.html")
def admin_speech_reports(request):
    return render(request, "adminNew/speech_reports.html")
def admin_training(request):
    return render(request, "adminNew/training.html")

def admin_activity_materials(request):
    return render(request, "adminNew/activity_materials.html")