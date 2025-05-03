from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Message
from django.contrib.auth.models import User
import json

@csrf_exempt

def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            subject = data.get('subject', '')
            body = data.get('body', '')

            if not sender_id or not receiver_id or not body:
                return JsonResponse({'error': 'Sender, receiver, and body are required.'}, status=400)

            try:
                sender = User.objects.get(id=sender_id)
                receiver = User.objects.get(id=receiver_id)
            except User.DoesNotExist:
                return JsonResponse({'error': 'Sender or receiver does not exist.'}, status=404)

            # Save the message to the database
            message = Message(sender=sender, receiver=receiver, subject=subject, body=body)
            message.save()

            return JsonResponse({'message': 'Message saved successfully.', 'id': message.id}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)