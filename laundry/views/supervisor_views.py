from django.shortcuts import render

def supervisor_laundry_home(request):
    return render(request,"supervisor_laundry/home.html")
def supervisor_laundry_messages(request):
    return render(request,"supervisor_laundry/messages.html")
def supervisor_laundry_reports(request):
    return render(request,"supervisor_laundry/reports.html")
 