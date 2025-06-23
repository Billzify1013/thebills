from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from time import gmtime, strftime
from django.db.models import Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from django.contrib import messages
import datetime
from django.http import JsonResponse
from django.db.models import Q
import json
import requests
import urllib.parse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import ExtractMonth
import calendar
from django.db.models import Count
from django.shortcuts import redirect, get_object_or_404
import threading
from .newcode import *
# Create your views here.
from .dynamicrates import *
from django.db.models import F
from . loyltys import searchcredit
from django.contrib.sessions.backends.db import SessionStore
import math
from .cm_file import update_inventory_task_cm



from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder

def custom_404(request, exception):
    return render(request, '404.html',{'error_message': str("Page Not Found")}, status=404)


def index(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            # Get the current year
            now = timezone.now()
            current_year = now.year 
            
            # Fetch data for the selected year (current_year)
            subtotalsale = Invoice.objects.filter(vendor=user, invoice_date__year=current_year).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            totaltax = Invoice.objects.filter(vendor=user, invoice_date__year=current_year).aggregate(total_sales=Sum('gst_amount'))['total_sales'] or 0
            subtotalsale = int(subtotalsale)
            totaltax = int(totaltax * 2)
            totalsalaryexpance = SalaryManagement.objects.filter(vendor=user).aggregate(total_sales=Sum('basic_salary'))['total_sales'] or 0
            totalsalaryexpance = int(totalsalaryexpance)
            totaltaxandsalary = totalsalaryexpance + totaltax
            totalsalaryexcludedeductions = subtotalsale - totaltaxandsalary
            subtotalsalereal = Invoice.objects.filter(vendor=user, invoice_date__year=current_year).aggregate(total_sales=Sum('subtotal_amount'))['total_sales'] or 0
            
            # Fetch highly booked room for the current year
            most_booked_room = Gueststay.objects.filter(vendor=user, checkindate__year=current_year).values('roomno') \
                .annotate(bookings_count=Count('roomno')) \
                .order_by('-bookings_count') \
                .values_list('roomno', flat=True).first()
            
            # Fetch monthly sales data for the current year
            monthly_data = Invoice.objects.filter(vendor=user, invoice_date__year=current_year) \
                                        .annotate(month=ExtractMonth('invoice_date')) \
                                        .values('month') \
                                        .annotate(total_sales=Sum('grand_total_amount')) \
                                        .order_by('month')

            # Prepare data for Chart.js
            labels = []
            data = []
            sales_data = {month: 0 for month in range(1, 13)}

            for entry in monthly_data:
                month = entry['month']
                total_sales = float(entry['total_sales'])  # Convert Decimal to float
                sales_data[month] = total_sales

            # Sort the sales_data dictionary by month and prepare labels and data
            for month, total_sales in sorted(sales_data.items()):
                labels.append(datetime(2024, month, 1).strftime('%b'))
                data.append(total_sales)

            # Calculate growth (example)
            growth = sum(data) / 12 if data else 0

            # Convert data to JSON format for Chart.js
            labels_json = json.dumps(labels)
            data_json = json.dumps(data)

            # Calculate total sales for all time
            total_sales_all_time = Invoice.objects.filter(vendor=user) \
                                                .aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            
            # Calculate total sales for the last 7 days
            total_sales_last_7_days = Invoice.objects.filter(vendor=user, 
                                                            invoice_date__gte=(datetime.now())-timedelta(days=7)) \
                                                    .aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            
            # Calculate sales percentage
            if total_sales_all_time > 0:
                sales_percent = 100 * total_sales_last_7_days / total_sales_all_time
            else:
                sales_percent = 0
            sales_percent = int(sales_percent)
            growth_json = json.dumps(sales_percent)

            # Weekly data for the current week (Sun to Sat)
            today = datetime.now().date()
            last_sunday = today - timedelta(days=today.weekday() + 1)
            next_saturday = last_sunday + timedelta(days=6)

            # Fetch invoices from last Sunday to next Saturday for the current year
            invoices = Invoice.objects.filter(vendor=user, invoice_date__year=current_year, invoice_date__range=[last_sunday, next_saturday])

            # Initialize a list for Sun to Sat with zeros
            weekly_data = [0] * 7

            # Fill the weekly data
            for invoice in invoices:
                day_index = (invoice.invoice_date - last_sunday).days
                weekly_data[day_index] += float(invoice.grand_total_amount)  # Convert Decimal to float

            # Create a dictionary to hold the data
            data_dict = {
                'today': today.isoformat(),
                'last_sunday': last_sunday.isoformat(),
                'next_saturday': next_saturday.isoformat(),
                'weekly_data': weekly_data
            }

            # Convert dictionary to JSON string with custom encoder
            weeklys_data = json.dumps(data_dict, cls=DjangoJSONEncoder)


            # Filter the Supplier model based on the year and sattle status
            total_purches_settled = Supplier.objects.filter(
                vendor=user,
                sattle=True,
                invoicedate__year=current_year
            ).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0

            # Sum the grand_total_amount for the filtered suppliers

            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__year=current_year).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            # totalsalaryexcludedeductions = totalsalaryexcludedeductions - total_cash_expense - total_purches_settled
            # Pass data to the template

            # commisiion data calculations
            check_invoices = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__year=current_year
                ).exclude(customer__saveguestid=None)

            # Step 2: Extract guest IDs from each invoice
            book_ids = [
                    invoice.customer.saveguestid
                    for invoice in check_invoices
                    if hasattr(invoice.customer, 'saveguestid')
                ]

            print("Filtered Guest IDs from Invoices:", book_ids)

            # ✅ Step 3: Correct filtering (no nested list)
            commmodel = tds_comm_model.objects.filter(
                    roombook__id__in=book_ids
                )

            totals = commmodel.aggregate(
                    total_commission=Sum('commission'),
                    total_tds=Sum('tds'),
                    total_tcs=Sum('tcs')
                )
            totals = {
                    'total_commission': totals['total_commission'] or 0,
                    'total_tds': totals['total_tds'] or 0,
                    'total_tcs': totals['total_tcs'] or 0,
                }
            # Print totals
            print("Total Commission:", totals['total_commission'] or 0)
            print("Total TDS:", totals['total_tds'] or 0)
            print("Total TCS:", totals['total_tcs'] or 0)

            print("Commission Models Found:", commmodel)
            total_deduct_balace = totaltax + totalsalaryexpance  + total_cash_expense  + total_purches_settled + int(totals['total_commission']) + int(totals['total_tds']) + int(totals['total_tcs'])
            
            totalsalaryexcludedeductions = totalsalaryexcludedeductions - total_cash_expense - total_purches_settled - int(totals['total_commission']) - int(totals['total_tds']) - int(totals['total_tcs'])
            print(total_deduct_balace,'check this')
            return render(request, 'index.html', {
                'subtotalsale': subtotalsale,
                'active_page': 'index',
                'labels_json': labels_json,
                'data_json': data_json,
                'growth_json': growth_json,
                'totaltax': totaltax,
                'totalsalaryexpance': totalsalaryexpance,
                'totalsalaryexcludedeductions': totalsalaryexcludedeductions,
                'most_booked_room': most_booked_room,
                'weeklys_data': weeklys_data,
                'current_year': current_year,
                'total_purches_settled':total_purches_settled,
                'total_cash_expense':total_cash_expense,
                'totals':totals,'total_deduct_balace':total_deduct_balace
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



    
def guestregform(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if Gueststay.objects.filter(vendor=user,id=id).exists():
                guestdata = Gueststay.objects.filter(vendor=user,id=id)
                hoteldata = HotelProfile.objects.filter(vendor=user)
                hoteldatas = HotelProfile.objects.get(vendor=user)
                terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
                return render(request,"guestregform.html",{'guestdata':guestdata,'hoteldata':hoteldata,'terms_lines':terms_lines})
            else:
                return render(request,"homepage.html")
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def myprofile(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    user=request.user
    subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
    if subuser:
        user = subuser.vendor  
    profiledata = HotelProfile.objects.filter(vendor=user)
    return render(request, 'profile.html', {'profiledata': profiledata})



def guesthistory(request):
    # try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # guestshistory = Gueststay.objects.filter(vendor=user).select_related('invoice').values(
            #    'fandbinvoiceid', 'checkoutdate', 'checkindate', 'roomno', 'guestname', 'id', 'guestphome', 'guestcity', 'noofrooms','invoice__foliostatus'
            # ).order_by('-id')
            guestshistory = Gueststay.objects.filter(vendor=user).order_by('-id')
            
            paginator = Paginator(guestshistory, 25)
            page = request.GET.get('page', 1)
            
            try:
                guesthistory = paginator.page(page)
            except PageNotAnInteger:
                guesthistory = paginator.page(1)
            except EmptyPage:
                guesthistory = paginator.page(paginator.num_pages)
            
            return render(request, 'guesthistory.html', {'guesthistory': guesthistory, 'active_page': 'guesthistory'})
        else:
            return render(request, 'login.html')
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)

        
    
def guestdetails(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestdetails = Gueststay.objects.filter(vendor=user, id=id).all()
            moredata = MoreGuestData.objects.filter(vendor=user, mainguest_id=id).all()
            moreids = Guest_BackId.objects.filter(vendor=user,guest__id__in=guestdetails)
            print(moreids)
            return render(request, 'guestdetails.html', {
                'guestdetails': guestdetails,
                'MoreGuestData': moredata,
                'active_page': 'guesthistory',
                'moreids':moreids
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def guestdetailsfrominvc(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcmain = Invoice.objects.filter(
                vendor=user, id=id).first()
            guestdetails = Gueststay.objects.filter(vendor=user,id=invcmain.customer.id).all()
            moredata = MoreGuestData.objects.filter(vendor=user, mainguest_id=invcmain.customer.id).all()
            moreids = Guest_BackId.objects.filter(vendor=user,guest__id__in=guestdetails)
            print(moreids)
            return render(request, 'guestdetails.html', {
                'guestdetails': guestdetails,
                'MoreGuestData': moredata,
                'active_page': 'guesthistory',
                'moreids':moreids
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


# def advanceroombookpage(request):
#     try:
#         if request.user.is_authenticated:
#             user = request.user
#             today = datetime.now().date()
#             tomorrow = today + timedelta(days=1)
#             booking_success = bookingdate(request, startdate=today, enddate=tomorrow)

#             br = Rooms.objects.filter(vendor=user)
#             channal = onlinechannls.objects.all()
#             return render(request, 'roombookpage.html', {
#                 'br': br,
#                 'channal': channal,
#                 'active_page': 'advanceroombookpage'
#             })
#         else:
#             return render(request, 'login.html')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)

from django.http import QueryDict
# advance room book page function
def advanceroombookpage(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Simulate POST data for startdate and enddate
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)

            # Create a mutable copy of the request
            new_request = request
            new_request.method = "POST"  # Simulate a POST request
            new_request.POST = QueryDict(mutable=True)
            new_request.POST.update({
                'startdate': str(today),
                'enddate': str(tomorrow)
            })

            # Call the bookingdate function with the modified request
            if Vendor_Service.objects.filter(vendor=user,only_cm=True):
                return redirect('cm')
            return bookingdate(new_request)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def foliobillingpage(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invoice_data = Invoice.objects.filter(vendor=user, foliostatus=False).order_by('room_no')
            return render(request, 'foliopage.html', {
                'invoice_data': invoice_data,
                'active_page': 'foliobillingpage'
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
    
def invoicepage(request, id):
    # try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            userid = id
            if Gueststay.objects.filter(vendor=user, id=userid).exists():
                pass
            else:
                if Invoice.objects.filter(vendor=user, id=userid,is_fandb=False).exists():
                    testinvcdata  = Invoice.objects.get(vendor=user, id=userid,is_fandb=False)
                    userid = testinvcdata.customer.id
                elif Invoice.objects.filter(vendor=user, id=userid,is_fandb=True).exists():
                    testinvcdata  = Invoice.objects.get(vendor=user, id=userid,is_fandb=True)
                    userid = testinvcdata.customer.id
                    print("haan ye to fand b invoice hai")
                    return redirect('fbinvoicepage',testinvcdata.id)
                    # print("haan ye to fand b invoice hai")

            guestdata = Gueststay.objects.filter(vendor=user, id=userid)
            invoice_data = Invoice.objects.get(vendor=user, customer=userid,is_fandb=False)
            profiledata = HotelProfile.objects.filter(vendor=user)
            itemid = invoice_data.id
            status = invoice_data.foliostatus

            invoice_datas = Invoice.objects.filter(vendor=user, customer=userid,is_fandb=False)
            invoiceitemdata = InvoiceItem.objects.filter(vendor=user, invoice=itemid).order_by('id')
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            invcpayments = InvoicesPayment.objects.filter(vendor=user,invoice=itemid).all()
            taxelab = taxSlab.objects.filter(vendor=user,invoice=itemid)
            if status is False:
                if invoice_data.taxtype == 'GST':
                    gstamounts = invoice_data.gst_amount
                    sstamounts = invoice_data.sgst_amount
                    return render(request, 'foliobill.html', {
                        'active_page': 'foliobillingpage',
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
                    istamts = invoice_data.sgst_amount + invoice_data.gst_amount
             
                    return render(request, 'foliobill.html', {
                        'active_page': 'foliobillingpage',
                        'profiledata': profiledata,
                        'guestdata': guestdata,
                        'invoice_data': invoice_datas,
                        'invoiceitemdata': invoiceitemdata,
                        'loyltydata': loyltydata,
                        'invcpayments':invcpayments,
                        'istamts':istamts,
                        'taxelab':taxelab
                    })
            else:
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
                    
                    elif invcheck.guestinvcdesign==3:
                        return render(request, 'invoicepage3.html', {
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
                    elif invcheck.guestinvcdesign==3:
                        print(invcpayments)
                        return render(request, 'invoicepage3.html', {
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
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)



def fbinvoicepage(request, id):
    # try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            userid = id
            
            testinvcdata  = Invoice.objects.get(vendor=user, id=userid,is_fandb=True)
            userid = testinvcdata.customer.id

                    
                  

            guestdata = Gueststay.objects.filter(vendor=user, id=userid)
            invoice_data = Invoice.objects.get(vendor=user, customer=userid,is_fandb=True)
            profiledata = HotelProfile.objects.filter(vendor=user)
            itemid = invoice_data.id
            status = invoice_data.foliostatus

            invoice_datas = Invoice.objects.filter(vendor=user, customer=userid,is_fandb=True)
            invoiceitemdata = InvoiceItem.objects.filter(vendor=user, invoice=itemid).order_by('id')
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            invcpayments = InvoicesPayment.objects.filter(vendor=user,invoice=itemid).all()
            taxelab = taxSlab.objects.filter(vendor=user,invoice=itemid)
            if status is False:
                if invoice_data.taxtype == 'GST':
                    gstamounts = invoice_data.gst_amount
                    sstamounts = invoice_data.sgst_amount
                    return render(request, 'foliobill.html', {
                        'active_page': 'foliobillingpage',
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
                    istamts = invoice_data.sgst_amount + invoice_data.gst_amount
             
                    return render(request, 'foliobill.html', {
                        'active_page': 'foliobillingpage',
                        'profiledata': profiledata,
                        'guestdata': guestdata,
                        'invoice_data': invoice_datas,
                        'invoiceitemdata': invoiceitemdata,
                        'loyltydata': loyltydata,
                        'invcpayments':invcpayments,
                        'istamts':istamts,
                        'taxelab':taxelab
                    })
            else:
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
                    
                    elif invcheck.guestinvcdesign==3:
                        return render(request, 'invoicepage3.html', {
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
                    
                    elif invcheck.guestinvcdesign==3:
                        print(invcpayments)
                        return render(request, 'invoicepage3.html', {
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
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)


def creditinvoicecheck(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            dataid = id
            data = CustomerCredit.objects.filter(vendor=user,id=dataid).last()
            
            new_request = request
            new_request.method = "POST"  # Simulate a POST request
            new_request.POST = QueryDict(mutable=True)
            new_request.POST.update({
                'name': str(''),
                'phone':str(data.phone) ,
                'date':str('')
            })
            messages.warning(request,"Panding Invoice Here")
            # Call the bookingdate function with the modified request
            return searchcredit(new_request)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
      

from django.urls import reverse
def editcustomergstnumber(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcid = request.POST.get('invcid')
            gstnumber = request.POST.get('gstnumber')
            customerphone = request.POST.get('customerphone')
            guestid = request.POST.get('guestid')
            company = request.POST.get('company')
            if Invoice.objects.filter(vendor=user,id=invcid).exists():
                Invoice.objects.filter(vendor=user,id=invcid).update(customer_gst_number=gstnumber,customer_company=company)
                invcdatas = Invoice.objects.get(vendor=user,id=invcid)
                if invcdatas.is_fandb:
                    invctype = 'F&B'
                else:
                    invctype = 'Main'
                Gueststay.objects.filter(vendor=user,id=invcdatas.customer.id).update(guestphome=customerphone)
                actionss = 'Edit Gst details'
                CustomGuestLog.objects.create(vendor=user,customer_id=invcdatas.customer.id,by=request.user,action=actionss,
                        description=f'edit Gst details in {invctype} invoice')

            else:
                pass

            url = reverse('guestearch', args=[guestid])

        
            return redirect(url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def rooms(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomdata = Rooms.objects.filter(vendor=user).order_by('room_name')
            category = RoomsCategory.objects.filter(vendor=user)
            tax = Taxes.objects.filter(vendor=user)
            return render(request, 'rooms.html', {
                'roomdata': roomdata,
                'active_page': 'rooms',
                'category': category,
                'tax': tax
            })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)






# def homepage(request):
#     try:
#         if request.user.is_authenticated:
#             user = request.user
             
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             # Filter data
#             category = RoomsCategory.objects.filter(vendor=user).order_by('id')
#             rooms = Rooms.objects.filter(vendor=user).order_by('id')
#             # desired_date = datetime.now().date() + timedelta(days=1)
#             desired_date = datetime.now().date()
#             if Roomcleancheck.objects.filter(vendor=user,current_date=desired_date).exists():
#                 pass
#             else:

#                 Roomcleancheck.objects.create(vendor=user,current_date=desired_date)
#                 roomsclans = Rooms.objects.filter(vendor=user, checkin__in=[1, 2])
#                 roomsclans.update(is_clean=False)
#                 Roomcleancheck.objects.filter(vendor=user).exclude(current_date=desired_date).delete()

            
#             # Update checkout status for guests
#             Gueststay.objects.filter(Q(vendor=user, checkoutdate__date__lte=desired_date) | Q(vendor=user, checkoutdate__date=desired_date)).update(checkoutstatus=True)

#             # Query sets
#             dats = Gueststay.objects.filter(vendor=user, checkoutdate__date__lte=desired_date, checkoutstatus=True, checkoutdone=False)
#             datsin = Gueststay.objects.filter(vendor=user, checkindate__date=desired_date)
#             tax = Taxes.objects.filter(vendor=user).all()
#             arriwaldata = RoomBookAdvance.objects.filter(
#                   # Include the vendor condition
#                 Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
#                 Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
#             ).exclude(vendor=user,saveguestdata__action='cancel')
            
#             bookedmisseddata = RoomBookAdvance.objects.filter(vendor=user, checkoutdate__lte=desired_date, checkinstatus=False).exclude(vendor=user,saveguestdata__action='cancel')
#             saveguestallroomcheckout = RoomBookAdvance.objects.filter(vendor=user, checkoutdate=desired_date, checkinstatus=True).exclude(vendor=user,saveguestdata__action='cancel')
            
#             # find to clour red
#             reddata = Gueststay.objects.filter(vendor=user, checkoutdate__date__gt=desired_date, checkoutstatus=False, checkoutdone=False)
#             for i in reddata:
#                 if Rooms.objects.filter(
#                         vendor=user,
#                         room_name=i.roomno,
#                         checkin__in=[1, 4, 5,2]
#                     ).exists():
#                         pass
#                 else:
#                     Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=1)
                    

#             # Update rooms based on filtered data
#             for i in saveguestallroomcheckout:
#                 roomnumber = i.roomno.room_name
#                 invcdata = InvoiceItem.objects.filter(vendor=user,description=roomnumber).last()
#                 if invcdata:
#                     if Invoice.objects.filter(vendor=user,id=invcdata.invoice.id,foliostatus=False,customer__checkoutdate=desired_date):
#                         Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=2)
#                     else:
#                         # Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=0)
#                         pass
#                 else:
#                     pass

#             for i in dats:
#                 Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=2)
                

#             for i in bookedmisseddata:
#                 if i.roomno.checkin == 5 or i.roomno.checkin == 4:
#                     Rooms.objects.filter(vendor=user, id=i.roomno.id).update(checkin=0)
            
#             # filter cancel booking jo cancel hai vo yaha filter ho rahe hai
#             arriwalcanceldata = RoomBookAdvance.objects.filter(
                 
#                 Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
#                 Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
#             ).exclude(vendor=user,saveguestdata__action='book')
            
            
#             # or jo book hai vo yaha


#             for data in  arriwalcanceldata:
#                     if data.roomno.checkin not in [1, 2, 6]:
#                         data = Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=0)
                        
#             for data in arriwaldata:
#                 if data.roomno.checkin not in [1, 2, 5]:
#                     Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=4)
            

#             # Additional queries
#             checkintimedata = HotelProfile.objects.filter(vendor=user)
#             stayover = Rooms.objects.filter(vendor=user, checkin=1).count()
#             availablerooms = Rooms.objects.filter(vendor=user, checkin=0).count()
#             totalrooms = Rooms.objects.filter(vendor=user).count()
#             checkoutcount = Gueststay.objects.filter(vendor=user, checkoutdate__date=desired_date, checkoutstatus=True, checkoutdone=False).count()
#             checkincountdays = len(datsin)

#             # Create rooms dictionary
#             roomsdict = {}
#             for cat in category:
#                 roomsdict[cat.category_name] = [[room.room_name, room.checkin,room.is_clean] for room in rooms.filter(room_type=cat)]

#             cleanrooms = Rooms.objects.filter(vendor=user, is_clean=True).count()        
#             uncleanrooms = Rooms.objects.filter(vendor=user, is_clean=False).count()     

#             return render(request, 'homepage.html', {
#                 'active_page': 'homepage',
#                 'category': category,
#                 'rooms': rooms,
#                 'roomsdict': roomsdict,
#                 'tax': tax,
#                 'checkintimedata': checkintimedata,
#                 'stayover': stayover,
#                 'availablerooms': availablerooms,
#                 'checkincount': checkincountdays,
#                 'checkoutcount': checkoutcount,
#                 'arriwalcount': len(arriwaldata),
#                 'cleanrooms':cleanrooms,
#                 'uncleanrooms':uncleanrooms,

#             })
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)

def addtax(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            taxname = request.POST.get('taxname')
            taxcode = request.POST.get('taxcode')
            taxrate = request.POST.get('taxrate')

            if Taxes.objects.filter(vendor=user, taxname=taxname, taxrate=taxrate).exists():
                messages.error(request, 'Tax Already Exists!')
            else:
                Taxes.objects.create(vendor=user, taxname=taxname, taxcode=taxcode, taxrate=taxrate)
                messages.success(request, 'Tax Added')

            return redirect('setting')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def addcategory(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomcategory = request.POST.get('catname')
            if RoomsCategory.objects.filter(vendor=user, category_name=roomcategory).exists():
                messages.error(request, 'Category already exists')
            else:
                price = request.POST.get('price')
                taxcategory = request.POST.get('taxcategory')
                hsccode = request.POST.get('hsccode')

                RoomsCategory.objects.create(
                    vendor=user,
                    category_name=roomcategory,
                    catprice=price,
                    category_tax_id=taxcategory,
                    Hsn_sac=hsccode
                )

                messages.success(request, 'Category added successfully')

            return redirect('setting')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def updatecategory(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomcategory = request.POST.get('catname')
            categoryid = request.POST.get('categoryid')
            price = request.POST.get('price')
            taxcategory = request.POST.get('taxcategory')
            hsccode = request.POST.get('hsccode')

            profile = RoomsCategory.objects.get(vendor=user, id=categoryid)
            tax = Taxes.objects.get(vendor=user, id=taxcategory)

            profile.category_name = roomcategory
            profile.catprice = price
            profile.category_tax = tax
            profile.Hsn_sac = hsccode

             # Update the image only if a new one is provided

            profile.save()

            taxrate = tax.taxrate
            taxamount = int(price) * taxrate // 100

            Rooms.objects.filter(vendor=user, room_type_id=categoryid).update(price=price, tax=tax, tax_amount=taxamount)

            messages.success(request, 'Category update successful')

            return redirect('setting')

        else:
            return redirect('loginpage')
    
    except RoomsCategory.DoesNotExist:
        messages.error(request, 'Category does not exist')
    
    except Taxes.DoesNotExist:
        messages.error(request, 'Tax category does not exist')
    
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    return redirect('setting')

 

def addroom(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomname = request.POST.get('roomname')
            category = request.POST.get('category')
            maxperson = request.POST.get('maxperson')
            catdata = RoomsCategory.objects.get(vendor=user, id=category)
            tax_price = catdata.category_tax.taxrate
            roomprice = catdata.catprice
            taxprice = roomprice * tax_price // 100
            tax_type = catdata.category_tax.id
            
            if Rooms.objects.filter(vendor=user, room_name=roomname).exists():
                return redirect('rooms')
            else:
                Rooms.objects.create(
                    vendor=user,
                    room_name=roomname,
                    room_type_id=category,
                    price=roomprice,
                    tax_id=tax_type,
                    tax_amount=taxprice,
                    max_person=maxperson
                )

            category = RoomsCategory.objects.filter(vendor=user)
            roomdata = Rooms.objects.filter(vendor=user).order_by('room_name')
            tax = Taxes.objects.filter(vendor=user)
            
            return render(request, 'rooms.html', {
                'roomdata': roomdata,
                'active_page': 'rooms',
                'category': category,
                'tax': tax,
            })
        
        else:
            return redirect('loginpage')
    
    except RoomsCategory.DoesNotExist:
        messages.error(request, 'Selected category does not exist')
    
    except Taxes.DoesNotExist:
        messages.error(request, 'Tax category does not exist')
    
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('rooms')



def updaterooms(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomname = request.POST.get('roomname')
            category = request.POST.get('category')
            roomid = request.POST.get('roomid')
            maxperson = request.POST.get('maxperson')

            catdata = RoomsCategory.objects.get(vendor=user, id=category)
            tax_price = catdata.category_tax.taxrate
            roomprice = catdata.catprice
            taxprice = roomprice * tax_price // 100
            tax_type = catdata.category_tax.id

            if Rooms.objects.filter(vendor=user, id=roomid).exists():
                Rooms.objects.filter(vendor=user, id=roomid).update(
                    room_name=roomname,
                    room_type_id=category,
                    price=roomprice,
                    tax_id=tax_type,
                    tax_amount=taxprice,
                    max_person=maxperson
                )

            category = RoomsCategory.objects.filter(vendor=user)
            roomdata = Rooms.objects.filter(vendor=user).order_by('room_name')
            tax = Taxes.objects.filter(vendor=user)

            return render(request, 'rooms.html', {
                'roomdata': roomdata,
                'active_page': 'rooms',
                'category': category,
                'tax': tax,
            })
        
        else:
            return redirect('loginpage')
    
    except RoomsCategory.DoesNotExist:
        messages.error(request, 'Selected category does not exist')
    
    except Taxes.DoesNotExist:
        messages.error(request, 'Tax category does not exist')
    
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    return redirect('rooms')
    
def deleteroom(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            try:
                room = Rooms.objects.get(vendor=user, id=id)
                room.delete()
            except Rooms.DoesNotExist:
                pass  # Room with given ID does not exist, no action needed
            
            return redirect('rooms')
        else:
            return redirect('loginpage')
    
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('rooms')


def openroomclickformpage(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            room_data = Rooms.objects.filter(vendor=user, room_name=id)
            roomno = id
            cat_data = Rooms.objects.get(vendor=user, room_name=id)
            today = datetime.now().date()
            if Booking.objects.filter(vendor=user,room=cat_data,status="CHECK IN").last():
                messages.error(request,"Guest Stay In This Room!")
                bookmodeldata = Booking.objects.filter(vendor=user,room=cat_data,status="CHECK IN").last()
                if bookmodeldata.check_out_date <= today:
                    Rooms.objects.filter(vendor=user, id=cat_data.id).update(checkin=2)
                else:
                    Rooms.objects.filter(vendor=user, id=cat_data.id).update(checkin=1)
                # return redirect('weekviews')
                # Create a mutable copy of the request
                new_request = request
                new_request.method = "POST"  # Simulate a POST request
                new_request.POST = QueryDict(mutable=True)
                new_request.POST.update({
                    'bookingmodelid': int(bookmodeldata.id),
                })

                # Call the bookingdate function with the modified request
                return weekwiewfromfolioviews(new_request)
            bookingdates = Booking.objects.filter(vendor=user,room=cat_data,check_in_date__gt=today).first()
            
            roomscategory_id = cat_data.room_type.id
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            meal_plan = RatePlan.objects.filter(vendor=user,room_category=roomscategory_id)
            current_date = datetime.now()
            ratedata = RoomsInventory.objects.none()
            if VendorCM.objects.filter(vendor=user,dynamic_price_active=True) and RoomsInventory.objects.filter(vendor=user,date=current_date,room_category=roomscategory_id):
                ratedata = RoomsInventory.objects.filter(vendor=user,date=current_date,room_category=roomscategory_id)
            
            return render(request, 'bookroomclickpage.html', {
                'id': roomno,
                'room_data': room_data,
                'loyltydata': loyltydata,
                'meal_plan':meal_plan,
                'ratedata':ratedata,
                'bookingdates':bookingdates,
            })
        else:
            return redirect('loginpage')
    
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('homepage')

def weekwiewfromfolioviews(request):
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

def roomcheckin(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomno=id
            
            realroomnuo=Rooms.objects.get(vendor=user,room_name=roomno)
            Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
            category = RoomsCategory.objects.filter(vendor=user).all()
            category_count = RoomsCategory.objects.filter(vendor=user).count()
            rooms =Rooms.objects.filter(vendor=user).all()
            roomsdict=dict()
            for i in category:
                newlist=[]
                for j in rooms:
                    roomsdict[i.category_name] =newlist
                    if j.room_type == i:
                        lst=[]
                        lst.append(j.room_name)
                        lst.append(j.checkin)
                        newlist.append(lst)
                    else:
                        continue
            showtimeb = strftime("%Y-%m-%d %H:%M:%S", gmtime())
           
            return render(request,'index.html')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



# def addguestdata(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             guestname = request.POST.get('guestname')
#             guestphome = request.POST.get('guestphone')
#             guestemail = request.POST.get('guestemail')
#             guestcity = request.POST.get('guestcity')
#             guestcountry = request.POST.get('guestcountry')
#             guestidimg = request.FILES.get('guestid')
#             checkindate = request.POST.get('guestcheckindate')
#             checkoutdate = request.POST.get('guestcheckoutdate')
#             noofguest = request.POST.get('noofguest')
#             male = request.POST.get('male')
#             female = request.POST.get('female')
#             other = request.POST.get('other')
#             arival = request.POST.get('arival')
#             departure = request.POST.get('departure')
#             adults = request.POST.get('guestadults')
#             children = request.POST.get('guestchildren')
#             purposeofvisit = request.POST.get('Purpose')
#             roomno = request.POST.get('roomno')
#             subtotal = request.POST.get('subtotal')
#             total = request.POST.get('total')
#             tax = request.POST.get('tax')
#             state = request.POST.get('STATE')
#             rateplanname = request.POST.get('rateplanname')
#             rateplanprice = int(request.POST.get('rateplanprice'))
#             subtotalbyform = int(request.POST.get('subtotal'))
#             rateplan = request.POST.get('rateplan')
#             idtype = request.POST.get('idtype')
#             iddetails = request.POST.get('iddetails')
#             staydays = float(request.POST.get('staydays'))
#             subtotal=int(subtotal)
#             total=int(total)
#             # discount = float(request.POST.get('discount'))
#             roomdata = Rooms.objects.filter(vendor=user,room_name=roomno).all()
#             for i in roomdata:
#                     roomprice = i.price + rateplanprice
#                     tax_rate = i.tax.taxrate
#                     roomname = i.room_name
#                     tax_amount = i.tax_amount
#                     roomtype = i.room_type.id
#                     room_details = i.room_type.category_name
#             discount = abs(roomprice*staydays - subtotalbyform)
#             checkmoredatastatus = request.POST.get('checkmoredatastatus')
#             current_date = datetime.now()
#             userstatedata = HotelProfile.objects.get(vendor=user)
#             userstate = userstatedata.zipcode
#             if Rooms.objects.filter(vendor=user,room_name=roomno,checkin=0).exists():
#                 Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
#                 taxtypes = "GST"
#                 guestdata = Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
#                                         checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
#                                         ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=1
#                                         ,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,rate_plan=rateplanname,
#                                         channel='PMS',saveguestid=None,male=male,female=female,transg=other,dp=departure,ar=arival)
#                 gsid=guestdata.id
#                 if checkmoredatastatus == 'on':
#                     moreguestname = request.POST.get('moreguestname')
#                     moreguestphone = request.POST.get('moreguestphone',0)
#                     moreguestaddress = request.POST.get('moreguestaddress')
#                     if moreguestphone == "":
#                         moreguestphone = 0
#                     else:
#                         pass
#                     MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
#                                                 another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                    
                
                
#                 gstname = "GST"+ str(tax_rate)
                
#                 divideamt = tax_amount / 2
#                 tax_rate = tax_rate / 2
#                 totalitemamount = roomprice * staydays
#                 subtotalamount = totalitemamount - discount
#                 gstamount = (subtotalamount * tax_rate) /100
#                 sgstamount = (subtotalamount * tax_rate) /100
#                 grandtotal_amount = subtotalamount + gstamount + sgstamount
#                 cat = RoomsCategory.objects.get(vendor=user,id=roomtype)
#                 hsnno = cat.Hsn_sac
            
#                 room_details = roomname
              
#                 daystotalprice = totalitemamount
#                 #  for invoice number
#                 current_date = datetime.now().date()
#                 invoice_number = ""
#                 invcitemtotal = (totalitemamount *(tax_rate * 2) /100) + totalitemamount

#                 Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
#                                                     invoice_number=invoice_number,invoice_date=checkindate,total_item_amount=subtotalamount,discount_amount=0.00,
#                                                     subtotal_amount=subtotalamount,gst_amount=gstamount,sgst_amount=sgstamount,
#                                                     grand_total_amount=grandtotal_amount,modeofpayment='',room_no=roomname,
#                                                     taxtype=taxtypes,accepted_amount=0.00 ,Due_amount=grandtotal_amount,)
                
#                 totaltaxesamt = sgstamount + gstamount
#                 taxSlab.objects.create(vendor=user,invoice=Invoiceid,tax_rate_name=gstname,
#                         cgst=tax_rate,sgst=tax_rate,cgst_amount=gstamount,sgst_amount=sgstamount,total_amount=totaltaxesamt)

#                 rateplandata=RatePlan.objects.filter(vendor=user,id=rateplan).first()
#                 pprice = subtotalamount / staydays
#                 msecs = cat.category_name + " : " + rateplanname + " " + rateplandata.rate_plan_code  + " " + " for "+ str(adults) + " adults " + " " +   " and " + str(children) + " " + "Child"
#                 invoiceitem = InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=room_details,quantity_likedays=staydays,
#                                         mdescription=msecs,is_room=True,price=pprice,cgst_rate=tax_rate,sgst_rate=tax_rate,hsncode=hsnno,total_amount=grandtotal_amount,
#                                         cgst_rate_amount=gstamount,sgst_rate_amount=sgstamount,totalwithouttax=daystotalprice)  
#                 Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
#                 roominventorydata = RoomsInventory.objects.filter(vendor=user,date__range = [checkindate,checkoutdate])
                
                
#                 # add to bookings
#                 roomids = Rooms.objects.get(vendor=user,room_name=roomno)
#                 current_time = datetime.now().time()
#                 noon_time_str = "12:00 PM"
#                 noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
#                 Booking.objects.create(vendor=user,room_id=roomids.id,guest_name=guestname,check_in_date=checkindate,
#                                       check_out_date=checkoutdate,check_in_time= current_time,segment="PMS",
#                                       totalamount=grandtotal_amount,totalroom='1',check_out_time=noon_time,
#                                       gueststay=guestdata,advancebook=None,status="CHECK IN")

#                 # Convert date strings to date objects
#                 checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
#                 checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

#                 # Generate the list of all dates between check-in and check-out (inclusive)
#                 all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

#                 # Query the RoomsInventory model to check if records exist for all those dates
#                 existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

#                 # Get the list of dates that already exist in the inventory
#                 existing_dates = set(existing_inventory.values_list('date', flat=True))

#                 # Identify the missing dates by comparing all_dates with existing_dates
#                 missing_dates = [date for date in all_dates if date not in existing_dates]

#                 # If there are missing dates, create new entries for those dates in the RoomsInventory model
#                 roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
             
                
              
#                 for inventory in existing_inventory:
#                     if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
#                         # Update room availability and booked rooms
#                         inventory.total_availibility -= 1
#                         inventory.booked_rooms += 1

#                         # Calculate total rooms
#                         total_rooms = inventory.total_availibility + inventory.booked_rooms

#                         # Recalculate the occupancy based on the updated values
#                         if total_rooms > 0:
#                             inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
#                         else:
#                             inventory.occupancy = 0  # Avoid division by zero if no rooms exist

#                         # Save the updated inventory
#                         inventory.save()
                
#                 catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
#                 totalrooms = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
#                 occupancccy = (1 *100 //totalrooms)
#                 if missing_dates:
#                     for missing_date in missing_dates:
                       
#                             RoomsInventory.objects.create(
#                                 vendor=user,
#                                 date=missing_date,
#                                 room_category_id=roomtype,  # Use the appropriate `roomtype` or other identifier here
#                                 total_availibility=roomcount-1,       # Set according to your logic
#                                 booked_rooms=1,                # Set according to your logic
#                                 price=catdatas.catprice,
#                                 occupancy=occupancccy,
#                             )
                    
#                 else:
#                     pass

#                 # api calling backend automatically
#                             # Start the long-running task in a separate thread
#                 if VendorCM.objects.filter(vendor=user):
#                     start_date = str(checkindate)
#                     end_date = str(checkoutdate)
#                     thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                     thread.start()
#                     # for dynamic pricing
#                     if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                         thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                         thread.start()
#                     else:
#                         pass

#                 else:
#                     pass
                
                
#                 userid = guestdata.id
#                 url = reverse('invoicepage', args=[userid])
#                 return redirect(url)
#                 # return redirect('foliobillingpage')
#             else:
#                 return redirect('foliobillingpage')
#         else:
#             return redirect('loginpage') 
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)
    


# def addguestdata(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             guestname = request.POST.get('guestname')
#             guestphome = request.POST.get('guestphone')
#             guestemail = request.POST.get('guestemail')
#             guestcity = request.POST.get('guestcity')
#             guestcountry = request.POST.get('guestcountry')
#             guestidimg = request.FILES.get('guestid')
#             checkindate = request.POST.get('guestcheckindate')
#             checkoutdate = request.POST.get('guestcheckoutdate')
#             noofguest = request.POST.get('noofguest')
#             male = request.POST.get('male')
#             female = request.POST.get('female')
#             other = request.POST.get('other')
#             arival = request.POST.get('arival')
#             departure = request.POST.get('departure')
#             adults = request.POST.get('guestadults')
#             children = request.POST.get('guestchildren')
#             purposeofvisit = request.POST.get('Purpose')
#             roomno = request.POST.get('roomno')
#             subtotal = request.POST.get('subtotal')
#             total = request.POST.get('total')
#             tax = request.POST.get('tax')
#             state = request.POST.get('STATE')
#             rateplanname = request.POST.get('rateplanname')
#             rateplanprice = int(request.POST.get('rateplanprice'))
#             subtotalbyform = int(request.POST.get('subtotal'))
#             rateplan = request.POST.get('rateplan')
#             idtype = request.POST.get('idtype')
#             iddetails = request.POST.get('iddetails')
#             staydays = float(request.POST.get('staydays'))
#             subtotal=int(subtotal)
#             total=int(total)
#             # discount = float(request.POST.get('discount'))
#             roomdata = Rooms.objects.filter(vendor=user,room_name=roomno).all()
#             for i in roomdata:
#                     roomprice = i.price + rateplanprice
#                     tax_rate = i.tax.taxrate
#                     roomname = i.room_name
#                     tax_amount = i.tax_amount
#                     roomtype = i.room_type.id
#                     room_details = i.room_type.category_name
#             discount = abs(roomprice*staydays - subtotalbyform)
#             checkmoredatastatus = request.POST.get('checkmoredatastatus')
#             current_date = datetime.now()
#             userstatedata = HotelProfile.objects.get(vendor=user)
#             userstate = userstatedata.zipcode
#             if Rooms.objects.filter(vendor=user,room_name=roomno,checkin=0).exists():
#                 Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
#                 divideamt = tax_amount / 2
#                 tax_rate = tax_rate / 2
#                 # totalitemamount = roomprice * staydays
#                 # subtotalamount = totalitemamount - discount
#                 # gstamount = (subtotalamount * tax_rate) /100
#                 # sgstamount = (subtotalamount * tax_rate) /100
#                 # grandtotal_amount = subtotalamount + gstamount + sgstamount
#                 cat = RoomsCategory.objects.get(vendor=user,id=roomtype)
                
            
#                 room_details = roomname
              
#                 # daystotalprice = totalitemamount
#                 #  for invoice number
#                 current_date = datetime.now().date()
#                 invoice_number = ""
#                 # invcitemtotal = (totalitemamount *(tax_rate * 2) /100) + totalitemamount

#                 #new tax working here
#                 print(int(total),int(staydays) ,"check this ")

#                 exceptedsttl = int(total) / int(staydays)   
#                 findamtsonly = float(exceptedsttl) / (1 + (tax_rate * 2) / 100)  # Fix: Divide by (1 + tax_rate/100) to calculate the base amount
#                 foundnetamts = findamtsonly  # Base amount after removing tax
#                 invoicetotalamount = foundnetamts * int(staydays) 
                


#                 if foundnetamts > 7500 and int(tax_rate * 2) == 18:
#                     GST_AMOUNT = invoicetotalamount * 18 /100
#                     CGST_AMOUNT = GST_AMOUNT / 2
#                     Sgst_AMOUNT = GST_AMOUNT / 2 
#                     gstname = "GST18"
#                     tax_rate_per = 9.0
#                     print("tax bhi 18 hi hai or acual bhi")

#                 elif foundnetamts <= 7500 and int(tax_rate * 2) == 18:
#                     GST_AMOUNT = invoicetotalamount * 12 /100
#                     CGST_AMOUNT = GST_AMOUNT / 2
#                     Sgst_AMOUNT = GST_AMOUNT / 2 
#                     gstname = "GST12"
#                     tax_rate_per = 6.0
#                     print("tax 18 hai lekin 12 k slab me aara hai",foundnetamts)

#                 elif foundnetamts > 7500 and int(tax_rate * 2) == 12:
#                     print("amount jayda hai or tax 12 hai 18 lagega")
#                     # Recalculate with 18% tax
#                     againfindsonly = float(exceptedsttl) / (1 + (9 * 2) / 100)  # Fix: Divide by (1 + (18/100)) for 18% tax
#                     againfoundnetamts = againfindsonly
#                     invoicetotalamount = againfoundnetamts * int(staydays) 
#                     GST_AMOUNT = invoicetotalamount * 18 /100
#                     CGST_AMOUNT = GST_AMOUNT / 2
#                     Sgst_AMOUNT = GST_AMOUNT / 2 
#                     gstname = "GST18"
#                     tax_rate_per = 9.0
#                     foundnetamts = againfoundnetamts
#                     print(againfoundnetamts, "again foundable amt")
#                 elif foundnetamts <= 7500 and int(tax_rate * 2) == 12:
#                     GST_AMOUNT = invoicetotalamount * 12 /100
#                     CGST_AMOUNT = GST_AMOUNT / 2
#                     Sgst_AMOUNT = GST_AMOUNT / 2 
#                     gstname = "GST12"
#                     tax_rate_per = 6.0
#                     print(foundnetamts, "tax rate bhi 12 hi hai and amount dekho")


#                 taxtypes = "GST"
#                 grabd_total_amount = invoicetotalamount + GST_AMOUNT
#                 guestdata = Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
#                                         checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
#                                         ,purposeofvisit=purposeofvisit,roomno=roomno,tax=gstname,discount=0.00,subtotal=invoicetotalamount,total=grabd_total_amount,noofrooms=1
#                                         ,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,rate_plan=rateplanname,
#                                         channel='PMS',saveguestid=None,male=male,female=female,transg=other,dp=departure,ar=arival)
#                 gsid=guestdata.id
#                 if checkmoredatastatus == 'on':
#                     moreguestname = request.POST.get('moreguestname')
#                     moreguestphone = request.POST.get('moreguestphone',0)
#                     moreguestaddress = request.POST.get('moreguestaddress')
#                     if moreguestphone == "":
#                         moreguestphone = 0
#                     else:
#                         pass
#                     MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
#                                                 another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                    

                
#                 Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
#                                                     invoice_number=invoice_number,invoice_date=checkindate,total_item_amount=invoicetotalamount,discount_amount=0.00,
#                                                     subtotal_amount=invoicetotalamount,gst_amount=CGST_AMOUNT,sgst_amount=Sgst_AMOUNT,
#                                                     grand_total_amount=grabd_total_amount,modeofpayment='',room_no=roomname,
#                                                     taxtype=taxtypes,accepted_amount=0.00 ,Due_amount=grabd_total_amount,taxable_amount=invoicetotalamount)
                
#                 totaltaxesamt = GST_AMOUNT
#                 taxSlab.objects.create(vendor=user,invoice=Invoiceid,tax_rate_name=gstname,
#                         cgst=tax_rate_per,sgst=tax_rate_per,cgst_amount=CGST_AMOUNT,sgst_amount=Sgst_AMOUNT,total_amount=totaltaxesamt)

                
#                 if Taxes.objects.filter(vendor=user,taxname=gstname).exists():
#                     taxnames = Taxes.objects.filter(vendor=user,taxname=gstname).last()
#                     HSNcode = taxnames.taxcode
#                 else:
#                     HSNcode=''
#                 rateplandata=RatePlan.objects.filter(vendor=user,id=rateplan).first()
               
#                 msecs = cat.category_name + " : " + rateplanname + " " + rateplandata.rate_plan_code  + " " + " for "+ str(adults) + " adults " + " " +   " and " + str(children) + " " + "Child"
#                 invoiceitem = InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=room_details,quantity_likedays=staydays,
#                                         mdescription=msecs,is_room=True,price=foundnetamts,cgst_rate=tax_rate_per,sgst_rate=tax_rate_per,hsncode=HSNcode,total_amount=grabd_total_amount,
#                                         cgst_rate_amount=CGST_AMOUNT,sgst_rate_amount=Sgst_AMOUNT,totalwithouttax=invoicetotalamount)  
                
#                 # end new working here


#                 Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
#                 roominventorydata = RoomsInventory.objects.filter(vendor=user,date__range = [checkindate,checkoutdate])
                
                
#                 # add to bookings
#                 roomids = Rooms.objects.get(vendor=user,room_name=roomno)
#                 current_time = datetime.now().time()
#                 noon_time_str = "12:00 PM"
#                 noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
#                 Booking.objects.create(vendor=user,room_id=roomids.id,guest_name=guestname,check_in_date=checkindate,
#                                       check_out_date=checkoutdate,check_in_time= current_time,segment="PMS",
#                                       totalamount=grabd_total_amount,totalroom='1',check_out_time=noon_time,
#                                       gueststay=guestdata,advancebook=None,status="CHECK IN")

#                 # Convert date strings to date objects
#                 checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
#                 checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

#                 # Generate the list of all dates between check-in and check-out (inclusive)
#                 all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

#                 # Query the RoomsInventory model to check if records exist for all those dates
#                 existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

#                 # Get the list of dates that already exist in the inventory
#                 existing_dates = set(existing_inventory.values_list('date', flat=True))

#                 # Identify the missing dates by comparing all_dates with existing_dates
#                 missing_dates = [date for date in all_dates if date not in existing_dates]

#                 # If there are missing dates, create new entries for those dates in the RoomsInventory model
#                 roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
             
                
              
#                 for inventory in existing_inventory:
#                     if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
#                         # Update room availability and booked rooms
#                         inventory.total_availibility -= 1
#                         inventory.booked_rooms += 1

#                         # Calculate total rooms
#                         total_rooms = inventory.total_availibility + inventory.booked_rooms

#                         # Recalculate the occupancy based on the updated values
#                         if total_rooms > 0:
#                             inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
#                         else:
#                             inventory.occupancy = 0  # Avoid division by zero if no rooms exist

#                         # Save the updated inventory
#                         inventory.save()
                
#                 catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
#                 totalrooms = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
#                 occupancccy = (1 *100 //totalrooms)
#                 if missing_dates:
#                     for missing_date in missing_dates:
                       
#                             RoomsInventory.objects.create(
#                                 vendor=user,
#                                 date=missing_date,
#                                 room_category_id=roomtype,  # Use the appropriate `roomtype` or other identifier here
#                                 total_availibility=roomcount-1,       # Set according to your logic
#                                 booked_rooms=1,                # Set according to your logic
#                                 price=catdatas.catprice,
#                                 occupancy=occupancccy,
#                             )
                    
#                 else:
#                     pass

#                 # api calling backend automatically
#                             # Start the long-running task in a separate thread
#                 if VendorCM.objects.filter(vendor=user):
#                     start_date = str(checkindate)
#                     end_date = str(checkoutdate)
#                     thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                     thread.start()
#                     # for dynamic pricing
#                     if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                         thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                         thread.start()
#                     else:
#                         pass

#                 else:
#                     pass
                
                
#                 userid = guestdata.id
#                 url = reverse('invoicepage', args=[userid])
#                 return redirect(url)
#                 # return redirect('foliobillingpage')
#             else:
#                 return redirect('foliobillingpage')
#         else:
#             return redirect('loginpage') 
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)


# def addguestdatafromadvanceroombook(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             guestname = request.POST.get('guestname')
#             guestphome = request.POST.get('guestphone')
#             guestemail = request.POST.get('guestemail')
#             guestcity = request.POST.get('guestcity')
#             guestcountry = request.POST.get('guestcountry')
#             guestidimg = request.FILES.get('guestid')
#             checkindate = request.POST.get('guestcheckindate')
#             checkoutdate = request.POST.get('guestcheckoutdate')
#             noofguest = request.POST.get('noofguest')
#             male = request.POST.get('male')
#             female = request.POST.get('female')
#             other = request.POST.get('other')
#             arival = request.POST.get('arival')
#             departure = request.POST.get('departure')
#             adults = request.POST.get('guestadults')
#             children = request.POST.get('guestchildren')
#             purposeofvisit = request.POST.get('Purpose')
#             roomno = request.POST.get('roomno')
#             subtotal = request.POST.get('subtotal')
#             total = request.POST.get('total')
#             tax = request.POST.get('tax')
#             noofrooms = request.POST.get('noofrooms')
#             saveguestdata = request.POST.get('saveguestdata')
#             msid = saveguestdata
#             SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestdata).update(checkinstatus=True)
#             checkmoredatastatus = request.POST.get('checkmoredatastatus')
#             roomalldefaultcheckinbutton = request.POST.get('roomalldefaultcheckinbutton')
#             discount = request.POST.get('discount')
#             state = request.POST['STATE']
#             idtype = request.POST.get('idtype')
#             iddetails = request.POST.get('iddetails')
#             subtotal=int(subtotal)
#             paidstatus = request.POST.get('paidstatus')
#             total=int(total)
#             saveguestdata =  SaveAdvanceBookGuestData.objects.get(vendor=user,id=saveguestdata)
#             guestcheckinstatus= False
#             userstatedata = HotelProfile.objects.get(vendor=user)
#             userstate = userstatedata.zipcode
#             roomsdatas = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestdata)
#             paymentstatus = saveguestdata.Payment_types
#             checkindoornot = True
#             for check in roomsdatas:
#                 if check.roomno.checkin == 1 or check.roomno.checkin == 2:
#                     checkindoornot = False
#             if checkindoornot == True:
                
#                 taxtypes = "GST"
                
#                 if guestcheckinstatus is True:
                    
#                     messages.error(request,'recently Check In this Room With Same Data Please Change Address Mobile And Guest Name heckIn CheckOut Date / Room No to CheckIn this Room')
#                 else:
#                     current_date = datetime.now()
#                     rateplansdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()
#                     guestdata=Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
#                                                 checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
#                                                 ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=noofrooms
#                                             ,rate_plan=rateplansdata.rateplan_code,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,saveguestid=saveguestdata.id,channel=saveguestdata.channal.channalname,
#                                             male=male,female=female,transg=other,dp=departure,ar=arival)
#                     Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
#                                                 invoice_number="",invoice_date=checkindate,total_item_amount=0.0,discount_amount=discount,
#                                                         subtotal_amount=0.0,gst_amount=0.0,sgst_amount=0.0,accepted_amount=0.00,
#                                                         Due_amount=0.00,grand_total_amount=0.0,modeofpayment=paymentstatus,room_no=0.0,taxtype=taxtypes)
#                     if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid,bookingguestphone=guestphome).exists():
#                         pass
#                     else:
#                         SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid).update(bookingguestphone=guestphome)
                    
#                     totalrooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
#                     staydays = saveguestdata.staydays
#                     for i in totalrooms:
#                             rid = i.roomno.id
#                             roomdata = Rooms.objects.get(vendor=user,id=rid)
#                             selllprice = i.sell_rate
#                             gstrate = roomdata.tax.taxrate/2
#                             hsn = roomdata.room_type.Hsn_sac
#                             if selllprice >7500 and gstrate==6.0:
#                                 if Taxes.objects.filter(vendor=user,taxrate=18).exists():
#                                     gstrate = 9.00
#                                     taxesdata = Taxes.objects.filter(vendor=user,taxrate=18).last()
#                                     hsn = taxesdata.taxcode
#                                 else:
#                                     Taxes.objects.create(vendor=user,taxrate=18,taxname='GST18',taxcode=18)
#                                     hsn = ''
#                                     gstrate = 9.00
#                             elif selllprice <=7500 and gstrate == 9.00:
#                                 gstrate = 6.00
#                                 taxesdata = Taxes.objects.filter(vendor=user,taxrate=12).last()
#                                 hsn = taxesdata.taxcode

#                             else:
#                                 pass
#                             # taxes=selllprice*roomdata.tax.taxrate/100
#                             # toalamtitem = selllprice + taxes 
#                             # toalamtitem = toalamtitem * staydays
#                             # hsn = roomdata.room_type.Hsn_sac
#                             # gstrate = roomdata.tax.taxrate/2
#                             # print(taxes,"taxes checking on code")
                    
#                             taxes=selllprice*(gstrate*2)/100
#                             toalamtitem = selllprice + taxes 
#                             print(toalamtitem,"toTAL ITEM AMOUNT")
#                             toalamtitem = toalamtitem * staydays
#                             print(toalamtitem,"TOTAL ITEM AMOUNT BAD ME ")
                            
                            
#                             print(taxes,"taxes checking on code")

#                             daystotalprice = selllprice * staydays
                            
                            
#                             checktaxrate = float(gstrate)
#                             individualtaxamt = taxes / 2
#                             bydaystaxamt = individualtaxamt * staydays
#                             totaltaxamounts = taxes * staydays
                            
#                             if taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).exists():
                                
#                                 taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).update(
#                                         cgst_amount=F('cgst_amount') + bydaystaxamt,
#                                         sgst_amount=F('sgst_amount') + bydaystaxamt,
#                                         total_amount=F('total_amount') + totaltaxamounts
#                                 )
#                             else:
#                                 taxname = "GST"+str(int(checktaxrate*2))
#                                 taxSlab.objects.create(vendor=user,invoice=Invoiceid,cgst=checktaxrate,
#                                         sgst=checktaxrate,tax_rate_name=taxname,cgst_amount=bydaystaxamt,
#                                         sgst_amount=bydaystaxamt,total_amount=totaltaxamounts)
                               
                            
#                             if RatePlan.objects.filter(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
#                                             max_persons=i.adults,childmaxallowed=i.children):
#                                 ipbs = RatePlan.objects.get(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
#                                             max_persons=i.adults,childmaxallowed=i.children)
#                                 base_price = ipbs.base_price + roomdata.price
#                                 msecs = roomdata.room_type.category_name + " "+ ipbs.rate_plan_code + " : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
#                                 InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)
#                             else:
#                                 if RatePlanforbooking.objects.filter(vendor=user,rate_plan_name=i.rateplan_code):
#                                     pdatas= RatePlanforbooking.objects.get(vendor=user,rate_plan_name=i.rateplan_code)
#                                     base_price = i.adults * (pdatas.base_price) + roomdata.price
#                                     msecs = roomdata.room_type.category_name + " " + pdatas.rate_plan_code +" : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
#                                     InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)

#                                 else:

#                                     InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription="ONLY ROOM",hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)
                            

#                     totalitemamount = saveguestdata.amount_before_tax + float(saveguestdata.discount)
#                     discamts = float(saveguestdata.discount)
#                     subttlamt = saveguestdata.amount_before_tax
#                     gtamts = saveguestdata.amount_after_tax
#                     taxamts = saveguestdata.tax/2 

#                     fisrroom = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()

                    
#                     if saveguestdata.segment == 'OTA' and saveguestdata.pah==False:
#                         otagstin = saveguestdata.channal.company_gstin
#                         companyname = saveguestdata.channal.channalname
#                         Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(
#                             customer_gst_number=otagstin,customer_company=companyname)
                        
#                     else:
#                         pass

#                     Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(total_item_amount=totalitemamount,
#                                     discount_amount=discamts,subtotal_amount=subttlamt,
#                                     modeofpayment=paymentstatus,grand_total_amount=gtamts,
#                                     gst_amount=taxamts,sgst_amount=taxamts,room_no=fisrroom.roomno.room_name,
#                                     taxable_amount=subttlamt)
                            

                            


                   
                    
#                     if InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id).exists():
#                         adpaymentdata = InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id)
                        
#                         advncspt = 0
#                         chechtotalamt = int(float(saveguestdata.total_amount))
#                         for i in adpaymentdata:
#                             InvoicesPayment.objects.filter(vendor=user,id=i.id).update(invoice=Invoiceid)
#                             invcdatas= InvoicesPayment.objects.get(vendor=user,id=i.id)
#                             advncspt = advncspt + int(float(invcdatas.payment_amount))
                               
#                         if advncspt == chechtotalamt:
#                                 Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                                  Due_amount=0.00,accepted_amount=float(advncspt)
#                                 )
#                         elif advncspt < chechtotalamt:
#                                 dueamts = chechtotalamt - advncspt
#                                 Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                                  Due_amount=float(dueamts),accepted_amount=float(advncspt)
#                                 )
#                     else:
#                         Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                              Due_amount=float(saveguestdata.total_amount),accepted_amount=0.00
#                             )
                        
                 
                
                


#                     if checkmoredatastatus == 'on':
#                         moreguestname = request.POST.get('moreguestname')
#                         moreguestphone = request.POST.get('moreguestphone')
#                         if moreguestphone == "":
#                             moreguestphone = 0
#                         else:
#                             pass
#                         moreguestaddress = request.POST.get('moreguestaddress')
#                         MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
#                                                     another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                     

            
                
#                     today = datetime.now().date()
#                     roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
#                     #  roomdata = Room_history.objects.filter(vendor=user,checkindate__range=[checkindate,checkoutdate],bookingstatus=True,bookingguestphone=guestphome).all()
#                     if roomalldefaultcheckinbutton == 'on':
#                         for data in roomdata:
                      
#                             Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=5)
#                             roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
                      
#                             RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(partly_checkin=True)
#                             Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(
#                                                                              gueststay=guestdata)
                            
#                         return redirect('todaybookingpage')
                            
                        
#                     else:
#                         for data in roomdata:
                           
#                             roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
#                             Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=1)
                      
#                             RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(checkinstatus=True,
#                                                 bookingdate=today)
#                             ctime = datetime.now().time()
#                             Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(status="CHECK IN",check_in_time=ctime,
#                                                                              gueststay=guestdata)
                        
#                         userid = guestdata.id
#                         url = reverse('invoicepage', args=[userid])
#                         return redirect(url)

                

                
#             else:
#                 messages.error(request,"Please check out the room that has not been checked out yet for the same guest before you can check in to a new room.")
#                 return redirect('todaybookingpage')
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)




# def addguestdatafromadvanceroombook(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             guestname = request.POST.get('guestname')
#             guestphome = request.POST.get('guestphone')
#             guestemail = request.POST.get('guestemail')
#             guestcity = request.POST.get('guestcity')
#             guestcountry = request.POST.get('guestcountry')
#             guestidimg = request.FILES.get('guestid')
#             checkindate = request.POST.get('guestcheckindate')
#             checkoutdate = request.POST.get('guestcheckoutdate')
#             noofguest = request.POST.get('noofguest')
#             male = request.POST.get('male')
#             female = request.POST.get('female')
#             other = request.POST.get('other')
#             arival = request.POST.get('arival')
#             departure = request.POST.get('departure')
#             adults = request.POST.get('guestadults')
#             children = request.POST.get('guestchildren')
#             purposeofvisit = request.POST.get('Purpose')
#             roomno = request.POST.get('roomno')
#             subtotal = request.POST.get('subtotal')
#             total = request.POST.get('total')
#             tax = request.POST.get('tax')
#             noofrooms = request.POST.get('noofrooms')
#             saveguestdata = request.POST.get('saveguestdata')
#             msid = saveguestdata
#             SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestdata).update(checkinstatus=True)
#             checkmoredatastatus = request.POST.get('checkmoredatastatus')
#             roomalldefaultcheckinbutton = request.POST.get('roomalldefaultcheckinbutton')
#             discount = request.POST.get('discount')
#             state = request.POST['STATE']
#             idtype = request.POST.get('idtype')
#             iddetails = request.POST.get('iddetails')
#             subtotal=int(subtotal)
#             paidstatus = request.POST.get('paidstatus')
#             total=int(total)
#             saveguestdata =  SaveAdvanceBookGuestData.objects.get(vendor=user,id=saveguestdata)
#             guestcheckinstatus= False
#             userstatedata = HotelProfile.objects.get(vendor=user)
#             userstate = userstatedata.zipcode
#             roomsdatas = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestdata)
#             paymentstatus = saveguestdata.Payment_types
#             checkindoornot = True
#             for check in roomsdatas:
#                 if check.roomno.checkin == 1 or check.roomno.checkin == 2:
#                     checkindoornot = False
#             if checkindoornot == True:
                
#                 taxtypes = "GST"
                
#                 if guestcheckinstatus is True:
                    
#                     messages.error(request,'recently Check In this Room With Same Data Please Change Address Mobile And Guest Name heckIn CheckOut Date / Room No to CheckIn this Room')
#                 else:
#                     current_date = datetime.now()
#                     rateplansdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()
#                     guestdata=Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
#                                                 checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
#                                                 ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=noofrooms
#                                             ,rate_plan=rateplansdata.rateplan_code,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,saveguestid=saveguestdata.id,channel=saveguestdata.channal.channalname,
#                                             male=male,female=female,transg=other,dp=departure,ar=arival)
#                     Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
#                                                 invoice_number="",invoice_date=checkindate,total_item_amount=0.0,discount_amount=discount,
#                                                         subtotal_amount=0.0,gst_amount=0.0,sgst_amount=0.0,accepted_amount=0.00,
#                                                         Due_amount=0.00,grand_total_amount=0.0,modeofpayment=paymentstatus,room_no=0.0,taxtype=taxtypes)
#                     if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid,bookingguestphone=guestphome).exists():
#                         pass
#                     else:
#                         SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid).update(bookingguestphone=guestphome)
                    
#                     totalrooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
#                     staydays = saveguestdata.staydays
#                     for i in totalrooms:
#                             rid = i.roomno.id
#                             roomdata = Rooms.objects.get(vendor=user,id=rid)
#                             selllprice = i.sell_rate
#                             gstrate = roomdata.tax.taxrate/2
#                             hsn = roomdata.room_type.Hsn_sac
#                             if selllprice >7500 and gstrate==6.0:
#                                 if Taxes.objects.filter(vendor=user,taxrate=18).exists():
#                                     gstrate = 9.00
#                                     taxesdata = Taxes.objects.filter(vendor=user,taxrate=18).last()
#                                     hsn = taxesdata.taxcode
#                                 else:
#                                     Taxes.objects.create(vendor=user,taxrate=18,taxname='GST18',taxcode=18)
#                                     hsn = ''
#                                     gstrate = 9.00
#                             elif selllprice <=7500 and gstrate == 9.00:
#                                 gstrate = 6.00
#                                 taxesdata = Taxes.objects.filter(vendor=user,taxrate=12).last()
#                                 hsn = taxesdata.taxcode

#                             else:
#                                 pass

#                             # if selllprice > 7500:
#                             #     print("yha aayaya nhi")
#                             #     if Taxes.objects.filter(vendor=user,taxrate=18).exists():
#                             #         gstrate = 9.00
#                             #         taxesdata = Taxes.objects.filter(vendor=user,taxrate=18).last()
#                             #         hsn = taxesdata.taxcode
#                             #     else:
#                             #         Taxes.objects.create(vendor=user,taxrate=18,taxname='GST18',taxcode=18)
#                             #         hsn = ''
#                             #         gstrate = 9.00

#                             # elif selllprice <= 7500:
#                             #     gstrate = 6.00
#                             #     taxesdata = Taxes.objects.filter(vendor=user,taxrate=12).last()
#                             #     hsn = taxesdata.taxcode
#                             # else:
#                             #     extraminusamount = selllprice - 8400
#                             #     selllprice = 7500 
#                             #     gstrate = 6.00
#                             #     taxesdata = Taxes.objects.filter(vendor=user,taxrate=12).last()
#                             #     hsn = taxesdata.taxcode

                    
#                             taxes=selllprice*(gstrate*2)/100
#                             toalamtitem = selllprice + taxes 
#                             print(toalamtitem,"toTAL ITEM AMOUNT")
#                             toalamtitem = toalamtitem * staydays
#                             print(toalamtitem,"TOTAL ITEM AMOUNT BAD ME ")
                            
                            
#                             print(taxes,"taxes checking on code")

#                             daystotalprice = selllprice * staydays
                            
                            
#                             checktaxrate = float(gstrate)
#                             individualtaxamt = taxes / 2
#                             bydaystaxamt = individualtaxamt * staydays
#                             totaltaxamounts = taxes * staydays
                            
#                             if taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).exists():
                                
#                                 taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).update(
#                                         cgst_amount=F('cgst_amount') + bydaystaxamt,
#                                         sgst_amount=F('sgst_amount') + bydaystaxamt,
#                                         total_amount=F('total_amount') + totaltaxamounts
#                                 )
#                             else:
#                                 taxname = "GST"+str(int(checktaxrate*2))
#                                 taxSlab.objects.create(vendor=user,invoice=Invoiceid,cgst=checktaxrate,
#                                         sgst=checktaxrate,tax_rate_name=taxname,cgst_amount=bydaystaxamt,
#                                         sgst_amount=bydaystaxamt,total_amount=totaltaxamounts)
                               
                            
#                             if RatePlan.objects.filter(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
#                                             max_persons=i.adults,childmaxallowed=i.children):
#                                 ipbs = RatePlan.objects.get(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
#                                             max_persons=i.adults,childmaxallowed=i.children)
#                                 base_price = ipbs.base_price + roomdata.price
#                                 msecs = roomdata.room_type.category_name + " "+ ipbs.rate_plan_code + " : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
#                                 InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)
#                             else:
#                                 if RatePlanforbooking.objects.filter(vendor=user,rate_plan_name=i.rateplan_code):
#                                     pdatas= RatePlanforbooking.objects.get(vendor=user,rate_plan_name=i.rateplan_code)
#                                     base_price = i.adults * (pdatas.base_price) + roomdata.price
#                                     msecs = roomdata.room_type.category_name + " " + pdatas.rate_plan_code +" : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
#                                     InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)

#                                 else:

#                                     InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
#                                                         mdescription="ONLY ROOM",hsncode=hsn,quantity_likedays=staydays,price=selllprice,
#                                                         total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
#                                                         is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice)
                            

#                     totalitemamount = saveguestdata.amount_before_tax + float(saveguestdata.discount)
#                     discamts = float(saveguestdata.discount)
#                     subttlamt = saveguestdata.amount_before_tax
#                     gtamts = saveguestdata.amount_after_tax
#                     taxamts = saveguestdata.tax/2 

#                     fisrroom = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()

                    
#                     if saveguestdata.segment == 'OTA' and saveguestdata.pah==False:
#                         otagstin = saveguestdata.channal.company_gstin
#                         companyname = saveguestdata.channal.channalname
#                         Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(
#                             customer_gst_number=otagstin,customer_company=companyname)
                        
#                     else:
#                         pass

#                     Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(total_item_amount=totalitemamount,
#                                     discount_amount=discamts,subtotal_amount=subttlamt,
#                                     modeofpayment=paymentstatus,grand_total_amount=gtamts,
#                                     gst_amount=taxamts,sgst_amount=taxamts,room_no=fisrroom.roomno.room_name,
#                                     taxable_amount=subttlamt)
                            

                            


                   
                    
#                     if InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id).exists():
#                         adpaymentdata = InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id)
                        
#                         advncspt = 0
#                         chechtotalamt = int(float(saveguestdata.total_amount))
#                         for i in adpaymentdata:
#                             InvoicesPayment.objects.filter(vendor=user,id=i.id).update(invoice=Invoiceid)
#                             invcdatas= InvoicesPayment.objects.get(vendor=user,id=i.id)
#                             advncspt = advncspt + int(float(invcdatas.payment_amount))
                               
#                         if advncspt == chechtotalamt:
#                                 Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                                  Due_amount=0.00,accepted_amount=float(advncspt)
#                                 )
#                         elif advncspt < chechtotalamt:
#                                 dueamts = chechtotalamt - advncspt
#                                 Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                                  Due_amount=float(dueamts),accepted_amount=float(advncspt)
#                                 )
#                     else:
#                         Invoice.objects.filter(vendor=user,customer=guestdata).update(
#                              Due_amount=float(saveguestdata.total_amount),accepted_amount=0.00
#                             )
                        
                 
                
                


#                     if checkmoredatastatus == 'on':
#                         moreguestname = request.POST.get('moreguestname')
#                         moreguestphone = request.POST.get('moreguestphone')
#                         if moreguestphone == "":
#                             moreguestphone = 0
#                         else:
#                             pass
#                         moreguestaddress = request.POST.get('moreguestaddress')
#                         MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
#                                                     another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                     

            
                
#                     today = datetime.now().date()
#                     roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
#                     #  roomdata = Room_history.objects.filter(vendor=user,checkindate__range=[checkindate,checkoutdate],bookingstatus=True,bookingguestphone=guestphome).all()
#                     if roomalldefaultcheckinbutton == 'on':
#                         for data in roomdata:
                      
#                             Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=5)
#                             roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
                      
#                             RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(partly_checkin=True)
#                             Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(
#                                                                              gueststay=guestdata)
                            
#                         return redirect('todaybookingpage')
                            
                        
#                     else:
#                         for data in roomdata:
                           
#                             roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
#                             Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=1)
                      
#                             RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(checkinstatus=True,
#                                                 bookingdate=today)
#                             ctime = datetime.now().time()
#                             Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(status="CHECK IN",check_in_time=ctime,
#                                                                              gueststay=guestdata)
                        
#                         userid = guestdata.id
#                         url = reverse('invoicepage', args=[userid])
#                         return redirect(url)

                

                
#             else:
#                 messages.error(request,"Please check out the room that has not been checked out yet for the same guest before you can check in to a new room.")
#                 return redirect('todaybookingpage')
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)




   

# checkout button function
from django.db.models import Max
# def checkoutroom(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             roomno = request.POST.get('roomno')
#             invoice_id = request.POST.get('invoice_id')
#             loyltycheck = request.POST.get('loyltycheck')
#             # paymentstatus = request.POST.get('paymentstatus')
#             paymentstatus = "PMS"
#             gstnumbercustomer = request.POST.get('gstnumber')
#             dueamount = request.POST.get('dueamount')
#             duedate = request.POST.get('duedate')
            
#             if Invoice.objects.filter(vendor=user,id=invoice_id,foliostatus=False).exists():
#                 if gstnumbercustomer:
#                     Invoice.objects.filter(vendor=user,id=invoice_id).update(customer_gst_number=gstnumbercustomer)
#                 else:
#                     pass
#                 if Invoice.objects.filter(vendor=user,id=invoice_id).exists():
#                     GUESTIDs = Invoice.objects.get(vendor=user,id=invoice_id)
#                     GUESTID = GUESTIDs.customer.id
#                     invoicegrandtotalpaymentstatus = GUESTIDs.grand_total_amount
                    
                    
#                     # new updated code
#                     if int(float(dueamount)) == 0 :
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=True)
#                         if companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).exists():
#                             companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).update(is_paid=True)
#                             cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=GUESTIDs)
#                             orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
#                             values = int(orgcmp.values)
#                             updateval = values + int(float(GUESTIDs.grand_total_amount))
#                             Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
#                                         values=updateval
#                             )
                        
#                     else: #unpaid 
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=False,invoice_number="unpaid")
#                         CustomerCredit.objects.create(vendor=user,customer_name=GUESTIDs.customer.guestname,amount=dueamount,
#                                                       due_date=duedate,invoice=GUESTIDs,phone=GUESTIDs.customer.guestphome)
                        



#                     guestdatas = Gueststay.objects.get(vendor=user,id=GUESTID)
#                     current_date = datetime.now()
#                     # Get the current date
#                     invccurrentdate = datetime.now().date()

#                     # Fetch the maximum invoice number for today for the given user
#                     max_invoice_today = Invoice.objects.filter(
#                         vendor=user,
#                         invoice_date=invccurrentdate,
#                         foliostatus=True
#                     ).aggregate(max_invoice_number=Max('invoice_number'))['max_invoice_number']

#                     # Determine the next invoice number
#                     if max_invoice_today is not None:
#                         # Extract the numeric part of the latest invoice number and increment it
#                         try:
#                             current_number = int(max_invoice_today.split('-')[-1])
#                             next_invoice_number = current_number + 1
#                         except (ValueError, IndexError):
#                             # Handle the case where the invoice number format is unexpected
#                             next_invoice_number = 1
#                     else:
#                         next_invoice_number = 1
#                     # Generate the invoice number
#                     invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'
                    
#                     # Check if the generated invoice number already exists
#                     while Invoice.objects.filter(vendor=user,invoice_number=invoice_number).exists():
#                         next_invoice_number += 1
#                         invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'

#                     Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_date=invccurrentdate)
                    

#                     if RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id = GUESTIDs.customer.saveguestid).exists():
                        
#                         ctime = datetime.now().time()
#                         saveguestid = GUESTIDs.customer.saveguestid
#                         multipleroomsdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestid).all()
                     
#                         for i in multipleroomsdata:
                            
#                             Rooms.objects.filter(vendor=user,id=i.roomno.id).update(checkin=0)
#                             Booking.objects.filter(vendor=user,advancebook_id=GUESTIDs.customer.saveguestid
#                                                ,room_id=i.roomno.id).update(status="CHECK OUT",check_out_time=ctime,check_out_date=current_date,advancebook=None)

#                         # update occupancy
#                         roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestid).all()
#                         if roomdata: 
#                             for data in roomdata:
#                                 # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
#                                 checkindate = data.bookingdate
#                                 checkoutdate = data.checkoutdate
#                                 while checkindate < checkoutdate:
#                                     roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
#                                     invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                                
#                                     invtavaible = invtdata.total_availibility + 1
#                                     invtabook = invtdata.booked_rooms - 1
#                                     total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
#                                     occupancy = invtabook * 100//total_rooms
                                                                            

#                                     RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
#                                                 total_availibility=invtavaible,occupancy=occupancy)
                        
#                                     checkindate += timedelta(days=1)

#                             if VendorCM.objects.filter(vendor=user):
#                                 start_date = str(data.bookingdate)
#                                 end_date = str(data.checkoutdate)
#                                 thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                                 thread.start()
#                                 # for dynamic pricing
#                                 if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                                     thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                                     thread.start()
#                                 else:
#                                     pass
#                             else:
#                                 pass

                        
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(foliostatus=True,invoice_number=invoice_number,modeofpayment=paymentstatus)
#                         # SaveAdvanceBookGuestData.objects.filter(id=saveguestid).delete()
#                         Gueststay.objects.filter(vendor=user,id=GUESTID).update(checkoutdone=True,checkoutstatus=True,checkoutdate=current_date)
#                     elif HourlyRoomsdata.objects.filter(vendor=user,rooms__room_name=guestdatas.roomno).exists():
#                         HourlyRoomsdata.objects.filter(vendor=user,rooms__room_name=guestdatas.roomno).update(checkinstatus=False)
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(foliostatus=True,invoice_number=invoice_number,modeofpayment=paymentstatus)
#                         Gueststay.objects.filter(vendor=user,id=GUESTID).update(checkoutdone=True,checkoutstatus=True,checkoutdate=current_date)
                
#                     else:
#                         room_no = guestdatas.roomno
#                         room_dats= Rooms.objects.get(vendor=user,room_name=room_no)
#                         r_category_id = room_dats.room_type.id
#                         checkindatedlt = guestdatas.checkindate
#                         checkoutdatedlt = guestdatas.checkoutdate- timedelta(days=1)
                        
                        
#                         rinvrdata = RoomsInventory.objects.filter(vendor=user,room_category_id=r_category_id,date__range=[checkindatedlt,checkoutdatedlt])
                        
#                         for date in rinvrdata:
#                             avalblty = RoomsInventory.objects.get(id=date.id)
#                             avlcount = avalblty.total_availibility
#                             RoomsInventory.objects.filter(id=date.id).update(total_availibility=avlcount+1)
                            
#                         # not minus1 to add new var with s
#                         checkoutdatedlts = guestdatas.checkoutdate
#                         if VendorCM.objects.filter(vendor=user):
#                             start_date = str(datetime.now().date())
#                             end_date = str(checkoutdatedlts.date())
#                             thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                             thread.start()
#                             # for dynamic pricing
#                             if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                                 thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                                 thread.start()
#                             else:
#                                 pass
#                         else:
#                             pass
#                         # booking datahandle
#                         ctime = datetime.now().time()
#                         Booking.objects.filter(vendor=user,gueststay_id=GUESTID).update(status="CHECK OUT",check_out_time=ctime,check_out_date=current_date)
#                         Gueststay.objects.filter(vendor=user,id=GUESTID).update(checkoutdone=True,checkoutstatus=True,checkoutdate=current_date)
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(foliostatus=True,invoice_number=invoice_number,modeofpayment=paymentstatus)
#                         Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=0,is_clean=False)

#                     if int(float(dueamount)) == 0 :
#                             pass
#                     else:
#                         Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_number="unpaid")
#                 if loyltycheck == 'on':
#                         guestphone = Gueststay.objects.get(vendor=user,id=GUESTID)
#                         guestphonenumber = guestphone.guestphome
#                         guestnameformsg = guestphone.guestname
#                         loyltyrate = loylty_data.objects.get(vendor=user)
#                         totalamountinvoice = GUESTIDs.grand_total_amount
#                         totalloyltyamount = int(totalamountinvoice)*loyltyrate.loylty_rate_prsantage//100
#                         if loylty_Guests_Data.objects.filter(vendor=user,guest_contact=guestphonenumber).exists():
#                                     loyltdatas = loylty_Guests_Data.objects.get(vendor=user,guest_contact=guestphonenumber)
#                                     existsamount = loyltdatas.loylty_point + totalloyltyamount
#                                     loylty_Guests_Data.objects.filter(vendor=user,guest_contact=guestphonenumber).update(loylty_point = existsamount)
#                         else:
#                                     loylty_Guests_Data.objects.create(vendor=user,guest_name=guestnameformsg,guest_contact=guestphonenumber,loylty_point=totalloyltyamount
#                                                                       ,smscount='0')
#                         # msg content 
#                         usermsglimit = Messgesinfo.objects.get(vendor=user)
#                         if usermsglimit.defaultlimit > usermsglimit.changedlimit :
#                                 addmsg = usermsglimit.changedlimit + 2
#                                 Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
#                                 profilename = HotelProfile.objects.get(vendor=user)
#                                 hotelname = profilename.name
#                                 mobile_number = guestphonenumber
#                                 user_name = "chandan"
#                                 val = 5
#                                 message_content = f"Dear Guest, you have earned loyalty points worth Rs {totalloyltyamount} at {hotelname}. We look forward to welcoming you back soon. - Billzify"
                                    
#                                 base_url = "http://control.yourbulksms.com/api/sendhttp.php"
#                                 params = {
#                                     'authkey': settings.YOURBULKSMS_API_KEY,
#                                     'mobiles': guestphonenumber,
#                                     'sender':  'BILZFY',
#                                     'route': '2',
#                                     'country': '0',
#                                     'DLT_TE_ID': '1707171993560691064'
#                                 }
#                                 encoded_message = urllib.parse.urlencode({'message': message_content})
#                                 url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                                
#                                 try:
#                                     response = requests.get(url)
#                                     if response.status_code == 200:
#                                         try:
#                                             response_data = response.json()
#                                             if response_data.get('Status') == 'success':
#                                                 messages.success(request, 'SMS sent successfully.')
#                                             else:
#                                                 messages.success(request, response_data.get('Description', 'Failed to send SMS'))
#                                         except ValueError:
#                                             messages.success(request, 'Failed to parse JSON response')
#                                     else:
#                                         messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
#                                 except requests.RequestException as e:
#                                     messages.success(request, f'Error: {str(e)}')
#                         else:
#                             messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
                                
#                 else:
#                     pass
#                 return redirect('invoicepage', id=GUESTID)
#             else:
#                 return redirect('invoicepage', id=GUESTID)
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def cancelroom(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomno = request.POST.get('roomno')
            invoice_id = request.POST.get('invoice_id')
            
            guest_id = request.POST.get('guest_id')
            guestdatas = Gueststay.objects.get(vendor=user,id=guest_id)
            if Gueststay.objects.filter(vendor=user,id=guest_id).exists():
                if Invoice.objects.filter(vendor=user,id=invoice_id).exists():
                    invcsadata = Invoice.objects.get(vendor=user,id=invoice_id)
                    mftdata = InvoiceItem.objects.filter(vendor=user,invoice=invcsadata)
                    for i in mftdata:
                        i.description
                        if Items.objects.filter(vendor=user,description=i.description).exists():
                            Items.objects.filter(vendor=user,description=i.description).update(
                                available_qty=F('available_qty')+i.quantity_likedays
                            )
                            
                        else:
                            pass

                    if companyinvoice.objects.filter(vendor=user,Invoicedata=invcsadata).exists():
                        cmpinvc = companyinvoice.objects.get(vendor=user,Invoicedata=invcsadata)
                        if Companies.objects.filter(vendor=user,id=cmpinvc.company.id).exists():
                            Companies.objects.filter(vendor=user,id=cmpinvc.company.id).update(
                               values=F('values')- float(cmpinvc.Invoicedata.grand_total_amount)
                            )
                            cmpinvc.delete()
                else:
                    pass
                if RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=guestdatas.saveguestid).exists():
                  
                    # saveguestid = RoomBookAdvance.objects.filter(vendor=user,roomno__room_name = roomno,bookingguestphone = guestdatas.guestphome,bookingdate__range = [guestdatas.checkindate , guestdatas.checkoutdate])
                    # for i in saveguestid:
                    saveguestidfilter = guestdatas.saveguestid
                    multipleroomsdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestidfilter).all()
                 
                    for i in multipleroomsdata:
                            Rooms.objects.filter(vendor=user,id=i.roomno.id).update(checkin=0)

                    # update occupancy
                    roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestidfilter).all()
                    if roomdata: 
                        for data in roomdata:
                            # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                            checkindate = data.bookingdate
                            checkoutdate = data.checkoutdate
                            while checkindate < checkoutdate:
                                roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                                invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                             
                                invtavaible = invtdata.total_availibility + 1
                                invtabook = invtdata.booked_rooms - 1
                                total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                occupancy = invtabook * 100//total_rooms
                                                                        

                                RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                            total_availibility=invtavaible,occupancy=occupancy)
                    
                                checkindate += timedelta(days=1)

                        if VendorCM.objects.filter(vendor=user):
                            start_date = str(data.bookingdate)
                            end_date = str(data.checkoutdate)
                            thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                            thread.start()
                            # for dynamic pricing
                            if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                thread.start()
                            else:
                                pass
                        else:
                            pass


                    # SaveAdvanceBookGuestData.objects.filter(id=saveguestidfilter).delete()
                    SaveAdvanceBookGuestData.objects.filter(id=saveguestidfilter).update(action='cancel')
                    Gueststay.objects.filter(vendor=user,id=guest_id).delete()
                elif HourlyRoomsdata.objects.filter(vendor=user,rooms__room_name=guestdatas.roomno).exists():
                    HourlyRoomsdata.objects.filter(vendor=user,rooms__room_name=guestdatas.roomno).update(checkinstatus=False)
                    Gueststay.objects.filter(vendor=user,id=guest_id).delete()
                else:
                    room_no = guestdatas.roomno
                    room_dats= Rooms.objects.get(vendor=user,room_name=room_no)
                    r_category_id = room_dats.room_type.id
                    checkindatedlt = guestdatas.checkindate
                    checkoutdatedlt = guestdatas.checkoutdate- timedelta(days=1)

                    rinvrdata = RoomsInventory.objects.filter(vendor=user,room_category_id=r_category_id,date__range=[checkindatedlt,checkoutdatedlt])
                   
                    for date in rinvrdata:
                        avalblty = RoomsInventory.objects.get(id=date.id)
                        avlcount = avalblty.total_availibility
                        bookcounts = avalblty.booked_rooms
                         # Safeguard against invalid operations
                        if bookcounts > 0:  # Ensure there are booked rooms to cancel
                            total_rooms = avlcount + bookcounts
                            
                            # Update availability and bookings
                            new_availability = avlcount + 1
                            new_booked_rooms = bookcounts - 1

                            # Calculate the new occupancy rate
                            if total_rooms > 0:
                                new_occupancy_rate = (new_booked_rooms / total_rooms) * 100
                            else:
                                new_occupancy_rate = 0

                            # Update the database
                            RoomsInventory.objects.filter(id=date.id).update(
                                total_availibility=new_availability,
                                booked_rooms=new_booked_rooms,
                                occupancy=new_occupancy_rate
                            )
                     
                        
                    # not minus1 to add new var with s
                    checkoutdatedlts = guestdatas.checkoutdate
                    if VendorCM.objects.filter(vendor=user):
                        start_date = str(checkindatedlt.date())
                        end_date = str(checkoutdatedlts.date())
                        thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                        thread.start()
                        # for dynamic pricing
                        if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                thread.start()
                        else:
                                pass
                    else:
                        pass
                    Booking.objects.filter(vendor=user,gueststay_id=guest_id).delete()

                    Gueststay.objects.filter(vendor=user,id=guest_id).delete()
                    Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=0)
                    
            else:
                pass
            return redirect('homepage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def gotoaddservice(request,id):
    try:    
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomno = id
            if Gueststay.objects.filter(vendor=user,roomno=roomno,checkoutdone=False).exists():
                custid = Gueststay.objects.filter(vendor=user,roomno=roomno,checkoutdone=False).last()
                customerid = custid.id
              
                if Invoice.objects.filter(vendor=user,customer_id=customerid).exists():
                    invcid = Invoice.objects.get(vendor=user,customer_id=customerid)
                    invcid=invcid.id
                    urlid = custid.id
            else:
                invcitemid = InvoiceItem.objects.filter(vendor=user,description=roomno,invoice__foliostatus=False)
                for i in invcitemid:
                    invcid = i.invoice.id

            tax = Taxes.objects.filter(vendor=user)
            folio = Invoice.objects.filter(vendor=user,foliostatus=False)
            iteams = Items.objects.filter(vendor=user)
            laundry = LaundryServices.objects.filter(vendor=user)
            return render(request,'pospage.html',{'tax':tax,'folio':folio,'iteams':iteams,'laundry':laundry,
                                                    'invoiceid':invcid,'roomno':roomno})
        else:
            return render(request, 'login.html')

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def gotofoliobyhome(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomno = id
            if Gueststay.objects.filter(vendor=user,roomno=roomno,checkoutdone=False).exists():
                custid = Gueststay.objects.filter(vendor=user,roomno=roomno,checkoutdone=False).last()
                customerid = custid.id
              
                if Invoice.objects.filter(vendor=user,customer_id=customerid,is_fandb=False).exists():
                    invcid = Invoice.objects.get(vendor=user,customer_id=customerid,is_fandb=False)
                    urlid = custid.id
                    # invoicepage
                    
                    return redirect('invoicepage', id=urlid)
                else:
                    Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=0)
                
                    return redirect('homepage')
            else:
           
                invcitemid = InvoiceItem.objects.filter(vendor=user,description=roomno,invoice__foliostatus=False)
                for i in invcitemid:
                    invceid = i.invoice.id
                if len(invcitemid) > 0:
                    if Invoice.objects.filter(vendor=user,id=invceid,is_fandb=False).exists():
                        invoicedata = Invoice.objects.get(vendor=user,id=invceid,is_fandb=False)
                        customerid = invoicedata.customer.id
                        return redirect('invoicepage', id=customerid)
                    else:
                        Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=0)
                        return redirect('homepage')
                else:
                    Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=0)
                    return redirect('homepage')
                
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


#login authencatation and subscription


def signuppage(request):
    try:
        form = UserCreationForm()
        return render(request, 'signup.html', {'form': form})
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

    
def loginpage(request):
    try:
        form = UserCreationForm()
        return render(request, 'login.html', {'form': form}) 
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

@csrf_exempt
def signup(request):
    try:
        if request.method == 'POST':
            form = UserCreationForm(request.POST)
            if form.is_valid():
                form.save()
                # username = form.cleaned_data.get('username')
                # raw_password = form.cleaned_data.get('password1')
                # user = authenticate(username=username, password=raw_password)
                # login(request, user)
                form = UserCreationForm()
                messages.success(request,'Registerd Succesfully!   ')
                
                return redirect('handleuser')
        else:
            form = UserCreationForm()
        return redirect('handleuser')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('handleuser')

from django.contrib.sessions.models import Session
from django.utils import timezone

# @csrf_exempt
# def login_view(request):
#     try:
#         if request.method == 'POST':
#             username = request.POST['username']
#             password = request.POST['password']
#             user = authenticate(request, username=username, password=password)
#             if user is not None:
#                 # # Invalidate any existing sessions for this user
#                 # current_session_key = request.session.session_key
#                 # user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
#                 # for session in user_sessions:
#                 #     session_data = session.get_decoded()
#                 #     if session_data.get('_auth_user_id') == str(user.id) and session.session_key != current_session_key:
#                 #         session.delete()

#                 # Log the user in
#                 login(request, user)

#                 # Ensure the session is correctly set
#                 request.session.save()

#                 # Check subscription status
#                 user_subscription = Subscription.objects.filter(user=user).last()
#                 if user_subscription and user_subscription.end_date >= date.today():
#                     messages.success(request, 'Successfully logged in!')
#                     return redirect('homepage')
#                 else:
#                     messages.error(request, 'Your plan is over. Please recharge to enjoy Billzify services.')
#                     return render(request, 'subscriptionplanpage.html', {'username': username})
#             else:
#                 messages.error(request, 'Invalid username and password!')
#                 return render(request, 'login.html')
#         return render(request, 'login.html')
#     except Exception as e:
#         messages.error(request, f'An error occurred: {str(e)}')
#         return redirect('login')


@csrf_exempt
def login_view(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            
            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if it's a subuser and handle login for both main and subuser
                if Subuser.objects.filter(user=user).exists():
                    # If subuser exists, log them in as a subuser
                    subuser = Subuser.objects.get(user=user)
                    request.session['is_subuser'] = True
                    request.session['permissions'] = subuser.permissions  # Store permissions in session
                    if subuser.is_cleaner==True:
                        login(request, user)
                        messages.success(request, 'Successfully logged in!')
                        url = reverse('roomclean', args=[user.id])
                        
                        return redirect(url)
                    else:
                        pass
                else:
                    # Main user - full access
                    request.session['is_subuser'] = False
                    request.session['permissions'] =  {
                        'TSel': True, 'Attd': True, 'cln': True, 'psle': True,
                        'si': True, 'saa': True, 'ext': True, 'emp': True,
                        'pdt': True, 'set': True, 'ups': True ,'fce':True , 'acc':True,
                    }  # Full access for main user
                
                # Log the user in
                login(request, user)
                
                # Set session expiry to midnight
                # tomorrow = timezone.now() + timedelta(days=1)
                # midnight = datetime.combine(tomorrow, datetime.min.time())  # Create naive datetime for midnight
                
                # # Convert midnight to timezone-aware datetime (assuming the timezone is UTC)
                # midnight = timezone.make_aware(midnight, timezone.utc)
                
                # # Calculate seconds until midnight
                # seconds_until_midnight = (midnight - timezone.now()).seconds
                # request.session.set_expiry(seconds_until_midnight)  # Set session expiry to midnight

                # # Save session
                # request.session.save()  # Make sure session data is saved

                
              

                # Check subscription status
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor 
                user_subscription = Subscription.objects.filter(user=user).last()
                if user_subscription and user_subscription.end_date >= date.today():
                    messages.success(request, 'Successfully logged in!')
                    if Vendor_Service.objects.filter(vendor=user,only_cm=True):
                        return redirect('cm')
                    else:
                        return redirect('homepage')
                else:
                    messages.error(request, 'Your plan is over. Please recharge to enjoy Billzify services.')
                    return render(request, 'subscriptionplanpage.html', {'username': username})
                
                # Redirect user to homepage
                # return redirect('homepage')
            else:
                messages.error(request, 'Invalid username or password!')
                return render(request, 'login.html')
        return render(request, 'login.html')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return render(request, 'login.html')

    

def subscribe(request):
    plans = SubscriptionPlan.objects.all()
    if request.method == 'POST':
        # Handle subscription creation here
        pass
    return render(request, 'subscribe.html', {'plans': plans})



def subscriptionplanpage(request):
    return render(request,'subscriptionplanpage.html')


# its a tempraory not real
def createsubscription(request,id):
    username = id
    user=User.objects.get(username=username)
    subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
    if subuser:
        user = subuser.vendor  
    sid=SubscriptionPlan.objects.get(id=1)
    b=datetime.now().date()
    enddate=datetime.now().date()
    delta = timedelta(days=28)
    # startdate = enddate + datetime.timedelta(days=30)
    startdate = enddate + delta
    if Messgesinfo.objects.filter(vendor=user).exists():
        data = Messgesinfo.objects.get(vendor=user)
        msg = data.defaultlimit + 250
        Messgesinfo.objects.filter(vendor=user).update(defaultlimit=msg)
    else:
        Messgesinfo.objects.create(vendor=user,defaultlimit=250)
    Subscription.objects.create(user=user,plan=sid,start_date=b,end_date=startdate)
    return render(request, 'login.html')



# ajax book date all rooms data
@csrf_exempt
def addbrnahc(request):
    if request.user.is_authenticated and request.method=="POST":
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  
        bokingdate=request.POST['date']
        data=Rooms.objects.filter(Q(vendor=user,checkin=0) | Q(vendor=user,checkin=2)).all()
       
        return JsonResponse(list(data.values('id', 'room_name','room_type','price' ,'tax')),safe=False)
    else:
        return redirect('loginpage')
    

# booking date search function
def bookingdate(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            bookingdate = datetime.strptime(startdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(enddate, '%Y-%m-%d').date()
            newbookdateminus = bookingdate + timedelta(days=1)

            if checkoutdate<bookingdate:
                messages.error(request, 'Please select correct dates!')
                return redirect('advanceroombookpage')

            if checkoutdate == bookingdate:
                messages.error(request, 'Same-Day Checkout Booking Are Not Allowed Here Book To Hourly Room Booking')
                return redirect('advanceroombookpage')
            else:

                # Fetching guest stays with checkoutstatus=False within the specified date range
                guestroomsdata = Gueststay.objects.filter(
                    Q(vendor=user, checkoutstatus=False) &
                    Q(checkindate__date__lte=checkoutdate) & 
                    Q(checkoutdate__date__gte=newbookdateminus)
                )

                # Fetching booked rooms within the specified date range
                bookedroomsdata = RoomBookAdvance.objects.filter(
                    Q(vendor=user) &
                    (Q(bookingdate__lte=checkoutdate) & Q(checkoutdate__gte=newbookdateminus))
                ).exclude(vendor=user,saveguestdata__action='cancel').exclude(checkOutstatus=True)

                # Collecting room numbers from guest stays
                occupied_rooms = set(guest.roomno for guest in guestroomsdata)
                
                # Collecting room numbers from booked rooms, except those starting from enddate
                booked_rooms = set(
                    booking.roomno for booking in bookedroomsdata
                    if booking.bookingdate != checkoutdate
                )
                
                # Fetching all room data excluding rooms with checkin=6
                roomdata = Rooms.objects.filter(vendor=user).exclude(checkin=6).order_by('room_name')

                # Filtering available rooms
                # availableroomdata = [
                #     room for room in roomdata
                #     if room.room_name not in occupied_rooms and room not in booked_rooms
                # ]

                # booking model work here
                # booking_data = Booking.objects.filter(
                #     vendor=user,
                #     check_in_date__lte=newbookdateminus,
                #     check_out_date__gt=startdate
                # )
                booking_data = Booking.objects.filter(
                        Q(vendor=user) &
                        (
                            Q(check_in_date__gte=startdate) & Q(check_in_date__lt=enddate) |  # Check-in date is within the range
                            Q(check_out_date__gt=startdate) & Q(check_out_date__lte=enddate) |  # Check-out date is within the range (excluding startdate)
                            Q(check_in_date__lt=startdate) & Q(check_out_date__gt=enddate)  # Booking spans the entire range
                        ) &
                        ~Q(check_out_date=startdate)  # Exclude bookings where check_out_date is exactly startdate
                    ).exclude(status='CHECK OUT')


                bookinghavedata = set(booking.room for booking in booking_data)

                availableroomdata = [
                    room for room in roomdata
                    if room not in bookinghavedata
                ]
                

              

                channal = onlinechannls.objects.filter(vendor=user)
                meal_plan = RatePlanforbooking.objects.filter(vendor=user)
                lenoflist = len(availableroomdata)
                emptymessage = "No Rooms Available On This Day!" if lenoflist == 0 else ""

                inventorydata = RoomsInventory.objects.none()
                if VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                    inventorydata = RoomsInventory.objects.filter(vendor=user,date__range=[startdate,enddate])

                return render(request, 'roombookpage.html', {
                    'active_page': 'advanceroombookpage',
                    'availableroomdata': availableroomdata,
                    'emptymessage': emptymessage,
                    'startdate': startdate,
                    'enddate': enddate,
                    'channal': channal,
                    'bookedroomsdata': bookedroomsdata,
                    'guestroomsdata': guestroomsdata,
                    'meal_plan': meal_plan,
                    'inventorydata':inventorydata
                })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
    
from datetime import datetime, timedelta

# def addadvancebooking(request):
#     # try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             bookingdate = request.POST.get('bookingdate')
#             guestname = request.POST.get('guestname')
#             totalstaydays = request.POST.get('totalstaydays')
#             phone = request.POST.get('phone',0)
#             channal = request.POST.get('channal')
#             bookenddate = request.POST.get('bookenddate')
#             totalamount = float(request.POST.get('totalamount'))
#             advanceamount = request.POST.get('advanceamount',0)
#             discountamount = float(request.POST.get('discountamount',0))
#             reaminingamount = request.POST.get('reaminingamount',0)
#             mealplan = request.POST.get('mealplan')
#             guestcount = request.POST.get('guestcount')
#             paymentmode = request.POST.get('paymentmode')
#             serialized_array = request.POST['news']
#             channal=onlinechannls.objects.get(id=channal)
#             my_array = json.loads(serialized_array)
#             noofrooms = len(my_array)
#             bookenddate = str(bookenddate)
#             # bookenddate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
#             bookingdate = datetime.strptime(bookingdate, '%Y-%m-%d').date()
#             checkoutdate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
#             checkoutdate -= timedelta(days=1)
#             # bookingdate -= timedelta(days=1)
           
            
#             # delta = timedelta(days=1)
#             # while bookingdate <= checkoutdate:
           
#             #         bookingdate += delta
#             current_date = datetime.now()
#             Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(vendor=user,bookingdate=bookingdate,noofrooms=noofrooms,bookingguest=guestname,
#                 bookingguestphone=phone,staydays=totalstaydays,advance_amount=advanceamount,reamaining_amount=reaminingamount,discount=discountamount,
#                 total_amount=totalamount,channal=channal,checkoutdate=bookenddate,email='',address_city='',state='',country='',totalguest=guestcount,
#                 action='book',booking_id=None,cm_booking_id=None,segment='PMS',special_requests='',pah=True,amount_after_tax=totalamount,amount_before_tax=0.00,
#                   tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=True)
#             paymenttypes = 'postpaid'
#             pah=True
#             if int(advanceamount) > 0:
#                 pah=False
#                 InvoicesPayment.objects.create(vendor=user,invoice=None,payment_amount=advanceamount,payment_date=current_date,
#                                                 payment_mode=paymentmode,transaction_id="ADVANCE AMOUNT",descriptions='ADVANCE',advancebook=Saveadvancebookdata)
#                 if int(advanceamount) < int(totalamount):
#                     paymenttypes = 'partially'
#                 else:
#                     paymenttypes = 'prepaid'
#             else:
#                 pass 
#             sellingprices = 0    
#             totaltax = 0   
#             guestcountsstored = int(guestcount) 
#             changedguestct = guestcountsstored

            

#             for i in my_array:
#                     roomid = int(i['id'])
#                     roomsellprice = int(float(i['price']))
#                     roomselltax = int(float(i['tax']))
#                     befortselprice=roomsellprice
#                     befortselprice = befortselprice / int(totalstaydays)
#                     sellingprices = sellingprices + roomsellprice
#                     totalsellprice = (roomsellprice * roomselltax //100) + roomsellprice
#                     totaltax = totaltax + (roomsellprice * roomselltax /100) 
                  
#                     roomid = Rooms.objects.get(id=roomid)
#                     roomtype = roomid.room_type.id

#                     # # manage rate plan guests
#                     maxperson = roomid.max_person
#                     if changedguestct >= maxperson:
            
#                         changedguestct = changedguestct - maxperson
                  
#                         satteldcount = maxperson
#                     else:
                 
#                         satteldcount = changedguestct

                  
                
#                     RoomBookAdvance.objects.create(vendor=user,saveguestdata=Saveadvancebookdata,bookingdate=bookingdate,roomno=roomid,
#                                                     bookingguest=guestname,bookingguestphone=phone
#                                                 ,checkoutdate=bookenddate,bookingstatus=True,channal=channal,totalguest=satteldcount,
#                                                rateplan_code=mealplan,guest_name='',adults=satteldcount,children=0,sell_rate=befortselprice )
#                     noon_time_str = "12:00 PM"
#                     noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
#                     Booking.objects.create(vendor=user,room=roomid,guest_name=guestname,check_in_date=bookingdate,check_out_date=bookenddate,
#                                 check_in_time=noon_time,check_out_time=noon_time,segment="PMS",totalamount=totalamount,totalroom=noofrooms,
#                                 gueststay=None,advancebook=Saveadvancebookdata,status="BOOKING"           )
#                     # inventory code
#                     # Convert date strings to date objects
#                     checkindate = str(bookingdate)
#                     checkoutdate = str(bookenddate)
#                     checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
#                     checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

#                     # Generate the list of all dates between check-in and check-out (inclusive)
#                     all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

#                     # Query the RoomsInventory model to check if records exist for all those dates
#                     existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

#                     # Get the list of dates that already exist in the inventory
#                     existing_dates = set(existing_inventory.values_list('date', flat=True))

#                     # Identify the missing dates by comparing all_dates with existing_dates
#                     missing_dates = [date for date in all_dates if date not in existing_dates]

#                     # If there are missing dates, create new entries for those dates in the RoomsInventory model
#                     roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
              
#                     # occupancy = (1 * 100 // roomcount)
                    
#                     for inventory in existing_inventory:
                        
                       
#                         if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
#                             # Update room availability and booked rooms
#                             inventory.total_availibility -= 1
#                             inventory.booked_rooms += 1

#                             # Calculate total rooms
#                             total_rooms = inventory.total_availibility + inventory.booked_rooms

#                             # Recalculate the occupancy rate
#                             if total_rooms > 0:
#                                 # Directly calculate occupancy as the percentage of booked rooms
#                                 inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
#                             else:
#                                 inventory.occupancy = 0  # Avoid division by zero if no rooms exist

#                             # Save the updated inventory
#                             inventory.save()

                    
#                     catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
#                     totalrooms = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
#                     occupancccy = (1 *100 //totalrooms)
#                     if missing_dates:
#                         for missing_date in missing_dates:
                        
#                                 RoomsInventory.objects.create(
#                                     vendor=user,
#                                     date=missing_date,
#                                     room_category_id=roomtype,  # Use the appropriate `roomtype` or other identifier here
#                                     total_availibility=totalrooms-1,       # Set according to your logic
#                                     booked_rooms=1,    
#                                     occupancy=occupancccy,
#                                     price=catdatas.catprice
#                                                             # Set according to your logic
#                                 )
                        
#                     else:
#                         pass

#                     # api calling backend automatically
#                                 # Start the long-running task in a separate thread
#             if VendorCM.objects.filter(vendor=user):
#                         start_date = str(checkindate)
#                         end_date = str(checkoutdate)
#                         thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                         thread.start()
#                         # for dynamic pricing
#                         if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                             thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                             thread.start()
#                         else:
#                             pass
#             else:
#                         pass
#             if TravelAgency.objects.filter(vendor=user,name=channal.channalname).exists():
#                 traveldata = TravelAgency.objects.filter(vendor=user,name=channal.channalname).first()
#                 curtdate = datetime.now().date()
#                 if traveldata.commission_rate > 0:
#                     agencydata = TravelAgency.objects.get(vendor=user,id=traveldata.id)
#                     if agencydata.commission_rate >0:
#                         commision = sellingprices*agencydata.commission_rate//100
#                         Travelagencyhandling.objects.create(vendor=user,agency=agencydata,bookingdata=Saveadvancebookdata,
#                                                 date=curtdate,commsion=commision)
#                     else:
#                         pass
#             SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_before_tax=sellingprices,
#                                 tax=float(totaltax),Payment_types=paymenttypes,pah=pah)
#             if Saveadvancebookdata:
#                 usermsglimit = Messgesinfo.objects.get(vendor=user)
#                 if channal.channalname== "self" :
#                     if usermsglimit.defaultlimit > usermsglimit.changedlimit :
#                         addmsg = usermsglimit.changedlimit + 2
#                         Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
#                         profilename = HotelProfile.objects.get(vendor=user)
#                         mobile_number = phone
                        
#                         # message_content = f"Dear guest, Your booking at {profilename.name} is confirmed. Advance payment of Rs.{advanceamount} received. Check-in date: {bookingdate}. We're thrilled to host you and make your stay unforgettable. For assistance, contact us at {profilename.contact}. -BILLZIFY"
#                         oururl = 'https://live.billzify.com/receipt/88/'
#                         # message_content = f"Hello {guestname}, Your reservation is confirmed. View your booking details here: {oururl}-BILLZIFY"
#                         bids=Saveadvancebookdata.id
#                         message_content = f"Hello {guestname}, Your hotel reservation is confirmed. View your booking details here: https://live.billzify.com/receipt/?cd={bids} -BILLZIFY"
                        
#                         base_url = "http://control.yourbulksms.com/api/sendhttp.php"
#                         params = {
#                             'authkey': settings.YOURBULKSMS_API_KEY,
#                             'mobiles': mobile_number,
#                             'sender':  'BILZFY',
#                             'route': '2',
#                             'country': '0',
#                             'DLT_TE_ID': '1707173659916248212'
#                         }
#                         encoded_message = urllib.parse.urlencode({'message': message_content})
#                         url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
#                         try:
#                             response = requests.get(url)
#                             if response.status_code == 200:
#                                 try:
#                                     response_data = response.json()
#                                     if response_data.get('Status') == 'success':
#                                         messages.success(request, 'SMS sent successfully.')
#                                     else:
#                                         messages.success(request, response_data.get('Description', 'Failed to send SMS'))
#                                 except ValueError:
#                                     messages.success(request, 'Failed to parse JSON response')
#                             else:
#                                 messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
#                         except requests.RequestException as e:
#                             messages.success(request, f'Error: {str(e)}')
#                     else:
#                         messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
#             else:
#                 messages.success(request, 'No data found matching the query')
            
        

#             messages.success(request,"Booking Done")
                
#             url = f"{reverse('receipt_view')}?cd={Saveadvancebookdata.id}"

#             if hasattr(user, 'subuser_profile'):
#                 subuser = user.subuser_profile
#                 if not subuser.is_cleaner:
#                     # Update main user's notification (for subuser)
#                     main_user = subuser.vendor
#                     if main_user.is_authenticated:
#                         request.session['notification'] = True  # Update main user's session
#                         request.session.modified = True
#                     # Update subuser's own notification
#                     request.session['notification'] = True  # Update subuser's session
#                     request.session.modified = True
#             else:
#                 # If it's a main user, update their notification
#                 request.session['notification'] = True
#                 request.session.modified = True
#             return redirect(url)
#             # return redirect('advanceroombookpage')
#         else:
#             return redirect('loginpage')
#     # except Exception as e:
#     #     return render(request, '404.html', {'error_message': str(e)}, status=500)

# ye last updated code hai isko abhi ke liye hide kr rha lekin same price ye de rha hia or running me ye chal rha
# def addadvancebooking(request):
#     try:
#         if request.user.is_authenticated and request.method=="POST":
#             user=request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             bookingdate = request.POST.get('bookingdate')
#             guestname = request.POST.get('guestname')
#             totalstaydays = request.POST.get('totalstaydays')
#             phone = request.POST.get('phone',0)
#             channal = request.POST.get('channal')
#             bookenddate = request.POST.get('bookenddate')
#             totalamount = float(request.POST.get('finalesamount'))
#             advanceamount = request.POST.get('advanceamount',0)
#             discountamount = float(request.POST.get('discountamount',0))
#             reaminingamount = request.POST.get('reaminingamount',0)
#             mealplan = request.POST.get('mealplan')
#             guestcount = request.POST.get('guestcount')
#             paymentmode = request.POST.get('paymentmode')

#             sprequest = request.POST.get('sprequest')

#             serialized_array = request.POST['news']
#             channal=onlinechannls.objects.get(id=channal)
#             my_array = json.loads(serialized_array)
#             noofrooms = len(my_array)
#             bookenddate = str(bookenddate)
#             # bookenddate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
#             bookingdate = datetime.strptime(bookingdate, '%Y-%m-%d').date()
#             checkoutdate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
#             checkoutdate -= timedelta(days=1)
#             # bookingdate -= timedelta(days=1)
#             if advanceamount == "":
#                 advanceamount = 0.0
#             else:
#                 pass
#             if float(advanceamount) > float(totalamount):
#                 messages.error(request,"Advance amount is greater than the booking amount!")
#                 return redirect('advanceroombookpage')


#             # delta = timedelta(days=1)
#             # while bookingdate <= checkoutdate:
           
#             #         bookingdate += delta
#             current_date = datetime.now()

#             checktestamount = float(totalamount)
#             onedayoneroomwithtax = checktestamount / int(totalstaydays) / int(noofrooms)
#             print(checktestamount,"this is total amount")
#             print(onedayoneroomwithtax,"one day room rate")
           
        
#             permissions = 'false'
#             if onedayoneroomwithtax > 8851:
#                 findamtsonly = float(onedayoneroomwithtax) / (1 + (18) / 100)
#                 taxamt = findamtsonly * 18/100
#                 total = taxamt + findamtsonly
#                 print("idhr 18 % ka tax rhega ")
#                 findamtsonly = float(findamtsonly)
#                 taxamt = float(taxamt)
#                 total = float(total)
#                 selltax = 18
#                 print(findamtsonly,"find amount",taxamt,"tax amount",total,"total amount")
#             elif onedayoneroomwithtax <= 8400:
#                 findamtsonly = float(onedayoneroomwithtax) / (1 + (12) / 100)
#                 taxamt = findamtsonly * 12/100
#                 total = taxamt + findamtsonly
#                 print("idhar 12 % hi lagega ")
#                 findamtsonly = float(findamtsonly)
#                 taxamt = float(taxamt)
#                 total = float(total)
#                 selltax = 12
#                 print(findamtsonly,"find amount",taxamt,"tax amount",total,"total amount")

#             else:
#                 checkpricediffrance = onedayoneroomwithtax -8400
#                 findamtsonly=7500
#                 taxamt = findamtsonly * 12/100
#                 total = taxamt + findamtsonly
#                 print("idhar 12 % hi lagega ")
#                 findamtsonly = float(findamtsonly)
#                 taxamt = float(taxamt)
#                 total = float(total)
#                 selltax = 12
#                 extraamountonedayprice = float(checkpricediffrance) / (1 + (18) / 100)
#                 permissions = 'true'
#                     # taxrate = 12 
#                     # putrat = 6.0
#                     # taxdata = Taxes.objects.get(vendor=user,taxrate=12)
#                     # hsncode = taxdata.taxcode
#                     # Extracharge='true'
#                     # withouttaxextracharge = float(checkpricediffrance) / (1 + (18) / 100)

             

#             reaminingamount = checktestamount - float(advanceamount)
#             Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(vendor=user,bookingdate=bookingdate,noofrooms=noofrooms,bookingguest=guestname,
#                 bookingguestphone=phone,staydays=totalstaydays,advance_amount=advanceamount,reamaining_amount=reaminingamount,discount=0.00,
#                 total_amount=totalamount,channal=channal,checkoutdate=bookenddate,email='',address_city='',state='',country='',totalguest=guestcount,
#                 action='book',booking_id=None,cm_booking_id=None,segment='PMS',special_requests=sprequest,pah=True,amount_after_tax=totalamount,amount_before_tax=0.00,
#                   tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=True)
#             paymenttypes = 'postpaid'
#             pah=True
#             if int(advanceamount) > 0:
                
#                 InvoicesPayment.objects.create(vendor=user,invoice=None,payment_amount=advanceamount,payment_date=current_date,
#                                                 payment_mode=paymentmode,transaction_id="ADVANCE AMOUNT",descriptions='ADVANCE',advancebook=Saveadvancebookdata)
#                 if int(advanceamount) < int(totalamount):
#                     paymenttypes = 'partially'
#                     pah=True
#                 else:
#                     paymenttypes = 'prepaid'
#                     pah=False
#             else:
#                 pass 
#             sellingprices = 0    
#             totaltax = 0   
#             guestcountsstored = int(guestcount) 
#             changedguestct = guestcountsstored

            
            
#             for i in my_array:
#                     roomid = int(i['id'])
#                     roomsellprice = findamtsonly
#                     roomselltax = selltax
#                     befortselprice=roomsellprice
#                     befortselprice = befortselprice / int(totalstaydays)
#                     sellingprices = sellingprices + roomsellprice * int(totalstaydays)
#                     totalsellprice = (roomsellprice * roomselltax //100) + roomsellprice
#                     totaltax = totaltax + (roomsellprice * roomselltax /100) 
#                     checktotaltax = totaltax * int(totalstaydays)
#                     roomid = Rooms.objects.get(id=roomid)
#                     roomtype = roomid.room_type.id

#                     # # manage rate plan guests
#                     maxperson = roomid.max_person
#                     if changedguestct >= maxperson:
            
#                         changedguestct = changedguestct - maxperson
                  
#                         satteldcount = maxperson
#                     else:
                 
#                         satteldcount = changedguestct

                
#                     bookdatas = RoomBookAdvance.objects.create(vendor=user,saveguestdata=Saveadvancebookdata,bookingdate=bookingdate,roomno=roomid,
#                                                     bookingguest=guestname,bookingguestphone=phone
#                                                 ,checkoutdate=bookenddate,bookingstatus=True,channal=channal,totalguest=satteldcount,
#                                                rateplan_code=mealplan,guest_name='',adults=satteldcount,children=0,sell_rate=roomsellprice )
                    
#                     if permissions == 'true':
#                         extraonedayprice = extraamountonedayprice
#                         extra_total_amount_allday = extraamountonedayprice * int(totalstaydays)
#                         extrataxamount = extra_total_amount_allday * 18 /100
#                         extracgstamount = extrataxamount / 2
#                         extragrandtotal  = extra_total_amount_allday + extrataxamount

#                         totalamount = extragrandtotal + totalamount
#                         extraBookingAmount.objects.create(vendor=user,bookdata=bookdatas,price=extraonedayprice,qty=int(totalstaydays),
#                                         taxable_amount=extra_total_amount_allday,csgst_amount=extracgstamount,sgst_amount=extracgstamount,
#                                         grand_total_amount=extragrandtotal)
                    
#                     noon_time_str = "12:00 PM"
#                     noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
#                     Booking.objects.create(vendor=user,room=roomid,guest_name=guestname,check_in_date=bookingdate,check_out_date=bookenddate,
#                                 check_in_time=noon_time,check_out_time=noon_time,segment=channal,totalamount=totalamount,totalroom=noofrooms,
#                                 gueststay=None,advancebook=Saveadvancebookdata,status="BOOKING"           )
#                     # inventory code
#                     # Convert date strings to date objects
#                     checkindate = str(bookingdate)
#                     checkoutdate = str(bookenddate)
#                     checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
#                     checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

#                     # Generate the list of all dates between check-in and check-out (inclusive)
#                     all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

#                     # Query the RoomsInventory model to check if records exist for all those dates
#                     existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

#                     # Get the list of dates that already exist in the inventory
#                     existing_dates = set(existing_inventory.values_list('date', flat=True))

#                     # Identify the missing dates by comparing all_dates with existing_dates
#                     missing_dates = [date for date in all_dates if date not in existing_dates]

#                     # If there are missing dates, create new entries for those dates in the RoomsInventory model
#                     roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
              
#                     # occupancy = (1 * 100 // roomcount)
                    
#                     for inventory in existing_inventory:
                        
                       
#                         if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
#                             # Update room availability and booked rooms
#                             inventory.total_availibility -= 1
#                             inventory.booked_rooms += 1

#                             # Calculate total rooms
#                             total_rooms = inventory.total_availibility + inventory.booked_rooms

#                             # Recalculate the occupancy rate
#                             if total_rooms > 0:
#                                 # Directly calculate occupancy as the percentage of booked rooms
#                                 inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
#                             else:
#                                 inventory.occupancy = 0  # Avoid division by zero if no rooms exist

#                             # Save the updated inventory
#                             inventory.save()

                    
#                     catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
#                     totalrooms = Rooms.objects.filter(vendor=user,room_type=catdatas).exclude(checkin=6).count()
#                     occupancccy = (1 *100 //totalrooms)
#                     if missing_dates:
#                         for missing_date in missing_dates:
                        
#                                 RoomsInventory.objects.create(
#                                     vendor=user,
#                                     date=missing_date,
#                                     room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
#                                     total_availibility=totalrooms-1,       # Set according to your logic
#                                     booked_rooms=1,    
#                                     occupancy=occupancccy,
#                                     price=catdatas.catprice
#                                                             # Set according to your logic
#                                 )
                        
#                     else:
#                         pass

#                     # api calling backend automatically
#                                 # Start the long-running task in a separate thread
#             if VendorCM.objects.filter(vendor=user):
#                         start_date = str(checkindate)
#                         end_date = str(checkoutdate)
#                         thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                         thread.start()
#                         # for dynamic pricing
#                         if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                             thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                             thread.start()
#                         else:
#                             pass
#             else:
#                         pass
#             if TravelAgency.objects.filter(vendor=user,name=channal.channalname).exists():
#                 traveldata = TravelAgency.objects.filter(vendor=user,name=channal.channalname).first()
#                 curtdate = datetime.now().date()
#                 if traveldata.commission_rate > 0:
#                     agencydata = TravelAgency.objects.get(vendor=user,id=traveldata.id)
#                     if agencydata.commission_rate >0:
#                         commision = sellingprices*agencydata.commission_rate//100
#                         Travelagencyhandling.objects.create(vendor=user,agency=agencydata,bookingdata=Saveadvancebookdata,
#                                                 date=curtdate,commsion=commision)
#                     else:
#                         pass
#             if permissions == 'true':
#                 sellingprices = sellingprices + (extraamountonedayprice * int(totalstaydays))
#                 extraamountsalldays = (extraamountonedayprice * int(totalstaydays))
#                 extrataxfinalamount = extraamountsalldays*18/100
#                 checktotaltax = checktotaltax + extrataxfinalamount
#             SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_before_tax=sellingprices,
#                                 tax=float(checktotaltax),Payment_types=paymenttypes,pah=pah)
            
#             actionss = 'Create Booking'
#             CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
#                     advancebook=Saveadvancebookdata,description=f'Booking Created for {Saveadvancebookdata.bookingguest}, in pms ')

#             if Saveadvancebookdata:
#                 usermsglimit = Messgesinfo.objects.get(vendor=user)
#                 if channal.channalname== "self" :
#                     if usermsglimit.defaultlimit > usermsglimit.changedlimit :
#                         addmsg = usermsglimit.changedlimit + 2
#                         Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
#                         profilename = HotelProfile.objects.get(vendor=user)
#                         mobile_number = phone
                        
#                         # message_content = f"Dear guest, Your booking at {profilename.name} is confirmed. Advance payment of Rs.{advanceamount} received. Check-in date: {bookingdate}. We're thrilled to host you and make your stay unforgettable. For assistance, contact us at {profilename.contact}. -BILLZIFY"
#                         oururl = 'https://live.billzify.com/receipt/88/'
#                         # message_content = f"Hello {guestname}, Your reservation is confirmed. View your booking details here: {oururl}-BILLZIFY"
#                         bids=Saveadvancebookdata.id
#                         message_content = f"Hello {guestname}, Your hotel reservation is confirmed. View your booking details here: https://live.billzify.com/receipt/?cd={bids} -BILLZIFY"
                        
#                         base_url = "http://control.yourbulksms.com/api/sendhttp.php"
#                         params = {
#                             'authkey': settings.YOURBULKSMS_API_KEY,
#                             'mobiles': mobile_number,
#                             'sender':  'BILZFY',
#                             'route': '2',
#                             'country': '0',
#                             'DLT_TE_ID': '1707173659916248212'
#                         }
#                         encoded_message = urllib.parse.urlencode({'message': message_content})
#                         url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
#                         try:
#                             response = requests.get(url)
#                             if response.status_code == 200:
#                                 try:
#                                     response_data = response.json()
#                                     if response_data.get('Status') == 'success':
#                                         messages.success(request, 'SMS sent successfully.')
#                                     else:
#                                         messages.success(request, response_data.get('Description', 'Failed to send SMS'))
#                                 except ValueError:
#                                     messages.success(request, 'Failed to parse JSON response')
#                             else:
#                                 messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
#                         except requests.RequestException as e:
#                             messages.success(request, f'Error: {str(e)}')
#                     else:
#                         messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
#             else:
#                 messages.success(request, 'No data found matching the query')
            
        

#             messages.success(request,"Booking Done")
                
#             url = f"{reverse('receipt_view')}?cd={Saveadvancebookdata.id}"

#             if hasattr(user, 'subuser_profile'):
#                 subuser = user.subuser_profile
#                 if not subuser.is_cleaner:
#                     # Update main user's notification (for subuser)
#                     main_user = subuser.vendor
#                     if main_user.is_authenticated:
#                         request.session['notification'] = True  # Update main user's session
#                         request.session.modified = True
#                     # Update subuser's own notification
#                     request.session['notification'] = True  # Update subuser's session
#                     request.session.modified = True
#             else:
#                 # If it's a main user, update their notification
#                 request.session['notification'] = True
#                 request.session.modified = True
#             return redirect(url)
#             # return redirect('advanceroombookpage')
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)


# ye new code bana rha me new amounts ke liye
def addadvancebooking(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookingdate = request.POST.get('bookingdate')
            guestname = request.POST.get('guestname')
            totalstaydays = request.POST.get('totalstaydays')
            phone = request.POST.get('phone',0)
            channal = request.POST.get('channal')
            bookenddate = request.POST.get('bookenddate')
            totalamount = float(request.POST.get('finalesamount'))
            advanceamount = request.POST.get('advanceamount',0)
            discountamount = float(request.POST.get('discountamount',0))
            reaminingamount = request.POST.get('reaminingamount',0)
            mealplan = request.POST.get('mealplan')
            guestcount = request.POST.get('guestcount')
            paymentmode = request.POST.get('paymentmode')

            sprequest = request.POST.get('sprequest')

            serialized_array = request.POST['news']
            channal=onlinechannls.objects.get(id=channal)
            my_array = json.loads(serialized_array)
            noofrooms = len(my_array)
            bookenddate = str(bookenddate)
            # bookenddate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
            bookingdate = datetime.strptime(bookingdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
            checkoutdate -= timedelta(days=1)
            # bookingdate -= timedelta(days=1)
            if advanceamount == "":
                advanceamount = 0.0
            else:
                pass
            if float(advanceamount) > float(totalamount):
                messages.error(request,"Advance amount is greater than the booking amount!")
                return redirect('advanceroombookpage')


            # delta = timedelta(days=1)
            # while bookingdate <= checkoutdate:
           
            #         bookingdate += delta
            current_date = datetime.now()

            checktestamount = float(totalamount)
           
            reaminingamount = checktestamount - float(advanceamount)
            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(vendor=user,bookingdate=bookingdate,noofrooms=noofrooms,bookingguest=guestname,
                bookingguestphone=phone,staydays=totalstaydays,advance_amount=advanceamount,reamaining_amount=reaminingamount,discount=0.00,
                total_amount=totalamount,channal=channal,checkoutdate=bookenddate,email='',address_city='',state='',country='',totalguest=guestcount,
                action='book',booking_id=None,cm_booking_id=None,segment='PMS',special_requests=sprequest,pah=True,amount_after_tax=totalamount,amount_before_tax=0.00,
                  tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=True,is_noshow=False,is_hold=False,)
            paymenttypes = 'postpaid'
            pah=True
            if int(advanceamount) > 0:
                
                InvoicesPayment.objects.create(vendor=user,invoice=None,payment_amount=advanceamount,payment_date=current_date,
                                                payment_mode=paymentmode,transaction_id="ADVANCE AMOUNT",descriptions='ADVANCE',advancebook=Saveadvancebookdata)
                if int(advanceamount) < int(totalamount):
                    paymenttypes = 'partially'
                    pah=True
                else:
                    paymenttypes = 'prepaid'
                    pah=False
            else:
                pass 
            sellingprices = 0    
            totaltax = 0   
            guestcountsstored = int(guestcount) 
            changedguestct = guestcountsstored

            # new code
            settled_amount = float(totalamount)
            system_total_amount = float(request.POST.get('totalamount'))
            stay_days = int(totalstaydays)
            adjustable_amount = settled_amount
            actual_total_price = system_total_amount
            total_actual_tax = 0

            # Step 1: Proportional adjustment
            adjusted_sum = 0
            for idx, i in enumerate(my_array):
                base_price = float(i['price'])
                tax_percent = float(i['tax'])
                final_price = base_price * (1 + tax_percent / 100)
                i['original_final'] = final_price

                i['adjust_ratio'] = final_price / actual_total_price

                if idx < len(my_array) - 1:
                    this_adjusted = round(adjustable_amount * i['adjust_ratio'], 2)
                    adjusted_sum += this_adjusted
                else:
                    this_adjusted = round(adjustable_amount - adjusted_sum, 2)

                per_day_adjusted_final = this_adjusted / stay_days
                i['adjusted_final_per_day'] = round(per_day_adjusted_final, 2)

            # Step 2: Tax logic on per-day price
            for i in my_array:
                per_day_final = i['adjusted_final_per_day']

                if per_day_final <= 8400:
                    base = per_day_final / 1.12
                    tax = per_day_final - base
                    tax_percent = 12

                    i['adjusted_base_per_day'] = round(base, 2)
                    i['adjusted_tax_per_day'] = round(tax, 2)
                    i['adjusted_tax_percent'] = tax_percent
                    i['multi_tax_permission'] = False
                    i['is_split_tax'] = False

                elif 8400 < per_day_final <= 8850:
                    base_12 = 7500
                    tax_12 = base_12 * 0.12
                    limit_12_total = base_12 + tax_12

                    extra_amt = per_day_final - limit_12_total
                    base_18 = extra_amt / 1.18
                    tax_18 = extra_amt - base_18

                    final_tax = tax_12 + tax_18

                    # ✅ Don't touch the base: Keep it 7500
                    i['adjusted_base_per_day'] = round(base_12, 2)
                    i['adjusted_tax_per_day'] = round(final_tax, 2)
                    i['adjusted_tax_percent'] = 12
                    i['multi_tax_permission'] = True
                    i['is_split_tax'] = True

                    # ✅ New vars for your model structure
                    i['extra_split_tax_details'] = {
                        'tax_12': round(tax_12, 2),
                        'extra_tax_18': round(tax_18, 2),
                        'base_18': round(base_18, 2)
                    }

                else:
                    base = per_day_final / 1.18
                    tax = per_day_final - base
                    tax_percent = 18

                    i['adjusted_base_per_day'] = round(base, 2)
                    i['adjusted_tax_per_day'] = round(tax, 2)
                    i['adjusted_tax_percent'] = tax_percent
                    i['multi_tax_permission'] = False
                    i['is_split_tax'] = False

            # Step 3: Total for full stay
            for i in my_array:
                i['adjusted_base'] = round(i['adjusted_base_per_day'] * stay_days, 2)
                i['adjusted_tax'] = round(i['adjusted_tax_per_day'] * stay_days, 2)
                i['adjusted_final'] = round(i['adjusted_base'] + i['adjusted_tax'], 2)
                total_actual_tax += i['adjusted_tax']

            # Step 4: Overwrite for frontend
            for i in my_array:
                i['price'] = round(i['adjusted_base_per_day'], 2)
                i['tax'] = i['adjusted_tax_percent']

                if i['is_split_tax']:
                    print(f"[SPLIT] Room ID {i['id']}  | Price: ₹{i['price']} | Tax: 12% + 18% (Base fixed: ₹7500, Extra Tax 18% on ₹{i['extra_split_tax_details']['base_18']})")
                else:
                    print(f"[REGULAR] Room ID {i['id']}  | Price: ₹{i['price']} | Tax: {i['tax']}%")

            print(f"📦 Total Adjusted Tax from all rooms: ₹{round(total_actual_tax, 2)}")


            # new code end
            
            for i in my_array:
                    roomid = int(i['id'])
                    # start nre work
                    roomsellprice = float(i['price'])
                    roomselltax = int(float(i['tax']))
                    print(roomsellprice,'price',roomselltax,'tax')
                    

                    # end here
                    # roomsellprice = findamtsonly
                    # roomselltax = selltax
                    befortselprice=roomsellprice
                    befortselprice = befortselprice / int(totalstaydays)
                    sellingprices = sellingprices + roomsellprice * int(totalstaydays)
                    totalsellprice = (roomsellprice * roomselltax //100) + roomsellprice
                    totaltax = totaltax + (roomsellprice * roomselltax /100) 
                    checktotaltax = totaltax * int(totalstaydays)
                    roomid = Rooms.objects.get(id=roomid)
                    roomtype = roomid.room_type.id

                    # # manage rate plan guests
                    maxperson = roomid.max_person
                    if changedguestct >= maxperson:
            
                        changedguestct = changedguestct - maxperson
                  
                        satteldcount = maxperson
                    else:
                 
                        satteldcount = changedguestct

                
                    bookdatas = RoomBookAdvance.objects.create(vendor=user,saveguestdata=Saveadvancebookdata,bookingdate=bookingdate,roomno=roomid,
                                                    bookingguest=guestname,bookingguestphone=phone
                                                ,checkoutdate=bookenddate,bookingstatus=True,channal=channal,totalguest=satteldcount,
                                               rateplan_code=mealplan,guest_name='',adults=satteldcount,children=0,sell_rate=roomsellprice )
                    
                    if i.get('multi_tax_permission'):
                        extra_base = i.get('extra_split_tax_details', {}).get('base_18', 0)
                        extra_tax = i.get('extra_split_tax_details', {}).get('extra_tax_18', 0)
                        # extraonedayprice = extraamountonedayprice
                        # extra_total_amount_allday = extraamountonedayprice * int(totalstaydays)
                        # extrataxamount = extra_total_amount_allday * 18 /100
                        # extracgstamount = extrataxamount / 2
                        # extragrandtotal  = extra_total_amount_allday + extrataxamount

                        # totalamount = extragrandtotal + totalamount
                        # extraBookingAmount.objects.create(vendor=user,bookdata=bookdatas,price=extraonedayprice,qty=int(totalstaydays),
                        #                 taxable_amount=extra_total_amount_allday,csgst_amount=extracgstamount,sgst_amount=extracgstamount,
                        #                 grand_total_amount=extragrandtotal)
                        totaltaxablesextramt = extra_base * int(totalstaydays)
                        cgsttaxextraamt = (extra_tax /2 ) * int(totalstaydays)
                        gtextramt = extra_tax *  int(totalstaydays) + totaltaxablesextramt
                        extraBookingAmount.objects.create(vendor=user,bookdata=bookdatas,price=extra_base,qty=int(totalstaydays),
                                        taxable_amount=totaltaxablesextramt,csgst_amount=cgsttaxextraamt,sgst_amount=cgsttaxextraamt,
                                        grand_total_amount=gtextramt)
                    
                    noon_time_str = "12:00 PM"
                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                    Booking.objects.create(vendor=user,room=roomid,guest_name=guestname,check_in_date=bookingdate,check_out_date=bookenddate,
                                check_in_time=noon_time,check_out_time=noon_time,segment=channal,totalamount=totalamount,totalroom=noofrooms,
                                gueststay=None,advancebook=Saveadvancebookdata,status="BOOKING"           )
                    # inventory code
                    # Convert date strings to date objects
                    checkindate = str(bookingdate)
                    checkoutdate = str(bookenddate)
                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                    checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                    # Generate the list of all dates between check-in and check-out (inclusive)
                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

                    # Query the RoomsInventory model to check if records exist for all those dates
                    existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

                    # Get the list of dates that already exist in the inventory
                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                    # Identify the missing dates by comparing all_dates with existing_dates
                    missing_dates = [date for date in all_dates if date not in existing_dates]

                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                    roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
              
                    # occupancy = (1 * 100 // roomcount)
                    
                    for inventory in existing_inventory:
                        
                       
                        if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
                            # Update room availability and booked rooms
                            inventory.total_availibility -= 1
                            inventory.booked_rooms += 1

                            # Calculate total rooms
                            total_rooms = inventory.total_availibility + inventory.booked_rooms

                            # Recalculate the occupancy rate
                            if total_rooms > 0:
                                # Directly calculate occupancy as the percentage of booked rooms
                                inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
                            else:
                                inventory.occupancy = 0  # Avoid division by zero if no rooms exist

                            # Save the updated inventory
                            inventory.save()

                    
                    catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
                    totalrooms = Rooms.objects.filter(vendor=user,room_type=catdatas).exclude(checkin=6).count()
                    occupancccy = (1 *100 //totalrooms)
                    if missing_dates:
                        for missing_date in missing_dates:
                        
                                RoomsInventory.objects.create(
                                    vendor=user,
                                    date=missing_date,
                                    room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
                                    total_availibility=totalrooms-1,       # Set according to your logic
                                    booked_rooms=1,    
                                    occupancy=occupancccy,
                                    price=catdatas.catprice
                                                            # Set according to your logic
                                )
                        
                    else:
                        pass

                    # api calling backend automatically
                                # Start the long-running task in a separate thread
            if VendorCM.objects.filter(vendor=user):
                        start_date = str(checkindate)
                        end_date = str(checkoutdate)
                        thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                        thread.start()
                        # for dynamic pricing
                        if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                            thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                            thread.start()
                        else:
                            pass
            else:
                        pass
            # if TravelAgency.objects.filter(vendor=user,name=channal.channalname).exists():
            #     traveldata = TravelAgency.objects.filter(vendor=user,name=channal.channalname).first()
            #     curtdate = datetime.now().date()
            #     if traveldata.commission_rate > 0:
            #         agencydata = TravelAgency.objects.get(vendor=user,id=traveldata.id)
            #         if agencydata.commission_rate >0:
            #             commision = sellingprices*agencydata.commission_rate//100
            #             Travelagencyhandling.objects.create(vendor=user,agency=agencydata,bookingdata=Saveadvancebookdata,
            #                                     date=curtdate,commsion=commision)
            #         else:
            #             pass
            # # if permissions == 'true':
            # #     sellingprices = sellingprices + (extraamountonedayprice * int(totalstaydays))
            # #     extraamountsalldays = (extraamountonedayprice * int(totalstaydays))
            # #     extrataxfinalamount = extraamountsalldays*18/100
            # #     checktotaltax = checktotaltax + extrataxfinalamount
            amtbeforetax = settled_amount - total_actual_tax
            amtaftertax = settled_amount
            SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_before_tax=amtbeforetax,
                                tax=float(total_actual_tax),Payment_types=paymenttypes,pah=pah)
            
            actionss = 'Create Booking'
            CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Booking Created for {Saveadvancebookdata.bookingguest}, in pms ')

            if Saveadvancebookdata:
                usermsglimit = Messgesinfo.objects.get(vendor=user)
                if channal.channalname== "self" :
                    if usermsglimit.defaultlimit > usermsglimit.changedlimit :
                        addmsg = usermsglimit.changedlimit + 2
                        Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                        profilename = HotelProfile.objects.get(vendor=user)
                        mobile_number = phone
                        
                        # message_content = f"Dear guest, Your booking at {profilename.name} is confirmed. Advance payment of Rs.{advanceamount} received. Check-in date: {bookingdate}. We're thrilled to host you and make your stay unforgettable. For assistance, contact us at {profilename.contact}. -BILLZIFY"
                        oururl = 'https://live.billzify.com/receipt/88/'
                        # message_content = f"Hello {guestname}, Your reservation is confirmed. View your booking details here: {oururl}-BILLZIFY"
                        bids=Saveadvancebookdata.id
                        message_content = f"Hello {guestname}, Your hotel reservation is confirmed. View your booking details here: https://live.billzify.com/receipt/?cd={bids} -BILLZIFY"
                        
                        base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                        params = {
                            'authkey': settings.YOURBULKSMS_API_KEY,
                            'mobiles': mobile_number,
                            'sender':  'BILZFY',
                            'route': '2',
                            'country': '0',
                            'DLT_TE_ID': '1707173659916248212'
                        }
                        encoded_message = urllib.parse.urlencode({'message': message_content})
                        url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('Status') == 'success':
                                        messages.success(request, 'SMS sent successfully.')
                                    else:
                                        messages.success(request, response_data.get('Description', 'Failed to send SMS'))
                                except ValueError:
                                    messages.success(request, 'Failed to parse JSON response')
                            else:
                                messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
                        except requests.RequestException as e:
                            messages.success(request, f'Error: {str(e)}')
                    else:
                        messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
            else:
                messages.success(request, 'No data found matching the query')
            
        

            messages.success(request,"Booking Done")
                
            url = f"{reverse('receipt_view')}?cd={Saveadvancebookdata.id}"

            if hasattr(user, 'subuser_profile'):
                subuser = user.subuser_profile
                if not subuser.is_cleaner:
                    # Update main user's notification (for subuser)
                    main_user = subuser.vendor
                    if main_user.is_authenticated:
                        request.session['notification'] = True  # Update main user's session
                        request.session.modified = True
                    # Update subuser's own notification
                    request.session['notification'] = True  # Update subuser's session
                    request.session.modified = True
            else:
                # If it's a main user, update their notification
                request.session['notification'] = True
                request.session.modified = True
            return redirect(url)
            # return redirect('advanceroombookpage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def todaybookingpage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor
            # today=datetime.date.today() 
            today = datetime.now().date()
            checkoutdate = datetime.now().date()
            changeddate = today - timedelta(days=1)
            roomdata = RoomBookAdvance.objects.filter(vendor=user,bookingdate=today,bookingstatus=True).all()
            # advancebookdata = RoomBookAdvance.objects.filter(vendor=user,bookingdate=today)
            advancebookcheckoutdata = RoomBookAdvance.objects.filter(vendor=user,checkoutdate=checkoutdate).exclude(vendor=user,saveguestdata__action='cancel')
            
          
            for i in advancebookcheckoutdata:
                if i.roomno.checkin == 4 :
                    if  i.roomno.checkin == 5:
                        pass
                    else: 
                        roomid = i.roomno.id
                       
                        Rooms.objects.filter(vendor=user,id=i.roomno.id).update(checkin=0) 
                else:
                    pass
            allbookdata = RoomBookAdvance.objects.filter(vendor=user,bookingdate__lte=today, checkoutdate__gte=today,checkinstatus=False).exclude(vendor=user,saveguestdata__action='cancel')
       
            return render(request,'todayarrivalsrom.html',{'active_page':'todaybookingpage','roomdata':roomdata,'advancebookdata':allbookdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def openroomclickformtodayarriwalspage(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            room_data = Rooms.objects.filter(vendor=user,room_name=id)
            roomno=id
            roomguestdata = RoomBookAdvance.objects.filter(vendor=user,id=id).all()
            loyltydata = loylty_data.objects.filter(vendor=user,Is_active=True)
            today=datetime.now().date()
            saveguestdata = 0
            guestphone = 0
            for i in roomguestdata:
                guestphone=i.bookingguestphone
                saveguestdata = i.saveguestdata.id
            paymentdatauserfromsaveadvancedata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestdata).all()
            roomnumberdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata)
            countrooms = len(roomnumberdata)
            adults = 0
            child = 0
            for i in roomnumberdata:
                adults  = adults + i.adults
                child = child +i.children

            # return render(request,'advanceroomclickpage.html',{'id':roomno,'countrooms':countrooms,'roomnumberdata':roomnumberdata,'room_data':room_data,'roomguestdata':roomguestdata})
            return render(request,'advanceroomclickpage.html',{'loyltydata':loyltydata,'id':roomno,
                                    'countrooms':countrooms,'roomnumberdata':roomnumberdata,
                                    'room_data':room_data,'roomguestdata':roomguestdata,
                                    'paymentdatauserfromsaveadvancedata':paymentdatauserfromsaveadvancedata,
                                    'adults':adults,'child':child})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def weekviewcheckin(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookidsmain = int(request.POST.get('bookidsmain'))

            if Booking.objects.filter(vendor=user,id=bookidsmain).exists():
                bookingdata = Booking.objects.get(vendor=user,id=bookidsmain)
                checkbookdata = Booking.objects.filter(vendor=user,advancebook=bookingdata.advancebook).all()
                for i in checkbookdata:
                    if Booking.objects.filter(vendor=user,room=i.room,status="CHECK IN").exclude(id=i.id).last():
                        messages.error(request,"You need to check out from your current room before you can check in to the new one.")
                        return redirect('weekviews')
                    else:
                        pass

                if checkbookdata.filter(room__checkin=5):
                    messages.error(request,'Guests are already checked in. Please proceed with the check-in one by one from here.')
                    return redirect('todaybookingpage')

                
                
                
                roomname  =   bookingdata.room.id
                room_data = Rooms.objects.filter(vendor=user,id=roomname)
                roomno = bookingdata.room.room_name
                if RoomBookAdvance.objects.filter(vendor=user,saveguestdata=bookingdata.advancebook):
                    
                    roomsbookdata = RoomBookAdvance.objects.get(vendor=user,saveguestdata=bookingdata.advancebook,roomno=bookingdata.room)
                    id = roomsbookdata.id
                    roomguestdata = RoomBookAdvance.objects.filter(vendor=user,id=id).all()
                    loyltydata = loylty_data.objects.filter(vendor=user,Is_active=True)
                    today=datetime.now().date()
                    saveguestdata = 0
                    guestphone = 0
                    for i in roomguestdata:
                        guestphone=i.bookingguestphone
                        saveguestdata = i.saveguestdata.id
                    paymentdatauserfromsaveadvancedata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestdata).all()
                    roomnumberdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata)
                    countrooms = len(roomnumberdata)
                    adults = 0
                    child = 0
                    for i in roomnumberdata:
                        adults  = adults + i.adults
                        child = child +i.children

                    # return render(request,'advanceroomclickpage.html',{'id':roomno,'countrooms':countrooms,'roomnumberdata':roomnumberdata,'room_data':room_data,'roomguestdata':roomguestdata})
                    return render(request,'advanceroomclickpage.html',{'loyltydata':loyltydata,'id':roomno,
                                            'countrooms':countrooms,'roomnumberdata':roomnumberdata,
                                            'room_data':room_data,'roomguestdata':roomguestdata,
                                            'paymentdatauserfromsaveadvancedata':paymentdatauserfromsaveadvancedata,
                                            'adults':adults,'child':child})
            else:
                messages.error(request,"Booking Id Not Found Please Check From Today Arrivals Page!")
                return redirect('weekviews')
            
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

    
# one by one chekcin function
def chekinonebyoneguestdata(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roombookadvanceiddata = request.POST.get('roombookadvanceiddata')
            roomnodata = request.POST.get('roomnodata')
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            roombookingdata = RoomBookAdvance.objects.get(vendor=user,id=roombookadvanceiddata)
            if roombookingdata and Gueststay.objects.filter(vendor=user,saveguestid=roombookingdata.saveguestdata.id).exists():
                guestdata = Gueststay.objects.filter(vendor=user,saveguestid=roombookingdata.saveguestdata.id).last()
                MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=name,another_guest_phone=phone,another_guest_address=address)
            today = datetime.now().date()
            RoomBookAdvance.objects.filter(vendor=user,id=roombookadvanceiddata).update(checkinstatus=True,bookingdate=today)
            
            Rooms.objects.filter(vendor=user,id=roombookingdata.roomno.id).update(checkin=1)
            ctime = datetime.now().time()
            Booking.objects.filter(vendor=user,advancebook_id=roombookingdata.saveguestdata.id,room_id=roombookingdata.roomno.id).update(status="CHECK IN",check_in_time=ctime)
                
            return  redirect('todaybookingpage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



def opencheckinforadvanebooking(request,pk):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            return render(request,'index.html')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


from django.db.models import OuterRef, Subquery
# advancebook page function
def advanceroomhistory(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            # Get today's date
            # today = timezone.now().date()
            today = datetime.now().date()

            # Define the date range
            # Example: Get dates within the next 7 days from today
            start_date = today
            end_date = today + timedelta(days=7)

            # Query to filter records within the date range and order by bookingdate
            filtered_orders = SaveAdvanceBookGuestData.objects.filter(
                vendor=user,
                bookingdate__range=(start_date, end_date)
                    ).order_by('-id')
            # advanceroomdata = RoomBookAdvance.objects.filter(vendor=user).all().order_by('bookingdate')
            advanceroomsdata = SaveAdvanceBookGuestData.objects.filter(vendor=user).all().order_by('-id')
            page = request.GET.get('page', 1) 
            paginator = Paginator(advanceroomsdata, 25) 
            try: 
                advanceroomdata = paginator.page(page) 
            except PageNotAnInteger: 
                advanceroomdata = paginator.page(1) 
            except EmptyPage: 
                advanceroomdata = paginator.page(paginator.num_pages) 

           
            now = timezone.now()

            # Determine the first and last day of the current month
            first_day_of_month = now.replace(day=1)
            if now.month == 12:  # Handle December to January transition
                # last_day_of_month = now.replace(year=now.year + 1, month=1, day=1) - timezone.timedelta(days=1)
                last_day_of_month = today
            else:
                # last_day_of_month = now.replace(month=now.month + 1, day=1) - timezone.timedelta(days=20)
                last_day_of_month = today
        


            # ye pahle ka code hai 
            # monthbookdata  = SaveAdvanceBookGuestData.objects.filter(
            #     vendor=user,
            #     bookingdate__range=(first_day_of_month, last_day_of_month)
            #         ).order_by('bookingdate')

            # ye new code hai
            from django.db.models import Prefetch
            from collections import Counter

            room_prefetch = Prefetch(
                'roombookadvance_set',
                queryset=RoomBookAdvance.objects.select_related('roomno__room_type'),
                to_attr='booked_rooms'
            )

            monthbookdata = SaveAdvanceBookGuestData.objects.filter(
                vendor=user,
                bookingdate__range=(first_day_of_month, last_day_of_month)
            ).prefetch_related(room_prefetch).order_by('bookingdate')

            for guest in monthbookdata:
                category_names = [
                    room.roomno.room_type.category_name
                    for room in guest.booked_rooms
                ]
                category_counts = Counter(category_names)

                guest.room_categories_summary = ", ".join(
                    f"({count}) {cat}" for cat, count in category_counts.items()
                )



            return render(request,'advancebookinghistory.html',{'filtered_orders':filtered_orders,'advanceroomdata':advanceroomdata,'active_page': 'advancebookhistory','monthbookdata':monthbookdata
                                                            ,'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



# advance details function
def advancebookingdetails(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id)
            roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=id).all()
            bookdatesdata = bookpricesdates.objects.filter(roombook__saveguestdata__id=id).all()
            tdscomm = tds_comm_model.objects.filter(roombook_id=id).first()

            advancepayment = InvoicesPayment.objects.filter(vendor=user,advancebook_id=id).all()
            return render(request,'advancebookingdetailspage.html',{'roomdata':roomdata,'guestdata':guestdata,'active_page': 'advancebookhistory',
                        'tdscomm':tdscomm,'advancepayment':advancepayment,'bookdatesdata':bookdatesdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

# advance booking delete function
def advancebookingdelete(request,id):
    # try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            saveguestid=id
            checkdatas = SaveAdvanceBookGuestData.objects.get(vendor=user,id=saveguestid)
            # if not  checkdatas.booking_id :
            if checkdatas.checkinstatus==False:
                roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid,partly_checkin=False).all()
                checkroomdata = Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid).all()
                if roomdata: 
                    for data in roomdata:
                        Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                        checkindate = data.bookingdate
                        checkoutdate = data.checkoutdate
                        while checkindate < checkoutdate:
                            
                            roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                            if RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).exists():
                                invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                        
                                invtavaible = invtdata.total_availibility + 1
                                invtabook = invtdata.booked_rooms - 1
                                total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                occupancy = invtabook * 100//total_rooms
                                                                        

                                RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                            total_availibility=invtavaible,occupancy=occupancy)
                
                            checkindate += timedelta(days=1)

                    if VendorCM.objects.filter(vendor=user):
                        start_date = str(checkdatas.bookingdate)
                        end_date = str(checkdatas.checkoutdate)
                        
                        thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                        thread.start()

                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid).update(action='cancel')
                    Booking.objects.filter(vendor=user,advancebook_id=saveguestid).delete()
                    actionss = 'Cancel Booking'
                    CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                        advancebook=checkdatas,description=f'Booking Cancel for {checkdatas.bookingguest},  ')

                  
                    messages.success(request,'booking Cancelled succesfully')
                elif checkroomdata:
                    for data in checkroomdata:
                        # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                        checkindate = checkdatas.bookingdate
                        checkoutdate = checkdatas.checkoutdate
                        while checkindate < checkoutdate:
                            
                            roomscat = data.room_category
                            if RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat).exists():
                                invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat)
                        
                                invtavaible = invtdata.total_availibility + 1
                                invtabook = invtdata.booked_rooms - 1
                                total_rooms = Rooms_count.objects.filter(vendor=user, room_type=roomscat).values_list('total_room_numbers', flat=True).first() or 0
                                occupancy = invtabook * 100//total_rooms
                                                                        

                                RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat).update(booked_rooms=invtabook,
                                            total_availibility=invtavaible,occupancy=occupancy)
                
                            checkindate += timedelta(days=1)

                    if VendorCM.objects.filter(vendor=user):
                        start_date = str(checkdatas.bookingdate)
                        end_date = str(checkdatas.checkoutdate)
                        
                        thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                        thread.start()

                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid).update(action='cancel')
                    Booking.objects.filter(vendor=user,advancebook_id=saveguestid).delete()
                    actionss = 'Cancel Booking'
                    CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                        advancebook=checkdatas,description=f'Booking Cancel for {checkdatas.bookingguest},  ')

                  
                    messages.success(request,'booking Cancelled succesfully')
                else:
                    messages.error(request,'Guest Is Stayed If You Want To Delete So cancel the folio room.')
                # advanceroomdata = SaveAdvanceBookGuestData.objects.filter(vendor=user).all()
                # return render(request,'advancebookinghistory.html',{'advanceroomdata':advanceroomdata,'active_page': 'advancebookhistory'})
                if Vendor_Service.objects.filter(vendor=user,only_cm=True):
                    return redirect('cm')
                return redirect('advanceroomhistory')
            else:
                if Vendor_Service.objects.filter(vendor=user,only_cm=True):
                    return redirect('cm')
                messages.error(request,'Guest Is Stayed If You Want To Delete So cancel the folio room.')
                return redirect('advanceroomhistory')
        else:
            return redirect('loginpage')
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)
    

# add profile hotels
def addprofile(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if HotelProfile.objects.filter(vendor=user).exists():
                profiledata =  HotelProfile.objects.filter(vendor=user)
                return render(request,'profile.html',{'profiledata':profiledata})
            else:
                hotelame = request.POST.get('hotelame')
                email = request.POST.get('email')
                phoneNumber = request.POST.get('phoneNumber',0)
                address = request.POST.get('address')
                ziCode = request.POST.get('zipCode')
                country = request.POST.get('country')
                checkintime = request.POST.get('checkintime')
                checkouttime = request.POST.get('checkouttime')
                logoimg = request.FILES['logoimg']
                gstnumber = request.POST.get('gstnumber')
                termscondition = request.POST.get('termscondition')
                HotelProfile.objects.create(vendor=user,name=hotelame,email=email,contact=phoneNumber,address=address,
                        zipcode=ziCode,gstin= gstnumber, profile_image=logoimg,counrty=country,
                        checkintimes=checkintime,checkouttimes=checkouttime,termscondition=termscondition)
                profiledata =  HotelProfile.objects.filter(vendor=user)
                return render(request,'profile.html',{'profiledata':profiledata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



def updateprofile(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            hotelame = request.POST.get('hotelame')
            email = request.POST.get('email')
            phoneNumber = request.POST.get('phoneNumber', 0)
            address = request.POST.get('address')
            zipCode = request.POST.get('zipCode')
            country = request.POST.get('country')
            logoimg = request.FILES.get('logonewimg')  # Use get to avoid KeyError if file is not uploaded
            gstnumber = request.POST.get('gstnumber')
            checkintime = request.POST.get('checkintime')
            checkouttime = request.POST.get('checkouttime')
            termscondition = request.POST.get('termscondition')
            try:
                profile = HotelProfile.objects.get(vendor=user)
                profile.name = hotelame
                profile.email = email
                profile.contact = phoneNumber
                profile.address = address
                profile.zipcode = zipCode
                profile.counrty = country
                profile.gstin = gstnumber
                profile.checkintimes = checkintime
                profile.checkouttimes = checkouttime
                profile.termscondition = termscondition
            
                if logoimg:
                    profile.profile_image = logoimg  # Update the image only if a new one is provided
                profile.save()
            except HotelProfile.DoesNotExist:
                messages.error(request, 'Profile does not exist')

            profiledata = HotelProfile.objects.filter(vendor=user)
            return render(request, 'profile.html', {'profiledata': profiledata})

        else:
            return redirect('loginpage')  # Redirect to login if not authenticated or not a POST request
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    




def IGfKg(request):
    try:
        return render(request,'IGfKg.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


import qrcode
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile

def generate_qr(request, url):
    # Generate the QR code
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Use high error correction to allow for logo
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Get the logo image path from the static files
        logo_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'img', 'newshadowlogo.png')
        print(f"Logo path: {logo_path}")  # Debug statement to print the logo path

        if not os.path.exists(logo_path):
            print(f"Logo file not found at: {logo_path}")
            return HttpResponseNotFound("Logo image not found.")
        
        try:
            # Open the logo image
            logo = Image.open(logo_path)
            print("Logo image opened successfully.")  # Debug statement to confirm the image is opened
            
            # Ensure the logo image has an alpha channel
            logo = logo.convert("RGBA")

            # Calculate logo size and position
            qr_width, qr_height = qr_image.size
            logo_size = qr_width // 5
            logo = logo.resize((logo_size, logo_size), Image.ANTIALIAS)

            # Calculate logo position to center it on the QR code
            logo_position = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

            # Paste the logo onto the QR code
            qr_image.paste(logo, logo_position, logo)

        except Exception as e:
            print(f"Error opening/logo image: {e}")
            return HttpResponse("Error opening/logo image.", status=500)

        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
                user = subuser.vendor  
        # Create an HTTP response with the QR code image
        # Save the QR code image to an in-memory file
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Create a Django file from the in-memory file
        file_name = f'user_{user.id}_qr.png'
        file_content = ContentFile(buffer.read(), name=file_name)

        # Save the file to the model's qr_code field
        # reviewQr.qrimage.save(file_name, file_content, save=True)
        # reviewQr.objects.create(vendor=user,qrimage=file_content)
        response = HttpResponse(content_type="image/png")
        qr_image.save(response, "PNG")
        return response
    
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


# views.py
from django.shortcuts import render

def qr_code(request):
    url = "https://www.billzify.com/IGfKg/120"  # Replace this with your desired URL
    return render(request, 'qr_code.html', {'url': url})
# isko chalane ke liye url map krni hogi empty us din jase 


# from django.shortcuts import render

# def subscription_expired(request):
#     return render(request, 'login.html')

# def no_subscription(request):
#     return render(request, 'login.html')


def password_reset_request(request):
    try:
        if request.method == 'POST':
            username = request.POST['username']
            new_password = request.POST['new_password']
            try:
                
                user = User.objects.get(username=username)
                if Subuser.objects.filter(user=user).exists():
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, 'Password reset successfully!')
                    return redirect('rollspermission')

                else:
                    messages.error(request,"Only Subuser Password chaned their!")
                    return render(request, 'password_reset_form.html')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username')
        return render(request, 'password_reset_form.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

from django.contrib.auth import logout as auth_logout

# def logout_view(request):
#     if 'permissions' in request.session:
#         del request.session['permissions']
#     if 'is_subuser' in request.session:
#         del request.session['is_subuser']
#     auth_logout(request)  # Log out the user
#     response = redirect('loginpage')  # Redirect to the login page or any other page
#     # Clear all cookies
#     for cookie in request.COOKIES:
#         response.delete_cookie(cookie)

    
#     return response

def logout_view(request):
    # Clear session data manually (or use request.session.flush() for clearing all)
    request.session.flush()

    # Log out the user using Django's authentication system
    auth_logout(request)

    # Redirect to login page
    response = redirect('loginpage')  # Update 'login' with your actual login view name

    # Optionally clear cookies (if needed)
    for cookie in request.COOKIES:
        response.delete_cookie(cookie)

    return response



from django.core.exceptions import ValidationError
# def deleteitemstofolio(request):
#     try:
#         if request.user.is_authenticated and request.method == "POST":
#             user = request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             invoiceid = request.POST.get('invoiceid')
#             invoiceitemsid = request.POST.get('invoiceitemsid')
#             qty = request.POST.get('qty')
#             if Invoice.objects.filter(vendor=user,id=invoiceid).exists():
#                 if InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).exists():
#                     invoiceitemdata = InvoiceItem.objects.get(vendor=user,id=invoiceitemsid,invoice_id=invoiceid)
#                     try:
#                         int_value = int(invoiceitemdata.description)
#                         # If successful, filter using Q objects to handle both int and str queries
#                         if  Rooms.objects.filter(vendor=user,room_name=int_value,price=invoiceitemdata.price).exists():
#                             pass
#                     except (ValueError, TypeError, ValidationError):
#                         if invoiceitemdata.cgst_rate == 0.00:
#                             invoiceamt = invoiceitemdata.total_amount
#                             invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
#                             totalamt = invoicedata.total_item_amount - invoiceamt
#                             subtotalamt = invoicedata.subtotal_amount - invoiceamt
#                             grandtotalamt = invoicedata.grand_total_amount - invoiceamt
#                             dueamount = invoicedata.Due_amount - invoiceamt
#                             if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
#                                 Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
#                                     available_qty=F('available_qty')+invoiceitemdata.quantity_likedays,
#                                 )
#                             else:
#                                 pass
#                             Invoice.objects.filter(vendor=user,id=invoiceid).update(total_item_amount=totalamt,subtotal_amount=subtotalamt,
#                                                             grand_total_amount=grandtotalamt,Due_amount=dueamount)
#                             InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).delete()
                            
                            
                            
#                         else:
#                             invoiceamt = invoiceitemdata.total_amount
#                             qtys = invoiceitemdata.quantity_likedays
#                             priceproduct = invoiceitemdata.price
#                             invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
#                             totalamt = invoicedata.total_item_amount - priceproduct*qtys
#                             subtotalamt = invoicedata.subtotal_amount - priceproduct*qtys
#                             cgstamt = invoicedata.sgst_amount - (invoiceamt-priceproduct*qtys)/2
#                             gstamt = invoicedata.gst_amount - (invoiceamt-priceproduct*qtys)/2
#                             grandtotalamt = invoicedata.grand_total_amount - invoiceamt
#                             dueamount = invoicedata.Due_amount - invoiceamt
#                             if Items.objects.filter(vendor=user,description=invoiceitemdata.description).exists():
#                                 Items.objects.filter(vendor=user,description=invoiceitemdata.description).update(
#                                     available_qty=F('available_qty')+invoiceitemdata.quantity_likedays,
#                                 )
#                             else:
#                                 pass
                            
#                             Invoice.objects.filter(vendor=user,id=invoiceid).update(gst_amount=gstamt,sgst_amount=cgstamt,
#                                                                                     total_item_amount=totalamt,subtotal_amount=subtotalamt,
#                                                                                     grand_total_amount=grandtotalamt,Due_amount=dueamount)
#                             InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).delete()
                            
#                             taxrate = float(invoiceitemdata.cgst_rate)
#                             taxamount = (invoiceamt-priceproduct*qtys)/2
#                             totaltaxamts = taxamount * 2
                          
#                             if taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).exists():
#                                 taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).update(
#                                     cgst_amount=F('cgst_amount') - taxamount,
#                                     sgst_amount=F('sgst_amount') - taxamount,
#                                     total_amount=F('total_amount') - totaltaxamts
#                                 )
                                
                    
#                 else:
#                     messages.error(request, 'Invoice item not exists')
#             else:
#                 messages.error(request, 'Invoice does not exist')
#             ckinvcdata = Invoice.objects.get(vendor=user,id=invoiceid)
#             cstmrid = ckinvcdata.customer.id
#             return redirect('invoicepage', id=cstmrid)
        
#         else:
#             return redirect('loginpage')
        
#     except Exception as e:
#             return render(request, '404.html', {'error_message': str(e)}, status=500) 
# 


def deleteitemstofolio(request):
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
                    try:
                        int_value = int(invoiceitemdata.description)
                        # If successful, filter using Q objects to handle both int and str queries
                        if  Rooms.objects.filter(vendor=user,room_name=int_value,price=invoiceitemdata.price).exists():
                            pass
                    except (ValueError, TypeError, ValidationError):
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
                                            description=f'Remove {invoiceitemdata.description} QTY {qty}')
                            
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
                                            description=f'Remove {invoiceitemdata.description} QTY {qty}')
                            
                            
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
                            # les qty work here
                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty}')


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


                                
                               
                                totaltaxamts = taxamounts * 2
                            
                                if taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).exists():
                                    taxSlab.objects.filter(vendor=user,invoice_id=invoiceid,cgst=taxrate).update(
                                        cgst_amount=F('cgst_amount') - taxamounts,
                                        sgst_amount=F('sgst_amount') - taxamounts,
                                        total_amount=F('total_amount') - totaltaxamts
                                    )

                                actionss = 'Remove Service'
                                CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                                            description=f'Remove {invoiceitemdata.description} QTY {qty}')
                                
                    
                else:
                    messages.error(request, 'Invoice item not exists')
            else:
                messages.error(request, 'Invoice does not exist')
            ckinvcdata = Invoice.objects.get(vendor=user,id=invoiceid)
            cstmrid = ckinvcdata.customer.id
            return redirect('invoicepage', id=cstmrid)
        
        else:
            return redirect('loginpage')
        
    except Exception as e:
            return render(request, '404.html', {'error_message': str(e)}, status=500)     


def addpaymentfolio(request):
     if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invoiceid = request.POST.get('invcids')
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
                InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=today,
                                payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
            elif amount > ida:
                pass
                messages.error(request,"amount graterthen to billing amount!")
            else:
                dueamt = ida-amount
                acceptamt = iaa + amount
                Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=float(dueamt),accepted_amount=float(acceptamt))
            
                messages.success(request,"Payment Added!")
                InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=today,
                                            payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
            
            actionss = 'Create Payment'
            CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                description=f'Payment Added {amount}')


            url = reverse('invoicepage', args=[userid])
            return redirect(url)


def addpaymentfoliocredit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                invoiceid = request.POST.get('invcid')
                amount = int(float(request.POST.get('amount')))
                paymentmode = request.POST.get('paymentmode')
                paymntdetails = request.POST.get('paymntdetails')
                comment = request.POST.get('comment')
                creditid = request.POST.get('creditid')
                today = datetime.now()
                invoicedata = Invoice.objects.get(vendor=user,id=invoiceid)
                igta = int(invoicedata.grand_total_amount)
                ida =int(invoicedata.Due_amount)
                iaa = int(invoicedata.accepted_amount)
                userid = invoicedata.customer.id
                
                if amount == igta:
                    Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=0.00,accepted_amount=float(igta))
                    
                    messages.success(request,"Payment Added!")
                    
                    InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=today,
                                    payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)
                    actionss = 'Create Payment'
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                        description=f'Payment Added {amount}') 

                        
                
                elif amount > ida:
                    pass
                    messages.error(request,"amount graterthen to billing amount!")

                else:
                    dueamt = ida-amount
                    acceptamt = iaa + amount
                    CustomerCredit.objects.filter(vendor=user,id=creditid).update(amount = dueamt)
                    Invoice.objects.filter(vendor=user,id=invoiceid).update(Due_amount=float(dueamt),accepted_amount=float(acceptamt))
                    
                    messages.success(request,"Payment Added!")
                    InvoicesPayment.objects.create(vendor=user,invoice_id=invoiceid,payment_amount=amount,payment_date=today,
                                                payment_mode=paymentmode,transaction_id=paymntdetails,descriptions=comment,advancebook=None)

                    actionss = 'Create Payment'
                    CustomGuestLog.objects.create(vendor=user,customer=invoicedata.customer,by=request.user,action=actionss,
                        description=f'Payment Added {amount}')

                    invoicedatasorg = Invoice.objects.get(vendor=user,id=invoiceid)
                    # if companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatasorg).exists():
                    #             cmpinvcamt = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatasorg)
                    #             reamins = int(float(cmpinvcamt.Value)) - int(float(invoicedatasorg.accepted_amount))
                    #             companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatasorg).update(
                    #                 Value=reamins
                    #             )
                    #             cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatasorg)
                    #             orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
                    #             values = int(float(orgcmp.values))
                    #             updateval = values - int(float(invoicedatasorg.accepted_amount))
                    #             Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
                    #                         values=updateval
                    #             )


                invoicedatas = Invoice.objects.get(vendor=user,id=invoiceid)
                duesamts = int(invoicedatas.Due_amount)
                if duesamts==0:
                        
                        invccurrentdate = datetime.now().date()
                        # invoicenumberfind=Invoice.objects.filter(vendor=user,invoice_status=True).exclude(invoice_number='unpaid').exclude(invoice_number='').last()
                        
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
                        
                        
                        Invoice.objects.filter(vendor=user,id=invoiceid).update(invoice_number=invoice_number,invoice_status=True,modeofpayment="pms",
                                                invoice_date=invccurrentdate)
                        if companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatas).exists():
                                companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatas).update(is_paid=True)
                                # cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatas)
                                # orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
                                # values = int(orgcmp.values)
                                # updateval = values + int(float(invoicedatas.grand_total_amount))
                                # Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
                                #             values=updateval
                                # )
                        CustomerCredit.objects.get(vendor=user,id=creditid).delete()
                        messages.success(request,"Invoice Sattle done Succesfully!")
                            
                        
                else:
                    pass
                # url = reverse('invoicepage', args=[invoicedata.id])
                # return redirect(url)
                return redirect('guestearch', id=invoicedata.customer.id)
     
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def openposforroom(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                invoiceid = request.POST.get('invcid')
                roomno = request.POST.get('roomno')
           
                tax = Taxes.objects.filter(vendor=user)
                folio = Invoice.objects.filter(vendor=user,foliostatus=False)
                iteams = Items.objects.filter(vendor=user)
                laundry = LaundryServices.objects.filter(vendor=user)
                return render(request,'pospage.html',{'tax':tax,'folio':folio,'iteams':iteams,'laundry':laundry,
                                                    'invoiceid':invoiceid,'roomno':roomno})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


from datetime import datetime, timedelta
from django.shortcuts import render
from .models import Booking, Rooms, RoomsCategory



from django.shortcuts import render
from datetime import datetime, timedelta
from .models import Rooms, RoomsCategory, Booking

def weekviews(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            today = datetime.today()

            # Get the current index for the center 7 days from GET parameter, default to 0
            current_index = int(request.GET.get('index', 0))

            # Calculate the starting date based on the current index
            start_date = today + timedelta(days=current_index)

            # Generate the list of 7 dates based on the current start date
            dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

            rooms = Rooms.objects.filter(vendor=user).order_by('room_name')
            categories = RoomsCategory.objects.filter(vendor=user).order_by('id')
            yestarday = start_date - timedelta(days=1)
            enddays = start_date + timedelta(days=6)
            # bookings = Booking.objects.filter(vendor=user,check_in_date__range =[yestarday,enddays] )

            bookings = Booking.objects.filter(
                    vendor=user
                ).filter(
                    Q(check_in_date__lte=enddays) & Q(check_out_date__gte=yestarday)
                )

            # Prepare a list of booking data with calculated widths
            booking_data = []
            for booking in bookings:
                # Calculate width percentages based on check-in and check-out times
                check_in_hour = booking.check_in_time.hour if booking.check_in_time else 0
                check_out_hour = booking.check_out_time.hour if booking.check_out_time else 24
                segment = booking.segment
                totalamount = booking.totalamount
                totalroom = booking.totalroom
                checkintime = booking.check_in_time
                checkouttime = booking.check_out_time
                status = booking.status
                # Calculate the width as a percentage of the day (24 hours)
                check_in_width = (24 - check_in_hour) * (100 / 24)  # Width from check-in to end of day
                check_out_width = check_out_hour * (100 / 24)        # Width from start of day to check-out
                
                booking_data.append({
                    'id':booking.id,
                    'room': booking.room,
                    'guest_name': booking.guest_name,
                    'check_in_date': booking.check_in_date,
                    'check_out_date': booking.check_out_date,
                    'check_in_hour': check_in_hour,
                    'check_out_hour': check_out_hour,
                    'check_in_width': check_in_width,
                    'check_out_width': check_out_width,
                    'segment':segment,
                    'totalamount':totalamount,
                    'totalroom':totalroom,
                    'checkintime':checkintime,
                    'checkouttime':checkouttime,
                    'status':status,
                    'fnbid':  booking.fnbinvoice.id if booking.fnbinvoice and booking.fnbinvoice.id is not None else 'default_value'



                    
                })


            return render(request, 'weekviewpage.html', {
                'dates': dates,
                'rooms': rooms,
                'categories': categories,
                'bookings': booking_data,  # Pass calculated booking data to the template
                'current_index': current_index,
                'active_page': 'weekviews'
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

    

def cleanroombtnajax(request):
    try:    
        if request.method == "POST":
            # Room instance ko fetch karte waqt vendor data ko bhi load karenge
            room_id = int(request.POST.get('roomno'))
            data = Rooms.objects.select_related('vendor').get(id=room_id)

            # Room status ko toggle karte hain
            new_status = not data.is_clean  # This will toggle the boolean value
            data.is_clean = new_status  # Update the is_clean field
            data.save(update_fields=['is_clean'])  # Sirf is_clean field ko save karein

            # User id ko URL mein pass karte hain
            user_id = data.vendor.id
            url = reverse('roomclean', args=[user_id])
            return redirect(url)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




from django.http import JsonResponse
from django.db.models import Sum
def changeindexyear(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            # Get the selected year from the request
            selected_year = request.GET.get('year')
            if not selected_year:
                selected_year = timezone.now().year  # Default to current year if no year is provided

            try:
                selected_year = int(selected_year)
            except ValueError:
                return render(request, '404.html', {'error_message': 'Invalid year format'}, status=400)

            # Fetch data for the selected year
            subtotalsale = Invoice.objects.filter(vendor=user, invoice_date__year=selected_year).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            totaltax = Invoice.objects.filter(vendor=user, invoice_date__year=selected_year).aggregate(total_sales=Sum('gst_amount'))['total_sales'] or 0
            subtotalsale = int(subtotalsale)
            totaltax = int(totaltax * 2)
            totalsalaryexpance = SalaryManagement.objects.filter(vendor=user).aggregate(total_sales=Sum('basic_salary'))['total_sales'] or 0
            totalsalaryexpance = int(totalsalaryexpance)
            totaltaxandsalary = totalsalaryexpance + totaltax
            totalsalaryexcludedeductions = subtotalsale - totaltaxandsalary
            subtotalsalereal = Invoice.objects.filter(vendor=user, invoice_date__year=selected_year).aggregate(total_sales=Sum('subtotal_amount'))['total_sales'] or 0

            # Fetch highly booked room
            most_booked_room = Gueststay.objects.filter(vendor=user, checkindate__year=selected_year).values('roomno').annotate(bookings_count=Count('roomno')).order_by('-bookings_count').values_list('roomno', flat=True).first()

            # Fetch monthly sales data for the selected year
            monthly_data = Invoice.objects.filter(vendor=user, invoice_date__year=selected_year) \
                                           .annotate(month=ExtractMonth('invoice_date')) \
                                           .values('month') \
                                           .annotate(total_sales=Sum('grand_total_amount')) \
                                           .order_by('month')

            # Prepare data for Chart.js
            labels = []
            data = []
            sales_data = {month: 0 for month in range(1, 13)}

            for entry in monthly_data:
                month = entry['month']
                total_sales = float(entry['total_sales'])
                sales_data[month] = total_sales

            for month, total_sales in sorted(sales_data.items()):
                labels.append(datetime(2024, month, 1).strftime('%b'))
                data.append(total_sales)

            # Calculate growth and sales percentage
            growth = sum(data) / 12 if data else 0
            total_sales_all_time = Invoice.objects.filter(vendor=user).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            total_sales_last_7_days = Invoice.objects.filter(vendor=user, invoice_date__gte=datetime.now() - timedelta(days=7)).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0

            sales_percent = (100 * total_sales_last_7_days / total_sales_all_time) if total_sales_all_time > 0 else 0
            sales_percent = int(sales_percent)

            labels_json = json.dumps(labels)
            data_json = json.dumps(data)
            growth_json = json.dumps(sales_percent)

            # Weekly data calculation
            today = datetime.now().date()
            last_sunday = today - timedelta(days=today.weekday() + 1)
            next_saturday = last_sunday + timedelta(days=6)

            invoices = Invoice.objects.filter(vendor=user, invoice_date__year=selected_year, invoice_date__range=[last_sunday, next_saturday])
            weekly_data = [0] * 7

            for invoice in invoices:
                day_index = (invoice.invoice_date - last_sunday).days
                weekly_data[day_index] += float(invoice.grand_total_amount)

            weeklys_data = json.dumps({
                'today': today.isoformat(),
                'last_sunday': last_sunday.isoformat(),
                'next_saturday': next_saturday.isoformat(),
                'weekly_data': weekly_data
            }, cls=DjangoJSONEncoder)
             # Filter the Supplier model based on the year and sattle status
            total_purches_settled = Supplier.objects.filter(
                vendor=user,
                sattle=True,
                invoicedate__year=selected_year
            ).aggregate(total_sales=Sum('grand_total_amount'))['total_sales'] or 0
            # Return the updated data to the index page

            total_cash_expense = expenseCash.objects.filter(vendor=user
                    ,date_time__year=selected_year).aggregate(less_amount=Sum('less_amount'))['less_amount'] or 0

            # totalsalaryexcludedeductions = totalsalaryexcludedeductions - total_cash_expense - total_purches_settled

            # commisiion data calculations
            check_invoices = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__year=selected_year
                ).exclude(customer__saveguestid=None)

            # Step 2: Extract guest IDs from each invoice
            book_ids = [
                    invoice.customer.saveguestid
                    for invoice in check_invoices
                    if hasattr(invoice.customer, 'saveguestid')
                ]

            print("Filtered Guest IDs from Invoices:", book_ids)

            # ✅ Step 3: Correct filtering (no nested list)
            commmodel = tds_comm_model.objects.filter(
                    roombook__id__in=book_ids
                )

            totals = commmodel.aggregate(
                    total_commission=Sum('commission') or 0,
                    total_tds=Sum('tds') or 0,
                    total_tcs=Sum('tcs') or 0
                )

            totals = {
                    'total_commission': totals['total_commission'] or 0,
                    'total_tds': totals['total_tds'] or 0,
                    'total_tcs': totals['total_tcs'] or 0,
                }


            # Print totals
            print("Total Commission:", totals['total_commission'] or 0)
            print("Total TDS:", totals['total_tds'] or 0)
            print("Total TCS:", totals['total_tcs'] or 0)

            print("Commission Models Found:", commmodel)
            total_deduct_balace = totaltax + totalsalaryexpance  + total_cash_expense  + total_purches_settled + int(totals['total_commission']) + int(totals['total_tds']) + int(totals['total_tcs'])
            
            totalsalaryexcludedeductions = totalsalaryexcludedeductions - total_cash_expense - total_purches_settled - int(totals['total_commission']) - int(totals['total_tds']) - int(totals['total_tcs'])
            print(total_deduct_balace,'check this')
            return render(request, 'index.html', {
                'subtotalsale': subtotalsale,
                'totaltax': totaltax,
                'totalsalaryexpance': totalsalaryexpance,
                'totalsalaryexcludedeductions': totalsalaryexcludedeductions,
                'most_booked_room': most_booked_room,
                'labels_json': labels_json,
                'data_json': data_json,
                'growth_json': growth_json,
                'weeklys_data': weeklys_data,
                'current_year': selected_year,
                'total_purches_settled':total_purches_settled,
                'total_cash_expense':total_cash_expense,
                'totals':totals,'total_deduct_balace':total_deduct_balace
            })
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)





def update_room_book_advance(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        try:
            # Find the room booking entry by ID
            roombookadvance = RoomBookAdvance.objects.get(id=data['id'])
            roombookadvance.adults = data['adults']
            roombookadvance.children = data['children']
            roombookadvance.save()

            # Return a success response with updated values
            return JsonResponse({
                'success': True,
                'adults': roombookadvance.adults,
                'children': roombookadvance.children
            })
        except RoomBookAdvance.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Item not found'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})




# one by one chekcin function
def guestaddfromfolio(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roombookadvanceiddata = request.POST.get('roombookadvanceiddata')
            roomnodata = request.POST.get('roomnodata')
            name = request.POST.get('name')
            phone = request.POST.get('phone')
            address = request.POST.get('address')
            guestid = request.POST.get('guestid')
            if Gueststay.objects.filter(vendor=user,id=guestid).exists():
                MoreGuestData.objects.create(vendor=user,mainguest_id=guestid,another_guest_name=name,another_guest_phone=phone,another_guest_address=address)
                messages.success(request, 'GUuest added successfully')
            else:

               messages.error(request, 'Data Not Found')
            url = reverse('invoicepage', args=[guestid])

        
            return redirect(url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

from django.views.decorators.csrf import csrf_protect


from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore

@csrf_protect
def cart_processing(request):
    if request.method == "POST":
        # try:
            # Parse JSON data
            data = json.loads(request.body)

            # Extract required data
            cart_items = data.get('items', [])
            total_price = data.get('totalPrice', 0)
            total_tax = data.get('totalTax', 0)
            total_discount = data.get('totalDiscount', 0)
            total_rooms = data.get('totalRooms', 0)
            check_in = data.get('checkIn', None)
            check_out = data.get('checkOut', None)
            days = data.get('days', 1)
            userids = data.get('userid', None)
            ttal_gt_amont = total_price + total_tax
       
            # Convert dates to proper format
            # check_in_date = datetime.strptime(check_in, '%b. %d, %Y').date()
            check_in_date = datetime.strptime(check_in, '%B %d, %Y').date()

            # check_out_date = datetime.strptime(check_out, '%b. %d, %Y').date()
            check_out_date = datetime.strptime(check_out, '%B %d, %Y').date()
            if Vendor_Service.objects.filter(vendor_id=userids,only_cm=True):
                return cart_cm_new_reservation(request)
            # Consolidate cart items by category
            total_guests = 0
            consolidated_items = {}
            for item in cart_items:
                category = item.get('category')
                count = item.get('count', 0)
                total_guests += item.get('adults', 0) + item.get('children', 0)
                if category in consolidated_items:
                    consolidated_items[category] += count
                else:
                    consolidated_items[category] = count

            all_categories_available = True
            room_availability_map = {}

            # Check room availability for each category
            for category, required_count in consolidated_items.items():
                # Fetch room IDs that are booked during the requested period
                booked_room_ids = Booking.objects.filter(
                    vendor_id=userids,
                    room__room_type__category_name=category,
                    check_in_date__lt=check_out_date,  # Booking overlaps the requested period
                    check_out_date__gt=check_in_date  # Exclude rooms available on check-out
                ).values_list('room_id', flat=True)

                # Available rooms for this category
                available_rooms = Rooms.objects.filter(
                    vendor_id=userids,
                    room_type__category_name=category
                ).exclude(id__in=booked_room_ids)

                if available_rooms.count() < required_count:
                    all_categories_available = False
                    room_availability_map[category] = False
                else:
                    room_availability_map[category] = True
                    

            if not all_categories_available:
                return JsonResponse({'success': False, 'message': 'Some rooms are SOLD. Please try again.'})

            # Create booking if all rooms are available
            guest_name = data.get('guestName', None)
            guest_phone = data.get('guestPhone', None)
            guest_country = data.get('guestCountry', None)
            guest_address = data.get('guestAddress', None)
            special_request = data.get('specialRequest', None)
            channal = onlinechannls.objects.filter(vendor_id=userids, channalname='BOOKING-ENGINE').first()
            if not channal:
                channal = onlinechannls.objects.create(vendor_id=userids, channalname='BOOKING-ENGINE')

            # Create SaveAdvanceBookGuestData record
            current_date = datetime.now()
            lastid = SaveAdvanceBookGuestData.objects.filter(vendor_id=userids).last().id or 0
            beid = f"BE-{lastid + 1}"

            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(
                vendor_id=userids,
                bookingdate=check_in_date,
                noofrooms=total_rooms,
                bookingguest=guest_name,
                bookingguestphone=guest_phone,
                staydays=days,
                advance_amount=0.00,
                reamaining_amount=ttal_gt_amont*days,
                discount=0.00,
                total_amount=ttal_gt_amont*days,
                channal=channal,
                checkoutdate=check_out_date,
                email='',
                address_city=guest_address,
                state='',
                country=guest_country,
                totalguest=total_guests,
                action='book',
                booking_id=beid,
                cm_booking_id=None,
                segment='BOOKING-ENGINE',
                special_requests=special_request,
                pah=True,
                amount_after_tax=ttal_gt_amont*days,
                amount_before_tax=total_price*days,
                tax=total_tax*days,
                currency="INR",
                checkin=current_date,
                Payment_types='postpaid',
                is_selfbook=False,
                is_noshow=False,
                is_hold=False,

            )

            # Create RoomBookAdvance records
            for item in cart_items:
                category_name = item['category']
                rate_plan = item['ratePlan']
                rate_plan_code = item['ratePlancode']
                ads = item['adults'] // item['count']
                cds = item['children'] // item['count']
                available_rooms = Rooms.objects.filter(
                    vendor_id=userids,
                    room_type__category_name=category_name
                ).exclude(
                    id__in=Booking.objects.filter(
                        Q(check_in_date__lt=check_out_date) &
                        Q(check_out_date__gt=check_in_date)
                    ).values_list('room_id', flat=True)
                ).exclude(checkin=6)
                
                if RatePlan.objects.filter(vendor_id=userids,rate_plan_name=rate_plan,rate_plan_code=rate_plan_code).exists():
                    rdatas = RatePlan.objects.get(vendor_id=userids,rate_plan_name=rate_plan,rate_plan_code=rate_plan_code)
                    ratecodes = rdatas.rate_plan_code
                    
                else:
                    ratecodes=''
                for loop in range(item['count']):
                    room = available_rooms.first()
                    if not room:
                        
                        continue
                    sellratebydays = (item['price']) 
                    RoomBookAdvance.objects.create(
                        vendor_id=userids,
                        saveguestdata=Saveadvancebookdata,
                        bookingdate=check_in_date,
                        roomno_id=room.id,
                        bookingguest=guest_name,
                        bookingguestphone=guest_phone,
                        checkoutdate=check_out_date,
                        bookingstatus=True,
                        channal=channal,
                        totalguest=ads + cds,
                        rateplan_code=rate_plan,
                        rateplan_code_main=ratecodes,
                        guest_name='',
                        adults=ads,
                        children=cds,
                        sell_rate=sellratebydays
                    )

                    # Handling check-in and check-out times
                    noon_time_str = "12:00 PM"
                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()

                    # Create the Booking entry for the room
                    Booking.objects.create(
                        vendor_id=userids,
                        room=room,
                        guest_name=guest_name,
                        check_in_date=check_in_date,
                        check_out_date=check_out_date,
                        check_in_time=noon_time,
                        check_out_time=noon_time,
                        segment="BOOKING-ENGINE",
                        totalamount=ttal_gt_amont,
                        totalroom=total_rooms,
                        gueststay=None,
                        advancebook=Saveadvancebookdata,
                        status="BOOKING"
                    )

                    catdatas = RoomsCategory.objects.get(vendor_id=userids,category_name=category_name)
                    # inventory code
                    # Convert date strings to date objects
                    checkindate = str(check_in_date)
                    checkoutdate = str(check_out_date)
                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                    checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                    # Generate the list of all dates between check-in and check-out (inclusive)
                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

                    # Query the RoomsInventory model to check if records exist for all those dates
                    existing_inventory = RoomsInventory.objects.filter(vendor_id=userids,room_category=catdatas, date__in=all_dates)

                    # Get the list of dates that already exist in the inventory
                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                    # Identify the missing dates by comparing all_dates with existing_dates
                    missing_dates = [date for date in all_dates if date not in existing_dates]

                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                    roomcount = Rooms.objects.filter(vendor_id=userids,room_type=catdatas).exclude(checkin=6).count()
                 
                    occupancy = (1 * 100 // roomcount)
                    for inventory in existing_inventory:
                        if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
                            inventory.total_availibility -= 1
                            inventory.booked_rooms += 1
                            if inventory.occupancy+occupancy==99:
                                inventory.occupancy=100
                            else:
                                inventory.occupancy +=occupancy
                            inventory.save()
                    
                    # catdatas = RoomsCategory.objects.get(vendor_id=userids,category_name=category_name)
                    totalrooms = Rooms.objects.filter(vendor_id=userids,room_type=catdatas).exclude(checkin=6).count()
                    occupancccy = (1 *100 //totalrooms)
                    if missing_dates:
                        for missing_date in missing_dates:
                        
                                RoomsInventory.objects.create(
                                    vendor_id=userids,
                                    date=missing_date,
                                    room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
                                    total_availibility=roomcount-1,       # Set according to your logic
                                    booked_rooms=1,    
                                    occupancy=occupancccy,
                                    price=catdatas.catprice
                                                            # Set according to your logic
                                )
                       
                    else:
                        pass
                    
                                 # api calling backend automatically
            usermsglimit = Messgesinfo.objects.get(vendor_id=userids)
            
            if True:
                        addmsg = usermsglimit.changedlimit + 2
                        Messgesinfo.objects.filter(vendor_id=userids).update(changedlimit=addmsg)
                        profilename = HotelProfile.objects.get(vendor_id=userids)
                        mobile_number = guest_phone
                        
                        # message_content = f"Dear guest, Your booking at {profilename.name} is confirmed. Advance payment of Rs.{advanceamount} received. Check-in date: {bookingdate}. We're thrilled to host you and make your stay unforgettable. For assistance, contact us at {profilename.contact}. -BILLZIFY"
                        # oururl = 'https://live.billzify.com/receipt/88/'
                        # message_content = f"Hello {guestname}, Your reservation is confirmed. View your booking details here: {oururl}-BILLZIFY"
                        bids=Saveadvancebookdata.id
                        message_content = f"Hello {guest_name}, Your hotel reservation is confirmed. View your booking details here: https://live.billzify.com/receipt/?cd={bids} -BILLZIFY"
                        
                        base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                        params = {
                            'authkey': settings.YOURBULKSMS_API_KEY,
                            'mobiles': mobile_number,
                            'sender':  'BILZFY',
                            'route': '2',
                            'country': '0',
                            'DLT_TE_ID': '1707173659916248212'
                        }
                        encoded_message = urllib.parse.urlencode({'message': message_content})
                        url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('Status') == 'success':
                                        messages.success(request, 'SMS sent successfully.')
                                    else:
                                        messages.success(request, response_data.get('Description', 'Failed to send SMS'))
                                except ValueError:
                                    messages.success(request, 'Failed to parse JSON response')
                            else:
                                messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
                        except requests.RequestException as e:
                            messages.success(request, f'Error: {str(e)}')
            else:
                pass
            
            
            # Start the long-running task in a separate thread
            if VendorCM.objects.filter(vendor_id=userids,):
                        start_date = str(checkindate)
                        end_date = str(checkoutdate)
                        thread = threading.Thread(target=update_inventory_task, args=(userids, start_date, end_date))
                        thread.start()
                        # for dynamic pricing
                        if  VendorCM.objects.filter(vendor_id=userids,dynamic_price_active=True):
                            thread = threading.Thread(target=rate_hit_channalmanager, args=(userids, start_date, end_date))
                            thread.start()
                        else:
                            pass
            else:
                        pass    


            user = User.objects.get(id=userids)
            actionss = 'Create Booking'
            CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Booking Created for {Saveadvancebookdata.bookingguest}, This Booking From Booking Engine ')


            # Fetch all active sessions (remove expiration filter temporarily for debugging)
            sessions = Session.objects.filter(expire_date__gte=timezone.now())  # You can remove this condition if needed

            # Iterate over all active sessions
            for session in sessions:
                session_store = SessionStore(session_key=session.session_key)
                data = session_store.load()  # Load session data
                
                # Debugging: Check the session data before making any changes

                # Match user ID with session data
                if str(user.id) == str(data.get('_auth_user_id')):
                    # Check if the user has a subuser profile
                    if hasattr(user, 'subuser_profile'):
                        subuser = user.subuser_profile
                        if not subuser.is_cleaner:
                            # Get the main user (vendor) of this subuser
                            main_user = subuser.vendor
                            if main_user:
                                # Iterate over all sessions to find the main user's session
                                for main_session in sessions:
                                    main_session_store = SessionStore(session_key=main_session.session_key)
                                    main_session_data = main_session_store.load()
                                    
                                    if str(main_user.id) == str(main_session_data.get('_auth_user_id')):
                                        # Update the main user's session with a notification
                                        main_session_data['notification'] = True
                                        main_session_store.update(main_session_data)
                                        main_session_store.save()  # Save after making changes

                        # Update the subuser's session
                        data['notification'] = True
                        session_store.update(data)
                        session_store.save()  # Save after making changes

                    else:
                        # If no subuser profile, update the main user's session
                        data['notification'] = True
                        session_store.update(data)
                        session_store.save()  # Save after making changes
                       

           
            

            return JsonResponse({'success': True, 'message': 'Booking successful','id':Saveadvancebookdata.id})

    #     except Exception as e:
            
    #         return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

def cart_cm_new_reservation(request):
    if request.method == "POST":
        # try:
            # Parse JSON data
            data = json.loads(request.body)

            # Extract required data
            cart_items = data.get('items', [])
            total_price = data.get('totalPrice', 0)
            total_tax = data.get('totalTax', 0)
            total_discount = data.get('totalDiscount', 0)
            total_rooms = data.get('totalRooms', 0)
            check_in = data.get('checkIn', None)
            check_out = data.get('checkOut', None)
            days = data.get('days', 1)
            userids = data.get('userid', None)
            ttal_gt_amont = total_price + total_tax
            
            # Convert dates to proper format
            # check_in_date = datetime.strptime(check_in, '%b. %d, %Y').date()
            check_in_date = datetime.strptime(check_in, '%B %d, %Y').date()

            # check_out_date = datetime.strptime(check_out, '%b. %d, %Y').date()
            check_out_date = datetime.strptime(check_out, '%B %d, %Y').date()
            
            # Consolidate cart items by category
            total_guests = 0
            consolidated_items = {}
            for item in cart_items:
                category = item.get('category')
                count = item.get('count', 0)
                total_guests += item.get('adults', 0) + item.get('children', 0)
                if category in consolidated_items:
                    consolidated_items[category] += count
                else:
                    consolidated_items[category] = count

            all_categories_available = True
            room_availability_map = {}

            # Check room availability for each category
            for category, required_count in consolidated_items.items():
                # Fetch room IDs that are booked during the requested period
                
                # new code here
                newcheckdate = check_out_date - timedelta(days=1)
                inventorycheck = RoomsInventory.objects.filter(vendor_id=userids,room_category__category_name=category,
                                date__range=[check_in_date,newcheckdate])
                print(newcheckdate,inventorycheck)
                for i in inventorycheck:
                    if i.total_availibility<required_count:
                        print("haan bhia bigad gaye inventory")
                        return JsonResponse({'success': False, 'message': 'Some rooms are SOLD. Please try again.'})
                    else:
                        print("barabar haiinventory")

                
            # Create booking if all rooms are available
            guest_name = data.get('guestName', None)
            guest_phone = data.get('guestPhone', None)
            guest_country = data.get('guestCountry', None)
            guest_address = data.get('guestAddress', None)
            special_request = data.get('specialRequest', None)
            channal = onlinechannls.objects.filter(vendor_id=userids, channalname='BOOKING-ENGINE').first()
            if not channal:
                channal = onlinechannls.objects.create(vendor_id=userids, channalname='BOOKING-ENGINE')

            # Create SaveAdvanceBookGuestData record
            current_date = datetime.now()
            lastid = SaveAdvanceBookGuestData.objects.filter(vendor_id=userids).last().id or 0
            beid = f"BE-{lastid + 1}"

            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(
                vendor_id=userids,
                bookingdate=check_in_date,
                noofrooms=total_rooms,
                bookingguest=guest_name,
                bookingguestphone=guest_phone,
                staydays=days,
                advance_amount=0.00,
                reamaining_amount=ttal_gt_amont*days,
                discount=0.00,
                total_amount=ttal_gt_amont*days,
                channal=channal,
                checkoutdate=check_out_date,
                email='',
                address_city=guest_address,
                state='',
                country=guest_country,
                totalguest=total_guests,
                action='book',
                booking_id=beid,
                cm_booking_id=None,
                segment='BOOKING-ENGINE',
                special_requests=special_request,
                pah=True,
                amount_after_tax=ttal_gt_amont*days,
                amount_before_tax=total_price*days,
                tax=total_tax*days,
                currency="INR",
                checkin=current_date,
                Payment_types='postpaid',
                is_selfbook=False,
                is_noshow=False,
                is_hold=False,

            )

            # Create RoomBookAdvance records
            for item in cart_items:
                category_name = item['category']
                rate_plan = item['ratePlan']
                rate_plan_code = item['ratePlancode']
                ads = item['adults'] // item['count']
                cds = item['children'] // item['count']
                
                
                if RatePlan.objects.filter(vendor_id=userids,rate_plan_name=rate_plan,rate_plan_code=rate_plan_code).exists():
                    rdatas = RatePlan.objects.get(vendor_id=userids,rate_plan_name=rate_plan,rate_plan_code=rate_plan_code)
                    ratecodes = rdatas.rate_plan_code
                    
                else:
                    ratecodes=''
                for loop in range(item['count']):
                    # room = available_rooms.first()
                    # if not room:
                        
                    #     continue
                    sellratebydays = (item['price']) 
                    catdatas = RoomsCategory.objects.get(vendor_id=userids,category_name=category_name)
                    Cm_RoomBookAdvance.objects.create(
                        vendor_id=userids,
                        saveguestdata=Saveadvancebookdata,
                        room_category=catdatas,
                        bookingguest=guest_name,
                        bookingguestphone=guest_phone,
                        totalguest=ads + cds,
                        rateplan_code=rate_plan,
                        rateplan_code_main=ratecodes,
                        guest_name='',
                        adults=ads,
                        children=cds,
                        sell_rate=sellratebydays
                    )

                    
                    
                    # inventory code
                    # Convert date strings to date objects
                    checkindate = str(check_in_date)
                    checkoutdate = str(check_out_date)
                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                    checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                    # Generate the list of all dates between check-in and check-out (inclusive)
                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

                    # Query the RoomsInventory model to check if records exist for all those dates
                    existing_inventory = RoomsInventory.objects.filter(vendor_id=userids,room_category=catdatas, date__in=all_dates)

                    # Get the list of dates that already exist in the inventory
                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                    # Identify the missing dates by comparing all_dates with existing_dates
                    missing_dates = [date for date in all_dates if date not in existing_dates]

                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                    roomcount = Rooms_count.objects.filter(vendor_id=userids, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
                 
                    occupancy = (1 * 100 // roomcount)
                    for inventory in existing_inventory:
                        if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
                            inventory.total_availibility -= 1
                            inventory.booked_rooms += 1
                            if inventory.occupancy+occupancy==99:
                                inventory.occupancy=100
                            else:
                                inventory.occupancy +=occupancy
                            inventory.save()
                    
                    # catdatas = RoomsCategory.objects.get(vendor_id=userids,category_name=category_name)
                    totalrooms = Rooms_count.objects.filter(vendor_id=userids, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
                    occupancccy = (1 *100 //totalrooms)
                    if missing_dates:
                        for missing_date in missing_dates:
                        
                                RoomsInventory.objects.create(
                                    vendor_id=userids,
                                    date=missing_date,
                                    room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
                                    total_availibility=roomcount-1,       # Set according to your logic
                                    booked_rooms=1,    
                                    occupancy=occupancccy,
                                    price=catdatas.catprice
                                                            # Set according to your logic
                                )
                       
                    else:
                        pass
                    
                                 # api calling backend automatically
            usermsglimit = Messgesinfo.objects.get(vendor_id=userids)
            
            if True:
                        addmsg = usermsglimit.changedlimit + 2
                        Messgesinfo.objects.filter(vendor_id=userids).update(changedlimit=addmsg)
                        profilename = HotelProfile.objects.get(vendor_id=userids)
                        mobile_number = guest_phone
                        
                        # message_content = f"Dear guest, Your booking at {profilename.name} is confirmed. Advance payment of Rs.{advanceamount} received. Check-in date: {bookingdate}. We're thrilled to host you and make your stay unforgettable. For assistance, contact us at {profilename.contact}. -BILLZIFY"
                        # oururl = 'https://live.billzify.com/receipt/88/'
                        # message_content = f"Hello {guestname}, Your reservation is confirmed. View your booking details here: {oururl}-BILLZIFY"
                        bids=Saveadvancebookdata.id
                        message_content = f"Hello {guest_name}, Your hotel reservation is confirmed. View your booking details here: https://live.billzify.com/receipt/?cd={bids} -BILLZIFY"
                        
                        base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                        params = {
                            'authkey': settings.YOURBULKSMS_API_KEY,
                            'mobiles': mobile_number,
                            'sender':  'BILZFY',
                            'route': '2',
                            'country': '0',
                            'DLT_TE_ID': '1707173659916248212'
                        }
                        encoded_message = urllib.parse.urlencode({'message': message_content})
                        url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('Status') == 'success':
                                        messages.success(request, 'SMS sent successfully.')
                                    else:
                                        messages.success(request, response_data.get('Description', 'Failed to send SMS'))
                                except ValueError:
                                    messages.success(request, 'Failed to parse JSON response')
                            else:
                                messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
                        except requests.RequestException as e:
                            messages.success(request, f'Error: {str(e)}')
            else:
                pass
            
            
            # Start the long-running task in a separate thread
            if VendorCM.objects.filter(vendor_id=userids,):
                        start_date = str(checkindate)
                        end_date = str(checkoutdate)
                        thread = threading.Thread(target=update_inventory_task, args=(userids, start_date, end_date))
                        thread.start()
                        # for dynamic pricing
                        if  VendorCM.objects.filter(vendor_id=userids,dynamic_price_active=True):
                            thread = threading.Thread(target=rate_hit_channalmanager, args=(userids, start_date, end_date))
                            thread.start()
                        else:
                            pass
            else:
                        pass    


            user = User.objects.get(id=userids)
            actionss = 'Create Booking'
            CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                    advancebook=Saveadvancebookdata,description=f'Booking Created for {Saveadvancebookdata.bookingguest}, This Booking From Booking Engine ')


            # Fetch all active sessions (remove expiration filter temporarily for debugging)
            sessions = Session.objects.filter(expire_date__gte=timezone.now())  # You can remove this condition if needed

            # Iterate over all active sessions
            for session in sessions:
                session_store = SessionStore(session_key=session.session_key)
                data = session_store.load()  # Load session data
                
                # Debugging: Check the session data before making any changes

                # Match user ID with session data
                if str(user.id) == str(data.get('_auth_user_id')):
                    # Check if the user has a subuser profile
                    if hasattr(user, 'subuser_profile'):
                        subuser = user.subuser_profile
                        if not subuser.is_cleaner:
                            # Get the main user (vendor) of this subuser
                            main_user = subuser.vendor
                            if main_user:
                                # Iterate over all sessions to find the main user's session
                                for main_session in sessions:
                                    main_session_store = SessionStore(session_key=main_session.session_key)
                                    main_session_data = main_session_store.load()
                                    
                                    if str(main_user.id) == str(main_session_data.get('_auth_user_id')):
                                        # Update the main user's session with a notification
                                        main_session_data['notification'] = True
                                        main_session_store.update(main_session_data)
                                        main_session_store.save()  # Save after making changes

                        # Update the subuser's session
                        data['notification'] = True
                        session_store.update(data)
                        session_store.save()  # Save after making changes

                    else:
                        # If no subuser profile, update the main user's session
                        data['notification'] = True
                        session_store.update(data)
                        session_store.save()  # Save after making changes
                       

           
            

            return JsonResponse({'success': True, 'message': 'Booking successful','id':Saveadvancebookdata.id})
    #     except Exception as e:
            
    #         return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

from django.shortcuts import render, get_object_or_404

def receipt_view_book(request, booking_id):
    try:
        # Fetch the booking data
        advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
        for i in advancebookdata:
            vid = i.vendor.id
        advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
        hoteldata = HotelProfile.objects.filter(vendor_id=vid)
        hoteldatas = HotelProfile.objects.get(vendor_id=vid)
        terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
        if advancebookingdatas:
            pass
        else:
            advancebookingdatas = Cm_RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
        return render(request, 'bookingrecipt.html', {
            'advancebookdata': advancebookdata,
            'advancebookingdatas': advancebookingdatas,
            'hoteldata': hoteldata,
            'terms_lines':terms_lines
        })
       
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def receipt_view(request):
    # Get the booking_id from the query parameter 'extra_param'
    booking_id = request.GET.get('cd')

    # If booking_id is not provided, return an error message
    if not booking_id:
        return HttpResponse("Error: Missing booking_id.")

    # Fetch the booking data using the booking_id
    advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
    for i in advancebookdata:
        vid = i.vendor.id
    advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
    hoteldata = HotelProfile.objects.filter(vendor_id=vid)
    hoteldatas = HotelProfile.objects.get(vendor_id=vid)
    terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
    if advancebookingdatas:
        pass
    else:
        advancebookingdatas = Cm_RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
    # Return the template with the booking data and query parameter
    return render(request, 'bookingrecipt.html', {
        'advancebookdata': advancebookdata,
        'advancebookingdatas': advancebookingdatas,
        'hoteldata': hoteldata,
        'terms_lines': terms_lines,
        'hoteldatas':hoteldatas,
        'booking_id': booking_id,  # Pass booking_id to the template if needed
    })



def advncereciptbiew(request, booking_id):
    try:
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
                user = subuser.vendor  
        advancebookingdatas = RoomBookAdvance.objects.filter(id=booking_id)
        for i in advancebookingdatas:
            vid = i.vendor.id
            saveguestidd=i.saveguestdata.id
        
        hoteldata = HotelProfile.objects.filter(vendor=user)
        advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=saveguestidd)

        return render(request, 'bookingrecipt.html', {
            'advancebookdata': advancebookdata,
            'advancebookingdatas': advancebookingdatas,
            'hoteldata': hoteldata
        })
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

    

def voucherfind(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookidsmain = int(request.POST.get('bookidsmain'))
            
            hoteldata = HotelProfile.objects.filter(vendor=user)
            
            if Booking.objects.filter(vendor=user,id=bookidsmain).exists():
                bookdata=Booking.objects.get(vendor=user,id=bookidsmain)
                advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=bookdata.advancebook.id)
                advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata=bookdata.advancebook)

                return render(request, 'bookingrecipt.html', {
                    'advancebookdata': advancebookdata,
                    'advancebookingdatas': advancebookingdatas,
                    'hoteldata': hoteldata
                })

            return redirect('weekviews')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)





# advance booking delete function
def advancebookingdeletebe(request,id):
    try:
        
            saveguestid=id
            savedata = SaveAdvanceBookGuestData.objects.get(id=saveguestid)
            user = savedata.vendor
            roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid,partly_checkin=False,checkinstatus=False).all()
            if roomdata: 
                for data in roomdata:
                    Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                    checkindate = data.bookingdate
                    checkoutdate = data.checkoutdate
                    while checkindate < checkoutdate:
                        roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                        invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                        
                        invtavaible = invtdata.total_availibility + 1
                        invtabook = invtdata.booked_rooms - 1
                        total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                        occupancy = invtabook * 100//total_rooms
                                                                

                        RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                    total_availibility=invtavaible,occupancy=occupancy)
            
                        checkindate += timedelta(days=1)

                if VendorCM.objects.filter(vendor=user):
                    start_date = str(data.bookingdate)
                    end_date = str(data.checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()

                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid).update(action='cancel')
                Booking.objects.filter(vendor=user,advancebook_id=saveguestid).delete()
                actionss = 'Cancel Booking'
                CustomGuestLog.objects.create(vendor=user,by='by Guest Canceled',action=actionss,
                        advancebook=savedata,description=f'Booking Cancel for {savedata.bookingguest}, This Booking From Booking Engine ')

                # roomchekinstatus = Rooms.objects.filter(vendor=user,id=roomid,checkin__range=[4,5]).exists()
                # if roomchekinstatus is True:
                #     Rooms.objects.filter(vendor=user,id=roomid).update(checkin=0)
                # RoomBookAdvance.objects.filter(vendor=user,id=id).delete()
                # Room_history.objects.filter(vendor=user,room_no=roomid).delete()
                # advanceroomdata = RoomBookAdvance.objects.filter(vendor=user).all()
                messages.success(request,'booking Cancelled succesfully')

            elif Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid):
                newroomdata = Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid)
                for data in newroomdata:
                    # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                    checkindate = savedata.bookingdate
                    checkoutdate = savedata.checkoutdate
                    while checkindate < checkoutdate:
                        # roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                        roomscat = data.room_category
                        invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat)
                        
                        invtavaible = invtdata.total_availibility + 1
                        invtabook = invtdata.booked_rooms - 1
                        total_rooms = Rooms_count.objects.filter(vendor=user, room_type=roomscat).values_list('total_room_numbers', flat=True).first() or 0
                        occupancy = invtabook * 100//total_rooms
                                                                

                        RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat).update(booked_rooms=invtabook,
                                    total_availibility=invtavaible,occupancy=occupancy)
            
                        checkindate += timedelta(days=1)

                if VendorCM.objects.filter(vendor=user):
                    start_date = str(savedata.bookingdate)
                    end_date = str(savedata.checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()

                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid).update(action='cancel')
                # Booking.objects.filter(vendor=user,advancebook_id=saveguestid).delete()
                actionss = 'Cancel Booking'
                CustomGuestLog.objects.create(vendor=user,by='by Guest Canceled',action=actionss,
                        advancebook=savedata,description=f'Booking Cancel for {savedata.bookingguest}, This Booking From Booking Engine ')

                # roomchekinstatus = Rooms.objects.filter(vendor=user,id=roomid,checkin__range=[4,5]).exists()
                # if roomchekinstatus is True:
                #     Rooms.objects.filter(vendor=user,id=roomid).update(checkin=0)
                # RoomBookAdvance.objects.filter(vendor=user,id=id).delete()
                # Room_history.objects.filter(vendor=user,room_no=roomid).delete()
                # advanceroomdata = RoomBookAdvance.objects.filter(vendor=user).all()
                messages.success(request,'booking Cancelled succesfully')
            else:
                messages.error(request,'Guest Is Stayed If You Want To Delete So cancel the folio room.')
            # advanceroomdata = SaveAdvanceBookGuestData.objects.filter(vendor=user).all()
            # return render(request,'advancebookinghistory.html',{'advanceroomdata':advanceroomdata,'active_page': 'advancebookhistory'})
            url = reverse('receipt_view_book', args=[saveguestid])

        
            return redirect(url)
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    



def addpaymenttobooking(request,booking_id):
    try:
        if request.user.is_authenticated:
            user=request.user 
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookingdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=booking_id)
            return render(request,'advanceamt.html',{'bookingdata':bookingdata})
        else:
            return redirect('loginpage')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def addpymenttoboking(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                bokkingid = request.POST.get('bokkingid')
                amount = int(float(request.POST.get('amount')))
                paymentmode = request.POST.get('paymentmode')
                paymntdetails = request.POST.get('paymntdetails')
                comment = request.POST.get('comment')
                today = datetime.now()
                invoicedata = SaveAdvanceBookGuestData.objects.get(vendor=user,id=bokkingid)

                advanceamount = int(invoicedata.advance_amount)
                reaminingamount =int(invoicedata.reamaining_amount)
                
                
                if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid,checkinstatus=False):
                    if amount == reaminingamount:
                        dueamount = reaminingamount - amount
                        acceptamount = advanceamount + amount

                        InvoicesPayment.objects.create(vendor=user,invoice_id=None,payment_amount=amount,
                                    payment_date=today,payment_mode=paymentmode,transaction_id=paymntdetails,
                                    descriptions=comment,advancebook=invoicedata)
                        
                        SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid).update(
                            advance_amount=acceptamount,reamaining_amount=dueamount,Payment_types='prepaid'
                        )

                        actionss = 'Add Payment Advance'
                        CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook_id=bokkingid,description=f'Payment Added As Advance {amount} ')

                        messages.success(request,"Payment added succesfully!")
                        url = reverse('advancebookingdetails', args=[bokkingid])
                        return redirect(url)
            
                    elif amount > reaminingamount:
                        
                        messages.error(request,"amount graterthen to billing amount!")
                        url = reverse('addpaymenttobooking', args=[bokkingid])
                        return redirect(url)
                    
                    else:

                        dueamount = reaminingamount - amount
                        acceptamount = advanceamount + amount
                        InvoicesPayment.objects.create(vendor=user,invoice_id=None,payment_amount=amount,
                                    payment_date=today,payment_mode=paymentmode,transaction_id=paymntdetails,
                                    descriptions=comment,advancebook=invoicedata)
                        
                        SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid).update(
                            advance_amount=acceptamount,reamaining_amount=dueamount,Payment_types='partially'
                        )

                        actionss = 'Add Payment Advance'
                        CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook_id=bokkingid,description=f'Payment Added As Advance {amount} ')

                        messages.success(request,"Payment added succesfully!")
                        url = reverse('advancebookingdetails', args=[bokkingid])
                        return redirect(url)

                    
                else:
                    
                    messages.error(request,"Guest are checked in add payment to folio page")
                    return redirect('advanceroomhistory')          
                
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def websettings(request):
    try:
        if request.user.is_authenticated:
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                amenities=beaminities.objects.filter(vendor=user)
                offers = OfferBE.objects.filter(vendor=user)
                cpdata = cancellationpolicy.objects.filter(vendor=user)
                roomcat = RoomsCategory.objects.filter(vendor=user)
                gallary = RoomImage.objects.filter(vendor=user)
                hotelimgs = HoelImage.objects.filter(vendor=user)
                ctdata = becallemail.objects.filter(vendor=user)
                checkstatus = bestatus.objects.filter(vendor=user)
                pptdescription = property_description.objects.filter(vendor=user)
                roomservicess = room_services.objects.filter(vendor=user)
                chatwhatsaap = whatsaap_link.objects.filter(vendor__username=user)
                return render(request,'websetings.html',{'active_page': 'websettings','amenities':amenities,'offers':offers,
                                                        'chatwhatsaap':chatwhatsaap,'roomservicess':roomservicess,'pptdescription':pptdescription,'checkstatus':checkstatus,'ctdata':ctdata,'cpdata':cpdata,'roomcat':roomcat,'gallary':gallary,'hotelimgs':hotelimgs})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

from django.views.decorators.http import require_POST
@csrf_exempt
@require_POST  # Ensure that only POST requests are processed
def create_demo(request):
    # Check if the request contains JSON or form data
    if request.content_type == 'application/json':
        # If the data is JSON
        try:
            data = json.loads(request.body)  # Parse the JSON request body
            name = data.get("name", "")
            email = data.get("email", "")
            phone = data.get("phone", "")
            business_name = data.get("businessname", "")

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
    else:
        # If the data is form-encoded
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        phone = request.POST.get("phone", "")
        business_name = request.POST.get("businessname", "")

    # Validation to ensure that all fields are provided
    if not name or not email or not phone or not business_name:
        return JsonResponse({"error": "All fields are required."}, status=400)

        

    # Optional: Save to the database if needed
    Freedemo.objects.create(
        name=name,
        email=email,
        phone=phone,
        businessname=business_name
    )

    # fulldata = name + str(email) + str(phone) + str(business_name)

    # message_content = f"Dear {name}, Welcome to {fulldata}. We are delighted to have you with us and look forward to making your stay enjoyable. Thank you for choosing us. - Billzify"

    # base_url = "http://control.yourbulksms.com/api/sendhttp.php"
    # params = {
    #                 "authkey": settings.YOURBULKSMS_API_KEY,
    #                 "mobiles": 8889381013,
    #                 "sender": "BILZFY",
    #                 "route": "2",
    #                 "country": "0",
    #                 "DLT_TE_ID": "1707171889808133640",
    #             }
    # encoded_message = urllib.parse.urlencode({"message": message_content})
    # url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"

    # try:
    #                 response = requests.get(url)
    #                 if response.status_code == 200:
    #                     try:
    #                         response_data = response.json()
    #                         if response_data.get("Status") == "success":
    #                             messages.success(request, "SMS sent successfully.")
    #                         else:
    #                             messages.success(
    #                                 request,
    #                                 response_data.get(
    #                                     "Description", "Failed to send SMS"
    #                                 ),
    #                             )
    #                     except ValueError:
    #                         messages.success(request, "Failed to parse JSON response")
    #                 else:
    #                     messages.success(
    #                         request,
    #                         f"Failed to send SMS. Status code: {response.status_code}",
    #                     )
    # except requests.RequestException as e:
    #                 messages.success(request, f"Error: {str(e)}")

    # Return a success response
    return JsonResponse({
        "message": "Demo request submitted successfully!",
        "data": {
            "name": name,
            "email": email,
            "phone": phone,
            "business_name": business_name,
        }
    }, status=200)


from django.db.models import Max

from django.db.models import Max, IntegerField
from django.db.models.functions import Cast

def checkoutroom(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomno = request.POST.get('roomno')
            invoice_id = request.POST.get('invoice_id')
            loyltycheck = request.POST.get('loyltycheck')
            # paymentstatus = request.POST.get('paymentstatus')
            paymentstatus = "PMS"
            gstnumbercustomer = request.POST.get('gstnumber')
            guestcompany = request.POST.get('guestcompany')
            dueamount = request.POST.get('dueamount')
            duedate = request.POST.get('duedate')
            
            if Invoice.objects.filter(vendor=user,id=invoice_id,foliostatus=False).exists():
                
                if Invoice.objects.filter(vendor=user,id=invoice_id).exists():
                    GUESTIDs = Invoice.objects.get(vendor=user,id=invoice_id)
                    GUESTID = GUESTIDs.customer.id
                    invoicegrandtotalpaymentstatus = GUESTIDs.grand_total_amount
                    
                    
                    # new updated code
                    if int(float(dueamount)) == 0 :
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=True)
                        if companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).exists():
                            companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).update(is_paid=True)
                            

                            
                        
                    else: #unpaid 
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=False,invoice_number="unpaid")
                        CustomerCredit.objects.create(vendor=user,customer_name=GUESTIDs.customer.guestname,amount=dueamount,
                                                      due_date=duedate,invoice=GUESTIDs,phone=GUESTIDs.customer.guestphome)
                        actionss = 'Create Credit Bill'
                        CustomGuestLog.objects.create(vendor=user,customer_id=GUESTID,by=request.user,action=actionss,
                                            description=f'Guest Check-Out But Payment Is Due {dueamount}')
                          



                    guestdatas = Gueststay.objects.get(vendor=user,id=GUESTID)
                    current_date = datetime.now()
                    # Get the current date
                    invccurrentdate = datetime.now().date()

                    if gstnumbercustomer:
                        if guestcompany == '':
                            guestcompany=guestdatas.guestname
                        else:
                            pass
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(customer_gst_number=gstnumbercustomer,customer_company=guestcompany)
                    else:
                        pass


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



                    

                    Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_date=invccurrentdate)
                    
                    # new checkout work start here
                    bookdata = Booking.objects.filter(vendor=user,gueststay_id=GUESTID).all()
                    ctime = datetime.now().time()
                    for i in bookdata:
                        if i.status=='CHECK OUT':
                            pass
                        else:
                            # update inventory operations
                            checkindate = invccurrentdate
                            checkoutdate = i.check_out_date
                           
                            while checkindate < checkoutdate:
                                    roomscat = Rooms.objects.get(vendor=user,id=i.room.id)
                                    invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                                
                                    invtavaible = invtdata.total_availibility + 1
                                    invtabook = invtdata.booked_rooms - 1
                                    total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                    occupancy = invtabook * 100//total_rooms
                                                                            

                                    RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                                total_availibility=invtavaible,occupancy=occupancy)
                        
                                    checkindate += timedelta(days=1)

                            if VendorCM.objects.filter(vendor=user):
                                start_date = str(invccurrentdate)
                                end_date = str(i.check_out_date)
                                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                thread.start()
                                # for dynamic pricing
                                if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                    thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                    thread.start()
                                else:
                                    pass
                            else:
                                pass

                            Rooms.objects.filter(vendor=user,id=i.room.id).update(checkin=0)
                            Booking.objects.filter(vendor=user,id=i.id).update(status="CHECK OUT",
                                            check_out_time=ctime,check_out_date=invccurrentdate)


                    actionss = 'Guest Check-Out'
                    CustomGuestLog.objects.create(vendor=user,customer_id=GUESTID,by=request.user,action=actionss,
                                            description=f'Guest Check-Out')
                                
                            

                    Invoice.objects.filter(vendor=user,id=invoice_id).update(foliostatus=True,invoice_number=invoice_number,modeofpayment=paymentstatus)
                    
                    if guestdatas.saveguestid:
                        pass
                        RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=guestdatas.saveguestid).update(checkOutstatus=True)
                    else:
                        pass
                    
                    Gueststay.objects.filter(vendor=user,id=GUESTID).update(checkoutdone=True,checkoutstatus=True,checkoutdate=current_date)
                    
                    if int(float(dueamount)) == 0 :
                            pass
                    else:
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_number="unpaid")
                            

                   


                if loyltycheck == 'on':
                        guestphone = Gueststay.objects.get(vendor=user,id=GUESTID)
                        guestphonenumber = guestphone.guestphome
                        guestnameformsg = guestphone.guestname
                        loyltyrate = loylty_data.objects.get(vendor=user)
                        totalamountinvoice = GUESTIDs.grand_total_amount
                        totalloyltyamount = int(totalamountinvoice)*loyltyrate.loylty_rate_prsantage//100
                        if loylty_Guests_Data.objects.filter(vendor=user,guest_contact=guestphonenumber).exists():
                                    loyltdatas = loylty_Guests_Data.objects.get(vendor=user,guest_contact=guestphonenumber)
                                    existsamount = loyltdatas.loylty_point + totalloyltyamount
                                    loylty_Guests_Data.objects.filter(vendor=user,guest_contact=guestphonenumber).update(loylty_point = existsamount)
                        else:
                                    loylty_Guests_Data.objects.create(vendor=user,guest_name=guestnameformsg,guest_contact=guestphonenumber,loylty_point=totalloyltyamount
                                                                      ,smscount='0')
                        # msg content 
                        usermsglimit = Messgesinfo.objects.get(vendor=user)
                        if usermsglimit.defaultlimit > usermsglimit.changedlimit :
                                addmsg = usermsglimit.changedlimit + 2
                                Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                                profilename = HotelProfile.objects.get(vendor=user)
                                hotelname = profilename.name
                                mobile_number = guestphonenumber
                                user_name = "chandan"
                                val = 5
                                message_content = f"Dear Guest, you have earned loyalty points worth Rs {totalloyltyamount} at {hotelname}. We look forward to welcoming you back soon. - Billzify"
                                    
                                base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                                params = {
                                    'authkey': settings.YOURBULKSMS_API_KEY,
                                    'mobiles': guestphonenumber,
                                    'sender':  'BILZFY',
                                    'route': '2',
                                    'country': '0',
                                    'DLT_TE_ID': '1707171993560691064'
                                }
                                encoded_message = urllib.parse.urlencode({'message': message_content})
                                url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                                
                                try:
                                    response = requests.get(url)
                                    if response.status_code == 200:
                                        try:
                                            response_data = response.json()
                                            if response_data.get('Status') == 'success':
                                                messages.success(request, 'SMS sent successfully.')
                                            else:
                                                messages.success(request, response_data.get('Description', 'Failed to send SMS'))
                                        except ValueError:
                                            messages.success(request, 'Failed to parse JSON response')
                                    else:
                                        messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
                                except requests.RequestException as e:
                                    messages.success(request, f'Error: {str(e)}')
                        else:
                            messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
                                
                else:
                    pass

                if Invoice.objects.filter(vendor=user,id=invoice_id,is_ota=True):
                    # service items
                    from . stayinvoices import makeotaandfnbinvc
                    new_request = request
                    new_request.method = "POST"  # Simulate a POST request
                    new_request.POST = QueryDict(mutable=True)
                    new_request.POST.update({
                        'guestid': GUESTID,
                        'selectvalue': str()
                    })

                    # Call the bookingdate function with the modified request
                    return makeotaandfnbinvc(new_request)
                else:
                    return redirect('guestearch', id=GUESTID)
            else:
                return redirect('invoicepage', id=GUESTID)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

# def homepage(request):
#     try:
#         if request.user.is_authenticated:
#             user = request.user
             
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             # Filter data
#             category = RoomsCategory.objects.filter(vendor=user).order_by('id')
#             rooms = Rooms.objects.filter(vendor=user).order_by('id')
#             desired_date = datetime.now().date() + timedelta(days=3)
#             # desired_date = datetime.now().date()
#             print(desired_date)
#             if Roomcleancheck.objects.filter(vendor=user,current_date=desired_date).exists():
#                 pass
#             else:
                
#                 Roomcleancheck.objects.create(vendor=user,current_date=desired_date)
#                 roomsclans = Rooms.objects.filter(vendor=user, checkin__in=[1, 2])
#                 roomsclans.update(is_clean=False)
#                 Roomcleancheck.objects.filter(vendor=user).exclude(current_date=desired_date).delete()

            
#             # Update checkout status for guests
#             Gueststay.objects.filter(Q(vendor=user, checkoutdate__date__lte=desired_date) | Q(vendor=user, checkoutdate__date=desired_date)).update(checkoutstatus=True)

#             # Query sets
#             dats = Gueststay.objects.filter(vendor=user, checkoutdate__date__lte=desired_date, checkoutstatus=True, checkoutdone=False)
#             datsin = Gueststay.objects.filter(vendor=user, checkindate__date=desired_date)
#             tax = Taxes.objects.filter(vendor=user).all()
#             arriwaldata = RoomBookAdvance.objects.filter(
#                   # Include the vendor condition
#                 Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
#                 Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
#             ).exclude(vendor=user,saveguestdata__action='cancel')
            
#             bookedmisseddata = RoomBookAdvance.objects.filter(vendor=user, checkoutdate__lte=desired_date, checkinstatus=False).exclude(vendor=user,saveguestdata__action='cancel')
#             saveguestallroomcheckout = RoomBookAdvance.objects.filter(vendor=user, checkoutdate=desired_date, checkinstatus=True).exclude(vendor=user,saveguestdata__action='cancel').exclude(checkOutstatus=True)
            
#             # find to clour red
#             reddata = Gueststay.objects.filter(vendor=user, checkoutdate__date__gt=desired_date, checkoutstatus=False, checkoutdone=False)
#             for i in reddata:
#                 print(i.roomno,"room no")
#                 if Rooms.objects.filter(
#                         vendor=user,
#                         room_name=i.roomno,
#                         checkin__in=[1, 4, 5]
#                     ).exists():
#                         pass
#                 else:
#                     Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=1)
                    

#             # Update rooms based on filtered data
#             for i in saveguestallroomcheckout:
#                 roomnumber = i.roomno.room_name
#                 invcdata = InvoiceItem.objects.filter(vendor=user,description=roomnumber).last()
#                 if invcdata:
#                     if Invoice.objects.filter(vendor=user,id=invcdata.invoice.id,foliostatus=False,customer__checkoutdate=desired_date):
#                         Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=2)
#                     else:
#                         # Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=0)
#                         pass
#                 else:
#                     pass

#             for i in dats:
#                 Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=2)
                

#             for i in bookedmisseddata:
#                 if i.roomno.checkin == 5 or i.roomno.checkin == 4:
#                     Rooms.objects.filter(vendor=user, id=i.roomno.id).update(checkin=0)
            
#             # filter cancel booking jo cancel hai vo yaha filter ho rahe hai
#             arriwalcanceldata = RoomBookAdvance.objects.filter(
                 
#                 Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
#                 Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
#             ).exclude(vendor=user,saveguestdata__action='book')
            
            
#             # or jo book hai vo yaha


#             for data in  arriwalcanceldata:
#                     if data.roomno.checkin not in [1, 2, 6]:
#                         data = Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=0)
                        
#             for data in arriwaldata:
#                 if data.roomno.checkin not in [1, 2, 5]:
#                     Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=4)
            

#             # Additional queries
#             checkintimedata = HotelProfile.objects.filter(vendor=user)
#             stayover = Rooms.objects.filter(vendor=user, checkin=1).count()
#             availablerooms = Rooms.objects.filter(vendor=user, checkin=0).count()
#             totalrooms = Rooms.objects.filter(vendor=user).count()
#             checkoutcount = Gueststay.objects.filter(vendor=user, checkoutdate__date=desired_date, checkoutstatus=True, checkoutdone=False).count()
#             checkincountdays = len(datsin)

#             # Create rooms dictionary
#             roomsdict = {}
#             for cat in category:
#                 roomsdict[cat.category_name] = [[room.room_name, room.checkin,room.is_clean] for room in rooms.filter(room_type=cat)]

#             cleanrooms = Rooms.objects.filter(vendor=user, is_clean=True).count()        
#             uncleanrooms = Rooms.objects.filter(vendor=user, is_clean=False).count()     

            
            
#             return render(request, 'homepage.html', {
#                 'active_page': 'homepage',
#                 'category': category,
#                 'rooms': rooms,
#                 'roomsdict': roomsdict,
#                 'tax': tax,
#                 'checkintimedata': checkintimedata,
#                 'stayover': stayover,
#                 'availablerooms': availablerooms,
#                 'checkincount': checkincountdays,
#                 'checkoutcount': checkoutcount,
#                 'arriwalcount': len(arriwaldata),
#                 'cleanrooms':cleanrooms,
#                 'uncleanrooms':uncleanrooms,

#             })
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)






# new add guest data function solving tax issue
def addguestdata(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestname = request.POST.get('guestname')
            guestphome = request.POST.get('guestphone')
            guestemail = request.POST.get('guestemail')
            guestcity = request.POST.get('guestcity')
            guestcountry = request.POST.get('guestcountry')
            guestidimg = request.FILES.get('guestid')
            guestidbackimg = request.FILES.get('guestid1')
            checkindate = request.POST.get('guestcheckindate')
            checkoutdate = request.POST.get('guestcheckoutdate')
            noofguest = request.POST.get('noofguest')
            male = request.POST.get('male')
            female = request.POST.get('female')
            other = request.POST.get('other')
            arival = request.POST.get('arival')
            departure = request.POST.get('departure')
            adults = request.POST.get('guestadults')
            children = request.POST.get('guestchildren')
            purposeofvisit = request.POST.get('Purpose')
            roomno = request.POST.get('roomno')
            subtotal = request.POST.get('subtotal')
            total = request.POST.get('total')
            tax = request.POST.get('tax')
            state = request.POST.get('STATE')
            rateplanname = request.POST.get('rateplanname')
            rateplanprice = int(request.POST.get('rateplanprice'))
            subtotalbyform = int(request.POST.get('subtotal'))
            rateplan = request.POST.get('rateplan')
            idtype = request.POST.get('idtype')
            iddetails = request.POST.get('iddetails')
            staydays = float(request.POST.get('staydays'))
            subtotal=int(subtotal)
            total=int(total)
            
            roomdata = Rooms.objects.filter(vendor=user,room_name=roomno).all()
            for i in roomdata:
                    roomprice = i.price + rateplanprice
                    tax_rate = i.tax.taxrate
                    roomname = i.room_name
                    tax_amount = i.tax_amount
                    roomtype = i.room_type.id
                    room_details = i.room_type.category_name
            discount = abs(roomprice*staydays - subtotalbyform)
            checkmoredatastatus = request.POST.get('checkmoredatastatus')
            current_date = datetime.now()
            userstatedata = HotelProfile.objects.get(vendor=user)
            userstate = userstatedata.zipcode
            if Rooms.objects.filter(vendor=user,room_name=roomno,checkin=0).exists():
                Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
                divideamt = tax_amount / 2
                tax_rate = tax_rate / 2
                
                cat = RoomsCategory.objects.get(vendor=user,id=roomtype)
                
            
                room_details = roomname
              
                # daystotalprice = totalitemamount
                #  for invoice number
                current_date = datetime.now().date()
                invoice_number = ""
                # invcitemtotal = (totalitemamount *(tax_rate * 2) /100) + totalitemamount

                #new tax working here
                print(int(total),int(staydays) ,"check this ")
                staydays = int(staydays)
                onedayroomprice = int(total) / int(staydays)   
                # findamtsonly = float(exceptedsttl) / (1 + (tax_rate * 2) / 100)  # Fix: Divide by (1 + tax_rate/100) to calculate the base amount
                # foundnetamts = findamtsonly  # Base amount after removing tax
                # invoicetotalamount = foundnetamts * int(staydays) 
                
                Extracharge='false'
                if onedayroomprice > 8851:
                    onedayroomprice = float(onedayroomprice) / (1 + (18) / 100)
                    taxrate = 18
                    putrat = 9.0
                    invoicetotalamount = onedayroomprice * staydays
                    taxamount = invoicetotalamount *18/100
                    cgstamount = taxamount / 2
                    gstname = "GST18"
                    taxdata = Taxes.objects.get(vendor=user,taxrate=18)
                    hsncode = taxdata.taxcode
                    grabd_total_amount = invoicetotalamount + taxamount
                    GST_AMOUNT = taxamount
                    CGST_AMOUNT = cgstamount
                    Sgst_AMOUNT = cgstamount

                elif onedayroomprice <= 8400:
                    onedayroomprice = float(onedayroomprice) / (1 + (12) / 100)
                    taxrate = 12
                    putrat = 6.0
                    invoicetotalamount = onedayroomprice * staydays
                    taxamount = invoicetotalamount *12/100
                    cgstamount = taxamount / 2
                    gstname = "GST12"
                    taxdata = Taxes.objects.get(vendor=user,taxrate=12)
                    hsncode = taxdata.taxcode
                    grabd_total_amount = invoicetotalamount + taxamount
                    GST_AMOUNT = taxamount
                    CGST_AMOUNT = cgstamount
                    Sgst_AMOUNT = cgstamount

                else:
                    checkpricediffrance = onedayroomprice - 8400
                    onedayroomprice=7500
                    taxrate = 12 
                    putrat = 6.0
                    gstname = "GST12"
                    invoicetotalamount = onedayroomprice * staydays
                    taxamount = invoicetotalamount *12/100
                    cgstamount = taxamount / 2
                    taxdata = Taxes.objects.get(vendor=user,taxrate=12)
                    hsncode = taxdata.taxcode
                    Extracharge='true'
                    withouttaxextracharge = float(checkpricediffrance) / (1 + (18) / 100)
                    
                    grabd_total_amount = invoicetotalamount + taxamount 

                

                    GST_AMOUNT = taxamount
                    CGST_AMOUNT = cgstamount
                    Sgst_AMOUNT = cgstamount



                taxtypes = "GST"
                
                guestdata = Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
                                        checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
                                        ,purposeofvisit=purposeofvisit,roomno=roomno,tax=gstname,discount=0.00,subtotal=invoicetotalamount,total=grabd_total_amount,noofrooms=1
                                        ,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,rate_plan=rateplanname,
                                        channel='PMS',saveguestid=None,male=male,female=female,transg=other,dp=departure,ar=arival)
                if guestidbackimg:
                    Guest_BackId.objects.create(vendor=user,guest=guestdata,
                                guestidbackimg=guestidbackimg)
                gsid=guestdata.id
                if checkmoredatastatus == 'on':
                    moreguestname = request.POST.get('moreguestname')
                    moreguestphone = request.POST.get('moreguestphone',0)
                    moreguestaddress = request.POST.get('moreguestaddress')
                    if moreguestphone == "":
                        moreguestphone = 0
                    else:
                        pass
                    MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
                                                another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                    

                
                Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
                                                    invoice_number=invoice_number,invoice_date=checkindate,total_item_amount=invoicetotalamount,discount_amount=0.00,
                                                    subtotal_amount=invoicetotalamount,gst_amount=CGST_AMOUNT,sgst_amount=Sgst_AMOUNT,
                                                    grand_total_amount=grabd_total_amount,modeofpayment='',room_no=roomname,
                                                    taxtype=taxtypes,accepted_amount=0.00 ,Due_amount=grabd_total_amount,taxable_amount=invoicetotalamount)
                
                totaltaxesamt = Sgst_AMOUNT * 2
                taxSlab.objects.create(vendor=user,invoice=Invoiceid,tax_rate_name=gstname,
                        cgst=putrat,sgst=putrat,cgst_amount=CGST_AMOUNT,sgst_amount=Sgst_AMOUNT,total_amount=taxamount)

                
                if Taxes.objects.filter(vendor=user,taxname=gstname).exists():
                    taxnames = Taxes.objects.filter(vendor=user,taxname=gstname).last()
                    HSNcode = taxnames.taxcode
                else:
                    HSNcode=0
                rateplandata=RatePlan.objects.filter(vendor=user,id=rateplan).first()
               
                msecs = cat.category_name + " : " + rateplanname + " " + rateplandata.rate_plan_code  + " " + " for "+ str(adults) + " adults " + " " +   " and " + str(children) + " " + "Child"
                if  rateplandata.rate_plan_name=="EP":
                    ismealprice = 0.0
                    ismeal=False
                    plannm = "EP"
                else:
                    ismeal = True
                    ismealprice = float(rateplandata.base_price) * staydays
                    plannm = rateplandata.rate_plan_name
                
                invoiceitem = InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=room_details,quantity_likedays=staydays,
                                        mdescription=msecs,is_room=True,price=onedayroomprice,cgst_rate=putrat,sgst_rate=putrat,hsncode=HSNcode,total_amount=grabd_total_amount,
                                        cgst_rate_amount=CGST_AMOUNT,sgst_rate_amount=Sgst_AMOUNT,totalwithouttax=invoicetotalamount,
                                        checkout_date=checkoutdate,is_mealp=ismeal,mealpprice=ismealprice,
                                        mealplanname=plannm)  
                
                if Extracharge=='true':
                    extrachargeprice = withouttaxextracharge 
                    exratotalwithdays = (withouttaxextracharge * staydays)
                    extrataxamount = exratotalwithdays *18/100
                    extracgstamount = extrataxamount/2
                    extragrandtotal = extrataxamount + exratotalwithdays
                    grabd_total_amount = grabd_total_amount + extragrandtotal
                    if Taxes.objects.filter(vendor=user,taxname=gstname).exists():
                        taxnames = Taxes.objects.filter(vendor=user,taxname='GST18').last()
                        HSNcode18 = taxnames.taxcode
                    else:
                        HSNcode18=0
                    
                    roomname = 'Room: ' + str(room_details)
                    InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomname,quantity_likedays=staydays,
                                        mdescription='Extra Charges',is_room=False,price=extrachargeprice,cgst_rate=9.0,sgst_rate=9.0,hsncode=HSNcode18,
                                        total_amount=extragrandtotal,is_room_extra=True,
                                        cgst_rate_amount=extracgstamount,sgst_rate_amount=extracgstamount,totalwithouttax=exratotalwithdays)  
                    
                    taxSlab.objects.create(vendor=user,invoice=Invoiceid,tax_rate_name='GST18',
                        cgst=9.0,sgst=9.0,cgst_amount=extracgstamount,sgst_amount=extracgstamount,total_amount=extrataxamount)

                    Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(total_item_amount=F('total_item_amount')+exratotalwithdays,
                                subtotal_amount=F('subtotal_amount')+exratotalwithdays,gst_amount=F('gst_amount')+extracgstamount,
                                sgst_amount=F('sgst_amount')+extracgstamount,grand_total_amount=F('grand_total_amount')+extragrandtotal,
                                taxable_amount=F('taxable_amount')+exratotalwithdays,Due_amount=F('Due_amount')+extragrandtotal)
                    

                Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
                roominventorydata = RoomsInventory.objects.filter(vendor=user,date__range = [checkindate,checkoutdate])
                
                
                # add to bookings
                roomids = Rooms.objects.get(vendor=user,room_name=roomno)
                current_time = datetime.now().time()
                noon_time_str = "12:00 PM"
                noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                Booking.objects.create(vendor=user,room_id=roomids.id,guest_name=guestname,check_in_date=checkindate,
                                      check_out_date=checkoutdate,check_in_time= current_time,segment="PMS",
                                      totalamount=grabd_total_amount,totalroom='1',check_out_time=noon_time,
                                      gueststay=guestdata,advancebook=None,status="CHECK IN")

                actionss = 'Create RoomAllocation'
                CustomGuestLog.objects.create(vendor=user,customer=guestdata,by=request.user,action=actionss,
                            description=f'Reservation is created from {checkindate} To {checkoutdate}')


                # Convert date strings to date objects
                checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                # Generate the list of all dates between check-in and check-out (inclusive)
                all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

                # Query the RoomsInventory model to check if records exist for all those dates
                existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category_id=roomtype, date__in=all_dates)

                # Get the list of dates that already exist in the inventory
                existing_dates = set(existing_inventory.values_list('date', flat=True))

                # Identify the missing dates by comparing all_dates with existing_dates
                missing_dates = [date for date in all_dates if date not in existing_dates]

                # If there are missing dates, create new entries for those dates in the RoomsInventory model
                roomcount = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
             
                
              
                for inventory in existing_inventory:
                    if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
                        # Update room availability and booked rooms
                        inventory.total_availibility -= 1
                        inventory.booked_rooms += 1

                        # Calculate total rooms
                        total_rooms = inventory.total_availibility + inventory.booked_rooms

                        # Recalculate the occupancy based on the updated values
                        if total_rooms > 0:
                            inventory.occupancy = (inventory.booked_rooms / total_rooms) * 100
                        else:
                            inventory.occupancy = 0  # Avoid division by zero if no rooms exist

                        # Save the updated inventory
                        inventory.save()
                
                catdatas = RoomsCategory.objects.get(vendor=user,id=roomtype)
                totalrooms = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
                occupancccy = (1 *100 //totalrooms)
                if missing_dates:
                    for missing_date in missing_dates:
                       
                            RoomsInventory.objects.create(
                                vendor=user,
                                date=missing_date,
                                room_category_id=roomtype,  # Use the appropriate `roomtype` or other identifier here
                                total_availibility=roomcount-1,       # Set according to your logic
                                booked_rooms=1,                # Set according to your logic
                                price=catdatas.catprice,
                                occupancy=occupancccy,
                            )
                    
                else:
                    pass

                # api calling backend automatically
                            # Start the long-running task in a separate thread
                if VendorCM.objects.filter(vendor=user):
                    start_date = str(checkindate)
                    end_date = str(checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()
                    # for dynamic pricing
                    if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                        thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                        thread.start()
                    else:
                        pass

                else:
                    pass
                
                
                userid = guestdata.id
                url = reverse('invoicepage', args=[userid])
                return redirect(url)
                # return redirect('foliobillingpage')
            else:
                return redirect('foliobillingpage')
        else:
            return redirect('loginpage') 
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)







def addguestdatafromadvanceroombook(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestname = request.POST.get('guestname')
            guestphome = request.POST.get('guestphone')
            guestemail = request.POST.get('guestemail')
            guestcity = request.POST.get('guestcity')
            guestcountry = request.POST.get('guestcountry')
            guestidimg = request.FILES.get('guestid')
            guestidbackimg = request.FILES.get('guestid1')
            checkindate = request.POST.get('guestcheckindate')
            checkoutdate = request.POST.get('guestcheckoutdate')
            noofguest = request.POST.get('noofguest')
            male = request.POST.get('male')
            female = request.POST.get('female')
            other = request.POST.get('other')
            arival = request.POST.get('arival')
            departure = request.POST.get('departure')
            adults = request.POST.get('guestadults')
            children = request.POST.get('guestchildren')
            purposeofvisit = request.POST.get('Purpose')
            roomno = request.POST.get('roomno')
            subtotal = request.POST.get('subtotal')
            total = request.POST.get('total')
            tax = request.POST.get('tax')
            noofrooms = request.POST.get('noofrooms')
            saveguestdata = request.POST.get('saveguestdata')
            msid = saveguestdata
            SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestdata).update(checkinstatus=True)
            checkmoredatastatus = request.POST.get('checkmoredatastatus')
            roomalldefaultcheckinbutton = request.POST.get('roomalldefaultcheckinbutton')
            discount = request.POST.get('discount')
            state = request.POST['STATE']
            idtype = request.POST.get('idtype')
            iddetails = request.POST.get('iddetails')
            subtotal=int(subtotal)
            paidstatus = request.POST.get('paidstatus')
            total=int(total)
            saveguestdata =  SaveAdvanceBookGuestData.objects.get(vendor=user,id=saveguestdata)
            guestcheckinstatus= False
            userstatedata = HotelProfile.objects.get(vendor=user)
            userstate = userstatedata.zipcode
            roomsdatas = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestdata)
            paymentstatus = saveguestdata.Payment_types
            checkindoornot = True
            for check in roomsdatas:
                if check.roomno.checkin == 1 or check.roomno.checkin == 2:
                    checkindoornot = False
            if checkindoornot == True:
                
                taxtypes = "GST"
                
                if guestcheckinstatus is True:
                    
                    messages.error(request,'recently Check In this Room With Same Data Please Change Address Mobile And Guest Name heckIn CheckOut Date / Room No to CheckIn this Room')
                else:
                    current_date = datetime.now()
                    rateplansdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()
                    guestdata=Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
                                                checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
                                                ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=noofrooms
                                            ,rate_plan=rateplansdata.rateplan_code,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,saveguestid=saveguestdata.id,channel=saveguestdata.channal.channalname,
                                            male=male,female=female,transg=other,dp=departure,ar=arival)
                    if guestidbackimg:
                        Guest_BackId.objects.create(vendor=user,guest=guestdata,
                                guestidbackimg=guestidbackimg)

                    Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,
                                                invoice_number="",invoice_date=checkindate,total_item_amount=0.0,discount_amount=discount,
                                                        subtotal_amount=0.0,gst_amount=0.0,sgst_amount=0.0,accepted_amount=0.00,
                                                        Due_amount=0.00,grand_total_amount=0.0,modeofpayment=paymentstatus,room_no=0.0,taxtype=taxtypes)
                    if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid,bookingguestphone=guestphome).exists():
                        pass
                    else:
                        SaveAdvanceBookGuestData.objects.filter(vendor=user,id=msid).update(bookingguestphone=guestphome)
                    
                    totalrooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
                    staydays = saveguestdata.staydays
                    totalgrandcheckamount = 0.0
                    permission = 'false'
                    for i in totalrooms:
                            rid = i.roomno.id
                            roomdata = Rooms.objects.get(vendor=user,id=rid)
                            if extraBookingAmount.objects.filter(vendor=user,bookdata_id=i.id).exists():
                                permission='true'
                                selllprice=7500
                            else:
                                selllprice = i.sell_rate
                            gstrate = roomdata.tax.taxrate/2
                            hsn = roomdata.room_type.Hsn_sac
                            if selllprice >7500 and gstrate==6.0:
                                if Taxes.objects.filter(vendor=user,taxrate=18).exists():
                                    gstrate = 9.00
                                    taxesdata = Taxes.objects.filter(vendor=user,taxrate=18).last()
                                    hsn = taxesdata.taxcode
                                else:
                                    Taxes.objects.create(vendor=user,taxrate=18,taxname='GST18',taxcode=18)
                                    hsn = 0
                                    gstrate = 9.00
                            elif selllprice <=7500 and gstrate == 9.00:
                                gstrate = 6.00
                                taxesdata = Taxes.objects.filter(vendor=user,taxrate=12).last()
                                hsn = taxesdata.taxcode

                            else:
                                pass

                            

                    
                            taxes=selllprice*(gstrate*2)/100
                            toalamtitem = selllprice + taxes 
                            print(toalamtitem,"toTAL ITEM AMOUNT")
                            toalamtitem = toalamtitem * staydays
                            print(toalamtitem,"TOTAL ITEM AMOUNT BAD ME ")
                            totalgrandcheckamount = toalamtitem + totalgrandcheckamount
                            
                            print(taxes,"taxes checking on code")

                            daystotalprice = selllprice * staydays
                            
                            
                            checktaxrate = float(gstrate)
                            individualtaxamt = taxes / 2
                            bydaystaxamt = individualtaxamt * staydays
                            totaltaxamounts = taxes * staydays
                            
                            if taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).exists():
                                
                                taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=checktaxrate).update(
                                        cgst_amount=F('cgst_amount') + bydaystaxamt,
                                        sgst_amount=F('sgst_amount') + bydaystaxamt,
                                        total_amount=F('total_amount') + totaltaxamounts
                                )
                            else:
                                taxname = "GST"+str(int(checktaxrate*2))
                                taxSlab.objects.create(vendor=user,invoice=Invoiceid,cgst=checktaxrate,
                                        sgst=checktaxrate,tax_rate_name=taxname,cgst_amount=bydaystaxamt,
                                        sgst_amount=bydaystaxamt,total_amount=totaltaxamounts)
                               
                            
                            if RatePlan.objects.filter(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
                                            max_persons=i.adults,childmaxallowed=i.children):
                                ipbs = RatePlan.objects.get(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
                                            max_persons=i.adults,childmaxallowed=i.children)
                                base_price = ipbs.base_price + roomdata.price
                                msecs = roomdata.room_type.category_name + " "+ ipbs.rate_plan_code + " : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
                                if  ipbs.rate_plan_name=="EP":
                                    ismealprice = 0.0
                                    ismeal=False
                                    plnnm ="EP"
                                else:
                                    ismeal = True
                                    ismealprice = float(ipbs.base_price) * staydays
                                    plnnm=ipbs.rate_plan_name
                                InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice,
                                                        checkout_date=checkoutdate,is_mealp=ismeal,mealpprice=ismealprice,mealplanname=plnnm)
                            else:
                                if RatePlanforbooking.objects.filter(vendor=user,rate_plan_name=i.rateplan_code):
                                    pdatas= RatePlanforbooking.objects.get(vendor=user,rate_plan_name=i.rateplan_code)
                                    base_price = i.adults * (pdatas.base_price) + roomdata.price
                                    msecs = roomdata.room_type.category_name + " " + pdatas.rate_plan_code +" : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
                                    
                                    if  pdatas.rate_plan_name=="EP":
                                        ismealprice = 0.0
                                        ismeal=False
                                        plnnm="EP"
                                    else:
                                        ismeal = True
                                        ismealprice = float(pdatas.base_price) * i.adults * staydays 
                                        plnnm = pdatas.rate_plan_name
                                    InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice,
                                                        checkout_date=checkoutdate,is_mealp=ismeal,mealpprice=ismealprice,mealplanname=plnnm)

                                else:

                                    InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription="ONLY ROOM",hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True,cgst_rate_amount=bydaystaxamt,sgst_rate_amount=bydaystaxamt,totalwithouttax=daystotalprice,
                                                        checkout_date=checkoutdate)
                            
                            if permission == 'true':
                                extradata = extraBookingAmount.objects.get(vendor=user,bookdata_id=i.id)
                                roomname = 'Room: ' + str(roomdata.room_name)
                                extrataxdata = Taxes.objects.get(vendor=user,taxrate=18) 
                                extrahsncode = extrataxdata.taxcode
                                InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomname,
                                                        mdescription='Extra Charges',hsncode=extrahsncode,quantity_likedays=extradata.qty,price=extradata.price,
                                                        total_amount=extradata.grand_total_amount,cgst_rate=9.0,sgst_rate=9.0,
                                                        is_room=False,cgst_rate_amount=extradata.sgst_amount,sgst_rate_amount=extradata.csgst_amount,
                                                        totalwithouttax=extradata.taxable_amount,is_room_extra=True)
                                permission = 'false'
                                if taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=9.0).exists():
                                
                                    taxSlab.objects.filter(vendor=user,invoice=Invoiceid,cgst=9.0).update(
                                            cgst_amount=F('cgst_amount') + extradata.csgst_amount,
                                            sgst_amount=F('sgst_amount') + extradata.csgst_amount,
                                            total_amount=F('total_amount') + extradata.csgst_amount*2
                                    )
                                else:
                                    taxname = "GST18"
                                    taxSlab.objects.create(vendor=user,invoice=Invoiceid,cgst=9.0,
                                            sgst=9.0,tax_rate_name=taxname,cgst_amount=extradata.csgst_amount,
                                            sgst_amount=extradata.csgst_amount,total_amount=extradata.csgst_amount*2)
                            


                    
                    totalitemamount = saveguestdata.amount_before_tax + float(saveguestdata.discount) 
                    discamts = float(saveguestdata.discount)
                    subttlamt = saveguestdata.amount_before_tax 
                    gtamts = saveguestdata.amount_after_tax 
                    taxamts = saveguestdata.tax/2 

                    fisrroom = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()

                    
                    if  saveguestdata.pah==False:
                        otagstin = saveguestdata.channal.company_gstin
                        if otagstin:
                            pass
                        else:
                            otagstin=''
                        companyname = saveguestdata.channal.channalname
                        # old code
                        # Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(
                        #     customer_gst_number=otagstin,customer_company=companyname,
                        #     is_ota=True)
                        # new code
                        Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(
                            is_ota=True)
                        
                    else:
                        pass
                    today = datetime.now().date()
                    Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(total_item_amount=totalitemamount,
                                    discount_amount=discamts,subtotal_amount=subttlamt,invoice_date=today,
                                    modeofpayment=paymentstatus,grand_total_amount=gtamts,
                                    gst_amount=taxamts,sgst_amount=taxamts,room_no=fisrroom.roomno.room_name,
                                    taxable_amount=subttlamt)
                            

                            


                   
                    
                    if InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id).exists():
                        adpaymentdata = InvoicesPayment.objects.filter(vendor=user,advancebook_id=saveguestdata.id)
                        
                        advncspt = 0
                        chechtotalamt = int(float(saveguestdata.total_amount))
                        for i in adpaymentdata:
                            InvoicesPayment.objects.filter(vendor=user,id=i.id).update(invoice=Invoiceid)
                            invcdatas= InvoicesPayment.objects.get(vendor=user,id=i.id)
                            advncspt = advncspt + int(float(invcdatas.payment_amount))
                               
                        if advncspt == chechtotalamt:
                                Invoice.objects.filter(vendor=user,customer=guestdata).update(
                                 Due_amount=0.00,accepted_amount=float(advncspt)
                                )
                        elif advncspt < chechtotalamt:
                                dueamts = chechtotalamt - advncspt
                                Invoice.objects.filter(vendor=user,customer=guestdata).update(
                                 Due_amount=float(dueamts),accepted_amount=float(advncspt)
                                )
                    else:
                        Invoice.objects.filter(vendor=user,customer=guestdata).update(
                             Due_amount=float(saveguestdata.total_amount),accepted_amount=0.00
                            )
                        
                 
                
                


                    if checkmoredatastatus == 'on':
                        moreguestname = request.POST.get('moreguestname')
                        moreguestphone = request.POST.get('moreguestphone')
                        if moreguestphone == "":
                            moreguestphone = 0
                        else:
                            pass
                        moreguestaddress = request.POST.get('moreguestaddress')
                        MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
                                                    another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                     

            
                
                    
                    roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
                    #  roomdata = Room_history.objects.filter(vendor=user,checkindate__range=[checkindate,checkoutdate],bookingstatus=True,bookingguestphone=guestphome).all()
                    if roomalldefaultcheckinbutton == 'on':
                        for data in roomdata:
                      
                            Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=5)
                            roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
                      
                            RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(partly_checkin=True)
                            Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(
                                                                             gueststay=guestdata)
                            
                        return redirect('todaybookingpage')
                            
                        
                    else:
                        for data in roomdata:
                           
                            roomid = Rooms.objects.get(vendor=user,id=data.roomno.id)
                            Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=1)
                      
                            RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).update(checkinstatus=True,
                                                bookingdate=today)
                            ctime = datetime.now().time()
                            Booking.objects.filter(vendor=user,advancebook_id=saveguestdata,room=roomid).update(status="CHECK IN",check_in_time=ctime,
                                                                    check_in_date=today,gueststay=guestdata)
                        CustomGuestLog.objects.filter(vendor=user,advancebook=saveguestdata).update(
                            customer=guestdata
                        )
                        if today!=checkindate:
                            textmsg = f'Check In date is chaged from {checkindate} to {today}'
                            CustomGuestLog.objects.create(vendor=user,customer=guestdata,by=request.user,action='Check In Date Change',
                            description=textmsg)
                        actionss = 'Create Check-in'
                        CustomGuestLog.objects.create(vendor=user,customer=guestdata,by=request.user,action=actionss,
                            description=f'Booking Check-in is created from {checkindate} To {checkoutdate}')


                        userid = guestdata.id
                        url = reverse('invoicepage', args=[userid])
                        return redirect(url)

                

                
            else:
                messages.error(request,"Please check out the room that has not been checked out yet for the same guest before you can check in to a new room.")
                return redirect('todaybookingpage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def homepage(request):
    try:
        if request.user.is_authenticated:
            user = request.user
             
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Filter data
            category = RoomsCategory.objects.filter(vendor=user).order_by('id')
            rooms = Rooms.objects.filter(vendor=user).order_by('id')
            # desired_date = datetime.now().date() + timedelta(days=1)
            desired_date = datetime.now().date()
            
            if Roomcleancheck.objects.filter(vendor=user,current_date=desired_date).exists():
                pass
            else:
                
                Roomcleancheck.objects.create(vendor=user,current_date=desired_date)
                roomsclans = Rooms.objects.filter(vendor=user, checkin__in=[1, 2])
                roomsclans.update(is_clean=False)
                Roomcleancheck.objects.filter(vendor=user).exclude(current_date=desired_date).delete()

            
            booking_advance_data = Booking.objects.filter(vendor=user,check_in_date__lte=desired_date,check_out_date__gt=desired_date,status='BOOKING')


            booking_advance_yestarday_data = Booking.objects.filter(vendor=user,check_out_date__lt=desired_date,status='BOOKING')
            # print(booking_advance_yestarday_data,'booking yestarday data this')

            booking_checkin_data = Booking.objects.filter(vendor=user,check_in_date__lte=desired_date,check_out_date__gt=desired_date,status='CHECK IN')
            # print(booking_checkin_data,'check this')


            booking_checkout_data = Booking.objects.filter(vendor=user,check_out_date__lte=desired_date).filter(status='CHECK IN') 
            # print(booking_checkout_data,'checkout data this')
            for i in booking_advance_yestarday_data:
                if i.room and Rooms.objects.filter(vendor=user, id=i.room.id, checkin__in=[4, 5]).exists():
                    Rooms.objects.filter(vendor=user,id=i.room.id).update(checkin=0)  

            for i in booking_advance_data:
                if i.room and Rooms.objects.filter(vendor=user,id=i.room.id,checkin=0).exists():
                    Rooms.objects.filter(vendor=user,id=i.room.id).update(checkin=4)

            for i in booking_checkout_data:
                if i.room and Rooms.objects.filter(vendor=user,id=i.room.id,checkin__in=[1,0]).exists():
                    Rooms.objects.filter(vendor=user,id=i.room.id).update(checkin=2)

            for i in booking_checkin_data:
                if i.room and Rooms.objects.filter(vendor=user,id=i.room.id,checkin__in=[1,4,5,6]).exists():
                    pass
                else:
                    Rooms.objects.filter(vendor=user,id=i.room.id).update(checkin=1)
                

                          




            # Update checkout status for guests
            Gueststay.objects.filter(Q(vendor=user, checkoutdate__date__lte=desired_date) | Q(vendor=user, checkoutdate__date=desired_date)).update(checkoutstatus=True)

            # # Query sets
            # dats = Gueststay.objects.filter(vendor=user, checkoutdate__date__lte=desired_date, checkoutstatus=True, checkoutdone=False)
            datsin = Gueststay.objects.filter(vendor=user, checkindate__date=desired_date)
            
            arriwaldata = RoomBookAdvance.objects.filter(
                Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
                Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
            ).exclude(vendor=user,saveguestdata__action='cancel')
            
            
            

            # Additional queries
            checkintimedata = HotelProfile.objects.filter(vendor=user)
            stayover = Rooms.objects.filter(vendor=user, checkin=1).count()
            availablerooms = Rooms.objects.filter(vendor=user, checkin=0).count()
            checkoutcount = Gueststay.objects.filter(vendor=user, checkoutdate__date__lte=desired_date, checkoutstatus=True, checkoutdone=False).count()
            checkincountdays = len(datsin)

            # Create rooms dictionary
            roomsdict = {}
            for cat in category:
                roomsdict[cat.category_name] = [[room.room_name, room.checkin,room.is_clean] for room in rooms.filter(room_type=cat)]

            cleanrooms = Rooms.objects.filter(vendor=user, is_clean=True).count()        
            uncleanrooms = Rooms.objects.filter(vendor=user, is_clean=False).count()     

            
            
            return render(request, 'homepage.html', {
                'active_page': 'homepage',
                'roomsdict': roomsdict,
                'checkintimedata': checkintimedata,
                'stayover': stayover,
                'availablerooms': availablerooms,
                'checkincount': checkincountdays,
                'checkoutcount': checkoutcount,
                'arriwalcount': len(arriwaldata),
                'cleanrooms':cleanrooms,
                'uncleanrooms':uncleanrooms,

            })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def guesthistorysearchview(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            

            bookindid = request.POST.get('bookingmodelid')

            if Booking.objects.filter(vendor=user,id=bookindid).exists():
                bookdata = Booking.objects.filter(vendor=user,id=bookindid).last()
                guestid = bookdata.gueststay.id
                guestshistory = Gueststay.objects.filter(vendor=user,id=guestid)
                
               
            else:
                messages.error(request, "No matching guests found.")
                return redirect('weekviews')

            if not guestshistory.exists():
                messages.error(request, "No matching guests found.")

            return render(request, 'guesthistory.html', {'guesthistory': guestshistory, 'active_page': 'guesthistory'})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    