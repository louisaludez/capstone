from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from adminNew.models import Activity
from .models import McqAttempt
from django.utils import timezone
import hashlib
import json


def mcq_home(request):
    activities_qs = Activity.objects.order_by('-created_at')
    top5 = list(activities_qs[:5])
    while len(top5) < 5:
        top5.append(None)
    acts_ids = [a.id if a else None for a in top5]
    # Lock tests 2..5 until Test 1 is submitted by this user
    rest_locked = True
    first_id = acts_ids[0]
    if first_id and request.user.is_authenticated:
        submitted = McqAttempt.objects.filter(
            activity_id=first_id,
            started_by=request.user,
            status=McqAttempt.STATUS_SUBMITTED,
        ).exists()
        rest_locked = not submitted
    return render(
        request,
        'assessment/mcq/home.html',
        { 'activities5': top5, 'acts_json': json.dumps(acts_ids), 'rest_locked': rest_locked }
    )


def mcq_start(request, activity_id: int):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    try:
        activity = get_object_or_404(Activity, id=activity_id)
        participant = (request.POST.get('participant') or '').strip()
        if not participant:
            return JsonResponse({'ok': False, 'error': 'Participant info required'}, status=400)
        # build participant_key (use user id if logged in, else hash of participant string)
        if request.user.is_authenticated:
            participant_key = f"user:{request.user.id}"
        else:
            participant_key = hashlib.sha256(participant.encode('utf-8')).hexdigest()

        # find existing in-progress attempt for this participant/activity
        existing = McqAttempt.objects.filter(
            activity=activity,
            participant_key=participant_key,
            status=McqAttempt.STATUS_IN_PROGRESS,
        ).order_by('-started_at').first()

        if existing:
            # Resume existing attempt
            return JsonResponse({'ok': True, 'attempt_id': existing.id, 'resumed': True, 'redirect': f"/assessment/mcq/take/{existing.id}/"})

        # otherwise, create a new attempt with incremented attempt_number
        last_attempt = McqAttempt.objects.filter(activity=activity, participant_key=participant_key).order_by('-attempt_number').first()
        next_number = (last_attempt.attempt_number + 1) if last_attempt else 1

        attempt = McqAttempt.objects.create(
            activity=activity,
            participant_info=participant,
            participant_key=participant_key,
            attempt_number=next_number,
            status=McqAttempt.STATUS_IN_PROGRESS,
            started_by=request.user if request.user.is_authenticated else None,
        )
        return JsonResponse({'ok': True, 'attempt_id': attempt.id, 'resumed': False, 'redirect': f"/assessment/mcq/take/{attempt.id}/"})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


def mcq_take(request, attempt_id: int):
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    activity = attempt.activity
    # Build choices list from ActivityChoice rows
    choices = list(activity.choices.order_by('display_order', 'id').values_list('text', flat=True))
    return render(request, 'assessment/mcq/take.html', {
        'attempt': attempt,
        'activity': activity,
        'choices': choices,
    })


def mcq_submit(request, attempt_id: int):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    attempt = get_object_or_404(McqAttempt, id=attempt_id)
    attempt.status = McqAttempt.STATUS_SUBMITTED
    attempt.finished_at = timezone.now()
    attempt.save(update_fields=['status', 'finished_at'])
    return JsonResponse({'ok': True})
def speech_home(request):
    return render(request,'assessment/speech/home.html')


     