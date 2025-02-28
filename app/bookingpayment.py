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



def hotelplrpt(request):
    # try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            today = datetime.datetime.now().date()
            yestarday = today - timedelta(days=1)

            startdate = yestarday
            enddate =   today

            from django.db.models import Sum

            # Filter the InvoiceItem records by vendor, date range, and is_room=True
            invoice_data = InvoiceItem.objects.filter(
                vendor=user, 
                date__range=[startdate, enddate], 
                is_room=True
            )

            # Aggregate the total quantity (Room Nights Sold) and total amount (Total Revenues)
            aggregated_data = invoice_data.aggregate(
                room_nights_sold=Sum('quantity_likedays'),  # Sum of quantity_likedays (Room Nights Sold)
                total_revenues=Sum('total_amount')         # Sum of total_amount (Total Revenues)
            )

            
            # Filter data for items where is_room=False
            item_data = InvoiceItem.objects.filter(
                vendor=user,
                date__range=[startdate, enddate],
                is_room=False
            )

            # Aggregate data for the items
            aggregated_item_data = item_data.values('description').annotate(
                total_quantity=Sum('quantity_likedays'),
                total_amount=Sum('total_amount')
            )

            # Calculate the overall totals for all items
            total_quantity = aggregated_item_data.aggregate(Sum('total_quantity'))['total_quantity__sum']
            total_amount = aggregated_item_data.aggregate(Sum('total_amount'))['total_amount__sum']

            
            # Query to fetch the items based on meal plan name, vendor, and date range
            meal_item_data = InvoiceItem.objects.filter(
                vendor=user,
                date__range=[startdate, enddate],
                is_mealp=True
            )

            # Aggregating by meal plan and calculating total price for each meal plan
            meal_plans = meal_item_data.values('mealplanname').annotate(
                total_quantity=Sum('quantity_likedays'),
                total_price=Sum(F('quantity_likedays') * F('mealpprice'))
            )

            # Calculate the overall totals for all items
            meal_total_quantity = meal_plans.aggregate(meal_total_quantity=Sum('total_quantity'))['meal_total_quantity']
            meal_total_amount = meal_plans.aggregate(meal_total_amount=Sum('total_price'))['meal_total_amount']
            
            
            return render(request,'hotelsalesrpt.html',{'aggregated_data':aggregated_data,'startdate':startdate,
                            'enddate':enddate,'item_data': aggregated_item_data,   # For Item Summary
                            'total_quantity': total_quantity,'meal_total_quantity':meal_total_quantity,
                            'total_amount': total_amount,'meal_plans':meal_plans,'meal_total_amount':meal_total_amount})

        else:
            return redirect('loginpage')
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)


def hotelplrptsearch(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            # Filter the InvoiceItem records by vendor, date range, and is_room=True
            invoice_data = InvoiceItem.objects.filter(
                vendor=user, 
                date__range=[startdate, enddate], 
                is_room=True
            )

            # Aggregate the total quantity (Room Nights Sold) and total amount (Total Revenues)
            aggregated_data = invoice_data.aggregate(
                room_nights_sold=Sum('quantity_likedays'),  # Sum of quantity_likedays (Room Nights Sold)
                total_revenues=Sum('total_amount')         # Sum of total_amount (Total Revenues)
            )

            
            # Filter data for items where is_room=False
            item_data = InvoiceItem.objects.filter(
                vendor=user,
                date__range=[startdate, enddate],
                is_room=False
            )

            # Aggregate data for the items
            aggregated_item_data = item_data.values('description').annotate(
                total_quantity=Sum('quantity_likedays'),
                total_amount=Sum('total_amount')
            )

            # Calculate the overall totals for all items
            total_quantity = aggregated_item_data.aggregate(Sum('total_quantity'))['total_quantity__sum']
            total_amount = aggregated_item_data.aggregate(Sum('total_amount'))['total_amount__sum']

            
            # Query to fetch the items based on meal plan name, vendor, and date range
            meal_item_data = InvoiceItem.objects.filter(
                vendor=user,
                date__range=[startdate, enddate],
                is_mealp=True
            )

            # Aggregating by meal plan and calculating total price for each meal plan
            meal_plans = meal_item_data.values('mealplanname').annotate(
                total_quantity=Sum('quantity_likedays'),
                total_price=Sum(F('quantity_likedays') * F('mealpprice'))
            )

            # Calculate the overall totals for all items
            meal_total_quantity = meal_plans.aggregate(meal_total_quantity=Sum('total_quantity'))['meal_total_quantity']
            meal_total_amount = meal_plans.aggregate(meal_total_amount=Sum('total_price'))['meal_total_amount']
            
            
            return render(request,'hotelsalesrpt.html',{'aggregated_data':aggregated_data,'startdate':startdate,
                            'enddate':enddate,'item_data': aggregated_item_data,   # For Item Summary
                            'total_quantity': total_quantity,'meal_total_quantity':meal_total_quantity,
                            'total_amount': total_amount,'meal_plans':meal_plans,'meal_total_amount':meal_total_amount})

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    




def hotelpandlrpt(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            # Get today's date
            today = datetime.datetime.now().date()

            # First day of the month
            startdate = today.replace(day=1)

            # Last day of the month
            next_month = today.replace(day=28) + timedelta(days=4)  # Ensure we go to the next month
            enddate = next_month.replace(day=1) - timedelta(days=1)

            invc_total_amount = Invoice.objects.filter(
                    vendor=user, 
                    invoice_date__range=[startdate, enddate]
                ).aggregate(Sum('grand_total_amount'))

            # The result will be a dictionary containing the sum of grand_total_amount
            invc_grand_total = invc_total_amount['grand_total_amount__sum']  # This will give the sum of grand_total_amount

            # If there are no invoices within the range, `grand_total` will be None
            if invc_grand_total is None:
                invc_grand_total = 0.00 

            suppliertotal = Supplier.objects.filter(vendor=user,
                    invoicedate__range=[startdate,enddate]).aggregate(Sum('grand_total_amount'))
            
            supplier_grand_total = suppliertotal['grand_total_amount__sum']
            if supplier_grand_total is None:
                supplier_grand_total = 0.00 


            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            totalsalaryexpance = SalaryManagement.objects.filter(vendor=user,
                        salary_date__range=[startdate,enddate]).aggregate(total_sales=Sum('basic_salary'))['total_sales'] or 0
            
            print(totalsalaryexpance,'salary ')
            print(total_cash_expense,"total cash expenses")
            print(supplier_grand_total,'purchase')
            print(invc_grand_total)

            print("Start date (first day of the month):", startdate)
            print("End date (last day of the month):", enddate)

            completetotal = invc_grand_total + supplier_grand_total + total_cash_expense + totalsalaryexpance
            
            profit =  invc_grand_total - (supplier_grand_total + total_cash_expense + totalsalaryexpance)
            # return redirect('todaysales')
            return render(request,'pandlrpt.html',{'startdate':startdate,'enddate':enddate,
                            'invc_grand_total':invc_grand_total,'supplier_grand_total':supplier_grand_total,
                            'total_cash_expense':total_cash_expense,'totalsalaryexpance':totalsalaryexpance,
                             'completetotal':completetotal,'profit':profit })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



def hotelpandlsearch(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            invc_total_amount = Invoice.objects.filter(
                    vendor=user, 
                    invoice_date__range=[startdate, enddate]
                ).aggregate(Sum('grand_total_amount'))

            # The result will be a dictionary containing the sum of grand_total_amount
            invc_grand_total = invc_total_amount['grand_total_amount__sum']  # This will give the sum of grand_total_amount

            # If there are no invoices within the range, `grand_total` will be None
            if invc_grand_total is None:
                invc_grand_total = 0.00 

            suppliertotal = Supplier.objects.filter(vendor=user,
                    invoicedate__range=[startdate,enddate]).aggregate(Sum('grand_total_amount'))
            
            supplier_grand_total = suppliertotal['grand_total_amount__sum']
            if supplier_grand_total is None:
                supplier_grand_total = 0.00 


            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            totalsalaryexpance = SalaryManagement.objects.filter(vendor=user,
                        salary_date__range=[startdate,enddate]).aggregate(total_sales=Sum('basic_salary'))['total_sales'] or 0
            
            print(totalsalaryexpance,'salary ')
            print(total_cash_expense,"total cash expenses")
            print(supplier_grand_total,'purchase')
            print(invc_grand_total)

            print("Start date (first day of the month):", startdate)
            print("End date (last day of the month):", enddate)

            completetotal = invc_grand_total + supplier_grand_total + total_cash_expense + totalsalaryexpance
            
            profit =  invc_grand_total - (supplier_grand_total + total_cash_expense + totalsalaryexpance)
            # return redirect('todaysales')
            return render(request,'pandlrpt.html',{'startdate':startdate,'enddate':enddate,
                            'invc_grand_total':invc_grand_total,'supplier_grand_total':supplier_grand_total,
                            'total_cash_expense':total_cash_expense,'totalsalaryexpance':totalsalaryexpance,
                             'completetotal':completetotal,'profit':profit })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def expensesrpt(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            # Get today's date
            today = datetime.datetime.now().date()

            # First day of the month
            startdate = today.replace(day=1)

            # Last day of the month
            next_month = today.replace(day=28) + timedelta(days=4)  # Ensure we go to the next month
            enddate = next_month.replace(day=1) - timedelta(days=1)

            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            expanses = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).all()
            
            # return redirect('todaysales')
            return render(request,'exppense.html',{'startdate':startdate,'enddate':enddate,
                            'expanses':expanses,
                            'total_cash_expense':total_cash_expense })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def searchexpenses(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            expanses = expenseCash.objects.filter(vendor=user
                    ,date_time__date__range=[startdate,enddate]).all()
            
            # return redirect('todaysales')
            return render(request,'exppense.html',{'startdate':startdate,'enddate':enddate,
                            'expanses':expanses,
                            'total_cash_expense':total_cash_expense })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)