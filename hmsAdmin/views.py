from django.shortcuts import render
from globals import decorator
# Create your views here.
@decorator.role_required('admin')
def home(request):
    return render(request, "hmsAdmin/home.html")
def messages(request):
    return render(request, "hmsAdmin/messages.html")
def training(request):
    return render(request, "hmsAdmin/training.html")
def analytics(request):
    return render(request, "hmsAdmin/analytics.html")
def accounts(request):
    return render(request, "hmsAdmin/accounts.html")

