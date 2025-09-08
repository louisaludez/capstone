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
from .models import Activity, ActivityItem, ActivityChoice, SpeechActivity
import locale
from decimal import Decimal

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
def admin_reports(request):
    return render(request, "adminNew/reports.html")
def admin_messenger(request):
    return render(request, "adminNew/messenger.html")
def admin_front_office_reports(request):
    guests = Guest.objects.all()

    total = 0
    for g in guests:
        total += (
            int(g.billing or 0) +
            int(g.room_service_billing or 0) +
            int(g.laundry_billing or 0) +
            int(g.cafe_billing or 0) +
            int(g.excess_pax_billing or 0) +
            int(g.additional_charge_billing or 0)
        )
    context = {'total_revenue': total}
    return render(request, "adminNew/front_office_reports.html", context)
def admin_cafe_reports(request):
    guests = Guest.objects.all()

    total = 0
    for g in guests:
        total += (
            int(g.cafe_billing or 0)
        )
    context = {'total_revenue': total}
    return render(request, "adminNew/cafe_reports.html", context)
def admin_housekeeping_reports(request):
    guests = Guest.objects.all()

    total = 0
    for g in guests:
        total += (
            int(g.housekeeping_billing or 0)
        )
    context = {'total_revenue': total}
    return render(request, "adminNew/housekeeping_reports.html", context)
def admin_laundry_reports(request):
    guests = Guest.objects.all()

    total = 0
   

    total = Decimal(0)
    for g in guests:
     total += Decimal(g.laundry_billing or 0)

    context = {'total_revenue': total}
    return render(request, "adminNew/laundry_reports.html", context)
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
def admin_training(request):
    return render(request, "adminNew/training.html")


   
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
                activity = Activity.objects.create(
                    title=data.get("title", "New Activity"),
                    description=data.get("description", ""),
                    created_by=request.user if request.user.is_authenticated else None
                )
            
            print(f"[add_activity][POST] target_activity_id={activity.id}, item_number={item_number}")
            
            # Update activity basic info
            activity.title = data.get("title", activity.title)
            activity.description = data.get("description", activity.description)
            activity.save()
            
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
                
                # Get or create activity item
                activity_item, created = ActivityItem.objects.get_or_create(
                    activity=activity,
                    item_number=item_number,
                    defaults={
                        'scenario': scenario,
                        'timer_seconds': int(data.get("timer_seconds", 0))
                    }
                )
                
                if not created:
                    activity_item.scenario = scenario
                    activity_item.timer_seconds = int(data.get("timer_seconds", activity_item.timer_seconds))
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