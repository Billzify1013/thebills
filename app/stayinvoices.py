from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from django.utils import timezone

def stayinvoice(request):
        if request.user.is_authenticated:
            user = request.user

            now = timezone.now()
        
            # Determine the first and last day of the current month
            first_day_of_month = now.replace(day=1)
            last_day_of_month = now.replace(day=1, month=now.month + 1) - timezone.timedelta(days=1)

            current_month = now.strftime("%B")  # e.g., "October"
            current_year = now.year  # e.g., 2024

            # agencydata = TravelAgency.objects.filter(vendor=user)
            guesthistory = Invoice.objects.filter(vendor=user, invoice_status=True,invoice_date__range=(first_day_of_month, last_day_of_month))
            print(guesthistory,first_day_of_month,last_day_of_month)
            channels = guesthistory.values_list('customer__channel', flat=True).distinct()
            return render(request,'invoicefilter.html',{'active_page': 'stayinvoice','guesthistory':guesthistory,
                        'current_month':current_month,'current_year':current_year,'channels':channels})   
        

from calendar import monthrange,month_name

def searchmonthinvoice(request):
    if request.user.is_authenticated and request.method == "POST":
        user = request.user
        month_input = request.POST.get('monthname')  # e.g., "2024-10"
        
        if month_input:
            try:
                # Parse the year and month from the input (YYYY-MM)
                year, month = map(int, month_input.split('-'))

                current_month = month_name[month]  
                current_year = year

                # Determine the first and last day of the chosen month
                first_day_of_month = timezone.datetime(year, month, 1)
                last_day_of_month = timezone.datetime(year, month, monthrange(year, month)[1])

                # Filter guest history based on the selected month and year
                guesthistory = Invoice.objects.filter(
                    vendor=user,
                    invoice_status=True,
                    invoice_date__range=(first_day_of_month, last_day_of_month)
                )

                # Get distinct channels from the filtered guest history
                channels = guesthistory.values_list('customer__channel', flat=True).distinct()

                return render(request, 'invoicefilter.html', {
                    'active_page': 'stayinvoice',
                    'guesthistory': guesthistory,
                    'current_month': month_input,
                    'channels': channels,
                    'current_month':current_month,
                    'current_year':current_year,
                })
            except ValueError:
                # Handle invalid month input format (not YYYY-MM)
                return render(request, 'invoicefilter.html', {
                    'error': 'Invalid month format. Please select a valid month.'
                })