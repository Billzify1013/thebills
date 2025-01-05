from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from django.utils import timezone

      

from datetime import timedelta
from django.utils import timezone




def stayinvoice(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  

            # Get the current time
            now = timezone.now()

            # Determine the first day of the current month, set the time to 00:00:00
            first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get the number of days in the current month (November, for example)
            _, last_day_of_month_day = monthrange(now.year, now.month)
            
            # Set the last day of the current month to 23:59:59.999999 (last second of the month)
            last_day_of_month = now.replace(day=last_day_of_month_day, hour=23, minute=59, second=59, microsecond=999999)

            # Get the name of the current month and the year
            current_month = now.strftime("%B")  # e.g., "November"
            current_year = now.year  # e.g., 2024

            # Print statements to confirm the range
            

            # Fetch invoices for the current month (Nov 1 to Nov 30)
            guesthistory = Invoice.objects.filter(vendor=user, invoice_status=True, invoice_date__range=(first_day_of_month, last_day_of_month))

            # Get distinct channels
            channels = guesthistory.values_list('customer__channel', flat=True).distinct()

            # Fetch payments related to the filtered invoices
            payments = InvoicesPayment.objects.filter(invoice__in=guesthistory)

            # Initialize dictionaries to store total payment amounts per mode
            payment_totals = {}
            total_payment = 0

            # Calculate total payments per mode
            for payment in payments:
                # Add to the total payment amount
                total_payment += payment.payment_amount

                # Add to the specific payment mode total
                if payment.payment_mode in payment_totals:
                    payment_totals[payment.payment_mode] += payment.payment_amount
                else:
                    payment_totals[payment.payment_mode] = payment.payment_amount

            # Send all necessary data to the template
            return render(request, 'invoicefilter.html', {
                'active_page': 'stayinvoice',
                'guesthistory': guesthistory,
                'current_month': current_month,
                'current_year': current_year,
                'channels': channels,
                'first_day_of_month': first_day_of_month,
                'last_day_of_month': last_day_of_month,
                'payment_totals': payment_totals,  # Payment totals per mode
                'total_payment': total_payment  # Overall total payment amount
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




from calendar import monthrange,month_name


def searchmonthinvoice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  

            # Get start_date and end_date from the form (make sure the form provides these as 'YYYY-MM-DD')
            start_date_input = request.POST.get('start_date')  # e.g., "2024-10-01"
            end_date_input = request.POST.get('end_date')  # e.g., "2024-10-31"
         
            if start_date_input and end_date_input:
                try:
                    # Parse the start_date and end_date to Python datetime objects
                    start_date = timezone.datetime.strptime(start_date_input, '%Y-%m-%d')
                    end_date = timezone.datetime.strptime(end_date_input, '%Y-%m-%d')

                    # Ensure that the end_date is the last moment of the day (i.e., 23:59:59)
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

                    # Filter guest history based on the selected date range
                    guesthistory = Invoice.objects.filter(
                        vendor=user,
                        invoice_status=True,
                        invoice_date__range=(start_date, end_date)
                    )

                    # Get distinct channels from the filtered guest history
                    channels = guesthistory.values_list('customer__channel', flat=True).distinct()

                        # Fetch payments related to the filtered invoices
                    payments = InvoicesPayment.objects.filter(invoice__in=guesthistory)

                    # Initialize dictionaries to store total payment amounts per mode
                    payment_totals = {}
                    total_payment = 0

                    # Calculate total payments per mode
                    for payment in payments:
                        # Add to the total payment amount
                        total_payment += payment.payment_amount

                        # Add to the specific payment mode total
                        if payment.payment_mode in payment_totals:
                            payment_totals[payment.payment_mode] += payment.payment_amount
                        else:
                            payment_totals[payment.payment_mode] = payment.payment_amount

                    # Send all necessary data to the template
                    return render(request, 'invoicefilter.html', {
                        'active_page': 'stayinvoice',
                        'guesthistory': guesthistory,
                        'channels': channels,
                        'first_day_of_month': start_date,
                        'last_day_of_month': end_date,
                        'payment_totals': payment_totals,  # Payment totals per mode
                        'total_payment': total_payment  # Overall total payment amount
                    })

                except ValueError:
                    # Handle invalid date input format
                    return render(request, 'invoicefilter.html', {
                        'error': 'Invalid date format. Please select valid start and end dates (YYYY-MM-DD).'
                    })
            else:
                # Handle case where either start or end date is missing
                return render(request, 'invoicefilter.html', {
                    'error': 'Both start and end dates are required.'
                })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)