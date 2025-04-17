from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "staff/home.html")
def message(request):
    return render(request, "staff/messages.html")