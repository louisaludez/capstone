from django.shortcuts import render

# Create your views here.
def housekeeping_home(request):
    return render(request, 'housekeeping/housekeeping_home.html')