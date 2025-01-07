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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
# def searchguestdataadvance(request):
#     try:
#         if request.user.is_authenticated and request.method == "POST":
#             user = request.user
#             subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
#             if subuser:
#                 user = subuser.vendor  
#             guests = SaveAdvanceBookGuestData.objects.filter(vendor=user).order_by('bookingdate')

#             guestname = request.POST.get('guestname', '').strip()
#             guestphone = request.POST.get('guestphone', '').strip()
#             checkindate_str = request.POST.get('checkindate', '').strip()
#             checkoutdate_str = request.POST.get('checkoutdate', '').strip()

            
#             filters = Q()

#             if guestname:
#                 filters &= Q(bookingguest__icontains=guestname)
#             if guestphone:
#                 filters &= Q(bookingguestphone__icontains=guestphone)
            
#             if checkindate_str and checkoutdate_str:
#                 # Convert string dates to date objects
#                 checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
#                 checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d') + timedelta(days=1)  # Include the entire checkout date
#                 checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
#                 # Apply date range filter
#                 filters &= Q(bookingdate__gte=checkindate) & Q(checkoutdate__lte=checkoutdate)
            
#             elif checkindate_str:
#                 # Convert checkindate string to date object
#                 checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
#                 checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
#                 # Filter guests with checkindate
#                 filters &= Q(bookingdate__gte=checkindate) & Q(bookingdate__lt=checkindate + timedelta(days=1))
            
#             elif checkoutdate_str:
#                 # Convert checkoutdate string to date object
#                 checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
#                 checkoutdatss =  datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                
#                 # Filter guests with checkoutdate
#                 filters &= Q(checkoutdate__gte=checkoutdate) & Q(checkoutdate__lt=checkoutdate + timedelta(days=1))

#             advancersoomdata = guests.filter(filters)

#             if not advancersoomdata.exists():
#                 messages.error(request, "No matching guests found.")

#             return render(request, 'advancebookinghistory.html', {'monthbookdata': advancersoomdata, 
#                                          'first_day_of_month':checkindate,'last_day_of_month':checkoutdatss ,'active_page': 'advancebookhistory'})
#         else:
#             return redirect('loginpage')
        
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
def searchguestdataadvance(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guests = SaveAdvanceBookGuestData.objects.filter(vendor=user).order_by('bookingdate')

            # Get input values
            guestname = request.POST.get('guestname', '').strip()
            guestphone = request.POST.get('guestphone', '').strip()
            checkindate_str = request.POST.get('checkindate', '').strip()
            checkoutdate_str = request.POST.get('checkoutdate', '').strip()

            bookid = request.POST.get('bookid', '').strip()

            # Initialize filters
            filters = Q()

            # Add filters for guest name and phone
            if guestname:
                filters &= Q(bookingguest__icontains=guestname)
            if guestphone:
                filters &= Q(bookingguestphone__icontains=guestphone)

            if bookid:
                filters &= Q(booking_id__icontains=bookid)

            # Handle date range filters
            checkindate = None
            checkoutdate = None
            if checkindate_str:
                try:
                    checkindate = datetime.strptime(checkindate_str, '%Y-%m-%d')
                except ValueError:
                    messages.error(request, "Invalid check-in date format.")
                    return redirect('advancebookhistory')  # Redirect to a safe page

            if checkoutdate_str:
                try:
                    checkoutdate = datetime.strptime(checkoutdate_str, '%Y-%m-%d')
                except ValueError:
                    messages.error(request, "Invalid check-out date format.")
                    return redirect('advancebookhistory')

            # Apply date filters
            if checkindate and checkoutdate:
                # If both dates are present
                filters &= Q(bookingdate__gte=checkindate) & Q(checkoutdate__lte=checkoutdate + timedelta(days=1))
            elif checkindate:
                # If only check-in date is provided
                filters &= Q(bookingdate__gte=checkindate) & Q(bookingdate__lt=checkindate + timedelta(days=1))
            elif checkoutdate:
                # If only check-out date is provided
                filters &= Q(checkoutdate__gte=checkoutdate) & Q(checkoutdate__lt=checkoutdate + timedelta(days=1))

            # Apply filters and fetch data
            advancersoomdata = guests.filter(filters)

            # If no results found
            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            # Return results
            return render(request, 'advancebookinghistory.html', {
                'monthbookdata': advancersoomdata,
                'first_day_of_month': checkindate,
                'last_day_of_month': checkoutdate,
                'active_page': 'advancebookhistory',
            })
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)





     

def searchguestdatabyfolio(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
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
    


def rollspermission(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if Subuser.objects.filter(user=user).exists():
                return redirect('loginpage')
            else:
                subuser = Subuser.objects.filter(vendor=user).all()
                return render(request,'rolsper.html',{'subuser':subuser})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  
    


def create_subuser(request):
    try:
        if request.user.is_authenticated:
            # Get the form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')

            # Ensure the logged-in user is the vendor
            vendor = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=request.user).first()

            if subuser:
                vendor = subuser.vendor  # Get the vendor for the subuser

            # Validate inputs: Check for existing username and email
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
                return redirect('rollspermission')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists!')
                return redirect('rollspermission')

            # Create the User (password will be hashed automatically)
            user = User.objects.create_user(username=username, email=email, password=password)

            

            # You can also send the fallback password to the user via email or display it
           

            # Create the Subuser linked to the vendor
            Subuser.objects.create(vendor=vendor, user=user, permissions={})

            # Success message
            messages.success(request, 'Subuser Created Successfully! PLease Set the password')

            return redirect('rollspermission')  # Redirect to the appropriate page
        else:
            return redirect('loginpage')  # If the user is not authenticated, redirect to login page
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return render(request, '404.html', {'error_message': str(e)}, status=500)  # Show the error message


def get_permissions(request, subuser_id):
    try:
        subuser = Subuser.objects.get(id=subuser_id)
        return JsonResponse({"permissions": subuser.permissions})
    except Subuser.DoesNotExist:
        return JsonResponse({"permissions": {}})
    
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.sessions.models import Session

@login_required
def createsubuserpermission(request):
    if request.method == "POST":
        # Get the subuser ID from the form
        subuser_id = request.POST.get('subuserid')
        selected_permissions = request.POST.getlist('selected_categories')

        # Ensure a subuser is selected
        if not subuser_id:
            messages.error(request,"SubUser Not Found ")
            return redirect('rollspermission')

        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
                user = subuser.vendor  
        # Get the subuser instance
        subuser = get_object_or_404(Subuser, id=subuser_id, vendor=user)

        # Update permissions in the database
        subuser.permissions = {perm: True for perm in selected_permissions}
        subuser.save()

        # Get the user associated with this subuser
        subuser_user = subuser.user  # The user associated with this subuser
        
        # Find the session for the specific user using the user ID
        sessions = Session.objects.all()  # Fetch all sessions
        
        for session in sessions:
            session_data = session.get_decoded()  # Decode the session data
            
            # Check if the session belongs to the user we want to log out by comparing the user ID
            if session_data.get('_auth_user_id') == str(subuser_user.id):
                session_key = session.session_key  # Get the session key
                session.delete()  # Delete the session to log out this specific user
                break  # Stop after finding the correct session
        else:
                    messages.success(request,"Permission Accepted!")
                    return redirect('rollspermission')  # Replace with your success URL
        messages.success(request,"Permission Accepted!")
        return redirect('rollspermission')
        # Redirect or render success message


    # For GET request, render the form
    messages.error(request,"Somthing Went Wrong")
    return redirect('rollspermission')

