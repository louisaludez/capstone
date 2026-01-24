from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from adminNew.models import Activity, ActivityChoice
from .models import McqAttempt, McqAnswer, SpeechAttempt, SpeechAnswer
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import hashlib
import json
import random
import difflib
import re


def calculate_speech_accuracy(transcription_text, activity):
    """
    Calculate speech accuracy score based on text comparison.
    This is a simplified version - in production, you might use more sophisticated methods.
    """
    # For now, we'll use a simple approach:
    # 1. If there's a reference text in the activity description, compare against it
    # 2. Otherwise, use basic text analysis
    
    # Normalize text for comparison
    def normalize_text(text):
        # Convert to lowercase, remove extra spaces, and basic punctuation
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    user_text = normalize_text(transcription_text)
    
    # Check if there's a reference text in the activity
    reference_text = ""
    
    # First, check if there's a dedicated reference_text field
    if hasattr(activity, 'reference_text') and activity.reference_text:
        reference_text = activity.reference_text
    # Fallback: look for reference text in description
    elif activity.description:
        # Simple heuristic: look for text that might be the reference
        desc_lines = activity.description.split('\n')
        for line in desc_lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith('Instructions') and not line.startswith('Note'):
                reference_text = line
                break
    
    if reference_text:
        # Compare against reference text
        ref_text = normalize_text(reference_text)
        
        # Use difflib to calculate similarity
        similarity = difflib.SequenceMatcher(None, user_text, ref_text).ratio()
        
        # Convert similarity (0-1) to percentage (0-100)
        accuracy_score = similarity * 100
        
        # Check for exact match (after normalization)
        if user_text == ref_text:
            # Perfect match - return 100%
            accuracy_score = 100.0
        # Apply some leniency for minor differences (but don't cap perfect scores)
        elif accuracy_score >= 95:
            # Very high accuracy - allow up to 100%
            accuracy_score = min(100, accuracy_score)
        elif accuracy_score >= 80:
            # High accuracy - small bonus
            accuracy_score = min(99, accuracy_score + 2)
        elif accuracy_score >= 60:
            # Medium accuracy - slight penalty
            accuracy_score = max(50, accuracy_score - 5)
        
    else:
        # No reference text - use basic text analysis
        # Check for basic quality indicators
        
        # Length-based scoring (assuming longer transcriptions are better)
        word_count = len(user_text.split())
        
        # Basic quality checks
        has_capitalization = any(c.isupper() for c in transcription_text)
        has_punctuation = any(c in '.,!?;:' for c in transcription_text)
        has_reasonable_length = word_count >= 5
        
        # Calculate base score
        base_score = 50  # Start with 50%
        
        if has_reasonable_length:
            base_score += 20
        if has_capitalization:
            base_score += 10
        if has_punctuation:
            base_score += 10
        if word_count >= 10:
            base_score += 10
        
        # Add some randomness to make it more realistic (but don't cap at 95%)
        random_factor = random.uniform(-5, 5)
        accuracy_score = max(30, min(100, base_score + random_factor))
    
    return round(accuracy_score, 1)


def mcq_home(request):
    # Require user to be authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # or whatever your login URL is
    
    activities_qs = Activity.objects.order_by('created_at')
    top5 = list(activities_qs[:5])
    # Always maintain exactly 5 slots for consistent layout
    while len(top5) < 5:
        top5.append(None)
    acts_ids = [a.id if a else None for a in top5]
    # Determine participant key to evaluate progression
    participant_key = request.session.get('mcq_participant_key')
    if not participant_key:
        participant_key = f"user:{request.user.id}"
    
    print(f"=== MCQ_HOME DEBUG ===")
    print(f"User: {request.user}")
    print(f"Participant key: {participant_key}")
    print(f"Activity IDs: {acts_ids}")
    
    # Debug: Check all attempts for this user
    all_attempts = McqAttempt.objects.filter(participant_key=participant_key)
    print(f"All attempts for this user:")
    for attempt in all_attempts:
        print(f"  Attempt {attempt.id}: Activity {attempt.activity_id}, Status: {attempt.status}, Started: {attempt.started_at}, Finished: {attempt.finished_at}")

    # Sequential unlocking: index 0 is always startable if present.
    can_start = [False] * 5
    if acts_ids[0]:
        can_start[0] = True
        print(f"Activity 0 ({acts_ids[0]}) is always startable")
    
    # For positions 1..4, only unlock if previous index is passed by this participant
    for i in range(1, 5):
        prev_id = acts_ids[i - 1]
        current_id = acts_ids[i]
        print(f"Checking activity {i}: current_id={current_id}, prev_id={prev_id}")
        
        if current_id and prev_id and participant_key:
            prev_passed = McqAttempt.objects.filter(
                activity_id=prev_id,
                participant_key=participant_key,
                status=McqAttempt.STATUS_SUBMITTED,
                passed=True,
            ).exists()
            print(f"Previous activity {prev_id} passed: {prev_passed}")
            can_start[i] = prev_passed
        else:
            print(f"Activity {i} not startable: current_id={current_id}, prev_id={prev_id}, participant_key={participant_key}")
            can_start[i] = False
    
    print(f"Can start array: {can_start}")
    print(f"=== END MCQ_HOME DEBUG ===")
    return render(
        request,
        'assessment/mcq/home.html',
        { 'activities5': top5, 'acts_json': json.dumps(acts_ids), 'can_start': can_start }
    )


@csrf_exempt
def mcq_start(request, activity_id: int):
    print(f"=== MCQ_START DEBUG ===")
    print(f"1. mcq_start called with activity_id: {activity_id}")
    print(f"2. Request method: {request.method}")
    print(f"3. User authenticated: {request.user.is_authenticated}")
    print(f"4. User: {request.user}")
    print(f"4.5. Request body: {request.body}")
    print(f"4.6. Request POST data: {request.POST}")
    
    # Handle both GET and POST for debugging
    if request.method == 'GET':
        print(f"5. DEBUG: Received GET request instead of POST")
        return JsonResponse({'ok': False, 'error': 'This endpoint requires POST method, but received GET', 'method': 'GET'}, status=400)
    
    if request.method != 'POST':
        print(f"5. ERROR: Invalid method - returning 405")
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    
    # Require user to be authenticated
    if not request.user.is_authenticated:
        print(f"5. ERROR: User not authenticated - returning 401")
        return JsonResponse({'ok': False, 'error': 'Authentication required'}, status=401)
    
    try:
        print(f"5. Looking for activity with id: {activity_id}")
        # Check if activity exists first
        try:
            activity = Activity.objects.get(id=activity_id)
            print(f"6. Found activity: {activity.title}")
            print(f"7. Activity has {activity.items.count()} items")
        except Activity.DoesNotExist:
            print(f"6. ERROR: Activity with id {activity_id} does not exist")
            return JsonResponse({'ok': False, 'error': f'Activity with ID {activity_id} not found'}, status=400)
        
        # Use logged-in user's information
        print(f"8. Getting participant info for user: {request.user}")
        try:
            # Try to get participant info from user model
            if hasattr(request.user, 'get_participant_info'):
                participant = request.user.get_participant_info()
            else:
                # Fallback: create participant info from user data
                participant = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            print(f"9. Participant info: {participant}")
        except Exception as e:
            print(f"9. ERROR getting participant info: {str(e)}")
            # Fallback: use username as participant info
            participant = request.user.username
            print(f"9. Using fallback participant info: {participant}")
        
        participant_key = f"user:{request.user.id}"
        print(f"10. Participant key: {participant_key}")
        
        # remember participant_key in session to drive locking on home page
        request.session['mcq_participant_key'] = participant_key
        print(f"11. Set session participant_key")

        # find existing in-progress attempt for this participant/activity
        print(f"12. Looking for existing attempts...")
        existing = McqAttempt.objects.filter(
            activity=activity,
            participant_key=participant_key,
            status=McqAttempt.STATUS_IN_PROGRESS,
        ).order_by('-started_at').first()

        if existing:
            print(f"13. Found existing attempt: {existing.id}")
            # Resume existing attempt
            return JsonResponse({'ok': True, 'attempt_id': existing.id, 'resumed': True, 'redirect': f"/assessment/mcq/take/{existing.id}/"})

        print(f"13. No existing attempt found, creating new one...")
        # otherwise, create a new attempt with incremented attempt_number
        last_attempt = McqAttempt.objects.filter(activity=activity, participant_key=participant_key).order_by('-attempt_number').first()
        next_number = (last_attempt.attempt_number + 1) if last_attempt else 1
        print(f"14. Next attempt number: {next_number}")

        print(f"15. Creating new McqAttempt...")
        attempt = McqAttempt.objects.create(
            activity=activity,
            participant_info=participant,
            participant_key=participant_key,
            attempt_number=next_number,
            status=McqAttempt.STATUS_IN_PROGRESS,
            started_by=request.user if request.user.is_authenticated else None,
        )
        print(f"16. Created attempt: {attempt.id}")
        print(f"17. SUCCESS: Returning redirect to /assessment/mcq/take/{attempt.id}/")
        return JsonResponse({'ok': True, 'attempt_id': attempt.id, 'resumed': False, 'redirect': f"/assessment/mcq/take/{attempt.id}/"})
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"=== EXCEPTION IN MCQ_START ===")
        print(f"Error: {str(e)}")
        print(f"Traceback: {error_details}")
        print(f"=== END EXCEPTION ===")
        return JsonResponse({'ok': False, 'error': f'Unexpected error: {str(e)}', 'details': error_details}, status=500)


def mcq_take(request, attempt_id: int):
    try:
        attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
        activity = attempt.activity
        
        # Check if activity has any items
        total_items = activity.items.count()
        if total_items == 0:
            # Activity has no items, redirect to home with error message
            return redirect('mcq_home')
        
        # Get current item
        try:
            current_item = activity.items.get(item_number=attempt.current_item_number)
        except:
            # If current item doesn't exist, redirect to home
            return redirect('mcq_home')
        
        # Build choices list from ActivityChoice rows for current item
        choices_qs = current_item.choices.order_by('display_order', 'id')
        choices = list(choices_qs.values('id', 'text'))
        
        # Shuffle choices to randomize order (so correct answer isn't always first)
        random.shuffle(choices)
        
        # Check if current item has choices
        if not choices:
            # Item has no choices, redirect to home
            return redirect('mcq_home')
        
        # previously saved answer (if any) while in progress for current item
        selected_choice_id = None
        saved = attempt.answers.filter(activity_item=current_item).select_related('choice').first()
        if saved:
            selected_choice_id = saved.choice_id
        
        # Check if there are more items
        has_next_item = attempt.current_item_number < total_items
        has_prev_item = attempt.current_item_number > 1
        
        # compute previous activity existence (based on same ordering as home page)
        prev_exists = False
        all_acts = list(Activity.objects.order_by('-created_at')[:5])
        if activity in all_acts:
            idx = all_acts.index(activity)
            if idx - 1 >= 0 and all_acts[idx - 1] is not None:
                prev_exists = True
        
        return render(request, 'assessment/mcq/take.html', {
            'attempt': attempt,
            'activity': activity,
            'current_item': current_item,
            'choices': choices,
            'selected_choice_id': selected_choice_id,
            'prev_exists': prev_exists,
            'has_next_item': has_next_item,
            'has_prev_item': has_prev_item,
            'total_items': total_items,
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in mcq_take: {error_details}")
        return redirect('mcq_home')


def mcq_prev(request, attempt_id: int):
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    activity = attempt.activity
    # figure out previous activity in ordering
    all_acts = list(Activity.objects.order_by('-created_at')[:5])
    if activity not in all_acts:
        return redirect('mcq_home')
    idx = all_acts.index(activity)
    if idx - 1 < 0 or not all_acts[idx - 1]:
        return redirect('mcq_home')
    prev_activity = all_acts[idx - 1]

    # use same participant_key
    participant_key = attempt.participant_key
    participant_info = attempt.participant_info
    # find existing in-progress attempt for previous activity
    existing = McqAttempt.objects.filter(
        activity=prev_activity,
        participant_key=participant_key,
        status=McqAttempt.STATUS_IN_PROGRESS,
    ).order_by('-started_at').first()
    if existing:
        return redirect('mcq_take', attempt_id=existing.id)

    # otherwise create a new attempt number
    last_attempt = McqAttempt.objects.filter(activity=prev_activity, participant_key=participant_key).order_by('-attempt_number').first()
    next_number = (last_attempt.attempt_number + 1) if last_attempt else 1
    new_attempt = McqAttempt.objects.create(
        activity=prev_activity,
        participant_info=participant_info,
        participant_key=participant_key,
        attempt_number=next_number,
        status=McqAttempt.STATUS_IN_PROGRESS,
        started_by=attempt.started_by,
    )
    return redirect('mcq_take', attempt_id=new_attempt.id)


def mcq_submit(request, attempt_id: int):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    
    # Handle previous item action
    if request.POST.get('action') == 'prev_item':
        if attempt.current_item_number > 1:
            attempt.current_item_number -= 1
            attempt.save(update_fields=['current_item_number'])
            return JsonResponse({'ok': True, 'redirect': f"/assessment/mcq/take/{attempt.id}/"})
        else:
            return JsonResponse({'ok': False, 'error': 'Already at first item'}, status=400)
    
    # Get current item
    try:
        current_item = attempt.activity.items.get(item_number=attempt.current_item_number)
    except:
        return JsonResponse({'ok': False, 'error': 'Current item not found'}, status=400)
    
    try:
        choice_id = int(request.POST.get('choice_id') or 0)
    except ValueError:
        choice_id = 0
    
    # Record answer for current item (even if no choice selected)
    if choice_id:
        # ensure choice belongs to the current item
        choice = get_object_or_404(ActivityChoice, id=choice_id, activity_item=current_item)
        
        # record answer for this item
        McqAnswer.objects.update_or_create(
            attempt=attempt,
            activity_item=current_item,
            defaults={
                'choice': choice,
                'is_correct': choice.is_correct,
            }
        )
    else:
        # No choice selected - remove any existing answer for this item
        McqAnswer.objects.filter(attempt=attempt, activity_item=current_item).delete()

    # Check if there are more items in this activity
    total_items = attempt.activity.items.count()
    if attempt.current_item_number < total_items:
        # Move to next item
        attempt.current_item_number += 1
        attempt.save(update_fields=['current_item_number'])
        return JsonResponse({'ok': True, 'next_item': True, 'redirect': f"/assessment/mcq/take/{attempt.id}/"})
    else:
        # All items completed - mark attempt as submitted
        print(f"=== MCQ_SUBMIT DEBUG ===")
        print(f"All items completed for attempt {attempt.id}")
        print(f"Current item number: {attempt.current_item_number}")
        print(f"Total items: {total_items}")
        print(f"Attempt status before: {attempt.status}")
        
        # Calculate score and determine if passed
        correct_answers = attempt.answers.filter(is_correct=True).count()
        score_percentage = (correct_answers / total_items * 100) if total_items > 0 else 0
        passed = score_percentage >= 70  # 70% passing threshold
        
        attempt.status = McqAttempt.STATUS_SUBMITTED
        attempt.finished_at = timezone.now()
        attempt.score = score_percentage
        attempt.passed = passed
        attempt.save(update_fields=['status', 'finished_at', 'score', 'passed'])
        
        print(f"Attempt status after: {attempt.status}")
        print(f"Finished at: {attempt.finished_at}")
        print(f"Score: {score_percentage}%")
        print(f"Passed: {passed}")
        print(f"=== END MCQ_SUBMIT DEBUG ===")
        
        # Redirect to results page instead of next activity
        return JsonResponse({'ok': True, 'next_item': False, 'redirect': f"/assessment/mcq/results/{attempt.id}/"})


def mcq_results(request, attempt_id: int):
    """Show results page after completing an MCQ activity"""
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    
    # Calculate score
    total_questions = attempt.activity.items.count()
    correct_answers = attempt.answers.filter(is_correct=True).count()
    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Use the stored passed field (already calculated in mcq_submit)
    passed = attempt.passed
    
    # Get next activity
    all_acts = list(Activity.objects.order_by('-created_at')[:5])
    next_activity = None
    if attempt.activity in all_acts:
        idx = all_acts.index(attempt.activity)
        if idx + 1 < len(all_acts) and all_acts[idx + 1] is not None:
            next_activity = all_acts[idx + 1]
    
    return render(request, 'assessment/mcq/results.html', {
        'attempt': attempt,
        'activity': attempt.activity,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'score_percentage': score_percentage,
        'passed': passed,
        'next_activity': next_activity,
    })


def mcq_save(request, attempt_id: int):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    
    # Get current item
    try:
        current_item = attempt.activity.items.get(item_number=attempt.current_item_number)
    except:
        return JsonResponse({'ok': False, 'error': 'Current item not found'}, status=400)
    
    try:
        choice_id = int(request.POST.get('choice_id') or 0)
    except ValueError:
        choice_id = 0
    if not choice_id:
        return JsonResponse({'ok': False, 'error': 'choice_id required'}, status=400)
    
    choice = get_object_or_404(ActivityChoice, id=choice_id, activity_item=current_item)
    # upsert saved answer while in-progress for current item
    McqAnswer.objects.update_or_create(
        attempt=attempt,
        activity_item=current_item,
        defaults={'choice': choice, 'is_correct': choice.is_correct},
    )
    return JsonResponse({'ok': True})
def speech_home(request):
    # Require user to be authenticated
    if not request.user.is_authenticated:
        return redirect('login')  # or whatever your login URL is
    
    # Import SpeechActivity from adminNew models
    from adminNew.models import SpeechActivity
    
    activities_qs = SpeechActivity.objects.order_by('created_at')
    top5 = list(activities_qs[:5])
    # Always maintain exactly 5 slots for consistent layout
    while len(top5) < 5:
        top5.append(None)
    acts_ids = [a.id if a else None for a in top5]
    
    # Determine participant key to evaluate progression
    participant_key = request.session.get('speech_participant_key')
    if not participant_key:
        participant_key = f"user:{request.user.id}"
    
    print(f"=== SPEECH_HOME DEBUG ===")
    print(f"User: {request.user}")
    print(f"Participant key: {participant_key}")
    print(f"Activity IDs: {acts_ids}")
    
    # Debug: Check all speech attempts for this user
    all_attempts = SpeechAttempt.objects.filter(participant_key=participant_key)
    print(f"All speech attempts for this user:")
    for attempt in all_attempts:
        print(f"  Attempt {attempt.id}: Activity {attempt.activity_id}, Status: {attempt.status}, Passed: {attempt.passed}, Started: {attempt.started_at}, Finished: {attempt.finished_at}")

    # Sequential unlocking: index 0 is always startable if present.
    can_start = [False] * 5
    if acts_ids[0]:
        can_start[0] = True
        print(f"Speech Activity 0 ({acts_ids[0]}) is always startable")
    
    # For positions 1..4, only unlock if previous index is passed by this participant
    for i in range(1, 5):
        prev_id = acts_ids[i - 1]
        current_id = acts_ids[i]
        print(f"Checking speech activity {i}: current_id={current_id}, prev_id={prev_id}")
        
        if current_id and prev_id and participant_key:
            prev_passed = SpeechAttempt.objects.filter(
                activity_id=prev_id,
                participant_key=participant_key,
                status=SpeechAttempt.STATUS_SUBMITTED,
                passed=True,
            ).exists()
            print(f"Previous speech activity {prev_id} passed: {prev_passed}")
            can_start[i] = prev_passed
        else:
            print(f"Speech activity {i} not startable: current_id={current_id}, prev_id={prev_id}, participant_key={participant_key}")
            can_start[i] = False
    
    print(f"Can start array: {can_start}")
    print(f"=== END SPEECH_HOME DEBUG ===")
    
    acts_json = json.dumps(acts_ids)
    
    context = {
        'activities5': top5,
        'can_start': can_start,
        'acts_json': acts_json,
    }
    
    return render(request, 'assessment/speech/home.html', context)


@csrf_exempt
def speech_start(request, activity_id: int):
    """Start a speech activity - similar to mcq_start but for speech activities"""
    print(f"=== SPEECH_START DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"Activity ID: {activity_id}")
    print(f"User: {request.user}")
    print(f"Request body: {request.body}")
    print(f"Request POST data: {request.POST}")
    
    # Handle both GET and POST for debugging
    if request.method == 'GET':
        print(f"DEBUG: Received GET request instead of POST")
        return JsonResponse({'ok': False, 'error': 'This endpoint requires POST method, but received GET', 'method': 'GET'}, status=400)
    
    if request.method != 'POST':
        print(f"ERROR: Invalid method - returning 405")
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    
    # Require user to be authenticated
    if not request.user.is_authenticated:
        print(f"ERROR: User not authenticated - returning 401")
        return JsonResponse({'ok': False, 'error': 'Authentication required'}, status=401)
    
    try:
        print(f"Looking for speech activity with id: {activity_id}")
        # Import SpeechActivity from adminNew models
        from adminNew.models import SpeechActivity
        
        # Check if activity exists first
        try:
            activity = SpeechActivity.objects.get(id=activity_id)
            print(f"Found activity: {activity.title}")
        except SpeechActivity.DoesNotExist:
            print(f"ERROR: SpeechActivity with id {activity_id} does not exist")
            return JsonResponse({'ok': False, 'error': f'SpeechActivity with ID {activity_id} not found'}, status=400)
        
        # Use logged-in user's information
        print(f"Getting participant info for user: {request.user}")
        try:
            # Try to get participant info from user model
            if hasattr(request.user, 'get_participant_info'):
                participant = request.user.get_participant_info()
            else:
                # Fallback: create participant info from user data
                participant = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
            print(f"Participant info: {participant}")
        except Exception as e:
            print(f"ERROR getting participant info: {str(e)}")
            # Fallback: use username as participant info
            participant = request.user.username
            print(f"Using fallback participant info: {participant}")
        
        participant_key = f"user:{request.user.id}"
        print(f"Participant key: {participant_key}")
        
        # remember participant_key in session to drive locking on home page
        request.session['speech_participant_key'] = participant_key
        print(f"Set session participant_key")

        # find existing in-progress attempt for this participant/activity
        print(f"Looking for existing speech attempts...")
        existing = SpeechAttempt.objects.filter(
            activity_id=activity_id,
            participant_key=participant_key,
            status=SpeechAttempt.STATUS_IN_PROGRESS
        ).first()
        
        if existing:
            print(f"Found existing in-progress attempt: {existing.id}")
            return JsonResponse({
                'ok': True, 
                'resumed': True,
                'attempt_id': existing.id,
                'redirect': f"/assessment/speech/take/{existing.id}/"
            })
        
        # create new attempt
        print(f"Creating new speech attempt...")
        attempt = SpeechAttempt.objects.create(
            activity_id=activity_id,
            participant_info=participant,
            participant_key=participant_key,
            started_by=request.user,
        )
        print(f"Created speech attempt: {attempt.id}")
        
        print(f"SUCCESS: Speech activity {activity.title} started for {participant}")
        return JsonResponse({
            'ok': True, 
            'resumed': False,
            'attempt_id': attempt.id,
            'redirect': f"/assessment/speech/take/{attempt.id}/"
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"=== EXCEPTION IN SPEECH_START ===")
        print(f"Error: {str(e)}")
        print(f"Traceback: {error_details}")
        print(f"=== END EXCEPTION ===")
        return JsonResponse({'ok': False, 'error': f'Unexpected error: {str(e)}', 'details': error_details}, status=500)


def speech_take(request, attempt_id: int):
    """Take a speech activity - similar to mcq_take but for speech activities"""
    try:
        # Get the attempt and related activity
        attempt = get_object_or_404(SpeechAttempt.objects.select_related('activity'), id=attempt_id)
        activity = attempt.activity
        
        # Check if attempt is still in progress
        if attempt.status != SpeechAttempt.STATUS_IN_PROGRESS:
            print(f"Attempt {attempt_id} is not in progress (status: {attempt.status})")
            return redirect('speech_home')
        
        # For speech activities, we don't have multiple items like MCQ
        # Each speech activity is a single activity
        context = {
            'attempt': attempt,
            'activity': activity,
            'timer_seconds': activity.timer_seconds,
        }
        
        return render(request, 'assessment/speech/take.html', context)
        
    except Exception as e:
        print(f"Error in speech_take: {str(e)}")
        return redirect('speech_home')


@csrf_exempt
def speech_submit(request, attempt_id: int):
    """Submit a speech activity transcription"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    
    try:
        attempt = get_object_or_404(SpeechAttempt.objects.select_related('activity'), id=attempt_id)
        
        # Check if attempt is still in progress
        if attempt.status != SpeechAttempt.STATUS_IN_PROGRESS:
            return JsonResponse({'ok': False, 'error': 'Attempt is not in progress'}, status=400)
        
        # Get transcription text
        transcription_text = request.POST.get('transcription_text', '').strip()
        
        if not transcription_text:
            return JsonResponse({'ok': False, 'error': 'Transcription text is required'}, status=400)
        
        # Calculate accuracy score based on text comparison
        accuracy_score = calculate_speech_accuracy(transcription_text, attempt.activity)
        passed = accuracy_score >= 70  # 70% passing threshold
        
        # Create speech answer
        SpeechAnswer.objects.create(
            attempt=attempt,
            transcription_text=transcription_text,
            accuracy_score=accuracy_score
        )
        
        # Mark attempt as submitted
        attempt.status = SpeechAttempt.STATUS_SUBMITTED
        attempt.finished_at = timezone.now()
        attempt.score = accuracy_score
        attempt.passed = passed
        attempt.save(update_fields=['status', 'finished_at', 'score', 'passed'])
        
        print(f"Speech attempt {attempt_id} submitted: score={accuracy_score:.1f}%, passed={passed}")
        
        # Redirect to results page
        return JsonResponse({
            'ok': True, 
            'redirect': f"/assessment/speech/results/{attempt.id}/"
        })
        
    except Exception as e:
        print(f"Error in speech_submit: {str(e)}")
        return JsonResponse({'ok': False, 'error': f'Unexpected error: {str(e)}'}, status=500)


def speech_results(request, attempt_id: int):
    """Show results page after completing a speech activity"""
    try:
        attempt = get_object_or_404(SpeechAttempt.objects.select_related('activity'), id=attempt_id)
        activity = attempt.activity
        
        # Get the speech answer
        speech_answer = attempt.answers.first()
        
        # Get next activity
        from adminNew.models import SpeechActivity
        all_acts = list(SpeechActivity.objects.order_by('-created_at')[:5])
        next_activity = None
        if activity in all_acts:
            idx = all_acts.index(activity)
            if idx + 1 < len(all_acts) and all_acts[idx + 1] is not None:
                next_activity = all_acts[idx + 1]
        
        context = {
            'attempt': attempt,
            'activity': activity,
            'speech_answer': speech_answer,
            'score_percentage': attempt.score or 0,
            'passed': attempt.passed,
            'next_activity': next_activity,
        }
        
        return render(request, 'assessment/speech/results.html', context)
        
    except Exception as e:
        print(f"Error in speech_results: {str(e)}")
        return redirect('speech_home')


@csrf_exempt
def speech_save(request, attempt_id: int):
    """Save speech transcription progress (auto-save)"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    
    try:
        attempt = get_object_or_404(SpeechAttempt, id=attempt_id)
        
        # Check if attempt is still in progress
        if attempt.status != SpeechAttempt.STATUS_IN_PROGRESS:
            return JsonResponse({'ok': False, 'error': 'Attempt is not in progress'}, status=400)
        
        # Get transcription text
        transcription_text = request.POST.get('transcription_text', '').strip()
        
        # Update or create speech answer for auto-save
        speech_answer, created = SpeechAnswer.objects.update_or_create(
            attempt=attempt,
            defaults={'transcription_text': transcription_text}
        )
        
        return JsonResponse({'ok': True, 'created': created})
        
    except Exception as e:
        print(f"Error in speech_save: {str(e)}")
        return JsonResponse({'ok': False, 'error': f'Unexpected error: {str(e)}'}, status=500)