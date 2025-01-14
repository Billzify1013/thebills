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
           
            # Pass data to the template
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
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestshistory = Gueststay.objects.filter(vendor=user).values(
                'checkoutdate', 'checkindate', 'roomno', 'guestname', 'id', 'guestphome', 'guestcity', 'noofrooms'
            ).order_by('-id')
            
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
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

        
    
def guestdetails(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestdetails = Gueststay.objects.filter(vendor=user, id=id).all()
            moredata = MoreGuestData.objects.filter(vendor=user, mainguest_id=id).all()
            
            return render(request, 'guestdetails.html', {
                'guestdetails': guestdetails,
                'MoreGuestData': moredata,
                'active_page': 'guesthistory'
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
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            userid = id
            guestdata = Gueststay.objects.filter(vendor=user, id=userid)
            invoice_data = Invoice.objects.get(vendor=user, customer=userid)
            profiledata = HotelProfile.objects.filter(vendor=user)
            itemid = invoice_data.id
            status = invoice_data.foliostatus

            invoice_datas = Invoice.objects.filter(vendor=user, customer=userid)
            invoiceitemdata = InvoiceItem.objects.filter(vendor=user, invoice=itemid).order_by('id')
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            invcpayments = InvoicesPayment.objects.filter(vendor=user,invoice=itemid).all()
            
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
                        'sstamounts':sstamounts
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
                        'istamts':istamts
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
                            'creditdata':creditdata
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
                            'creditdata':creditdata
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
                            'istamts':istamts
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
                            'istamts':istamts
                        })
             
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


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
            if Invoice.objects.filter(vendor=user,customer_id=invcid).exists():
                Invoice.objects.filter(vendor=user,customer_id=invcid).update(customer_gst_number=gstnumber)
                Gueststay.objects.filter(vendor=user,id=invcid).update(guestphome=customerphone)
                

            else:
                pass

            url = reverse('invoicepage', args=[invcid])

        
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
            bookingdates = Booking.objects.filter(vendor=user,room=cat_data,check_in_date__gt=today).first()
            
            roomscategory_id = cat_data.room_type.id
            loyltydata = loylty_data.objects.filter(vendor=user, Is_active=True)
            meal_plan = RatePlan.objects.filter(vendor=user,room_category=roomscategory_id)
            current_date = datetime.now()
            ratedata = RoomsInventory.objects.none()
            if RoomsInventory.objects.filter(vendor=user,date=current_date,room_category=roomscategory_id):
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
            checkindate = request.POST.get('guestcheckindate')
            checkoutdate = request.POST.get('guestcheckoutdate')
            noofguest = request.POST.get('noofguest')
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
            # discount = float(request.POST.get('discount'))
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
                if userstate == state:
                    taxtypes = "GST"
                else:
                    taxtypes = "IGST"
                guestdata = Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
                                        checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
                                        ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=1
                                        ,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,rate_plan=rateplanname,
                                        channel='PMS',saveguestid=None)
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
                    
                
                
                
                divideamt = tax_amount / 2
                tax_rate = tax_rate / 2
                totalitemamount = roomprice * staydays
                subtotalamount = totalitemamount - discount
                gstamount = (subtotalamount * tax_rate) /100
                sgstamount = (subtotalamount * tax_rate) /100
                grandtotal_amount = subtotalamount + gstamount + sgstamount
                cat = RoomsCategory.objects.get(vendor=user,id=roomtype)
                hsnno = cat.Hsn_sac
            
                room_details = roomname
              
                #  for invoice number
                current_date = datetime.now().date()
                invoice_number = ""
                invcitemtotal = (totalitemamount *(tax_rate * 2) /100) + totalitemamount
                
                Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
                                                    invoice_number=invoice_number,invoice_date=checkindate,total_item_amount=subtotalamount,discount_amount=0.00,
                                                    subtotal_amount=subtotalamount,gst_amount=gstamount,sgst_amount=sgstamount,
                                                    grand_total_amount=grandtotal_amount,modeofpayment='',room_no=roomname,
                                                    taxtype=taxtypes,accepted_amount=0.00 ,Due_amount=grandtotal_amount,)
                
                rateplandata=RatePlan.objects.filter(vendor=user,id=rateplan).first()
                pprice = subtotalamount / staydays
                msecs = cat.category_name + " : " + rateplanname + " " + rateplandata.rate_plan_code  + " " + " for "+ str(adults) + " adults " + " " +   " and " + str(children) + " " + "Child"
                invoiceitem = InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=room_details,quantity_likedays=staydays,
                                        mdescription=msecs,is_room=True,price=pprice,cgst_rate=tax_rate,sgst_rate=tax_rate,hsncode=hsnno,total_amount=grandtotal_amount)  
                Rooms.objects.filter(vendor=user,room_name=roomno).update(checkin=1)
                
                roominventorydata = RoomsInventory.objects.filter(vendor=user,date__range = [checkindate,checkoutdate])
                
                
                # add to bookings
                roomids = Rooms.objects.get(vendor=user,room_name=roomno)
                current_time = datetime.now().time()
                noon_time_str = "12:00 PM"
                noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                Booking.objects.create(vendor=user,room_id=roomids.id,guest_name=guestname,check_in_date=checkindate,
                                      check_out_date=checkoutdate,check_in_time= current_time,segment="PMS",
                                      totalamount=grandtotal_amount,totalroom='1',check_out_time=noon_time,
                                      gueststay=guestdata,advancebook=None,status="CHECK IN")

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
            checkindate = request.POST.get('guestcheckindate')
            checkoutdate = request.POST.get('guestcheckoutdate')
            noofguest = request.POST.get('noofguest')
            adults = request.POST.get('guestadults')
            children = request.POST.get('guestchildren')
            purposeofvisit = request.POST.get('Purpose')
            roomno = request.POST.get('roomno')
            subtotal = request.POST.get('subtotal')
            total = request.POST.get('total')
            tax = request.POST.get('tax')
            noofrooms = request.POST.get('noofrooms')
            saveguestdata = request.POST.get('saveguestdata')
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
                if userstate == state:
                    taxtypes = "GST"
                else:
                    taxtypes = "IGST"
                if guestcheckinstatus is True:
                    
                    messages.error(request,'recently Check In this Room With Same Data Please Change Address Mobile And Guest Name heckIn CheckOut Date / Room No to CheckIn this Room')
                else:
                    current_date = datetime.now()
                    rateplansdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()
                    guestdata=Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
                                                checkindate=current_date,checkoutdate=checkoutdate ,noofguest=noofguest,adults=adults,children=children
                                                ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=noofrooms
                                            ,rate_plan=rateplansdata.rateplan_code,guestidtypes=idtype,guestsdetails=iddetails,gueststates=state,saveguestid=saveguestdata.id,channel=saveguestdata.channal.channalname)
                    Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
                                                invoice_number="",invoice_date=checkindate,total_item_amount=0.0,discount_amount=discount,
                                                        subtotal_amount=0.0,gst_amount=0.0,sgst_amount=0.0,accepted_amount=0.00,
                                                        Due_amount=0.00,grand_total_amount=0.0,modeofpayment=paymentstatus,room_no=0.0,taxtype=taxtypes)
                        
                    
                    totalrooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).all()
                    staydays = saveguestdata.staydays
                    for i in totalrooms:
                            rid = i.roomno.id
                            roomdata = Rooms.objects.get(vendor=user,id=rid)
                            selllprice = i.sell_rate
                            taxes=selllprice*roomdata.tax.taxrate/100
                            toalamtitem = selllprice + taxes 
                            toalamtitem = toalamtitem * staydays
                            hsn = roomdata.room_type.Hsn_sac
                            gstrate = roomdata.tax.taxrate/2

                            
                            
                            if RatePlan.objects.filter(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
                                            max_persons=i.adults,childmaxallowed=i.children):
                                ipbs = RatePlan.objects.get(vendor=user,room_category_id=roomdata.room_type.id,rate_plan_name=i.rateplan_code,
                                            max_persons=i.adults,childmaxallowed=i.children)
                                base_price = ipbs.base_price + roomdata.price
                                msecs = roomdata.room_type.category_name + " "+ ipbs.rate_plan_code + " : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
                                InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True)
                            else:
                                if RatePlanforbooking.objects.filter(vendor=user,rate_plan_name=i.rateplan_code):
                                    pdatas= RatePlanforbooking.objects.get(vendor=user,rate_plan_name=i.rateplan_code)
                                    base_price = i.adults * (pdatas.base_price) + roomdata.price
                                    msecs = roomdata.room_type.category_name + " " + pdatas.rate_plan_code +" : " + i.rateplan_code + " " + " for "+ str(i.adults) + " adults " + " " +   " and " + str(i.children) + " " + "Child"
                                    InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription=msecs,hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True)

                                else:

                                    InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomdata.room_name,
                                                        mdescription="ONLY ROOM",hsncode=hsn,quantity_likedays=staydays,price=selllprice,
                                                        total_amount=toalamtitem,cgst_rate=gstrate,sgst_rate=gstrate,
                                                        is_room=True)
                            

                    totalitemamount = saveguestdata.amount_before_tax + float(saveguestdata.discount)
                    discamts = float(saveguestdata.discount)
                    subttlamt = saveguestdata.amount_before_tax
                    gtamts = saveguestdata.amount_after_tax
                    taxamts = saveguestdata.tax/2 

                    fisrroom = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestdata).first()

                    

                    Invoice.objects.filter(vendor=user,id=Invoiceid.id).update(total_item_amount=totalitemamount,
                                    discount_amount=discamts,subtotal_amount=subttlamt,
                                    modeofpayment=paymentstatus,grand_total_amount=gtamts,
                                    gst_amount=taxamts,sgst_amount=taxamts,room_no=fisrroom.roomno.room_name)
                            

                            


                   
                    
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
                     

            
                
                    today = datetime.now().date()
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
                                                                             gueststay=guestdata)
                        
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


                    SaveAdvanceBookGuestData.objects.filter(id=saveguestidfilter).delete()
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
              
                if Invoice.objects.filter(vendor=user,customer_id=customerid).exists():
                    invcid = Invoice.objects.get(vendor=user,customer_id=customerid)
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
                    if Invoice.objects.filter(vendor=user,id=invceid).exists():
                        invoicedata = Invoice.objects.get(vendor=user,id=invceid)
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
                        'pdt': True, 'set': True, 'ups': True ,'fce':True
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

            if checkoutdate == bookingdate:
                messages.error(request, 'Same-Day Checkout Booking Are Not Allowed Here Book To Hourly Room Booking')
                return redirect('advanceroombookpage')
            else:

                # Fetching guest stays with checkoutstatus=False within the specified date range
                guestroomsdata = Gueststay.objects.filter(
                    Q(vendor=user, checkoutstatus=False) &
                    Q(checkindate__lte=checkoutdate) & 
                    Q(checkoutdate__gte=newbookdateminus)
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
                availableroomdata = [
                    room for room in roomdata
                    if room.room_name not in occupied_rooms and room not in booked_rooms
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

def addadvancebooking(request):
    # try:
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
            totalamount = float(request.POST.get('totalamount'))
            advanceamount = request.POST.get('advanceamount',0)
            discountamount = float(request.POST.get('discountamount',0))
            reaminingamount = request.POST.get('reaminingamount',0)
            mealplan = request.POST.get('mealplan')
            guestcount = request.POST.get('guestcount')
            paymentmode = request.POST.get('paymentmode')
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
           
            
            # delta = timedelta(days=1)
            # while bookingdate <= checkoutdate:
           
            #         bookingdate += delta
            current_date = datetime.now()
            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(vendor=user,bookingdate=bookingdate,noofrooms=noofrooms,bookingguest=guestname,
                bookingguestphone=phone,staydays=totalstaydays,advance_amount=advanceamount,reamaining_amount=reaminingamount,discount=discountamount,
                total_amount=totalamount,channal=channal,checkoutdate=bookenddate,email='',address_city='',state='',country='',totalguest=guestcount,
                action='book',booking_id=None,cm_booking_id=None,segment='PMS',special_requests='',pah=True,amount_after_tax=totalamount,amount_before_tax=0.00,
                  tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=True)
            paymenttypes = 'postpaid'
            pah=True
            if int(advanceamount) > 0:
                pah=False
                InvoicesPayment.objects.create(vendor=user,invoice=None,payment_amount=advanceamount,payment_date=current_date,
                                                payment_mode=paymentmode,transaction_id="ADVANCE AMOUNT",descriptions='ADVANCE',advancebook=Saveadvancebookdata)
                if int(advanceamount) < int(totalamount):
                    paymenttypes = 'partially'
                else:
                    paymenttypes = 'prepaid'
            else:
                pass 
            sellingprices = 0    
            totaltax = 0   
            guestcountsstored = int(guestcount) 
            changedguestct = guestcountsstored
            for i in my_array:
                    roomid = int(i['id'])
                    roomsellprice = int(float(i['price']))
                    roomselltax = int(float(i['tax']))
                    befortselprice=roomsellprice
                    befortselprice = befortselprice / int(totalstaydays)
                    sellingprices = sellingprices + roomsellprice
                    totalsellprice = (roomsellprice * roomselltax //100) + roomsellprice
                    totaltax = totaltax + (roomsellprice * roomselltax /100) 
                  
                    roomid = Rooms.objects.get(id=roomid)
                    roomtype = roomid.room_type.id

                    # # manage rate plan guests
                    maxperson = roomid.max_person
                    if changedguestct >= maxperson:
            
                        changedguestct = changedguestct - maxperson
                  
                        satteldcount = maxperson
                    else:
                 
                        satteldcount = changedguestct

                  
                
                    RoomBookAdvance.objects.create(vendor=user,saveguestdata=Saveadvancebookdata,bookingdate=bookingdate,roomno=roomid,
                                                    bookingguest=guestname,bookingguestphone=phone
                                                ,checkoutdate=bookenddate,bookingstatus=True,channal=channal,totalguest=satteldcount,
                                               rateplan_code=mealplan,guest_name='',adults=satteldcount,children=0,sell_rate=befortselprice )
                    noon_time_str = "12:00 PM"
                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                    Booking.objects.create(vendor=user,room=roomid,guest_name=guestname,check_in_date=bookingdate,check_out_date=bookenddate,
                                check_in_time=noon_time,check_out_time=noon_time,segment="PMS",totalamount=totalamount,totalroom=noofrooms,
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
                    totalrooms = Rooms.objects.filter(vendor=user,room_type_id=roomtype).exclude(checkin=6).count()
                    occupancccy = (1 *100 //totalrooms)
                    if missing_dates:
                        for missing_date in missing_dates:
                        
                                RoomsInventory.objects.create(
                                    vendor=user,
                                    date=missing_date,
                                    room_category_id=roomtype,  # Use the appropriate `roomtype` or other identifier here
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
            if TravelAgency.objects.filter(vendor=user,name=channal.channalname).exists():
                traveldata = TravelAgency.objects.filter(vendor=user,name=channal.channalname).first()
                curtdate = datetime.now().date()
                if traveldata.commission_rate > 0:
                    agencydata = TravelAgency.objects.get(vendor=user,id=traveldata.id)
                    if agencydata.commission_rate >0:
                        commision = sellingprices*agencydata.commission_rate//100
                        Travelagencyhandling.objects.create(vendor=user,agency=agencydata,bookingdata=Saveadvancebookdata,
                                                date=curtdate,commsion=commision)
                    else:
                        pass
            SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_before_tax=sellingprices,
                                tax=float(totaltax),Payment_types=paymenttypes,pah=pah)
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
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)
    


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
            # return render(request,'advanceroomclickpage.html',{'id':roomno,'countrooms':countrooms,'roomnumberdata':roomnumberdata,'room_data':room_data,'roomguestdata':roomguestdata})
            return render(request,'advanceroomclickpage.html',{'loyltydata':loyltydata,'id':roomno,'countrooms':countrooms,'roomnumberdata':roomnumberdata,'room_data':room_data,'roomguestdata':roomguestdata,'paymentdatauserfromsaveadvancedata':paymentdatauserfromsaveadvancedata})
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
                    ).order_by('bookingdate')
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
        



            monthbookdata  = SaveAdvanceBookGuestData.objects.filter(
                vendor=user,
                bookingdate__range=(first_day_of_month, last_day_of_month)
                    ).order_by('bookingdate')

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
            return render(request,'advancebookingdetailspage.html',{'roomdata':roomdata,'guestdata':guestdata,'active_page': 'advancebookhistory'})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

# advance booking delete function
def advancebookingdelete(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            saveguestid=id
            checkdatas = SaveAdvanceBookGuestData.objects.get(vendor=user,id=saveguestid)
            if not  checkdatas.booking_id :
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
                    
                  
                    messages.success(request,'booking Cancelled succesfully')
                else:
                    messages.error(request,'Guest Is Stayed If You Want To Delete So cancel the folio room.')
                # advanceroomdata = SaveAdvanceBookGuestData.objects.filter(vendor=user).all()
                # return render(request,'advancebookinghistory.html',{'advanceroomdata':advanceroomdata,'active_page': 'advancebookhistory'})
                return redirect('advanceroomhistory')
            else:
                messages.error(request,'This Booking From OTA SO You Cant Delete this!.')
                return redirect('advanceroomhistory')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

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
def deleteitemstofolio(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invoiceid = request.POST.get('invoiceid')
            invoiceitemsid = request.POST.get('invoiceitemsid')
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
                            
                            
                            
                        else:
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
                                                                                    grand_total_amount=grandtotalamt,Due_amount=dueamount)
                            InvoiceItem.objects.filter(vendor=user,id=invoiceitemsid,invoice_id=invoiceid).delete()
                            
                    
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

                    invoicedatasorg = Invoice.objects.get(vendor=user,id=invoiceid)
                    if companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatasorg).exists():
                                cmpinvcamt = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatasorg)
                                reamins = int(float(cmpinvcamt.Value)) - int(float(invoicedatasorg.accepted_amount))
                                companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatasorg).update(
                                    Value=reamins
                                )
                                cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatasorg)
                                orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
                                values = int(float(orgcmp.values))
                                updateval = values - int(float(invoicedatasorg.accepted_amount))
                                Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
                                            values=updateval
                                )


                invoicedatas = Invoice.objects.get(vendor=user,id=invoiceid)
                duesamts = int(invoicedatas.Due_amount)
                if duesamts==0:
                        
                        invccurrentdate = datetime.now().date()

                        # Fetch the maximum invoice number for today for the given user
                        max_invoice_today = Invoice.objects.filter(
                            vendor=user,
                            invoice_date=invccurrentdate,
                            foliostatus=True
                        ).aggregate(max_invoice_number=Max('invoice_number'))['max_invoice_number']

                        # Determine the next invoice number
                        if max_invoice_today is not None:
                            # Extract the numeric part of the latest invoice number and increment it
                            try:
                                current_number = int(max_invoice_today.split('-')[-1])
                                next_invoice_number = current_number + 1
                            except (ValueError, IndexError):
                                # Handle the case where the invoice number format is unexpected
                                next_invoice_number = 1
                        else:
                            next_invoice_number = 1

                        # Generate the invoice number
                        invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'
                        
                        # Check if the generated invoice number already exists
                        while Invoice.objects.filter(vendor=user,invoice_number=invoice_number).exists():
                            next_invoice_number += 1
                            invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'

                        
                        
                        Invoice.objects.filter(vendor=user,id=invoiceid).update(invoice_number=invoice_number,invoice_status=True,modeofpayment="pms",
                                                invoice_date=invccurrentdate)
                        if companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatas).exists():
                                companyinvoice.objects.filter(vendor=user,Invoicedata=invoicedatas).update(is_paid=True)
                                cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=invoicedatas)
                                orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
                                values = int(orgcmp.values)
                                updateval = values + int(float(invoicedatas.grand_total_amount))
                                Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
                                            values=updateval
                                )
                        CustomerCredit.objects.get(vendor=user,id=creditid).delete()
                        messages.success(request,"Invoice Sattle done Succesfully!")
                            
                        
                else:
                    pass
                url = reverse('invoicepage', args=[userid])
                return redirect(url)
     
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

            rooms = Rooms.objects.filter(vendor=user)
            categories = RoomsCategory.objects.filter(vendor=user).order_by('id')
            bookings = Booking.objects.filter(vendor=user)

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
        try:
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
            check_in_date = datetime.strptime(check_in, '%b. %d, %Y').date()
            check_out_date = datetime.strptime(check_out, '%b. %d, %Y').date()

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
                total_amount=total_price*days,
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
                is_selfbook=False

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

        except Exception as e:
            
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)



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
        return render(request, 'bookingrecipt.html', {
            'advancebookdata': advancebookdata,
            'advancebookingdatas': advancebookingdatas,
            'hoteldata': hoteldata,
            'terms_lines':terms_lines
        })
       
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

# def receipt_view(request, booking_id):
#     try:
#         # Access the query parameter using request.GET.get('key')
#         extra_param = request.GET.get('extra_param', None)  # Default to None if the parameter doesn't exist

#         # Fetch the booking data based on `booking_id`
#         advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
#         for i in advancebookdata:
#             vid = i.vendor.id
#         advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
#         hoteldata = HotelProfile.objects.filter(vendor_id=vid)
#         hoteldatas = HotelProfile.objects.get(vendor_id=vid)
#         terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []

#         # Return the template with the booking data and optional query parameter
#         return render(request, 'bookingrecipt.html', {
#             'advancebookdata': advancebookdata,
#             'advancebookingdatas': advancebookingdatas,
#             'hoteldata': hoteldata,
#             'terms_lines': terms_lines,
#             'extra_param': extra_param,  # Send the query parameter to the template
#         })
#     except Exception as e:
#         return HttpResponse(f"Error occurred: {e}")

# def receipt_view(request):
#     try:
#         # Get the booking_id from the query parameter 'extra_param'
#         booking_id = request.GET.get('cd')

#         # If the booking_id is not provided, return an error message
#         if not booking_id:
#             return HttpResponse("Error: Missing booking_id.")

#         # Fetch the booking data using `booking_id`
#         advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
#         for i in advancebookdata:
#             vid = i.vendor.id
#         advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
#         hoteldata = HotelProfile.objects.filter(vendor_id=vid)
#         hoteldatas = HotelProfile.objects.get(vendor_id=vid)
#         terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []

#         # Return the template with the booking data and query parameter
#         return render(request, 'bookingrecipt.html', {
#             'advancebookdata': advancebookdata,
#             'advancebookingdatas': advancebookingdatas,
#             'hoteldata': hoteldata,
#             'terms_lines': terms_lines,
#             'booking_id': booking_id,  # Send the booking_id to the template
#         })
#     except Exception as e:
#         return HttpResponse(f"Error occurred: {e}")

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

    # Return the template with the booking data and query parameter
    return render(request, 'bookingrecipt.html', {
        'advancebookdata': advancebookdata,
        'advancebookingdatas': advancebookingdatas,
        'hoteldata': hoteldata,
        'terms_lines': terms_lines,
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
                
                # SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid).delete()
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
            url = reverse('receipt_view', args=[saveguestid])

        
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
                
                return render(request,'websetings.html',{'active_page': 'websettings','amenities':amenities,'offers':offers,
                                                        'checkstatus':checkstatus,'ctdata':ctdata,'cpdata':cpdata,'roomcat':roomcat,'gallary':gallary,'hotelimgs':hotelimgs})
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
            dueamount = request.POST.get('dueamount')
            duedate = request.POST.get('duedate')
            
            if Invoice.objects.filter(vendor=user,id=invoice_id,foliostatus=False).exists():
                if gstnumbercustomer:
                    Invoice.objects.filter(vendor=user,id=invoice_id).update(customer_gst_number=gstnumbercustomer)
                else:
                    pass
                if Invoice.objects.filter(vendor=user,id=invoice_id).exists():
                    GUESTIDs = Invoice.objects.get(vendor=user,id=invoice_id)
                    GUESTID = GUESTIDs.customer.id
                    invoicegrandtotalpaymentstatus = GUESTIDs.grand_total_amount
                    
                    
                    # new updated code
                    if int(float(dueamount)) == 0 :
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=True)
                        if companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).exists():
                            companyinvoice.objects.filter(vendor=user,Invoicedata=GUESTIDs).update(is_paid=True)
                            cmpdats = companyinvoice.objects.get(vendor=user,Invoicedata=GUESTIDs)
                            orgcmp = Companies.objects.get(vendor=user,id=cmpdats.company.id)
                            values = int(orgcmp.values)
                            updateval = values + int(float(GUESTIDs.grand_total_amount))
                            Companies.objects.filter(vendor=user,id=cmpdats.company.id).update(
                                        values=updateval
                            )
                        
                    else: #unpaid 
                        Invoice.objects.filter(vendor=user,id=invoice_id).update(invoice_status=False,invoice_number="unpaid")
                        CustomerCredit.objects.create(vendor=user,customer_name=GUESTIDs.customer.guestname,amount=dueamount,
                                                      due_date=duedate,invoice=GUESTIDs,phone=GUESTIDs.customer.guestphome)
                        



                    guestdatas = Gueststay.objects.get(vendor=user,id=GUESTID)
                    current_date = datetime.now()
                    # Get the current date
                    invccurrentdate = datetime.now().date()

                    # Fetch the maximum invoice number for today for the given user
                    max_invoice_today = Invoice.objects.filter(
                        vendor=user,
                        invoice_date=invccurrentdate,
                        foliostatus=True
                    ).aggregate(max_invoice_number=Max('invoice_number'))['max_invoice_number']

                    # Determine the next invoice number
                    if max_invoice_today is not None:
                        # Extract the numeric part of the latest invoice number and increment it
                        try:
                            current_number = int(max_invoice_today.split('-')[-1])
                            next_invoice_number = current_number + 1
                        except (ValueError, IndexError):
                            # Handle the case where the invoice number format is unexpected
                            next_invoice_number = 1
                    else:
                        next_invoice_number = 1
                    # Generate the invoice number
                    invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'
                    
                    # Check if the generated invoice number already exists
                    while Invoice.objects.filter(vendor=user,invoice_number=invoice_number).exists():
                        next_invoice_number += 1
                        invoice_number = f'INV-{invccurrentdate}-{next_invoice_number}'

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

                            
                    Invoice.objects.filter(vendor=user,id=invoice_id).update(foliostatus=True,invoice_number=invoice_number,modeofpayment=paymentstatus)
                        # SaveAdvanceBookGuestData.objects.filter(id=saveguestid).delete()
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
                return redirect('invoicepage', id=GUESTID)
            else:
                return redirect('invoicepage', id=GUESTID)
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

            
            # Update checkout status for guests
            Gueststay.objects.filter(Q(vendor=user, checkoutdate__date__lte=desired_date) | Q(vendor=user, checkoutdate__date=desired_date)).update(checkoutstatus=True)

            # Query sets
            dats = Gueststay.objects.filter(vendor=user, checkoutdate__date__lte=desired_date, checkoutstatus=True, checkoutdone=False)
            datsin = Gueststay.objects.filter(vendor=user, checkindate__date=desired_date)
            tax = Taxes.objects.filter(vendor=user).all()
            arriwaldata = RoomBookAdvance.objects.filter(
                  # Include the vendor condition
                Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
                Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
            ).exclude(vendor=user,saveguestdata__action='cancel')
            
            bookedmisseddata = RoomBookAdvance.objects.filter(vendor=user, checkoutdate__lte=desired_date, checkinstatus=False).exclude(vendor=user,saveguestdata__action='cancel')
            saveguestallroomcheckout = RoomBookAdvance.objects.filter(vendor=user, checkoutdate=desired_date, checkinstatus=True).exclude(vendor=user,saveguestdata__action='cancel').exclude(checkOutstatus=True)
            
            # find to clour red
            reddata = Gueststay.objects.filter(vendor=user, checkoutdate__date__gt=desired_date, checkoutstatus=False, checkoutdone=False)
            for i in reddata:
                print(i.roomno,"room no")
                if Rooms.objects.filter(
                        vendor=user,
                        room_name=i.roomno,
                        checkin__in=[1, 4, 5]
                    ).exists():
                        pass
                else:
                    Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=1)
                    

            # Update rooms based on filtered data
            for i in saveguestallroomcheckout:
                roomnumber = i.roomno.room_name
                invcdata = InvoiceItem.objects.filter(vendor=user,description=roomnumber).last()
                if invcdata:
                    if Invoice.objects.filter(vendor=user,id=invcdata.invoice.id,foliostatus=False,customer__checkoutdate=desired_date):
                        Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=2)
                    else:
                        # Rooms.objects.filter(vendor=user, room_name=i.roomno.room_name).exclude(checkin=6).update(checkin=0)
                        pass
                else:
                    pass

            for i in dats:
                Rooms.objects.filter(vendor=user, room_name=i.roomno).exclude(checkin=6).update(checkin=2)
                

            for i in bookedmisseddata:
                if i.roomno.checkin == 5 or i.roomno.checkin == 4:
                    Rooms.objects.filter(vendor=user, id=i.roomno.id).update(checkin=0)
            
            # filter cancel booking jo cancel hai vo yaha filter ho rahe hai
            arriwalcanceldata = RoomBookAdvance.objects.filter(
                 
                Q(vendor=user,bookingdate=desired_date,checkinstatus=False) | 
                Q(vendor=user,bookingdate__lte=desired_date, checkoutdate__gt=desired_date,checkinstatus=False)
            ).exclude(vendor=user,saveguestdata__action='book')
            
            
            # or jo book hai vo yaha


            for data in  arriwalcanceldata:
                    if data.roomno.checkin not in [1, 2, 6]:
                        data = Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=0)
                        
            for data in arriwaldata:
                if data.roomno.checkin not in [1, 2, 5]:
                    Rooms.objects.filter(vendor=user, id=data.roomno.id).update(checkin=4)
            

            # Additional queries
            checkintimedata = HotelProfile.objects.filter(vendor=user)
            stayover = Rooms.objects.filter(vendor=user, checkin=1).count()
            availablerooms = Rooms.objects.filter(vendor=user, checkin=0).count()
            totalrooms = Rooms.objects.filter(vendor=user).count()
            checkoutcount = Gueststay.objects.filter(vendor=user, checkoutdate__date=desired_date, checkoutstatus=True, checkoutdone=False).count()
            checkincountdays = len(datsin)

            # Create rooms dictionary
            roomsdict = {}
            for cat in category:
                roomsdict[cat.category_name] = [[room.room_name, room.checkin,room.is_clean] for room in rooms.filter(room_type=cat)]

            cleanrooms = Rooms.objects.filter(vendor=user, is_clean=True).count()        
            uncleanrooms = Rooms.objects.filter(vendor=user, is_clean=False).count()     

            
            
            return render(request, 'homepage.html', {
                'active_page': 'homepage',
                'category': category,
                'rooms': rooms,
                'roomsdict': roomsdict,
                'tax': tax,
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