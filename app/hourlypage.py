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
                checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                # Apply date range filter
                filters &= Q(bookingdate__gte=checkindate) & Q(checkoutdate__lte=checkoutdate)
            
            elif checkindate_str:
                # Convert checkindate string to date object
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Filter guests with checkindate
                filters &= Q(bookingdate__gte=checkindate) & Q(bookingdate__lt=checkindate + timedelta(days=1))
            
            elif checkoutdate_str:
                # Convert checkoutdate string to date object
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
                # Filter guests with checkoutdate
                filters &= Q(checkoutdate__gte=checkoutdate) & Q(checkoutdate__lt=checkoutdate + timedelta(days=1))

            advancersoomdata = guests.filter(filters)

            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            return render(request, 'advancebookinghistory.html', {'monthbookdata': advancersoomdata, 
                                         'first_day_of_month':checkindate,'last_day_of_month':checkoutdatss ,'active_page': 'advancebookhistory'})
        else:
            return redirect('loginpage')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     

def searchguestdatabyfolio(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            guests = Invoice.objects.filter(vendor=user, foliostatus=False).order_by('invoice_date')

            guestname = request.POST.get('guestname', '').strip()
            guestphone = request.POST.get('guestphone', '').strip()
            checkindate_str = request.POST.get('checkindate', '').strip()
            checkoutdate_str = request.POST.get('checkoutdate', '').strip()
            roomno = request.POST.get('roomno', '').strip()
            filters = Q()

            # Apply filters based on conditions within Gueststay (customer) model
            if guestname:
                filters &= Q(customer__guestname__icontains=guestname)
            if guestphone:
                filters &= Q(customer__guestphome__icontains=guestphone)
            if roomno:
                filters &= Q(customer__roomno__icontains=roomno)  # Search by room number in Gueststay

            # Use correct date fields in Gueststay model
            if checkindate_str and checkoutdate_str:
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                filters &= Q(customer__checkindate__gte=checkindate) & Q(customer__checkoutdate__lte=checkoutdate)
            elif checkindate_str:
                checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                filters &= Q(customer__checkindate__date=checkindate.date())
            elif checkoutdate_str:
                checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                filters &= Q(customer__checkoutdate__date=checkoutdate.date())

            # Filter guests based on combined filters
            invoice_data = guests.filter(filters)

            # If no results found, display an error message
            if not invoice_data.exists():
                pass

            return render(request, 'foliopage.html', {'invoice_data': invoice_data, 'active_page': 'foliobillingpage'})
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
            loyltyguestsdatas = loylty_Guests_Data.objects.filter(vendor=user, loylty_point__gt=0)
            
            return render(request,'loyltypage.html',{'active_page':'loylty','loyltyguestsdatas':loyltyguestsdatas})
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
            
            
            return render(request,'eventssales.html',{'active_page':'eventsalse','total_subtotal_amount':total_subtotal_amount,
                                                'event_details':event_details,'total_tax_amount':total_tax_amount,  'total_grand_amount':total_grand_amount})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
     
def addaminities(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            servicename = request.POST.get('servicename', '')
            if beaminities.objects.filter(vendor=user,description=servicename).exists():
                messages.error(request, "Name already exists!")
            else:
                beaminities.objects.create(vendor=user,description=servicename)
                messages.success(request, "Name added!")

            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    

def deleteaminity(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            if beaminities.objects.filter(vendor=user,id=id).exists():
                beaminities.objects.filter(vendor=user,id=id).delete()
                messages.success(request, "Name deleted!")

            else:
                messages.error(request, "Name Not exists!")

            return redirect('websettings')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    


def addoffers(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            discription = request.POST.get('discription', '')
            discountpersantage = request.POST.get('discountpersantage', '')
            offerminprice = request.POST.get('offerminprice', '')
            if OfferBE.objects.filter(vendor=user).exists():
                OfferBE.objects.filter(vendor=user).delete()

                OfferBE.objects.create(vendor=user,description=discription,min_price=float(offerminprice),
                                       discount_percentage=discountpersantage)

                messages.success(request, "Offer Added!")
            else:
                OfferBE.objects.create(vendor=user,description=discription,min_price=float(offerminprice),
                                       discount_percentage=discountpersantage)
                messages.success(request, "Offer Added!")

            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    


def addcp(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            cp = request.POST.get('cp', '')
            if cancellationpolicy.objects.filter(vendor=user).exists():
                cancellationpolicy.objects.filter(vendor=user).delete()

                cancellationpolicy.objects.create(vendor=user,cancellention_policy=cp)

                messages.success(request, "cancellention_policy Added!")
            else:
                cancellationpolicy.objects.create(vendor=user,cancellention_policy=cp)
                messages.success(request, "cancellention_policy  Added!")

            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    


def addcatimg(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            roomcat = request.POST.get('roomcat', '')
            galaryimg = request.FILES.get('galaryimg')
            roomcategory = RoomsCategory.objects.get(id=roomcat)
            RoomImage.objects.create(vendor=user,category=roomcategory,image=galaryimg)
            messages.success(request, "Image  Added!")

            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    


def deleteimg(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            if RoomImage.objects.filter(vendor=user,id=id).exists():
                RoomImage.objects.filter(vendor=user,id=id).delete()
                messages.success(request, "image deleted!")

            else:
                messages.error(request, "image not exists!")

            return redirect('websettings')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    


def deletehotelimg(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user
            if HoelImage.objects.filter(vendor=user,id=id).exists():
                HoelImage.objects.filter(vendor=user,id=id).delete()
                messages.success(request, "image deleted!")

            else:
                messages.error(request, "image not exists!")

            return redirect('websettings')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)   

def addhotelimg(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            addhotelimg = request.FILES.get('addhotelimg')
            HoelImage.objects.create(vendor=user,image=addhotelimg)
            messages.success(request, "Image  Added!")

            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)   
    


def addcontactbe(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            emails = request.POST.get('emails')
            contact = request.POST.get('contact')
            url = request.POST.get('url')
            if  becallemail.objects.filter(vendor=user).exists():
                becallemail.objects.filter(vendor=user).update(phome=contact,guestemail=emails,linkmap=url)
                messages.success(request, "Contact details updated!")
            else:
                becallemail.objects.create(vendor=user,phome=contact,guestemail=emails,linkmap=url)
                messages.success(request, "Contact details updated!")
            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  
    
def updatebookeg(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            checkinpt = request.FILES.get('checkinpt')
            if bestatus.objects.filter(vendor=user).exists():
                pass
            else:
                bestatus.objects.create(vendor=user,is_active=True)

            ckdata = bestatus.objects.get(vendor=user)

            if ckdata.is_active is True:
                bestatus.objects.filter(vendor=user).update(is_active=False)
               
            else:
                bestatus.objects.filter(vendor=user).update(is_active=True)


            return redirect('websettings')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  