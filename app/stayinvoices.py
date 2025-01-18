from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from django.utils import timezone

import datetime

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models import F


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
    

def notification(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if hasattr(user, 'subuser_profile'):
                    subuser = user.subuser_profile
                    if not subuser.is_cleaner:
                        # Update main user's notification (for subuser)
                        main_user = subuser.vendor
                        if main_user.is_authenticated:
                            request.session['notification'] = False  # Update main user's session
                            request.session.modified = True
                        # Update subuser's own notification
                        request.session['notification'] = False  # Update subuser's session
                        request.session.modified = True
            else:
                        # If it's a main user, update their notification
                        request.session['notification'] = False
                        request.session.modified = True
            # Get today's date
            # today = timezone.now().date()
           

            
            # advanceroomdata = RoomBookAdvance.objects.filter(vendor=user).all().order_by('bookingdate')
            saveadvancebookdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,checkinstatus=False).all().order_by('-id')[:25]
            
           
            return render(request,'notify.html',{'saveadvancebookdata':saveadvancebookdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def cashflow(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            startdate_str = f"{yesterday} 00:00:00"  # Start at 00:00:00
            enddate_str = f"{today} 23:59:59" 

            addcashdata = addCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            expansedata = expenseCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            casoutdata = CashOut.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            handoverdata = hand_overCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            total_cash_amount = addCash.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('add_amount'))['total']

            # Handle the case where no records match
            total_cash_amount = total_cash_amount if total_cash_amount is not None else 0

            total_less_amount = expenseCash.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('less_amount'))['total']

            # Handle the case where no records match
            total_less_amount = total_less_amount if total_less_amount is not None else 0
            cashavailable =avlCash.objects.filter(vendor=user).last()

            total_cash_out_amount = CashOut.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('cash_out_amount'))['total']

            # Handle the case where no records match
            total_cash_out_amount = total_cash_out_amount if total_cash_out_amount is not None else 0

            users = Subuser.objects.filter(vendor=user,is_cleaner=False)
            mainuser = user
            
            

            return render(request,'cashflow.html',{'active_page':'cashflow','addcashdata':addcashdata,
                                'startdate_str':yesterday,'enddate_str':today,'expansedata':expansedata,
                                'total_cash_amount':total_cash_amount,'total_less_amount':total_less_amount,
                                'cashavailable':cashavailable,'casoutdata':casoutdata,'total_cash_out_amount':total_cash_out_amount,
                                'users':users,'mainuser':mainuser,'handoverdata':handoverdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


    

from datetime import datetime
def addcashamount(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            else:
                subuser = None
            today = datetime.now()
            cashamout = int(request.POST.get('cashamout'))
            addCash.objects.create(vendor=user,subuser=subuser,add_amount=cashamout,date_time=today)
            if avlCash.objects.filter(vendor=user).exists():
                avlCash.objects.filter(vendor=user).update(avl_amount=F('avl_amount') + cashamout)
            else:
                avlCash.objects.create(vendor=user,avl_amount =cashamout)
            messages.success(request,'cash added!')
            return redirect('cashflow')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
        
def expenseamount(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            else:
                subuser = None
            today = datetime.now()
            cashamout = request.POST.get('cashamout')
            cmt = request.POST.get('cmt')
            exdata=expenseCash.objects.create(vendor=user,subuser=subuser,less_amount=cashamout,date_time=today,comments=cmt)
            if avlCash.objects.filter(vendor=user).exists():
                avlCash.objects.filter(vendor=user).update(avl_amount=F('avl_amount') - cashamout)
            else:
                pass
            messages.success(request,'expenses added!')
            return redirect('cashflow')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def cashoutamount(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            else:
                subuser = None
            today = datetime.now()
            cashamout = int(request.POST.get('cashamout'))
            existsmount = int(request.POST.get('existsmount'))
            if existsmount > 0:
                if existsmount>=cashamout:
                    cmt = request.POST.get('cmt')
                    CashOut.objects.create(vendor=user,subuser=subuser,cash_out_amount=cashamout,date_time=today,comments=cmt)
                    if avlCash.objects.filter(vendor=user).exists():
                        avlCash.objects.filter(vendor=user).update(avl_amount=F('avl_amount') - cashamout)
                    else:
                        pass
                    messages.success(request,'expenses added!')
                else:
                    messages.error(request,'amount grater then cash available!')
            else:
                messages.error(request,'amount grater then cash available!')
            
            return redirect('cashflow')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def handovercash(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            else:
                subuser = None
            today = datetime.now()
            userto = request.POST.get('user')
            cashamout = int(request.POST.get('cashamout'))
            userfrom = request.POST.get('userfrom')

            hand_overCash.objects.create(vendor=user,amount=cashamout,date_time=today,
                            userto=userto,userfrom=userfrom)
          
            messages.success(request,'Handover Succesfully!')
           
            
            return redirect('cashflow')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def searchcashdata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
                
            yesterday = request.POST.get('startdate')
            today = request.POST.get('enddate')
            
            startdate_str = f"{yesterday} 00:00:00"  # Start at 00:00:00
            enddate_str = f"{today} 23:59:59" 

            addcashdata = addCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            expansedata = expenseCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            casoutdata = CashOut.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            handoverdata = hand_overCash.objects.filter(vendor=user,date_time__range=[startdate_str,enddate_str]).order_by('-id')

            total_cash_amount = addCash.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('add_amount'))['total']

            # Handle the case where no records match
            total_cash_amount = total_cash_amount if total_cash_amount is not None else 0

            total_less_amount = expenseCash.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('less_amount'))['total']

            # Handle the case where no records match
            total_less_amount = total_less_amount if total_less_amount is not None else 0
            cashavailable =avlCash.objects.filter(vendor=user).last()

            total_cash_out_amount = CashOut.objects.filter(
                    vendor=user, 
                    date_time__range=[startdate_str, enddate_str]
                ).aggregate(total=Sum('cash_out_amount'))['total']

            # Handle the case where no records match
            total_cash_out_amount = total_cash_out_amount if total_cash_out_amount is not None else 0

            users = Subuser.objects.filter(vendor=user,is_cleaner=False)
            mainuser = user
            
            

            return render(request,'cashflow.html',{'active_page':'cashflow','addcashdata':addcashdata,
                                'startdate_str':yesterday,'enddate_str':today,'expansedata':expansedata,
                                'total_cash_amount':total_cash_amount,'total_less_amount':total_less_amount,
                                'cashavailable':cashavailable,'casoutdata':casoutdata,'total_cash_out_amount':total_cash_out_amount,
                                'users':users,'mainuser':mainuser,'handoverdata':handoverdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)