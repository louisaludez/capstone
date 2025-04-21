from django.shortcuts import render

def staff_laundry_home(request):
    return render(request,"staff_laundry/home.html")
def staff_laundry_messages(request):
    return render(request,"staff_laundry/messages.html")
def staff_laundry_orders(request):
    return render(request,"staff_laundry/orders.html")
