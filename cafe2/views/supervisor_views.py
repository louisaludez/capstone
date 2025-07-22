from django.shortcuts import render

def supervisor_cafe_home(request):
    return render(request,'supervisor_cafe/home.html')
def supervisor_cafe_orders(request):
    return render(request,'supervisor_cafe/orders.html')
def supervisor_cafe_messages(request):
    return render(request,'supervisor_cafe/messages.html')