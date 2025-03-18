from django.shortcuts import render, redirect,HttpResponse , get_object_or_404
from . models import *
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError

import datetime

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models import F
from django.urls import reverse

from django.db.models import IntegerField
from django.db.models.functions import Cast
def stayinvoice(request):
    # try:
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
            # guesthistory = Invoice.objects.filter(vendor=user, invoice_status=True, invoice_date__range=(first_day_of_month, last_day_of_month)).order_by('invoice_number')

            guesthistory = Invoice.objects.filter(
                vendor=user, 
                invoice_status=True, 
                invoice_date__range=(first_day_of_month, last_day_of_month)
            ).annotate(
                invoice_number_int=Cast('invoice_number', IntegerField())  # Convert to Integer
            ).order_by('-invoice_number_int')  # Order by integer field

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
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)




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
    


def weekwiewfromfolio(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
                
            bookingmodelid = request.POST.get('bookingmodelid')
            if Booking.objects.filter(vendor=user,id=bookingmodelid).exists():
                bookdata = Booking.objects.get(vendor=user,id=bookingmodelid)
                guestid = bookdata.gueststay
                print(guestid.id)

                url = reverse('invoicepage', args=[guestid.id])

        
                return redirect(url)
            else:
            
                return redirect('weekviews')
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    




def editinvoice(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            invoice_data = Invoice.objects.get(vendor=user, id=id)
            userid = invoice_data.customer.id
            guestdata = Gueststay.objects.filter(vendor=user, id=userid)
            invoice_data = Invoice.objects.get(vendor=user, id=id)
            profiledata = HotelProfile.objects.filter(vendor=user)
            itemid = invoice_data.id
            status = True

            invoice_datas = Invoice.objects.filter(vendor=user, id=id)
            invoiceitemdata = InvoiceItem.objects.filter(vendor=user, invoice=itemid).order_by('id')
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            invcpayments = InvoicesPayment.objects.filter(vendor=user,invoice=itemid).all()
            taxelab = taxSlab.objects.filter(vendor=user,invoice=itemid)
            if status is True:
               
                gstamounts = invoice_data.gst_amount
                sstamounts = invoice_data.sgst_amount
                return render(request, 'invoiceeditpage.html', {
                       
                        'profiledata': profiledata,
                        'guestdata': guestdata,
                        'invoice_data': invoice_datas,
                        'invoiceitemdata': invoiceitemdata,
                        'loyltydata': loyltydata,
                        'invcpayments':invcpayments,
                        'gstamounts':gstamounts,
                        'sstamounts':sstamounts,
                        'taxelab':taxelab
                    })

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def editaddpaymentfolio(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invoiceid = request.POST.get('invcids')
            dates = request.POST.get('dates')
            amount = int(float(request.POST.get('amount')))
            paymentmode = request.POST.get('paymentmode')
            paymntdetails = request.POST.get('paymntdetails')
            comment = request.POST.get('comment')
            today = datetime.now()
            invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
            igta = int(invoicedata.grand_total_amount)
            ida =int(invoicedata.Due_amount)
            iaa = invoicedata.accepted_amount
            userid = invoicedata.customer.id
            if amount == igta:
                Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=0.00,accepted_amount=float(igta))
                
                messages.success(request,"Payment Added!")
                InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=dates,
                                payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
                actionss = 'Edit Bill Create Payment'
                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                        description=f'Payment Added {amount}')
            
            elif amount > ida:
                pass
                messages.error(request,"amount graterthen to billing amount!")
            else:
                dueamt = ida-amount
                acceptamt = iaa + amount
                Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=float(dueamt),accepted_amount=float(acceptamt))
            
                messages.success(request,"Payment Added!")
                actionss = 'Edit Bill Create Payment'
                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                        description=f'Payment Added {amount}')
                InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=dates,
                                            payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
            
            url = reverse('editinvoice', args=[invoiceid])
            return redirect(url)

        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)     



def editinvoicepayment(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            payid = request.POST.get('invcids')
            invoicepaydata = InvoicesPayment.objects.get(vendor=user,id=payid)

            invoiceid = invoicepaydata.invoice.id
            amount = int(float(request.POST.get('amount')))
            paymentmode = request.POST.get('paymentmode')
            paymntdetails = request.POST.get('paymntdetails')
            comment = request.POST.get('comment')
            today = datetime.now()
            invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
            igta = int(invoicedata.grand_total_amount)
            ida =int(invoicedata.Due_amount)
            iaa = invoicedata.accepted_amount
            userid = invoicedata.customer.id
            if InvoicesPayment.objects.filter(vendor=user,id=payid).exists():
                if amount == igta:
                    Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=0.00,accepted_amount=float(igta))
                    
                    messages.success(request,"Payment Added!")
                    actionss = 'Edit Bill Payment'
                    invcspay = InvoicesPayment.objects.get(vendor=user,id=payid)
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                            description=f'Payment Edited {invcspay.payment_amount} To {amount}')
                    InvoicesPayment.objects.filter(vendor=user,id=payid).update(payment_amount=amount,
                                    payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
                elif amount > ida:
                    pass
                    messages.error(request,"amount graterthen to billing amount!")
                else:
                    dueamt = ida-amount
                    acceptamt = iaa + amount
                    Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=float(dueamt),accepted_amount=float(acceptamt))
                    actionss = 'Edit Bill Payment'
                    invcspay = InvoicesPayment.objects.get(vendor=user,id=payid)
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                            description=f'Payment Edited {invcspay.payment_amount} To {amount}')
                    messages.success(request,"Payment Added!")
                    InvoicesPayment.objects.filter(vendor=user,id=payid).update(payment_amount=amount,
                                                payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
                
                url = reverse('editinvoice', args=[invoiceid])
                return redirect(url)

        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)



def invoicepaymentedit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            payid = request.POST.get('invcids')
            invoicepaydata = InvoicesPayment.objects.get(vendor=user,id=payid)

            invoiceid = invoicepaydata.invoice.id
            amount = int(float(request.POST.get('amount')))
            paymentmode = request.POST.get('paymentmode')
            paymntdetails = request.POST.get('paymntdetails')
            comment = request.POST.get('comment')
            today = datetime.now()
            if invoicepaydata.payment_amount < amount:
                messages.error(request,"amount grater then to Current Payment  amount!")

            elif invoicepaydata.payment_amount == amount:
                InvoicesPayment.objects.filter(vendor=user,
                    id=payid).update(payment_amount=amount,
                    payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,
                    advancebook=None)

                actionss = 'Edit Payment Details'
                CustomGuestLog.objects.create(vendor=user,customer=invoicepaydata.invoice.customer,
                            by=request.user,action=actionss,
                            description=f'Edit Payment Details, Not Amount.')
                messages.success(request,'Details edit succesfully!')


            elif invoicepaydata.payment_amount > amount:
                finddue = float(invoicepaydata.payment_amount-amount)
                Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=F('Due_amount') + finddue,
                                    accepted_amount=F('accepted_amount') - finddue )
                
                InvoicesPayment.objects.filter(vendor=user,
                    id=payid).update(payment_amount=amount,
                    payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,
                    advancebook=None)

                actionss = 'Edit Bill Payment'
                CustomGuestLog.objects.create(vendor=user,customer=invoicepaydata.invoice.customer,
                            by=request.user,action=actionss,
                            description=f'Payment Edited {str(invoicepaydata.payment_amount)} To {str(amount)}')
                messages.success(request,'payment edit succesfully!')
            
            url = reverse('invoicepage', args=[invoiceid])
            return redirect(url)

        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)


def editbookingpayment(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            payid = request.POST.get('invcids')
            invoicepaydata = InvoicesPayment.objects.get(vendor=user,id=payid)
            if invoicepaydata.advancebook:
                invoiceid = invoicepaydata.advancebook.id
                amount = int(float(request.POST.get('amount')))
                paymentmode = request.POST.get('paymentmode')
                paymntdetails = request.POST.get('paymntdetails')
                comment = request.POST.get('comment')
                today = datetime.now()
                if invoicepaydata.payment_amount < amount:
                    messages.error(request,"amount grater then to Current Payment  amount!")

                elif invoicepaydata.payment_amount == amount:
                    InvoicesPayment.objects.filter(vendor=user,
                        id=payid).update(payment_amount=amount,
                        payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,
                       )

                    actionss = 'Edit Booking Details'
                    CustomGuestLog.objects.create(vendor=user,advancebook=invoicepaydata.advancebook,
                                by=request.user,action=actionss,
                                description=f'Edit Payment Details, Not Amount.')
                    messages.success(request,'Details edit succesfully!')


                elif invoicepaydata.payment_amount > amount:
                    finddue = float(invoicepaydata.payment_amount-amount)
                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=invoiceid).update(reamaining_amount=F('reamaining_amount') + finddue,
                                        advance_amount=F('advance_amount') - finddue )
                    
                    InvoicesPayment.objects.filter(vendor=user,
                        id=payid).update(payment_amount=amount,
                        payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,
                        )

                    actionss = 'Edit Booking Payment'
                    CustomGuestLog.objects.create(vendor=user,advancebook=invoicepaydata.advancebook,
                                by=request.user,action=actionss,
                                description=f'Payment Edited {str(invoicepaydata.payment_amount)} To {str(amount)}')
                    messages.success(request,'payment edit succesfully!')
            else:
                messages.error(request,'Booking Not Found!')
            
            url = reverse('advancebookingdetails', args=[invoicepaydata.advancebook.id])
            return redirect(url)

        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)



def deletepayment(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            payid = id
            if InvoicesPayment.objects.filter(vendor=user,id=payid).exists():
                paydata = InvoicesPayment.objects.get(vendor=user,id=payid)
                Invoice.objects.filter(vendor=user,id=paydata.invoice.id).update(
                    accepted_amount=F('accepted_amount') - paydata.payment_amount,
                    Due_amount = F('Due_amount') + paydata.payment_amount
                )

                actionss = 'Delete Bill Payment'
                invcspay = InvoicesPayment.objects.get(vendor=user,id=payid)
                CustomGuestLog.objects.create(vendor=user,customer=paydata.invoice.customer,by=request.user,action=actionss,
                            description=f'Payment Delete {invcspay.payment_amount} ')

                InvoicesPayment.objects.filter(vendor=user,id=payid).delete()
                messages.success(request,'deleted !')
            else:
                messages.error(request,'id not found')

            url = reverse('editinvoice', args=[paydata.invoice.id])
            return redirect(url)

        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)     


def deleteitemstofolioedit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invoiceid = request.POST.get('invoiceid')
            invoiceitemsid = request.POST.get('invoiceitemsid')
            qty = int(request.POST.get('qty'))
            if Invoice.objects.filter(vendor=user,id=invoiceid).exists():
                if InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).exists():
                    invoiceitemdata = InvoiceItem.objects.get(vendor=user,id=invoiceitemsid,invoice_id=invoiceid)
                   
                    
                    if invoiceitemdata.cgst_rate == 0.00:
                            if invoiceitemdata.quantity_likedays < qty:
                                messages.error(request, 'item Quantity Grater Then Stored Quantity')
                                ckinvcdata = Invoice.objects.get(vendor=user,id=invoiceid)
                                cstmrid = ckinvcdata.customer.id
                                return redirect('invoicepage', id=cstmrid)
                            if invoiceitemdata.quantity_likedays == qty:
                                invoiceamt = invoiceitemdata.total_amount
                                invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                                totalamt = invoicedata.total_item_amount - invoiceamt
                                subtotalamt = invoicedata.subtotal_amount - invoiceamt
                                grandtotalamt = invoicedata.grand_total_amount - invoiceamt
                                dueamount = invoicedata.Due_amount - invoiceamt
                                if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
                                    Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
                                        available_qty=F('available_qty')+invoiceitemdata.quantity_likedays,
                                    )
                                else:
                                    pass
                                Invoice.objects.filter(vendor=user,id=invoiceid).update(total_item_amount=totalamt,subtotal_amount=subtotalamt,
                                                                grand_total_amount=grandtotalamt,Due_amount=dueamount)
                                InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).delete()
                            
                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty} from edit invoice')

                            else:
                                
                                invoiceamt = invoiceitemdata.price * qty
                                oldqty = invoiceitemdata.quantity_likedays
                                invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                                totalamt = invoicedata.total_item_amount - invoiceamt
                                subtotalamt = invoicedata.subtotal_amount - invoiceamt
                                grandtotalamt = invoicedata.grand_total_amount - invoiceamt
                                dueamount = invoicedata.Due_amount - invoiceamt
                                if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
                                    Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
                                        available_qty=F('available_qty')+qty,
                                    )
                                else:
                                    pass
                                Invoice.objects.filter(vendor=user,id=invoiceid).update(total_item_amount=totalamt,subtotal_amount=subtotalamt,
                                                                grand_total_amount=grandtotalamt,Due_amount=dueamount)
                                remainqty = oldqty - qty
                                totalamountss = remainqty * invoiceitemdata.price
                                InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).update(
                                    quantity_likedays = remainqty,total_amount=totalamountss,totalwithouttax=totalamountss
                                )

                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty} from edit invoice')
                            
                            
                    else:
                            if invoiceitemdata.quantity_likedays < qty:
                                messages.error(request, 'item Quantity Grater Then Stored Quantity')
                                ckinvcdata = Invoice.objects.get(vendor=user,id=invoiceid)
                                cstmrid = ckinvcdata.customer.id
                                return redirect('invoicepage', id=cstmrid)
                            
                            if invoiceitemdata.quantity_likedays == qty:
                                invoiceamt = invoiceitemdata.total_amount
                                qtys = invoiceitemdata.quantity_likedays
                                priceproduct = invoiceitemdata.price
                                invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                                totalamt = invoicedata.total_item_amount - priceproduct*qtys
                                subtotalamt = invoicedata.subtotal_amount - priceproduct*qtys
                                cgstamt = invoicedata.sgst_amount - (invoiceamt-priceproduct*qtys)/2
                                gstamt = invoicedata.gst_amount - (invoiceamt-priceproduct*qtys)/2
                                grandtotalamt = invoicedata.grand_total_amount - invoiceamt
                                dueamount = invoicedata.Due_amount - invoiceamt
                                if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
                                    Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
                                        available_qty=F('available_qty')+invoiceitemdata.quantity_likedays,
                                    )
                                else:
                                    pass
                                
                                Invoice.objects.filter(vendor=user,id=invoiceid).update(gst_amount=gstamt,sgst_amount=cgstamt,
                                                                                        total_item_amount=totalamt,subtotal_amount=subtotalamt,
                                                                                        grand_total_amount=grandtotalamt,Due_amount=dueamount,
                                                                                        taxable_amount=F('taxable_amount')-priceproduct*qtys)
                                InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).delete()
                                
                                taxrate = float(invoiceitemdata.cgst_rate)
                                taxamount = (invoiceamt-priceproduct*qtys)/2
                                totaltaxamts = taxamount * 2
                            
                                if taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).exists():
                                    taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).update(
                                        cgst_amount=F('cgst_amount') - taxamount,
                                        sgst_amount=F('sgst_amount') - taxamount,
                                        total_amount=F('total_amount') - totaltaxamts
                                    )

                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty} from edit invoice')
                            # les qty work here
                            else:
                                taxrate = invoiceitemdata.cgst_rate
                                invoiceamt = invoiceitemdata.price * qty
                                qtys = qty
                                oldqty = invoiceitemdata.quantity_likedays
                                taxamounts = invoiceamt * taxrate/100
                                
                                priceproduct = invoiceitemdata.price
                                invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                                totalamt = invoicedata.total_item_amount - priceproduct*qtys
                                subtotalamt = invoicedata.subtotal_amount - priceproduct*qtys
                                cgstamt = invoicedata.sgst_amount - taxamounts
                                gstamt = invoicedata.gst_amount - taxamounts
                                grandtotalamt = invoicedata.grand_total_amount - (invoiceamt+taxamounts*2)
                                dueamount = invoicedata.Due_amount - (invoiceamt+taxamounts*2)
                                if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
                                    Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
                                        available_qty=F('available_qty')+qty,
                                    )
                                else:
                                    pass

                                Invoice.objects.filter(vendor=user,id=invoiceid).update(gst_amount=gstamt,sgst_amount=cgstamt,
                                                                                        total_item_amount=totalamt,subtotal_amount=subtotalamt,
                                                                                        grand_total_amount=grandtotalamt,Due_amount=dueamount,
                                                                                        taxable_amount=F('taxable_amount')-invoiceamt)
                                remainqty = oldqty - qty
                                totalamountss = remainqty * invoiceitemdata.price
                                cgst_rate = invoiceitemdata.cgst_rate
                                taxwithtotalamount = (totalamountss * cgst_rate*2 / 100) + totalamountss
                                taxableamountschanged = (totalamountss * cgst_rate / 100)
                                InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).update(
                                    quantity_likedays = remainqty,total_amount=taxwithtotalamount,totalwithouttax=totalamountss,
                                    cgst_rate_amount=taxableamountschanged,sgst_rate_amount=taxableamountschanged
                                )


                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty} from edit invoice')
                               
                                totaltaxamts = taxamounts * 2
                            
                                if taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).exists():
                                    taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).update(
                                        cgst_amount=F('cgst_amount') - taxamounts,
                                        sgst_amount=F('sgst_amount') - taxamounts,
                                        total_amount=F('total_amount') - totaltaxamts
                                    )
                                
                    
                else:
                    messages.error(request, 'Invoice item not exists')
            else:
                messages.error(request, 'Invoice does not exist')
            ckinvcdata = Invoice.objects.get(vendor=user,id=invoiceid)
            cstmrid = ckinvcdata.customer.id
            return redirect('editinvoice', id=invoiceid)
        
        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)     






def editcustomergstnumberbyedit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcid = request.POST.get('invcid')
            gstnumber = request.POST.get('gstnumber')
            customerphone = request.POST.get('customerphone')
            customercompany = request.POST.get('customercompany')
            if Invoice.objects.filter(vendor=user,id=invcid).exists():
                Invoice.objects.filter(vendor=user,id=invcid).update(customer_gst_number=gstnumber,customer_company=customercompany)
                checkdata = Invoice.objects.get(vendor=user,id=invcid)
                customer = checkdata.customer
                Gueststay.objects.filter(vendor=user,id=customer.id).update(guestphome=customerphone)
                actionss = 'Edit Gst details'
                CustomGuestLog.objects.create(vendor=user,customer=customer,by=request.user,action=actionss,
                        description=f'edit Gst details in  invoice')
                    

            else:
                pass

            url = reverse('editinvoice', args=[invcid])

        
            return redirect(url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def addproductonedit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            foliocustomer = request.POST.get('invcid')
            pname = request.POST.get('pname')
            gstrate = int(request.POST.get('gstrate'))
            producthsn = int(request.POST.get('producthsn'))
            pprice = float(request.POST.get('pprice'))
            pqty = int(request.POST.get('pqty'))
            gstrate = float(request.POST.get('gstrate'))
            grandtotal = float(request.POST.get('grandtotal'))
            grandtotalss= grandtotal
            totalamountwithouttax = float(request.POST.get('totalamountwithouttax'))
            totaltax = float(request.POST.get('totaltax'))
            cgstrate = gstrate / 2
            csgsttaxamount = totaltax / 2
            if Invoice.objects.filter(vendor=user,id=foliocustomer).exists():
                InvoiceItem.objects.create(vendor=user,invoice_id=foliocustomer,description=pname,mdescription='',price=pprice,
                                            quantity_likedays=pqty,cgst_rate=cgstrate,sgst_rate=cgstrate,
                                            hsncode=producthsn,total_amount=grandtotal,is_room=False,
                                        cgst_rate_amount=csgsttaxamount,sgst_rate_amount=csgsttaxamount,totalwithouttax=totalamountwithouttax)
                invc = Invoice.objects.get(vendor=user,id=foliocustomer)
                totalamtinvc = float(invc.total_item_amount) + totalamountwithouttax
                subtotalinvc = totalamountwithouttax + float(invc.subtotal_amount)
                grandtotal = float(invc.grand_total_amount) + grandtotal 
                sgsttotal = float(invc.sgst_amount) + csgsttaxamount
                gsttotal = float(invc.gst_amount) + csgsttaxamount
                dueamount = float(invc.Due_amount) + grandtotalss
                Invoice.objects.filter(vendor=user,id=foliocustomer).update(total_item_amount=totalamtinvc,subtotal_amount=subtotalinvc,
                                        grand_total_amount =grandtotal,sgst_amount=sgsttotal,gst_amount=gsttotal,
                                        Due_amount=dueamount,
                                        taxable_amount=F('taxable_amount')+totalamountwithouttax)
                        
                testtaxrate = float(gstrate) / 2
                totaltaxamts = csgsttaxamount * 2 
                if taxSlab.objects.filter(vendor=user,invoice_id=foliocustomer,cgst=testtaxrate).exists():
                            
                            taxSlab.objects.filter(vendor=user,invoice_id=foliocustomer,cgst=testtaxrate).update(
                                    cgst_amount=F('cgst_amount') + csgsttaxamount,
                                    sgst_amount=F('sgst_amount') + csgsttaxamount,
                                    total_amount=F('total_amount') + totaltaxamts
                            )
                else:
                            taxname = "GST"+str(int(testtaxrate*2))
                        
                            taxSlab.objects.create(vendor=user,invoice_id=foliocustomer,
                                    tax_rate_name=taxname,
                                    cgst=testtaxrate,
                                    sgst=testtaxrate,
                                    cgst_amount=csgsttaxamount,
                                    sgst_amount=csgsttaxamount,
                                    total_amount=totaltaxamts
                            )                   
                messages.success(request,'Invoice Item added succesfully')

                actionss = 'Create Service'
                descss = str(pname) + " " + str(pqty) + " Added From Edit Invoice"
                CustomGuestLog.objects.create(vendor=user,customer=invc.customer,by=request.user,action=actionss,
                            description=descss)
                        
                userid = invc.id
                url = reverse('editinvoice', args=[userid])
                return redirect(url)

            
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def editdueamount(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            foliocustomer = request.POST.get('invcid')
            Recivedamount = float(request.POST.get('Recivedamount'))
            dueamount = float(request.POST.get('dueamount'))
            if Invoice.objects.filter(vendor=user,id=foliocustomer).exists():
                Invoice.objects.filter(vendor=user,id=foliocustomer).update(accepted_amount=Recivedamount,
                                        Due_amount=dueamount)
                messages.success(request,'Due Amount Edited succesfully')
                        
                userid = foliocustomer
                url = reverse('editinvoice', args=[userid])
                return redirect(url)
            
            else:
                 
                messages.error(request,'Invoice Not Found')
                        
                userid = foliocustomer
                url = reverse('editinvoice', args=[userid])
                return redirect(url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
from django.db.models import Max
from django.db.models import Q
def makeseprateinvoice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            guestid = request.POST.get('guestid')
            selectvalue = request.POST.get('selectvalue')
            # print(guestid,invoiceid,selectvalue)
            today = datetime.now().date()
            
             

            if Gueststay.objects.filter(vendor=user,id=guestid).exists():
                minvcfata = Invoice.objects.get(vendor=user,customer_id=guestid,is_fandb=False)

                invoiceid = minvcfata.id
            else:
                messages.error(request,'Guest Id Not Found')
                return redirect('guesthistory')
            
            
            if Invoice.objects.filter(vendor=user,id=invoiceid,foliostatus=True).exists():
                if InvoiceItem.objects.filter(vendor=user,invoice_id=invoiceid,is_room=False).exclude(mdescription ='Extra Charges').exists():
                    invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                    print("main invoice",invoicedata.grand_total_amount,invoicedata.sgst_amount,invoicedata.subtotal_amount)


                    itemsinvoiceitems = InvoiceItem.objects.filter(
                        vendor=user,
                        invoice_id=invoiceid,
                        is_room=False
                    ).exclude(
                        mdescription ='Extra Charges'
                    )

                    item_invoice_total = 0.0
                    item_invoice_cgst_total = 0.0
                    item_invoice_grandtotal = 0.0
                    item_invoice_taxable_amount = 0.0
                    for item in itemsinvoiceitems:
                        item_invoice_total = item_invoice_total + float(item.totalwithouttax)
                        item_invoice_cgst_total = item_invoice_cgst_total + float(item.cgst_rate_amount )
                        item_invoice_grandtotal = item_invoice_grandtotal + float(item.total_amount)
                        if float(item.cgst_rate_amount ) > 0.0:
                            item_invoice_taxable_amount = float(item.totalwithouttax) + item_invoice_taxable_amount

                    latest_invoice = Invoice.objects.filter(
                        vendor=user, 
                        invoice_status=True
                    ).exclude(
                        invoice_number__in=['unpaid', '']
                    ).annotate(
                        invoice_number_int=Cast('invoice_number', IntegerField())  # Convert to Integer
                    ).aggregate(max_invoice=Max('invoice_number_int'))  # Get max invoice number

                    max_invoice_number = latest_invoice['max_invoice'] if latest_invoice['max_invoice'] else 0

                    invoice_number = max_invoice_number + 1  # Next invoice number

                    print(invoice_number, 'check this')

                    if selectvalue == "yes":
                        customer_gst_number = invoicedata.customer_gst_number
                        customer_company = invoicedata.customer_company
                    else:
                        customer_gst_number=''
                        customer_company=''

                    print(item_invoice_total,item_invoice_cgst_total,item_invoice_grandtotal,item_invoice_taxable_amount)
                    itemsinvoicemain = Invoice.objects.create(vendor=user,customer=invoicedata.customer,total_item_amount=item_invoice_total,
                                discount_amount=0.0,subtotal_amount=item_invoice_total,gst_amount=item_invoice_cgst_total,
                                sgst_amount=item_invoice_cgst_total,grand_total_amount=item_invoice_grandtotal,taxable_amount=item_invoice_taxable_amount,
                                modeofpayment='',accepted_amount=item_invoice_grandtotal,Due_amount=0.00,room_no='',foliostatus=True,invoice_status=True,taxtype='GST',
                                is_fandb=True,invoice_date=invoicedata.invoice_date,invoice_number=invoice_number,
                                customer_gst_number=customer_gst_number,customer_company=customer_company)

                    for i in itemsinvoiceitems:
                        InvoiceItem.objects.filter(vendor=user,id=i.id).update(
                            invoice=itemsinvoicemain
                        )


                        if taxSlab.objects.filter(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate)).exists():
                                
                                taxSlab.objects.filter(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate)).update(
                                        cgst_amount=F('cgst_amount') + i.cgst_rate_amount,
                                        sgst_amount=F('sgst_amount') + i.sgst_rate_amount,
                                        total_amount=F('total_amount') + i.sgst_rate_amount + i.cgst_rate_amount,
                                )
                        else:
                                taxname = "GST"+str(int(float(i.cgst_rate)*2))
                                taxSlab.objects.create(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate),
                                        sgst=float(i.cgst_rate),tax_rate_name=taxname,cgst_amount=i.cgst_rate_amount,
                                        sgst_amount=i.sgst_rate_amount,total_amount=i.sgst_rate_amount + i.cgst_rate_amount)

                    Gueststay.objects.filter(vendor=user,id=guestid).update(fandbinvoiceid=itemsinvoicemain.id)
                    
                    
                    #  room invoice code start here
                    roominvoiceitems = InvoiceItem.objects.filter(
                        vendor=user,
                        invoice_id=invoiceid
                    ).filter(
                        Q(is_room=True) | Q(mdescription='Extra Charges')
                    )

                    room_invoice_total = 0.0
                    room_invoice_cgst_total = 0.0
                    room_invoice_grandtotal = 0.0
                    room_invoice_taxable_amount = 0.0

                    taxSlab.objects.filter(vendor=user,invoice=invoicedata).delete()
                    for room in roominvoiceitems:
                        room_invoice_total = room_invoice_total + float(room.totalwithouttax)
                        room_invoice_cgst_total = room_invoice_cgst_total + float(room.cgst_rate_amount )
                        room_invoice_grandtotal = room_invoice_grandtotal + float(room.total_amount)
                        if float(room.cgst_rate_amount ) > 0.0:
                            room_invoice_taxable_amount = float(room.totalwithouttax) + room_invoice_taxable_amount

                        if taxSlab.objects.filter(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate)).exists():
                                
                                taxSlab.objects.filter(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate)).update(
                                        cgst_amount=F('cgst_amount') + room.cgst_rate_amount,
                                        sgst_amount=F('sgst_amount') + room.sgst_rate_amount,
                                        total_amount=F('total_amount') + room.sgst_rate_amount + room.cgst_rate_amount,
                                )
                        else:
                                taxname = "GST"+str(int(float(room.cgst_rate)*2))
                                taxSlab.objects.create(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate),
                                        sgst=float(room.cgst_rate),tax_rate_name=taxname,cgst_amount=room.cgst_rate_amount,
                                        sgst_amount=room.sgst_rate_amount,total_amount=room.sgst_rate_amount + room.cgst_rate_amount)

                    # credit calculation here
                    total_due_amount = float(invoicedata.Due_amount)
                    total_recived_amount = float(invoicedata.accepted_amount)
                    item_edit_recived = 0.00
                    item_due_amount = 0.00
                    room_recived_amount=0.00
                    room_due_amount=0.00
                    if total_recived_amount == item_invoice_grandtotal:
                        item_due_amount = 0.00
                        item_edit_recived = item_invoice_grandtotal
                        room_recived_amount = 0.00
                        room_due_amount = float(invoicedata.grand_total_amount) - item_invoice_grandtotal

                         
                    elif total_recived_amount == 0.00:
                        
                        item_edit_recived = 0.00
                        room_recived_amount = 0.00
                        item_due_amount = item_invoice_grandtotal
                        room_due_amount = float(invoicedata.grand_total_amount) - item_invoice_grandtotal
                        # split due on both invoice grand total amount

                    elif total_recived_amount > item_invoice_grandtotal:
                        item_edit_recived = item_invoice_grandtotal
                        item_due_amount = 0.00
                        # bacha hua amount
                        room_recived_amount = total_recived_amount - item_invoice_grandtotal
                        room_due_amount = float(invoicedata.grand_total_amount) - item_invoice_grandtotal - room_recived_amount
                        # yaha fnb ka clear krna or bacha hua main invc me clear krn hai 

                    elif total_recived_amount<item_invoice_grandtotal:
                        item_edit_recived = total_recived_amount
                        item_due_amount = item_invoice_grandtotal - total_recived_amount
                        if item_due_amount <0.99: 
                            item_due_amount=0.00
                        room_recived_amount = 0.00
                        room_due_amount = room_invoice_grandtotal



                    Invoice.objects.filter(vendor=user,id=itemsinvoicemain.id).update(
                        accepted_amount=item_edit_recived,Due_amount=item_due_amount
                    )

                    if item_due_amount>0.99 :
                        today = datetime.now().date()
                        Invoice.objects.filter(vendor=user,id=itemsinvoicemain.id).update(invoice_status=False,invoice_number="unpaid")
                        CustomerCredit.objects.create(vendor=user,customer_name=itemsinvoicemain.customer.guestname,amount=item_due_amount,
                                                        due_date=today,invoice=itemsinvoicemain,phone=itemsinvoicemain.customer.guestphome)
                        actionss = 'Create Credit Bill'
                        CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Guest Check-Out and F&b Split But Payment Is Due {item_due_amount}')
                        
                    if room_due_amount >0.99:
                        CustomerCredit.objects.filter(vendor=user,invoice=invoicedata).update(
                            amount=F('amount') - item_due_amount
                        )
                        actionss = 'Edit Credit Bill'
                        CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Edit Main Credit Bill (Because F&B Invoice Created) remove {item_edit_recived}')


                    Invoice.objects.filter(vendor=user,id=invoiceid).update(
                        total_item_amount=room_invoice_total,discount_amount=0.0,subtotal_amount=room_invoice_total,
                        gst_amount=room_invoice_cgst_total,sgst_amount=room_invoice_cgst_total,grand_total_amount=room_invoice_grandtotal,
                        taxable_amount=room_invoice_taxable_amount,
                        accepted_amount=room_recived_amount,Due_amount=room_due_amount
                    )



                    invcpayment = InvoicesPayment.objects.filter(vendor=user,invoice=invoicedata)
                    # invcpayment.descriptions = invcpayment.descriptions + " " + "This Amount Sattled From Main Invoice"

                    totalpaybleamounts = item_invoice_grandtotal
                    for pay in invcpayment:
                        if totalpaybleamounts == 0.0:
                            break
                        eqdescrs = pay.descriptions + " " + "This amount has been settled from the main invoice."
                        if float(pay.payment_amount) == totalpaybleamounts:
                            
                            InvoicesPayment.objects.create(vendor=user,invoice=itemsinvoicemain,advancebook=pay.advancebook,
                                    payment_amount=pay.payment_amount,payment_date=pay.payment_date,payment_mode=pay.payment_mode,
                                    transaction_id=pay.transaction_id,descriptions=eqdescrs  )
                        
                            InvoicesPayment.objects.filter(vendor=user,id=pay.id).delete()

                            totalpaybleamounts = 0.0
                        
                        elif float(pay.payment_amount) > totalpaybleamounts:
                            remainamount = float(pay.payment_amount) - totalpaybleamounts
                            
                            InvoicesPayment.objects.create(vendor=user,invoice=itemsinvoicemain,advancebook=pay.advancebook,
                                    payment_amount=totalpaybleamounts,payment_date=pay.payment_date,payment_mode=pay.payment_mode,
                                    transaction_id=pay.transaction_id,descriptions=eqdescrs  )
                            
                            InvoicesPayment.objects.filter(vendor=user,id=pay.id).update(
                                 payment_amount=remainamount
                             )
                            
                            totalpaybleamounts = 0.0

                        elif float(pay.payment_amount) < totalpaybleamounts:
                            InvoicesPayment.objects.create(vendor=user,invoice=itemsinvoicemain,advancebook=pay.advancebook,
                                    payment_amount=float(pay.payment_amount),payment_date=pay.payment_date,payment_mode=pay.payment_mode,
                                    transaction_id=pay.transaction_id,descriptions=eqdescrs  )
                            
                            totalpaybleamounts = totalpaybleamounts - float(pay.payment_amount)
                            InvoicesPayment.objects.filter(vendor=user,id=pay.id).delete()
                        
                    
                    Booking.objects.filter(vendor=user,gueststay=invoicedata.customer).update(fnbinvoice=itemsinvoicemain)
                    
                    
                    actionss = 'Split Invoice'
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Split Invoice for Room and Food Service ')

                    
                    messages.success(request,"Invoice Seprated Succesfully!")
                else:
                    messages.error(request,"No Service Items In This Invoice")

            else:
                messages.error(request,"First, check out the guest, and then split the invoice.")  
           


            bookdatas = Booking.objects.filter(vendor=user,gueststay=guestid).last()
                
            booking_id = bookdatas.id

            
        
            new_request = request
            new_request.method = "POST"  # Simulate a POST request
            new_request.POST = QueryDict(mutable=True)
            new_request.POST.update({
                'bookingmodelid': booking_id
            })

            # Call the bookingdate function with the modified request
            return guesthistorysearchview(new_request)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)





# new code for amount handling

def makeotaandfnbinvc(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            guestid = request.POST.get('guestid')
            selectvalue = request.POST.get('selectvalue')
            # print(guestid,invoiceid,selectvalue)
            today = datetime.now().date()
            
             

            if Gueststay.objects.filter(vendor=user,id=guestid).exists():
                minvcfata = Invoice.objects.get(vendor=user,customer_id=guestid,is_fandb=False)

                invoiceid = minvcfata.id
            else:
                messages.error(request,'Guest Id Not Found')
                return redirect('guesthistory')
            
            
            if True:
                # if InvoiceItem.objects.filter(vendor=user,invoice_id=invoiceid,is_room=False).exclude(mdescription ='Extra Charges').exists():
                if InvoiceItem.objects.filter(Q(vendor=user, invoice_id=invoiceid, is_room=False) |Q(vendor=user, invoice_id=invoiceid, is_room=True, is_extend=True)).exists():
                
                    invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                    print("main invoice",invoicedata.grand_total_amount,invoicedata.sgst_amount,invoicedata.subtotal_amount)

                    Invoice.objects.filter(vendor=user,id=invoiceid).update(invoice_number='unpaid',invoice_status=False)

                    itemsinvoiceitems = InvoiceItem.objects.filter(
                       Q(vendor=user, invoice_id=invoiceid, is_room=False) |Q(vendor=user, invoice_id=invoiceid, is_room=True, is_extend=True) 
                    ).exclude(is_room_extra=True)

                    item_invoice_total = 0.0
                    item_invoice_cgst_total = 0.0
                    item_invoice_grandtotal = 0.0
                    item_invoice_taxable_amount = 0.0
                    
                    for item in itemsinvoiceitems:
                        item_invoice_total = item_invoice_total + float(item.totalwithouttax)
                        item_invoice_cgst_total = item_invoice_cgst_total + float(item.cgst_rate_amount )
                        item_invoice_grandtotal = item_invoice_grandtotal + float(item.total_amount)
                        if float(item.cgst_rate_amount ) > 0.0:
                            item_invoice_taxable_amount = float(item.totalwithouttax) + item_invoice_taxable_amount

                    latest_invoice = Invoice.objects.filter(
                        vendor=user, 
                        invoice_status=True
                    ).exclude(
                        invoice_number__in=['unpaid', '']
                    ).annotate(
                        invoice_number_int=Cast('invoice_number', IntegerField())  # Convert to Integer
                    ).aggregate(max_invoice=Max('invoice_number_int'))  # Get max invoice number

                    max_invoice_number = latest_invoice['max_invoice'] if latest_invoice['max_invoice'] else 0

                    invoice_number = max_invoice_number + 1  # Next invoice number

                    print(invoice_number, 'check this')

                    
                    customer_gst_number=''
                    customer_company=''

                    item_invoice_due_amount = float(invoicedata.Due_amount)
                    item_amount_recived_amount = item_invoice_grandtotal - float(invoicedata.Due_amount)

                    print(item_invoice_total,item_invoice_cgst_total,item_invoice_grandtotal,item_invoice_taxable_amount)
                    itemsinvoicemain = Invoice.objects.create(vendor=user,customer=invoicedata.customer,total_item_amount=item_invoice_total,
                                discount_amount=0.0,subtotal_amount=item_invoice_total,gst_amount=item_invoice_cgst_total,
                                sgst_amount=item_invoice_cgst_total,grand_total_amount=item_invoice_grandtotal,taxable_amount=item_invoice_taxable_amount,
                                modeofpayment='',accepted_amount=item_amount_recived_amount,Due_amount=item_invoice_due_amount,room_no='',foliostatus=True,invoice_status=True,taxtype='GST',
                                is_fandb=True,invoice_date=invoicedata.invoice_date,invoice_number=invoice_number,
                                customer_gst_number=customer_gst_number,customer_company=customer_company)

                    for i in itemsinvoiceitems:
                        InvoiceItem.objects.filter(vendor=user,id=i.id).update(
                            invoice=itemsinvoicemain
                        )


                        if taxSlab.objects.filter(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate)).exists():
                                
                                taxSlab.objects.filter(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate)).update(
                                        cgst_amount=F('cgst_amount') + i.cgst_rate_amount,
                                        sgst_amount=F('sgst_amount') + i.sgst_rate_amount,
                                        total_amount=F('total_amount') + i.sgst_rate_amount + i.cgst_rate_amount,
                                )
                        else:
                                taxname = "GST"+str(int(float(i.cgst_rate)*2))
                                taxSlab.objects.create(vendor=user,invoice=itemsinvoicemain,cgst=float(i.cgst_rate),
                                        sgst=float(i.cgst_rate),tax_rate_name=taxname,cgst_amount=i.cgst_rate_amount,
                                        sgst_amount=i.sgst_rate_amount,total_amount=i.sgst_rate_amount + i.cgst_rate_amount)

                    Gueststay.objects.filter(vendor=user,id=guestid).update(fandbinvoiceid=itemsinvoicemain.id)
                    
                    
                    #  room invoice code start here
                    # roominvoiceitems = InvoiceItem.objects.filter(
                    #     vendor=user,
                    #     invoice_id=invoiceid,
                    #     is_room=True,
                    #     is_extend=False
                    # )

                    roominvoiceitems = InvoiceItem.objects.filter(
                                vendor=user,
                                invoice_id=invoiceid,
                                is_extend=False,
                                
                            ).filter(
                                Q(is_room=False, is_room_extra=True) | Q(is_room=True, is_room_extra=False)
                            )

                    room_invoice_total = 0.0
                    room_invoice_cgst_total = 0.0
                    room_invoice_grandtotal = 0.0
                    room_invoice_taxable_amount = 0.0

                    taxSlab.objects.filter(vendor=user,invoice=invoicedata).delete()
                    for room in roominvoiceitems:
                        room_invoice_total = room_invoice_total + float(room.totalwithouttax)
                        room_invoice_cgst_total = room_invoice_cgst_total + float(room.cgst_rate_amount )
                        room_invoice_grandtotal = room_invoice_grandtotal + float(room.total_amount)
                        if float(room.cgst_rate_amount ) > 0.0:
                            room_invoice_taxable_amount = float(room.totalwithouttax) + room_invoice_taxable_amount

                        if taxSlab.objects.filter(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate)).exists():
                                
                                taxSlab.objects.filter(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate)).update(
                                        cgst_amount=F('cgst_amount') + room.cgst_rate_amount,
                                        sgst_amount=F('sgst_amount') + room.sgst_rate_amount,
                                        total_amount=F('total_amount') + room.sgst_rate_amount + room.cgst_rate_amount,
                                )
                        else:
                                taxname = "GST"+str(int(float(room.cgst_rate)*2))
                                taxSlab.objects.create(vendor=user,invoice=invoicedata,cgst=float(room.cgst_rate),
                                        sgst=float(room.cgst_rate),tax_rate_name=taxname,cgst_amount=room.cgst_rate_amount,
                                        sgst_amount=room.sgst_rate_amount,total_amount=room.sgst_rate_amount + room.cgst_rate_amount)

                    # credit calculation here
                    


                    

                    if item_invoice_due_amount>0.99 :
                        today = datetime.now().date()
                        Invoice.objects.filter(vendor=user,id=itemsinvoicemain.id).update(invoice_status=False,invoice_number="unpaid")
                        CustomerCredit.objects.filter(vendor=user,invoice=invoicedata).delete()
                        CustomerCredit.objects.create(vendor=user,customer_name=itemsinvoicemain.customer.guestname,amount=item_invoice_due_amount,
                                                        due_date=today,invoice=itemsinvoicemain,phone=itemsinvoicemain.customer.guestphome)
                        
                        actionss = 'Create Credit Bill'
                        CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Guest Check-Out and F&b Split But Payment Is Due {item_invoice_due_amount}')
                        
                    new_latest_invoice = Invoice.objects.filter(
                        vendor=user, 
                        invoice_status=True
                    ).exclude(
                        invoice_number__in=['unpaid', '']
                    ).annotate(
                        invoice_number_int=Cast('invoice_number', IntegerField())  # Convert to Integer
                    ).aggregate(max_invoice=Max('invoice_number_int'))  # Get max invoice number

                    new_max_invoice_number = new_latest_invoice['max_invoice'] if new_latest_invoice['max_invoice'] else 0

                    new_invoice_number = new_max_invoice_number + 1  # Next invoice number

                    print(new_invoice_number, 'check this')
                   

                    Invoice.objects.filter(vendor=user,id=invoiceid).update(invoice_number=new_invoice_number,invoice_status=True,
                        total_item_amount=room_invoice_total,discount_amount=0.0,subtotal_amount=room_invoice_total,
                        gst_amount=room_invoice_cgst_total,sgst_amount=room_invoice_cgst_total,grand_total_amount=room_invoice_grandtotal,
                        taxable_amount=room_invoice_taxable_amount,
                        accepted_amount=room_invoice_grandtotal,Due_amount=0.00
                    )

                    if float(invoicedata.accepted_amount) > item_invoice_grandtotal:

                        invcpayment = InvoicesPayment.objects.filter(vendor=user,invoice=invoicedata)
                        # invcpayment.descriptions = invcpayment.descriptions + " " + "This Amount Sattled From Main Invoice"

                        totalpaybleamounts = item_invoice_grandtotal
                        room_recived_amt = room_invoice_grandtotal
                        added_amounts = 0.0
                        checkminusamount=0.0
                        roomamtis = room_recived_amt
                        for pay in invcpayment:
                            # eqdescrs = pay.descriptions + " " + "This amount has been settled from the main invoice."
                            if roomamtis > 0.99:
                                if roomamtis==float(pay.payment_amount):
                                
                                    roomamtis = 0.0

                                elif float(pay.payment_amount) < roomamtis:
                                    remainroomamt = room_recived_amt - float(pay.payment_amount)
                                    roomamtis=remainroomamt
                                elif roomamtis < float(pay.payment_amount):
                                    diffranceamount = float(pay.payment_amount) - roomamtis
                                    InvoicesPayment.objects.filter(id=pay.id).update(
                                            payment_amount=F('payment_amount')-diffranceamount  
                                        )
                                    InvoicesPayment.objects.create(vendor=user,invoice=itemsinvoicemain,advancebook=pay.advancebook,
                                                payment_amount=diffranceamount,payment_date=pay.payment_date,payment_mode=pay.payment_mode,
                                                transaction_id=pay.transaction_id,descriptions=pay.descriptions  )
                                    actionss = 'SPlit Payment To F&B'
                                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Amount Sattled main invoice to F&B. {diffranceamount}')
                        

                                    roomamtis = 0.0
                            else:
                                InvoicesPayment.objects.filter(id=pay.id).update(
                                            invoice=itemsinvoicemain,descriptions=pay.descriptions
                                        ) 
                                
                            
                        
                    
                    Booking.objects.filter(vendor=user,gueststay=invoicedata.customer).update(fnbinvoice=itemsinvoicemain)
                    
                    print("is room:",room_invoice_total,room_invoice_cgst_total,room_invoice_cgst_total,room_invoice_grandtotal,
                          room_invoice_taxable_amount)
                    actionss = 'Split Invoice'
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Split Invoice for Room and Food Service ')

                    
                    messages.success(request,"Invoice Seprated Succesfully!")
                else:
                    messages.error(request,"No Service Items In This Invoice")

            else:
                messages.error(request,"First, check out the guest, and then split the invoice.")  
           


            bookdatas = Booking.objects.filter(vendor=user,gueststay=guestid).last()
                
            booking_id = bookdatas.id

            
        
            new_request = request
            new_request.method = "POST"  # Simulate a POST request
            new_request.POST = QueryDict(mutable=True)
            new_request.POST.update({
                'bookingmodelid': booking_id
            })

            # Call the bookingdate function with the modified request
            return guesthistorysearchview(new_request)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



from django.http import QueryDict
from .views import guesthistorysearchview
import requests
from django.urls import reverse
from django.http import JsonResponse



def guest_logs(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            logs = CustomGuestLog.objects.filter(vendor=user,customer_id=id)

            return render(request,'logs.html',{'logs':logs,})
                 
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def showlogs(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            bookid = request.POST.get('bookingmodelidlogs')

            if Booking.objects.filter(vendor=user,id=bookid).exists():
                booksdata =  Booking.objects.get(vendor=user,id=bookid)
                
                logs = CustomGuestLog.objects.filter(vendor=user,customer=booksdata.gueststay)
                
                return render(request,'logs.html',{'logs':logs,})
            
            else:
                messages.error(request,'Booking Not Found')
                return redirect('weekviews')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def showlogsbook(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            bookid = request.POST.get('bookingmodelidlogs')

            if Booking.objects.filter(vendor=user,id=bookid).exists():
                booksdata =  Booking.objects.get(vendor=user,id=bookid)
                
                logs = CustomGuestLog.objects.filter(vendor=user,advancebook=booksdata.advancebook)
                
                return render(request,'logs.html',{'logs':logs,})
            
            else:
                messages.error(request,'Booking Not Found')
                return redirect('weekviews')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def showbooklog(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
           
            

            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                booksdata =  SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                
                logs = CustomGuestLog.objects.filter(vendor=user,advancebook=booksdata)
                
                return render(request,'logs.html',{'logs':logs,})
            
            else:
                messages.error(request,'Booking Not Found')
                return redirect('weekviews')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def editminvc(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

        invoice = Gueststay.objects.get(id=id)

        maininvc = Invoice.objects.filter(customer=invoice).first()
        # Prepare the data you want to send back as JSON
        return render(request,'editcustomer.html',{'invoicedata':maininvc})
        
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)

def geditfbinvc(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

        invoice = Gueststay.objects.get(id=id)

        maininvc = Invoice.objects.filter(customer=invoice).last()
        # Prepare the data you want to send back as JSON
        return render(request,'editcustomer.html',{'invoicedata':maininvc})
        
    except Invoice.DoesNotExist:
        return JsonResponse({'error': 'Invoice not found'}, status=404)

def guestearch(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            guesthistory = Gueststay.objects.filter(vendor=user,id=id)
            
            return render(request, 'guesthistory.html', {'guesthistory': guesthistory, 'active_page': 'guesthistory'})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def invcshow(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            userid = id
            
            
            if Invoice.objects.filter(vendor=user, id=userid).exists():
                    testinvcdata  = Invoice.objects.get(vendor=user, id=userid)
                    userid = testinvcdata.customer.id
                

            guestdata = Gueststay.objects.filter(vendor=user, id=userid)
            invoice_data = Invoice.objects.get(vendor=user, id=id)
            profiledata = HotelProfile.objects.filter(vendor=user)
            itemid = invoice_data.id
            status = invoice_data.foliostatus

            invoice_datas = Invoice.objects.filter(vendor=user, id=id)
            invoiceitemdata = InvoiceItem.objects.filter(vendor=user, invoice=itemid).order_by('id')
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            invcpayments = InvoicesPayment.objects.filter(vendor=user,invoice=itemid).all()
            taxelab = taxSlab.objects.filter(vendor=user,invoice=itemid)
            
            if True:
                creditdata = CustomerCredit.objects.filter(vendor=user,phone=invoice_data.customer.guestphome)
                if invoice_data.taxtype == 'GST':
                    gstamounts = invoice_data.gst_amount
                    sstamounts = invoice_data.sgst_amount
                    
                    invcheck =  invoiceDesign.objects.get(vendor=user)
                    if invcheck.guestinvcdesign==1:
                        return render(request, 'invoicepage.html', {
                            'profiledata': profiledata,
                            'guestdata': guestdata,
                            'invoice_data': invoice_datas,
                            'invoiceitemdata': invoiceitemdata,
                            'invcpayments':invcpayments,
                            'gstamounts':gstamounts,
                            'sstamounts':sstamounts,
                            'creditdata':creditdata,
                            'taxelab':taxelab
                        })
                    elif invcheck.guestinvcdesign==2:
                        return render(request, 'invoicepage2.html', {
                            'profiledata': profiledata,
                            'guestdata': guestdata,
                            'invoice_data': invoice_datas,
                            'invoiceitemdata': invoiceitemdata,
                            'invcpayments':invcpayments,
                            'gstamounts':gstamounts,
                            'sstamounts':sstamounts,
                            'creditdata':creditdata,
                            'taxelab':taxelab
                        })
                        
                        
                else:
                    istamts = invoice_data.sgst_amount + invoice_data.gst_amount
                    invcheck =  invoiceDesign.objects.get(vendor=user)
                    if invcheck.guestinvcdesign==1:
                        return render(request, 'invoicepage.html', {
                            'profiledata': profiledata,
                            'guestdata': guestdata,
                            'invoice_data': invoice_datas,
                            'invoiceitemdata': invoiceitemdata,
                            'invcpayments':invcpayments,
                            'creditdata':creditdata,
                            'istamts':istamts,
                            'taxelab':taxelab
                        })
                    elif invcheck.guestinvcdesign==2:
                        print(invcpayments)
                        return render(request, 'invoicepage2.html', {
                            'profiledata': profiledata,
                            'guestdata': guestdata,
                            'invoice_data': invoice_datas,
                            'invoiceitemdata': invoiceitemdata,
                            'invcpayments':invcpayments,
                            'creditdata':creditdata,
                            'istamts':istamts,
                            'taxelab':taxelab
                        })
             
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def bookingsearchview(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            bookidsmain = request.POST.get('bookidsmain')
            if Booking.objects.filter(vendor=user,id=bookidsmain):
                bookdata=Booking.objects.get(vendor=user,id=bookidsmain)
                advancersoomdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,
                                    id=bookdata.advancebook.id )

            # If no results found
            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            # Return results
            return render(request, 'advancebookinghistory.html', {
                'monthbookdata': advancersoomdata,
                'active_page': 'advancebookhistory',
            })
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def searchbooking(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            boookid=id
            
            advancersoomdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,
                                    id=boookid )

            # If no results found
            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            # Return results
            return render(request, 'advancebookinghistory.html', {
                'monthbookdata': advancersoomdata,
                'active_page': 'advancebookhistory',
            })
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def deletecancelbokings(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            boookid=id
            
            data=SaveAdvanceBookGuestData.objects.filter(vendor=user,
                                    action='cancel').all().delete()
            
            messages.success(request,'Delete All Cancel Bookins!')
            return redirect('advanceroomhistory')
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def editbookingdetails(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('id')
            guestname = request.POST.get('guestname')
            phone = request.POST.get('phone')
            sprequest = request.POST.get('sprequest')
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).update(
                    bookingguest=guestname,
                    bookingguestphone=phone,
                    special_requests=sprequest,
                 )
                Saveadvancebookdata = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                actionss = 'Edit Booking'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Edit Guest Details Name And Number ')

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('advancebookingdetails',id)
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def editamountdetailsbooking(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('id')
            # checkindate = request.POST.get('checkindate')
            # checkoutdate = request.POST.get('checkoutdate')
            advanceamount = int(request.POST.get('advanceamount'))
            remainamount = int(request.POST.get('remainamount'))
            taxamount = float(request.POST.get('taxamount'))
            grandtotalamount = int(request.POST.get('grandtotalamount'))
            amtaftertax = float(request.POST.get('amtaftertax'))
            amtbeforetax = float(request.POST.get('amtbeforetax'))
            bookingid = request.POST.get('bookingid')
            
            
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).update(
                    # bookingdate=checkindate,
                    # checkoutdate=checkoutdate,
                    advance_amount=advanceamount,
                    reamaining_amount=remainamount,
                    tax=taxamount,
                    total_amount=grandtotalamount,
                    amount_after_tax=amtaftertax,
                    amount_before_tax=amtbeforetax,
                    booking_id=bookingid,
                 )
                Saveadvancebookdata = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                actionss = 'Edit Booking'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Edit Amount Details ')

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('advancebookingdetails',id)
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def editroomsdata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('id')
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                room_id = request.POST.getlist("roomid")  # सभी roomid लेंगे
                sell_rates = request.POST.getlist("sellrateamt")  # सभी sell rates लेंगे

                for r_id, rate in zip(room_id, sell_rates):
                    room = get_object_or_404(RoomBookAdvance, id=r_id)
                    room.sell_rate = float(rate)  # नया rate सेट करें
                    room.save() 
                
                Saveadvancebookdata = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                actionss = 'Edit Rooms Rates'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Edit Amount Details In Rooms')

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('advancebookingdetails',id)
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def edittaxes(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('maintaxid')
            if Taxes.objects.filter(vendor=user,id=id).exists():
                taxnames = request.POST.get("taxnames") 
                hsncodess = request.POST.get("hsncodess")  
                taxratez = request.POST.get("taxratez")  
                Taxes.objects.filter(vendor=user,id=id).update(
                        taxname=taxnames,taxcode=hsncodess,taxrate=taxratez
                )

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('setting')
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def editrateplanbooking(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('maintaxid')
            if RatePlanforbooking.objects.filter(vendor=user,id=id).exists():
                taxnames = request.POST.get("taxnames") 
                hsncodess = request.POST.get("hsncodess")  
                taxratez = request.POST.get("taxratez")  
                RatePlanforbooking.objects.filter(vendor=user,id=id).update(
                        rate_plan_name=taxnames,rate_plan_code=hsncodess,base_price=taxratez
                )
          

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('rateplanpage')
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def editotarateplan(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            id = request.POST.get('maintaxid')
            if RatePlan.objects.filter(vendor=user,id=id).exists():
                planname = request.POST.get("planname") 
                planbasepriceota = request.POST.get("planbasepriceota")  
                plancode = request.POST.get("plancode")
                descptn = request.POST.get("descptn") 
                maxprs = request.POST.get("maxprs")  
                addperprice = request.POST.get("addpersonprice")  
                childs = request.POST.get("childs")  

                RatePlan.objects.filter(vendor=user,id=id).update(
                        rate_plan_name=planname,rate_plan_code=plancode,base_price=planbasepriceota,
                      rate_plan_description= descptn,additional_person_price=addperprice,max_persons=maxprs,
                      childmaxallowed=childs
                )

              

                messages.success(request,"Succesfully Edited!")
            else:
                messages.error(request,"Id Not Found")

            return redirect('rateplanpage')
            
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)