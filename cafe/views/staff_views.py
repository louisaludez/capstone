from django.shortcuts import render

def staff_cafe_home(request):
    return render(request,'staff_cafe/home.html')
def staff_cafe_orders(request):
    return render(request,'staff_cafe/orders.html')
def staff_cafe_messages(request):
    return render(request,'staff_cafe/messages.html')