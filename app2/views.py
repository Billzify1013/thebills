from django.shortcuts import render,redirect
from app.models import Freedemo
from django.contrib import messages

# Create your views here.
#test

def app2index(request):
    return render(request,'start.html')

def terms(request):
    return render(request,'terms.html')

def privcy(request):
    return render(request,'privacy.html')

def refund(request):
    return render(request,'refund.html')

def addfreedemo(request):
    if request.method=="POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        businessname = request.POST.get('businessname')
        Freedemo.objects.create(name=name,email=email,phone=phone,businessname=businessname)
        messages.success(request,"Billzify sales team will be in touch with you shortly.")
        return redirect('app2index')
    else:
        messages.error(request,"Somthing Went wrong!.")
        return redirect('app2index')
                            