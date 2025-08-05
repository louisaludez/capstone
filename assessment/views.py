from django.shortcuts import render,redirect


def mcq_home(request):
    return render(request,'assessment/mcq/home.html')
def speech_home(request):
    return render(request,'assessment/speech/home.html')
     