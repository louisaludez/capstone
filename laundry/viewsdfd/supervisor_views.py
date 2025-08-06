from django.shortcuts import render, redirect
from chat.models import Message
from django.contrib.auth import get_user_model

User = get_user_model()
def supervisor_laundry_home(request):
    return render(request,"supervisor_laundry/home.html")
def supervisor_laundry_messages(request):
    print("supervisor_laundry_messages called")

    if not request.user.is_authenticated:
        print("User not authenticated")
        return redirect('login')  # Redirect to login if not authenticated

    # Fetch all messages
    messages = Message.objects.all().order_by('created_at')
    print("Messages fetched:", messages)
    return render(request, "supervisor_laundry/messages.html", {'messages': messages})
def supervisor_laundry_reports(request):
    return render(request,"supervisor_laundry/reports.html")

def send_message_view(request):
    print("send_message_view called")
    if not request.user.is_authenticated:
        print("User not authenticated")
        return redirect('login')  # Redirect to login if not authenticated
    if request.method == 'POST':
        receiver_id = request.POST.get('receiver_id')
        subject = request.POST.get('subject', '')
        body = request.POST.get('body', '')

        try:
            receiver = User.objects.get(id=receiver_id)
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=subject,
                body=body
            )
            return redirect('supervisor_laundry_messages') 
        except User.DoesNotExist:
            return render(request, 'supervisor_laundry/messages.html', {
                'error': 'Receiver not found.'
            })

    users = User.objects.exclude(id=request.user.id)
    return render(request, 'supervisor_laundry/messages.html', {'users': users})
