from django.shortcuts import render

def staff_cafe_home(request):
    return render(request,'staff_cafe/home.html')
