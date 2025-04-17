from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "laundryManager/home.html")
def reports(request):
    return render(request, "laundryManager/reports.html")
def messages(request):
    return render(request, "laundryManager/messages.html")