from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def hourlyhomepage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            roomdata = Rooms.objects.filter(vendor=user,checkin=0)
            hourlydata = HourlyRoomsdata.objects.filter(vendor=user,checkinstatus=False)
            checkinhourlydata = HourlyRoomsdata.objects.filter(vendor=user,checkinstatus=True)
            hourlyallrooms = HourlyRoomsdata.objects.filter(vendor=user)
            return render(request,'hourlyhomepage.html',{'active_page': 'hourlyhomepage','roomdata':roomdata,'hourlydata':hourlydata,
                                                        'checkinhourlydata':checkinhourlydata,'hourlyallrooms':hourlyallrooms})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    


def addroomtohourlyrooms(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            roomno = request.POST.get('roomno')

            if HourlyRoomsdata.objects.filter(vendor=user,rooms=roomno).exists():
                pass
            else:
                current_time = timezone.now() 
                HourlyRoomsdata.objects.create(vendor=user,rooms_id=roomno,checkinstatus=False,checkoutstatus=False,
                                            checkIntime=current_time,checkottime=current_time,time="3hours")
                Rooms.objects.filter(vendor=user,id=roomno).update(checkin=6)
            return redirect('hourlyhomepage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def removeroomfromhourly(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            roomno = request.POST.get('roomno')
            if HourlyRoomsdata.objects.filter(vendor=user,id=roomno).exists():
                roomid = HourlyRoomsdata.objects.get(vendor=user,id=roomno)
                Rooms.objects.filter(vendor=user,id=roomid.rooms.id).update(checkin=0)
                HourlyRoomsdata.objects.filter(vendor=user,id=roomno).delete()
            
            return redirect('hourlyhomepage') 
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def hourlyroomclickform(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            if Rooms.objects.filter(vendor=user,id=id).exists():
                roomdata = Rooms.objects.get(vendor=user,id=id)
                loyltydata = loylty_data.objects.filter(vendor=user,Is_active=True)
                return render(request,'hourlycheckinform.html',{'active_page': 'hourlyhomepage','loyltydata':loyltydata,'roomdata':roomdata,})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
          
def hourlycheckinroom(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            guestname = request.POST.get('guestname')
            guestphome = request.POST.get('guestphone')
            guestemail = request.POST.get('guestemail')
            guestcity = request.POST.get('guestcity')
            guestcountry = request.POST.get('guestcountry')
            guestidimg = request.FILES.get('guestid')
            checkindate = request.POST.get('guestcheckindate')
            noofguest = request.POST.get('noofguest')
            adults = request.POST.get('guestadults')
            children = request.POST.get('guestchildren')
            purposeofvisit = request.POST.get('Purpose')
            roomno = request.POST.get('roomno')
            hourlystatus = request.POST.get('hourlystatus')
            subtotal = int(request.POST.get('Vendortotalamount'))
            total = request.POST.get('total')
            roomid = request.POST.get('roomid')
            tax = request.POST.get('tax')
            paidstatus = request.POST.get('paidstatus')
            paymentstatus = request.POST.get('paymentstatus')
            discount = float(request.POST.get('discount'))
            checkmoredatastatus = request.POST.get('checkmoredatastatus')   
            state = request.POST['STATE']
            current_date = datetime.now()
            userstatedata = HotelProfile.objects.get(vendor=user)
            userstate = userstatedata.zipcode
            if userstate == state:
                taxtypes = "GST"
            else:
                taxtypes = "IGST"
            guestdata = Gueststay.objects.create(vendor=user,guestname=guestname,guestphome=guestphome,guestemail=guestemail,guestcity=guestcity,guestcountry=guestcountry,guestidimg=guestidimg,
                                    checkindate=current_date,checkoutdate=current_date ,noofguest=noofguest,adults=adults,children=children
                                    ,purposeofvisit=purposeofvisit,roomno=roomno,tax=tax,discount=discount,subtotal=subtotal,total=total,noofrooms=1)
            gsid=guestdata.id
            if checkmoredatastatus == 'on':
                moreguestname = request.POST.get('moreguestname')
                moreguestphone = request.POST.get('moreguestphone')
                moreguestaddress = request.POST.get('moreguestaddress')
                MoreGuestData.objects.create(vendor=user,mainguest=guestdata,another_guest_name=moreguestname,
                                            another_guest_phone=moreguestphone,another_guest_address=moreguestaddress)
                
            if HourlyRoomsdata.objects.filter(vendor=user,rooms_id=roomid).exists():
                current_time = timezone.localtime(timezone.now())

                # Check the hourly status and add hours accordingly
                if hourlystatus == "3hours":
                    new_datetime = (current_time + timedelta(hours=3))
                elif hourlystatus == "6hours":
                    new_datetime = (current_time + timedelta(hours=6))
                elif hourlystatus == "9hours":
                    new_datetime = (current_time + timedelta(hours=9))
                else:
                    new_datetime = (current_time + timedelta(hours=12))
                HourlyRoomsdata.objects.filter(vendor=user,rooms_id=roomid).update(checkinstatus=True,
                        checkIntime=current_time,checkottime=new_datetime,time=hourlystatus)
            roomdata = Rooms.objects.get(vendor=user,id=roomid)
            roomspriceplusgst = roomdata.price 
            hscsac = roomdata.room_type.Hsn_sac
            taxrateroom = roomdata.tax.taxrate
            updatesubtotal = subtotal - discount
            taxamt = updatesubtotal*taxrateroom //100
            grandtotalamount = updatesubtotal + taxamt
            dividetaxamt = taxamt / 2
            taxrates = taxrateroom/2
            current_date = datetime.now().date()
            cashamount = 0.00
            onlineamount = 0.00
            invoice_number = ''
            if paidstatus == "Paid":
                statuspaid = True
                if paymentstatus == "cash":
                    cashamount = grandtotalamount
                elif paymentstatus == "online":
                    onlineamount = grandtotalamount
                else:
                    cashamount = float(request.POST.get('cashamount'))
                    onlineamount = float(request.POST.get('onlineamount'))
            else:
                statuspaid = False
            Invoiceid = Invoice.objects.create(vendor=user,customer=guestdata,customer_gst_number="",
                                                invoice_number=invoice_number,invoice_date=checkindate,total_item_amount=roomspriceplusgst,discount_amount=discount,
                                                subtotal_amount=updatesubtotal,gst_amount=dividetaxamt,sgst_amount=dividetaxamt,
                                            cash_amount=cashamount,online_amount=onlineamount,  grand_total_amount=grandtotalamount,modeofpayment=paymentstatus,room_no=roomno,taxtype=taxtypes)

            invoiceitem = InvoiceItem.objects.create(vendor=user,invoice=Invoiceid,description=roomno,quantity_likedays=1,
                                    paidstatus=statuspaid,price=subtotal,cgst_rate=taxrates,sgst_rate=taxrates,hsncode=hscsac,total_amount=grandtotalamount)  
            
            return redirect('hourlyhomepage')
        else:
            return redirect('loginpage') 
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     

# guest history search
def searchguestdata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            guests = Gueststay.objects.filter(vendor=user).order_by('checkindate')

            guestname = request.POST.get('guestname', '').strip()
            guestphone = request.POST.get('guestphone', '').strip()
            checkindate_str = request.POST.get('checkindate', '').strip()
            checkoutdate_str = request.POST.get('checkoutdate', '').strip()

            filters = Q()

            if guestname:
                filters &= Q(guestname__icontains=guestname)
            if guestphone:
                filters &= Q(guestphome__icontains=guestphone)
            
            if checkindate_str and checkoutdate_str:
                # Convert string dates to datetime objects
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Apply date range filter
                filters &= Q(checkindate__date__gte=checkindate) & Q(checkoutdate__date__lte=checkoutdate)
            
            elif checkindate_str:
                # Convert checkindate string to datetime object
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                
                # Filter guests with checkindate
                filters &= Q(checkindate__date=checkindate.date())
            
            elif checkoutdate_str:
                # Convert checkoutdate string to datetime object
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Filter guests with checkoutdate
                filters &= Q(checkoutdate__date=checkoutdate.date())

            guestshistory = guests.filter(filters)

            if not guestshistory.exists():
                messages.error(request, "No matching guests found.")

            return render(request, 'guesthistory.html', {'guesthistory': guestshistory, 'active_page': 'guesthistory'})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     


# advance history search
def searchguestdataadvance(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            guests = SaveAdvanceBookGuestData.objects.filter(vendor=user).order_by('bookingdate')

            guestname = request.POST.get('guestname', '').strip()
            guestphone = request.POST.get('guestphone', '').strip()
            checkindate_str = request.POST.get('checkindate', '').strip()
            checkoutdate_str = request.POST.get('checkoutdate', '').strip()

            filters = Q()

            if guestname:
                filters &= Q(bookingguest__icontains=guestname)
            if guestphone:
                filters &= Q(bookingguestphone__icontains=guestphone)
            
            if checkindate_str and checkoutdate_str:
                # Convert string dates to date objects
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d') + timedelta(days=1)  # Include the entire checkout date
                
                # Apply date range filter
                filters &= Q(bookingdate__gte=checkindate) & Q(checkoutdate__lte=checkoutdate)
            
            elif checkindate_str:
                # Convert checkindate string to date object
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                
                # Filter guests with checkindate
                filters &= Q(bookingdate__gte=checkindate) & Q(bookingdate__lt=checkindate + timedelta(days=1))
            
            elif checkoutdate_str:
                # Convert checkoutdate string to date object
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Filter guests with checkoutdate
                filters &= Q(checkoutdate__gte=checkoutdate) & Q(checkoutdate__lt=checkoutdate + timedelta(days=1))

            advancersoomdata = guests.filter(filters)

            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            return render(request, 'advancebookinghistory.html', {'advancersoomdata': advancersoomdata, 'active_page': 'advancebookhistory'})
        else:
            return redirect('loginpage')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
# events search
def searchdateevents(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            events = EventBookGuest.objects.filter(vendor=user).order_by('start_date')

            guestname = request.POST.get('guestname', '').strip()
            guestphone = request.POST.get('guestphone', '').strip()
            checkindate_str = request.POST.get('checkindate', '').strip()
            checkoutdate_str = request.POST.get('checkoutdate', '').strip()

            filters = Q()

            if guestname:
                filters &= Q(customername__icontains=guestname)
            if guestphone:
                filters &= Q(customer_contact__icontains=guestphone)
            
            if checkindate_str and checkoutdate_str:
                # Convert string dates to datetime objects
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d') + timedelta(days=1)  # Include the entire checkout date
                
                # Apply date range filter
                filters &= Q(start_date__gte=checkindate) & Q(end_date__lt=checkoutdate)
            
            elif checkindate_str:
                # Convert checkindate string to datetime object
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                
                # Filter events with start_date equal to checkindate
                next_day = checkindate + timedelta(days=1)
                filters &= Q(start_date__gte=checkindate) & Q(start_date__lt=next_day)
            
            elif checkoutdate_str:
                # Convert checkoutdate string to datetime object
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Filter events with end_date equal to checkoutdate
                next_day = checkoutdate + timedelta(days=1)
                filters &= Q(end_date__gte=checkoutdate) & Q(end_date__lt=next_day)

            eventdata = events.filter(filters)

            if not eventdata.exists():
                messages.error(request, "No matching guests found.")
            
            return render(request, 'upcomingevents.html', {'active_page': 'upcomingevent', 'eventdata': eventdata})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def loylty(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            return render(request,'loyltypage.html',{'active_page':'loylty'})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def offers(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            offers = offerwebsitevendor.objects.filter(vendor=user)
            return render(request,'offerspage.html',{'active_page':'offers','offers':offers})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
from django.db.models import Sum
from django.db.models import Count
def eventsalse(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            EventBookGuest.objects.filter(vendor=user)
            total_grand_amount = EventBookGuest.objects.filter(vendor=user,status=True).aggregate(total=Sum('Grand_total_amount'))['total']
            total_tax_amount = EventBookGuest.objects.filter(vendor=user,status=True).aggregate(total=Sum('taxamount'))['total']
            total_subtotal_amount = EventBookGuest.objects.filter(vendor=user,status=True).aggregate(total=Sum('subtotal'))['total']
            top_events = EventBookGuest.objects.filter(vendor=user).values('event').annotate(
            event_count=Count('event')
                ).order_by('-event_count')[:4]

            event_details = []
            for event_data in top_events:
                    event_id = event_data['event']
                    event_count = event_data['event_count']
                    event = Events.objects.get(id=event_id)
                    event_details.append((event, event_count))
            
            
            return render(request,'eventssales.html',{'active_page':'eventsalse','offers':offers,'total_subtotal_amount':total_subtotal_amount,
                                                'event_details':event_details,'total_tax_amount':total_tax_amount,  'total_grand_amount':total_grand_amount})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def billzifymall(request):
    try:
        if request.user.is_authenticated:
            data = MarketIteams.objects.all()
            user=request.user
            return render(request,'billzifymall.html',{'active_page':'billzifymall','data':data})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     