from django.shortcuts import render,redirect, get_object_or_404
from django.http import JsonResponse
from adminNew.models import Activity, ActivityChoice
from .models import McqAttempt, McqAnswer
from django.utils import timezone
import hashlib
import json


def mcq_home(request):
    activities_qs = Activity.objects.order_by('-created_at')
    top5 = list(activities_qs[:5])
    while len(top5) < 5:
        top5.append(None)
    acts_ids = [a.id if a else None for a in top5]
    # Determine participant key to evaluate progression
    participant_key = request.session.get('mcq_participant_key')
    if not participant_key and request.user.is_authenticated:
        participant_key = f"user:{request.user.id}"

    # Sequential unlocking: index 0 is always startable if present.
    can_start = [False] * 5
    if acts_ids[0]:
        can_start[0] = True
    # For positions 1..4, only unlock if previous index is submitted by this participant
    for i in range(1, 5):
        prev_id = acts_ids[i - 1]
        if acts_ids[i] and prev_id and participant_key:
            prev_submitted = McqAttempt.objects.filter(
                activity_id=prev_id,
                participant_key=participant_key,
                status=McqAttempt.STATUS_SUBMITTED,
            ).exists()
            can_start[i] = prev_submitted
        else:
            can_start[i] = False
    return render(
        request,
        'assessment/mcq/home.html',
        { 'activities5': top5, 'acts_json': json.dumps(acts_ids), 'can_start': can_start }
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
        # remember participant_key in session to drive locking on home page
        request.session['mcq_participant_key'] = participant_key

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
    choices_qs = activity.choices.order_by('display_order', 'id')
    choices = list(choices_qs.values('id', 'text'))
    # previously saved answer (if any) while in progress
    selected_choice_id = None
    saved = attempt.answers.select_related('choice').order_by('-selected_at').first()
    if saved:
        selected_choice_id = saved.choice_id
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
        'choices': choices,
        'selected_choice_id': selected_choice_id,
        'prev_exists': prev_exists,
    })


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
    try:
        choice_id = int(request.POST.get('choice_id') or 0)
    except ValueError:
        choice_id = 0
    if not choice_id:
        # treat as timeout/no answer; still mark submitted and proceed
        attempt.status = McqAttempt.STATUS_SUBMITTED
        attempt.finished_at = timezone.now()
        attempt.save(update_fields=['status', 'finished_at'])
        # compute next
        all_acts = list(Activity.objects.order_by('-created_at')[:5])
        next_redirect = None
        if attempt.activity in all_acts:
            idx = all_acts.index(attempt.activity)
            if idx + 1 < len(all_acts) and all_acts[idx + 1] is not None:
                next_redirect = f"/assessment/mcq/start/{all_acts[idx+1].id}/"
        return JsonResponse({'ok': True, 'next': next_redirect})
    # ensure choice belongs to the same activity
    choice = get_object_or_404(ActivityChoice, id=choice_id, activity=attempt.activity)

    # record answer
    McqAnswer.objects.filter(attempt=attempt).delete()
    McqAnswer.objects.create(
        attempt=attempt,
        choice=choice,
        is_correct=choice.is_correct,
    )

    # mark attempt submitted
    attempt.status = McqAttempt.STATUS_SUBMITTED
    attempt.finished_at = timezone.now()
    attempt.save(update_fields=['status', 'finished_at'])

    # compute next activity id (ordered by created_at desc like home page top5)
    all_acts = list(Activity.objects.order_by('-created_at')[:5])
    next_redirect = None
    if attempt.activity in all_acts:
        idx = all_acts.index(attempt.activity)
        if idx + 1 < len(all_acts) and all_acts[idx + 1] is not None:
            next_redirect = f"/assessment/mcq/start/{all_acts[idx+1].id}/"

    return JsonResponse({'ok': True, 'next': next_redirect})


def mcq_save(request, attempt_id: int):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Invalid method'}, status=405)
    attempt = get_object_or_404(McqAttempt.objects.select_related('activity'), id=attempt_id)
    try:
        choice_id = int(request.POST.get('choice_id') or 0)
    except ValueError:
        choice_id = 0
    if not choice_id:
        return JsonResponse({'ok': False, 'error': 'choice_id required'}, status=400)
    choice = get_object_or_404(ActivityChoice, id=choice_id, activity=attempt.activity)
    # upsert saved answer while in-progress
    McqAnswer.objects.update_or_create(
        attempt=attempt,
        defaults={'choice': choice, 'is_correct': choice.is_correct},
    )
    return JsonResponse({'ok': True})
def speech_home(request):
    return render(request,'assessment/speech/home.html')


     