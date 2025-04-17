from django.shortcuts import render

# Create your views here.
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

