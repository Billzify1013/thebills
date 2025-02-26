from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from django.utils import timezone

import datetime

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models import F
from calendar import monthrange,month_name

import datetime
from datetime import  timedelta
from django.db.models import Q


def bookingpayments(request):
    try:    
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            now = timezone.now()

            # First day of the current month (start at 00:00:00)
            first_day_of_month = now.replace(day=1).date()

            # Get the number of days in the current month
            _, last_day_of_month_day = monthrange(now.year, now.month)

            # Last day of the current month (date only, no time)
            last_day_of_month = now.replace(day=last_day_of_month_day).date()
           

            # Print statements to confirm the range
            
            print(first_day_of_month,last_day_of_month)

            # Fetch invoices for the current month (Nov 1 to Nov 30)
            invcpayment = InvoicesPayment.objects.filter(vendor=user, invoice=None, maindate__range=(first_day_of_month, last_day_of_month))

            print(invcpayment)
            
   

            return render(request,'bookpaymentpage.html',{
                 'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month,
                 'invcpayment':invcpayment,'active_page':'bookingpayments',
            })
            
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def bookpaymentsearch(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            now = timezone.now()

            # First day of the current month (start at 00:00:00)
            first_day_of_month = startdate

            # Get the number of days in the current month
            # _, last_day_of_month_day = monthrange(now.year, now.month)

            # Last day of the current month (date only, no time)
            last_day_of_month = enddate
           

            # Print statements to confirm the range
            
            print(first_day_of_month,last_day_of_month)

            # Fetch invoices for the current month (Nov 1 to Nov 30)
            invcpayment = InvoicesPayment.objects.filter(vendor=user, invoice=None, maindate__range=(first_day_of_month, last_day_of_month))

            print(invcpayment)
            


            return render(request,'bookpaymentpage.html',{
                 'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month,
                 'invcpayment':invcpayment,'active_page':'bookingpayments',
            })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def invoicepayment(request):
    try:   
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            now = timezone.now()

            # First day of the current month (start at 00:00:00)
            first_day_of_month = now.replace(day=1).date()

            # Get the number of days in the current month
            _, last_day_of_month_day = monthrange(now.year, now.month)

            # Last day of the current month (date only, no time)
            last_day_of_month = now.replace(day=last_day_of_month_day).date()
           

            # Print statements to confirm the range
            
            print(first_day_of_month,last_day_of_month)

            # Fetch invoices for the current month (Nov 1 to Nov 30)
            invcpayment = InvoicesPayment.objects.filter(vendor=user, invoice__isnull=False, maindate__range=(first_day_of_month, last_day_of_month))

            print(invcpayment)
            
   

            return render(request,'invoicepayment.html',{
                 'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month,
                 'invcpayment':invcpayment,'active_page':'bookingpayments',
            })
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

            

def checkinpaymentsearch(request):
    try:   
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            now = timezone.now()

            # First day of the current month (start at 00:00:00)
            first_day_of_month = startdate

            # Get the number of days in the current month
            # _, last_day_of_month_day = monthrange(now.year, now.month)

            # Last day of the current month (date only, no time)
            last_day_of_month = enddate
           

            # Print statements to confirm the range
            
            print(first_day_of_month,last_day_of_month)

            # Fetch invoices for the current month (Nov 1 to Nov 30)
            invcpayment = InvoicesPayment.objects.filter(vendor=user, invoice__isnull=False, maindate__range=(first_day_of_month, last_day_of_month))

            print(invcpayment)
            
   

            return render(request,'invoicepayment.html',{
                 'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month,
                 'invcpayment':invcpayment,'active_page':'bookingpayments',
            })

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def roomsales(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            yestarday = today - timedelta(days=1)

            startdate = yestarday
            enddate = today 

           
            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            invoicedata = Invoice.objects.filter(
                    (
                        Q(customer__checkindate__date__range=(startdate, enddate)) |  # Check-in falls in the range
                        Q(customer__checkoutdate__date__range=(startdate, enddate)) |  # Check-out falls in the range
                        Q(customer__checkindate__date__lte=startdate, customer__checkoutdate__date__gte=enddate)  # Spans the entire range
                    ),
                    vendor=user  # Additional condition to filter by vendor
                ).prefetch_related('items')
            
            
            return render(request,'invctransection.html',{'invoicedata':invoicedata,'startdate':startdate,
                            'enddate':enddate})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def salestablesearch(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            invoicedata = Invoice.objects.filter(
                    (
                        Q(customer__checkindate__date__range=(startdate, enddate)) |  # Check-in falls in the range
                        Q(customer__checkoutdate__date__range=(startdate, enddate)) |  # Check-out falls in the range
                        Q(customer__checkindate__date__lte=startdate, customer__checkoutdate__date__gte=enddate)  # Spans the entire range
                    ),
                    vendor=user  # Additional condition to filter by vendor
                ).prefetch_related('items')
            
            
            return render(request,'invctransection.html',{'invoicedata':invoicedata,'startdate':startdate,
                            'enddate':enddate})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def productssales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            yestarday = today - timedelta(days=1)

            startdate = yestarday
            enddate = today 

           
            

            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            invoicedata=InvoiceItem.objects.filter(vendor=user,date__range=[startdate, enddate],is_room=False)
            
            return render(request,'itemstransections.html',{'invoicedata':invoicedata,'startdate':startdate,
                            'enddate':enddate})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def arriwalsrpt(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            tommrow = today + timedelta(days=1)

            startdate = today
            enddate =   tommrow

           
            

            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            bookingdata=Booking.objects.filter(vendor=user,check_in_date__range=[startdate, enddate])
            
            return render(request,'arrivalreport.html',{'bookingdata':bookingdata,'startdate':startdate,
                            'enddate':enddate})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def searchitemsales(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            invoicedata=InvoiceItem.objects.filter(vendor=user,date__range=[startdate, enddate],is_room=False)
            
            return render(request,'itemstransections.html',{'invoicedata':invoicedata,'startdate':startdate,
                            'enddate':enddate})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def searcharriwlasrpt(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            bookingdata=Booking.objects.filter(vendor=user,check_in_date__range=[startdate, enddate])
            
            return render(request,'arrivalreport.html',{'bookingdata':bookingdata,'startdate':startdate,
                            'enddate':enddate})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def departurerpt(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            # tommrow = today + timedelta(days=1)

            startdate = today
            enddate =   today

           
            

            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            bookingdata=Booking.objects.filter(vendor=user,check_out_date__range=[startdate, enddate])
            
            return render(request,'departurerpt.html',{'bookingdata':bookingdata,'startdate':startdate,
                            'enddate':enddate})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def searchdeparture(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            bookingdata=Booking.objects.filter(vendor=user,check_out_date__range=[startdate, enddate])
            
            return render(request,'departurerpt.html',{'bookingdata':bookingdata,'startdate':startdate,
                            'enddate':enddate})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def rvrpt(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            yestarday = today - timedelta(days=1)

            startdate = yestarday
            enddate =   today

           
            

            # invoicedata = Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate])
            
            bookingdata=InvoiceItem.objects.filter(vendor=user,date__range=[startdate, enddate],is_room=True)
            
            return render(request,'roomviserpt.html',{'bookingdata':bookingdata,'startdate':startdate,
                            'enddate':enddate})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
