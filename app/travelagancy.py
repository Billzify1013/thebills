from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from django.contrib import messages
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
import threading
from .newcode import *
# Create your views here.
from .dynamicrates import *
from datetime import date
from django.utils import timezone
from django.conf import settings
import urllib.parse
from django.urls import reverse
from collections import defaultdict

def travelagancy(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            agencydata = TravelAgency.objects.filter(vendor=user)
            return render(request,'travelagancy.html',{'active_page': 'travelagancy','agencydata':agencydata})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def createtravelagancy(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            agencyname = request.POST.get('agencyname')
            contactname = request.POST.get('contactname')
            Phone = request.POST.get('Phone')
            email = request.POST.get('email')
            Commission = request.POST.get('Commission')

            if TravelAgency.objects.filter(vendor=user,name=agencyname).exists():
                
                messages.error(request, 'Name already exists')
            else:
                TravelAgency.objects.create(
                        vendor=user,
                        name=agencyname,
                        contact_person=contactname,
                        phone_number=Phone,
                        email=email,
                        commission_rate=Commission

                  )
                if onlinechannls.objects.filter(vendor=user,channalname=agencyname).exists():
                      pass
                else:
                    onlinechannls.objects.create(vendor=user,channalname=agencyname)
                messages.success(request, 'Travel Partner added successfully')

            return redirect('travelagancy')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def deletetravelagency(request,id):
    try:
        if request.user.is_authenticated:
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                        user = subuser.vendor  
                
                if TravelAgency.objects.filter(vendor=user,id=id).exists():
                        TravelAgency.objects.filter(vendor=user,id=id).delete()
                        messages.success(request, 'Travel Partner delete successfully')

                else:
                    messages.error(request, 'Travel Partner Not Found ') 


                return redirect('travelagancy')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def updatetravelagancy(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                        user = subuser.vendor  
                ids = request.POST.get('ids')
                contactname = request.POST.get('contactname')
                Phone = request.POST.get('Phone')
                email = request.POST.get('email')
                Commission = request.POST.get('Commission')

                if not TravelAgency.objects.filter(vendor=user,id=ids).exists():
                    
                    messages.error(request, 'Not Found')
                else:
                    TravelAgency.objects.filter(
                            vendor=user,
                            id=ids).update(
                            contact_person=contactname,
                            phone_number=Phone,
                            email=email,
                            commission_rate=Commission

                    )
                    messages.success(request, 'Travel Partner Update  successfully')

                return redirect('travelagancy')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def opentravelagencydata(request, id):
    try:
        # Get agency data based on the provided ID
        agencydata = TravelAgency.objects.get(id=id)
        user = agencydata.vendor
        
        # Get current date and time
        now = timezone.now()
        
        # Calculate the first and last day of the current month
        first_day_of_month = now.replace(day=1)  # First day of the current month
        # Last day of the current month: move to the first day of the next month, then subtract one day
        next_month = now.replace(day=28) + timezone.timedelta(days=4)  # This gives us the next month
        last_day_of_month = next_month.replace(day=1) - timezone.timedelta(days=1)  # Last day of the current month
        
        # Formatting the current month and year
        current_month = now.strftime("%B")  # e.g., "October"
        current_year = now.year  # e.g., 2024
        
        # Fetch the channel ID for the current vendor and agency
        channelid = onlinechannls.objects.filter(vendor=user, channalname=agencydata.name).last()
        
        # Fetch the booking data within the date range of the current month
        bookingdata = SaveAdvanceBookGuestData.objects.filter(
            vendor=user,
            channal=channelid,
            bookingdate__range=(first_day_of_month, last_day_of_month)
        ).prefetch_related('travelagencyhandling_set')
        
        # Render the data in the template
        return render(request, 'agencydata.html', {
            'agencydata': agencydata,
            'current_month': current_month,
            'current_year': current_year,
            'bookingdata': bookingdata,
            'first_day_of_month': first_day_of_month,
            'last_day_of_month': last_day_of_month
        })
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)















def bookrooms(request, user_name, mids):
    try:  
            user = User.objects.get(username=user_name)
            # user = request.user
            today = datetime.now().date()
            tommrow = today + timedelta(days=1)
            startdate = str(today)
            enddate = str(tommrow)

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
                ).exclude(vendor=user,saveguestdata__action='cancel')

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
                hoteldata = HotelProfile.objects.get(vendor=user)
                travelagency = TravelAgency.objects.filter(vendor=user,id=mids)
                inventorydata = RoomsInventory.objects.none()
                if VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                    inventorydata = RoomsInventory.objects.filter(vendor=user,date__range=[today,tommrow],
                                                             )

                return render(request, 'travelbookroom.html', {
                    'active_page': 'advanceroombookpage',
                    'availableroomdata': availableroomdata,
                    'emptymessage': emptymessage,
                    'startdate': startdate,
                    'enddate': enddate,
                    'channal': channal,
                    'bookedroomsdata': bookedroomsdata,
                    'guestroomsdata': guestroomsdata,
                    'meal_plan': meal_plan,
                    'hoteldata':hoteldata,
                    'travelagency':travelagency,
                    'mids':mids,
                    'user':user,
                    'inventorydata':inventorydata
                })
      
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



# bookingsearch

# booking date search function
def bookingdatetravel(request):
    try:
        if  request.method == "POST":
            travelid = request.POST.get('travelid')
            username = request.POST.get('user')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            user = User.objects.get(username=username)
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
                ).exclude(vendor=user,saveguestdata__action='cancel')

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
                travelagency = TravelAgency.objects.filter(vendor=user,id=travelid)
                hoteldata = HotelProfile.objects.get(vendor=user)
                return render(request, 'travelbookroom.html', {
                    'active_page': 'advanceroombookpage',
                    'availableroomdata': availableroomdata,
                    'emptymessage': emptymessage,
                    'startdate': startdate,
                    'enddate': enddate,
                    'channal': channal,
                    'bookedroomsdata': bookedroomsdata,
                    'guestroomsdata': guestroomsdata,
                    'meal_plan': meal_plan,
                    'mids':travelid,
                    'user':user,
                    'travelagency':travelagency,
                    'hoteldata':hoteldata
                })
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore

def addadvancebookingfromtrvel(request):
    try:
        if request.method=="POST":
            travelid = request.POST.get('travelid')
            username = request.POST.get('user')
            user = User.objects.get(username=username)
            bookingdate = request.POST.get('bookingdate')
            guestname = request.POST.get('guestname')
            totalstaydays = request.POST.get('totalstaydays')
            phone = request.POST.get('phone',0)
            channal = request.POST.get('channal')
            bookenddate = request.POST.get('bookenddate')
            totalamount = float(request.POST.get('totalamount'))
            advanceamount = request.POST.get('advanceamount')
            discountamount = float(request.POST.get('discountamount'))
            reaminingamount = request.POST.get('reaminingamount',0)
            mealplan = request.POST.get('mealplan')
            guestcount = request.POST.get('guestcount')
            guestcountss = int(request.POST.get('guestcountss'))
            paymentmode = request.POST.get('paymentmode')
            serialized_array = request.POST['news']
            traveldata = TravelAgency.objects.get(id=travelid)
            travelname = traveldata.name
            channal=onlinechannls.objects.filter(vendor=user,channalname=travelname).last()
            my_array = json.loads(serialized_array)
            noofrooms = len(my_array)
            bookenddate = str(bookenddate)
            # bookenddate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
            bookingdate = datetime.strptime(bookingdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(bookenddate, '%Y-%m-%d').date()
            checkoutdate -= timedelta(days=1)
            # bookingdate -= timedelta(days=1)
  
            
           
            current_date = datetime.now()
            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(vendor=user,bookingdate=bookingdate,noofrooms=noofrooms,bookingguest=guestname,
                bookingguestphone=phone,staydays=totalstaydays,advance_amount=advanceamount,reamaining_amount=reaminingamount,discount=discountamount,
                total_amount=totalamount,channal=channal,checkoutdate=bookenddate,email='',address_city='',state='',country='',totalguest=guestcountss,
                action='book',booking_id=None,cm_booking_id=None,segment=travelname,special_requests='',pah=True,amount_after_tax=totalamount,amount_before_tax=0.00,
                  tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=False,is_noshow=False,is_hold=False,  )
            paymenttypes = 'postpaid'
            if int(advanceamount) > 0:
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
            guestcountsstored = int(guestcountss) 
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
               
                    occupancy = (1 * 100 // roomcount)
                    
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
                                    total_availibility=roomcount-1,       # Set according to your logic
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
            curtdate = datetime.now().date()
            if traveldata.commission_rate > 0:
                agencydata = TravelAgency.objects.get(vendor=user,id=travelid)
                if agencydata.commission_rate >0:
                    commision = sellingprices*agencydata.commission_rate//100
                    Travelagencyhandling.objects.create(vendor=user,agency=agencydata,bookingdata=Saveadvancebookdata,
                                             date=curtdate,commsion=commision)
                else:
                     pass
            
            SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_before_tax=sellingprices,
                                                tax=float(totaltax),Payment_types=paymenttypes)
            messages.success(request,"Booking Done")
            user_name = user.username
            mids=travelid
            
            url = reverse('bookrooms', args=[user_name, mids])

           

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
                       
            return redirect(url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

from django.utils import timezone
from calendar import monthrange,month_name
def searchmonthbookingagent(request):
    try:
        if request.method=="POST":
            agentid = request.POST.get('agentid')
            # month_input = request.POST.get('monthname')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            agencydata = TravelAgency.objects.get(id=agentid)
            user = agencydata.vendor
            
            channelid= onlinechannls.objects.filter(vendor=user,channalname=agencydata.name).last()
            # bookingdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,channal=channelid,bookingdate__range=(first_day_of_month, last_day_of_month))
            bookingdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,channal=channelid,bookingdate__range=(startdate, enddate)).prefetch_related('travelagencyhandling_set')
            return render(request,'agencydata.html',{'agencydata':agencydata,
                                                    'current_month':startdate,
                                                    'current_year':startdate,
                                                    'bookingdata':bookingdata,
                                                    'first_day_of_month':startdate,
                                                    'last_day_of_month':enddate,
                                                    })
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def updatepptdesc(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            description = request.POST.get('description')
            if property_description.objects.filter(vendor=user).exists():
                property_description.objects.filter(vendor=user).update(
                     description =description
                 )
            else:
                property_description.objects.create(vendor=user,
                     description =description
                 )
                
            messages.success(request,'Description update Sucesfully! ')
            return redirect('websettings')
        else:
            return redirect('loginpage')           

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def addcatservice(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            roomcatids = request.POST.get('roomcatids')
            servicenamecat = request.POST.get('servicenamecat')
            if RoomsCategory.objects.filter(vendor=user,id=roomcatids).exists():
                categoryid = RoomsCategory.objects.get(vendor=user,id=roomcatids)
                if room_services.objects.filter(vendor=user,category=categoryid,service=servicenamecat).exists():
                    messages.error(request,'Already Exists! ')
                else:
                    room_services.objects.create(vendor=user,category=categoryid,service=servicenamecat)
                    
                    messages.success(request,'Service Created Sucesfully! ')
            else:
                messages.error(request,'Category Id Not Found! ')
            return redirect('websettings')
        else:
            return redirect('loginpage')           

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def deletecatservice(request,id):
    try:
        if request.user.is_authenticated :
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            if room_services.objects.filter(vendor=user,id=id).exists():
                room_services.objects.filter(vendor=user,id=id).delete()
                messages.success(request,'Service Deleted Sucesfully! ')
            else:
                messages.error(request,' Id Not Found! ')

            return redirect('websettings')  
        else:
            return redirect('loginpage')           

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def whatsaapchat(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            whatsapurl = request.POST.get('whatsapurl')
            if whatsaap_link.objects.filter(vendor=user).exists():
                whatsaap_link.objects.filter(vendor=user).update(
                     link =whatsapurl
                 )
            else:
                whatsaap_link.objects.create(vendor=user,
                     link =whatsapurl
                 )
            messages.success(request,'Updated! ')
            return redirect('websettings')
        else:
            return redirect('loginpage')           

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def deletewhatsapchat(request,id):
    try:
        if request.user.is_authenticated :
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            
            if whatsaap_link.objects.filter(vendor=user,id=id).exists():
                whatsaap_link.objects.filter(vendor=user,id=id).delete()
                messages.success(request,'Service Deleted Sucesfully! ')
            else:
                messages.error(request,' Id Not Found! ')

            return redirect('websettings')  
        else:
            return redirect('loginpage')           

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def ota_Commission(request):
    try:
        if not request.user.is_authenticated:
            return render(request, 'login.html')

        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor

        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        filter_type = request.GET.get('filter_type', 'checkin')

        today = datetime.today().date()
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today

        filter_field = {
            'checkin': 'bookingdate',
            'booking': 'checkin',
            'checkout': 'checkoutdate'
        }.get(filter_type, 'bookingdate')

        filter_range = {f"roombook__{filter_field}__range": (start_date, end_date)}

        commissions = tds_comm_model.objects.filter(
            roombook__vendor=user,
            roombook__channal__isnull=False,
            **filter_range
        ).exclude(roombook__action='cancel').select_related('roombook__channal')

        data = {}

        for comm in commissions:
            booking = comm.roombook
            channel = booking.channal.channalname

            if channel not in data:
                data[channel] = {'revenue': 0.0, 'commission': 0.0, 'rns': 0}

            data[channel]['revenue'] += booking.amount_before_tax or 0.0
            data[channel]['commission'] += comm.commission or 0.0
            data[channel]['rns'] += 1

        final_data = []
        total_rns = total_revenue = total_commission = 0.0

        for ch, values in data.items():
            revenue = values['revenue']
            commission = values['commission']
            rns = values['rns']
            commission_percent = round((commission / revenue) * 100, 2) if revenue > 0 else 0.0

            final_data.append({
                'channel': ch,
                'rns': rns,
                'revenue': round(revenue, 2),
                'commission': round(commission, 2),
                'commission_percent': commission_percent
            })

            total_rns += rns
            total_revenue += revenue
            total_commission += commission

        avg_comm_percent = round((total_commission / total_revenue) * 100, 2) if total_revenue > 0 else 0.0

        context = {
            'active_page': 'ota_Commission',
            'channel_data': final_data,
            'total_rns': total_rns,
            'total_revenue': round(total_revenue, 2),
            'total_commission': round(total_commission, 2),
            'avg_comm_percent': avg_comm_percent,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'filter_type': filter_type
        }

        return render(request, 'otacommisioon.html', context)
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


# def formo_view(request):
#     # Get the booking_id from the query parameter 'extra_param'
#     booking_id = request.GET.get('cd')
#     # If booking_id is not provided, return an error message
#     if not booking_id:
#         return HttpResponse("Error: Missing booking_id.")

#     # Fetch the booking data using the booking_id
#     advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
#     for i in advancebookdata:
#         vid = i.vendor.id

#     advancebookingmain = SaveAdvanceBookGuestData.objects.get(id=booking_id)
#     advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
#     profiledata = HotelProfile.objects.filter(vendor_id=vid)
#     hoteldatas = HotelProfile.objects.get(vendor_id=vid)
#     invcpayments = InvoicesPayment.objects.filter(advancebook=advancebookingmain)
#     terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
#     if hoteldatas.gstin == "UNREGISTERED":
#         gststatus = False
#     else:
#         gststatus = True
#     # gststatus = False
#     print(gststatus)
#     # Return the template with the booking data and query parameter
#     return render(request, 'booking_fromo_recipt.html', {
#         'advancebookdata': advancebookdata,
#         'advancebookingdatas': advancebookingdatas,
#         'profiledata': profiledata,
#         'terms_lines': terms_lines,
#         'hoteldatas':hoteldatas,
#         'booking_id': booking_id,  # Pass booking_id to the template if needed
#         'gststatus':gststatus,
#         'advancebookingmain':advancebookingmain,
#         'invcpayments':invcpayments,
#     })

    


def formo_view(request):
    booking_id = request.GET.get('cd')
    if not booking_id:
        return HttpResponse("Error: Missing booking_id.")

    advancebookdata = SaveAdvanceBookGuestData.objects.filter(id=booking_id)
    for i in advancebookdata:
        vid = i.vendor.id

    advancebookingmain = SaveAdvanceBookGuestData.objects.get(id=booking_id)
    advancebookingdatas = RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
    if advancebookingdatas:
        changealgo=False
    else:
        changealgo = True
        advancebookingdatas= Cm_RoomBookAdvance.objects.filter(saveguestdata_id=booking_id)
    profiledata = HotelProfile.objects.filter(vendor_id=vid)
    hoteldatas = HotelProfile.objects.get(vendor_id=vid)
    invcpayments = InvoicesPayment.objects.filter(advancebook=advancebookingmain)
    terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []

    gststatus = hoteldatas.gstin != "UNREGISTERED"
    print(gststatus)

    if changealgo:
        grouped_room_data = defaultdict(lambda: {'sell_rate': 0.0, 'count': 0})
        for item in advancebookingdatas:
            room_type = item.room_category.category_name
            grouped_room_data[room_type]['sell_rate'] = item.sell_rate  # Assuming same rate for same room type
            grouped_room_data[room_type]['count'] += 1

        grouped_room_data = grouped_room_data.items()

    else:
        # ✅ Group rooms by category_name
        grouped_room_data = defaultdict(lambda: {'sell_rate': 0.0, 'count': 0})
        for item in advancebookingdatas:
            room_type = item.roomno.room_type.category_name
            grouped_room_data[room_type]['sell_rate'] = item.sell_rate  # Assuming same rate for same room type
            grouped_room_data[room_type]['count'] += 1

        grouped_room_data = grouped_room_data.items()

    return render(request, 'booking_fromo_recipt.html', {
        'advancebookdata': advancebookdata,
        'advancebookingdatas': advancebookingdatas,
        'profiledata': profiledata,
        'terms_lines': terms_lines,
        'hoteldatas': hoteldatas,
        'booking_id': booking_id,
        'gststatus': gststatus,
        'advancebookingmain': advancebookingmain,
        'invcpayments': invcpayments,
        'grouped_room_data': grouped_room_data,  # ✅ Pass grouped data to template
    })

    

def sync_inventory(request):
    try:
        if request.user.is_authenticated :
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor
            rinvdata = RoomsInventory.objects.filter(vendor=user).order_by('-date').first() 

            if rinvdata:
                start_date = datetime.now().date()
                end_date = rinvdata.date
                start_date=str(start_date)
                end_date = str(end_date)
                # Start the long-running task in a separate thread
                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                thread.start()
                
                # Add a success message
                messages.success(request, "Inventory sync has been started successfully.") 
                bulklogs.objects.create(vendor=user,by=request.user,action="sync inventory",
                        description=f"Inventory Update From {start_date} to {end_date} ")
                return redirect('inventory_view') 
            else:
                rinvdata=None
            return redirect('inventory_view')
        return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def edittotalbookingamount(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            total_amount = request.POST.get('total_amount')
            bid = request.POST.get('id')
            print(total_amount)
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bid).exists():
                main_guest = SaveAdvanceBookGuestData.objects.get(vendor=user,id=bid)
                all_rooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=main_guest)
                rooms_count = all_rooms.count()
                total_amount = float(total_amount)
                if main_guest.amount_after_tax == total_amount:
                    messages.error(request,'Old and new amount is equal')
                from decimal import Decimal, ROUND_HALF_UP
                check_total_amount =total_amount
                check_old_totalamount = main_guest.amount_after_tax
                if main_guest.amount_after_tax != total_amount:
                    total_amount = Decimal(str(total_amount))
                    stay_days = Decimal(main_guest.staydays)
                    rooms = list(all_rooms)
                    room_count = len(rooms)

                    # ✅ Step 1: Sort rooms by sell_rate descending
                    rooms.sort(key=lambda r: Decimal(str(r.sell_rate)), reverse=True)

                    # ✅ Step 2: Per day total amount (with tax)
                    total_per_day = (total_amount / stay_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    # ✅ Step 3: Calculate weights for room allocation
                    weights = []
                    total_weight = Decimal('0.00')
                    for r in rooms:
                        w = Decimal(str(r.sell_rate)) * stay_days
                        weights.append(w)
                        total_weight += w

                    room_data = []
                    tax_total = Decimal('0.00')
                    base_total = Decimal('0.00')

                    for i, r in enumerate(rooms):
                        proportion = weights[i] / total_weight if total_weight > 0 else Decimal('1') / room_count
                        room_amount_with_tax = (total_per_day * proportion).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                        # ✅ GST slab selection based on room sell rate
                        estimated_base = (room_amount_with_tax / Decimal('1.12')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                        if estimated_base <= 7500:
                            gst_percent = Decimal('12')
                            gst_multiplier = Decimal('1.12')
                            base = estimated_base
                        else:
                            gst_percent = Decimal('18')
                            gst_multiplier = Decimal('1.18')
                            base = (room_amount_with_tax / gst_multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                        tax = (room_amount_with_tax - base).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                        room_data.append({
                            'room': r,
                            'base': base,
                            'tax': tax,
                            'gst_percent': gst_percent,
                            'amount_with_tax': room_amount_with_tax
                        })
                        base_total += base
                        tax_total += tax

                    # ✅ Step 4: Fix rounding difference on last room
                    final_total = base_total + tax_total
                    difference = total_per_day - final_total
                    if abs(difference) >= Decimal('0.01'):
                        last = room_data[-1]
                        last['base'] = (last['base'] + difference).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        last['tax'] = (last['base'] * (last['gst_percent'] / Decimal('100'))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    # ✅ Step 5: Save values to DB
                    total_base_sum = Decimal('0.00')
                    total_tax_sum = Decimal('0.00')
                    for d in room_data:
                        room = d['room']
                        room.sell_rate = float(d['base'])  # base rate per day
                        room.save()
                        total_base_sum += d['base']
                        total_tax_sum += d['tax']

                    main_guest.amount_before_tax = float((total_base_sum * stay_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                    main_guest.tax = float((total_tax_sum * stay_days).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                    main_guest.amount_after_tax = float(total_amount)
                    main_guest.total_amount = int(total_amount)

                    advance_amount = main_guest.advance_amount
                    remainamt = check_total_amount - advance_amount
                    main_guest.reamaining_amount =  remainamt
                        

                    main_guest.save()

                    Booking.objects.filter(vendor=user, advancebook=main_guest).update(totalamount=int(total_amount))
                    actionss = 'Change Booking Amount'
                    CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                            advancebook=main_guest,description=f'Booking amount changed from {check_old_totalamount} to {check_total_amount}.')


                    extraBookingAmount.objects.filter(vendor=user, bookdata__in=all_rooms).delete()
                    messages.success(request,'Booking amount changed!')
            else:
                messages.error(request,'id not found!')
            return redirect('advancebookingdetails',bid)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def editbookingdate(request):
    
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            check_indate_str = request.POST.get('check_indate')
            check_outdate_str = request.POST.get('check_outdate')

            # Convert strings to date objects
            check_indate = datetime.strptime(check_indate_str, '%Y-%m-%d').date()
            check_outdate = datetime.strptime(check_outdate_str, '%Y-%m-%d').date()
            bid = request.POST.get('id')
            print(check_indate,check_outdate)
            if SaveAdvanceBookGuestData.objects.filter(id=bid).exists():
                main_guest = SaveAdvanceBookGuestData.objects.get(vendor=user,id=bid)
                if main_guest.checkinstatus == True:
                    messages.error(request,"The guest has already checked in, so the dates cannot be updated anymore.")
                else:
                    if main_guest.bookingdate == check_indate and main_guest.checkoutdate == check_outdate:
                        messages.error(request,'both dates are same')
                    elif check_indate == check_outdate:
                        messages.error(request,'both dates are same')
                    # else:
                        # rooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=main_guest).all()
                        # for room in rooms:
                        #     room_category = room.roomno.room_type
                        #     Booking.objects.filter(vendor=user,check_in_date__gte=check_indate,check_out_date__gt=check_outdate)
                        

            return redirect('advancebookingdetails',bid)
        
def editcommtdc(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            id = request.POST.get('id')
            commission = request.POST.get('commission')
            tds = request.POST.get('tds')
            tcs = request.POST.get('tcs')
            if tds_comm_model.objects.filter(roombook__id=id).exists():
                mainguest = SaveAdvanceBookGuestData.objects.get(id=id)
                tdsdata = tds_comm_model.objects.get(roombook__id=id)
                tds_comm_model.objects.filter(roombook__id=id).update(
                    commission=commission,tds=tds,tcs=tcs
                )
                actionss = 'Update Commision Amount'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                advancebook=mainguest,description=f'Booking Commission amount Updates, old commission: {tdsdata.commission}, tds :{tdsdata.tds}, tcs :{tdsdata.tcs}.  new = commission: {commission}, tds :{tcs}, tds :{tcs}.')
            else:
                mainguest = SaveAdvanceBookGuestData.objects.get(id=id)
                tds_comm_model.objects.create(roombook=mainguest,
                    commission=commission,tds=tds,tcs=tcs
                )
                actionss = 'Create Commision Amount'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                advancebook=mainguest,description=f'Booking Commission amount Created, commission: {commission}, tds :{tds}, tcs :{tcs}.')

            messages.success(request,'data saved!')
            if Vendor_Service.objects.filter(vendor=user,only_cm=True):
                return redirect('advancebookingdetails_cm',id)
            return redirect('advancebookingdetails',id)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def bookingrevoke(request,id):

    if request.user.is_authenticated:
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor 
        checkdatas = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
        today = datetime.now().date()
        if checkdatas.checkoutdate >= today:
            roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=checkdatas).all()
            checkindate = checkdatas.bookingdate
            checkoutdate = checkdatas.checkoutdate 
            print(checkindate,checkoutdate)
            status = True
            rooms_list = []
            for check in roomdata:
                roomcatname = check.roomno.room_type.category_name
                if  Rooms.objects.filter(vendor=user,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                    available_rooms = Rooms.objects.filter(
                                vendor=user,
                                room_type__category_name=roomcatname
                                ).exclude(
                                    id__in=rooms_list
                                ).exclude(
                                    id__in=Booking.objects.filter(
                                    Q(check_in_date__lt=checkoutdate) &
                                    Q(check_out_date__gt=checkindate)
                                ).values_list('room_id', flat=True)
                                )
                    room = available_rooms.first()
                                    
                    if not room:
                        status=False
                    else:
                        rooms_list.append(room.id)

            if status == True:
                print(rooms_list,"jab chle tb ye ")
                count = 0
                for room in roomdata:
                    id = rooms_list[count]
                    newroom = Rooms.objects.filter(vendor=user,id=id).first()

                    print(newroom.room_name,'check this one')

                    RoomBookAdvance.objects.filter(vendor=user,id=room.id).update(
                        roomno=newroom
                    )
                    noon_time_str = "12:00 PM"
                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                    Booking.objects.create(
                            vendor=user,
                            room=newroom,
                            guest_name=checkdatas.bookingguest,
                            check_in_date=checkindate,
                            check_out_date=checkoutdate,
                            check_in_time=noon_time,
                            check_out_time=noon_time,
                            segment=checkdatas.channal.channalname,
                            totalamount=0.0,
                            totalroom=1,
                            gueststay=None,
                            advancebook=checkdatas,
                            status="BOOKING"
                            )
                    catdatas = RoomsCategory.objects.get(vendor=user,id=newroom.room_type.id)
                                    # inventory code
                                    # Convert date strings to date objects
                    checkindate = str(checkindate)
                    checkoutdate = str(checkoutdate)
                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                    checkoutdates = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                                    # Generate the list of all dates between check-in and check-out (inclusive)
                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                    existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category=catdatas, date__in=all_dates)

                    roomcount = Rooms.objects.filter(vendor=user,room_type=catdatas).count()
                                   
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
                    count +=1
                roomdatacount = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=checkdatas).count()
                Booking.objects.filter(vendor=user,advancebook=checkdatas).update(
                            totalroom=roomdatacount,totalamount=checkdatas.total_amount
                )

                actionss = 'Booking Revoked'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook=checkdatas,description=f'Booking Revoked in PMS')

                if VendorCM.objects.filter(vendor=user):
                    start_date = str(checkdatas.bookingdate)
                    end_date = str(checkdatas.checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()
                    
                checkdatas.action='modify'
                checkdatas.is_hold=False
                checkdatas.save()
                messages.success(request,'booking Revoked')
                return redirect('notification')
                    
                # messages.error(request, "This Service is not available yet!")
            else:
                messages.error(request, "Some rooms are not available in guest selected rooms category!")


        else:
            messages.error(request, "The guest's checkout date has already passed.")
            print("date ja chuke hai ")
        # return redirect('notification')
        return redirect('advanceroomhistory')


def bookingrevokenot(request,id):
    if request.user.is_authenticated:
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor 
        checkdatas = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
        today = datetime.now().date()
        if checkdatas.checkoutdate >= today:
            roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=checkdatas).all()
            checkindate = checkdatas.bookingdate
            checkoutdate = checkdatas.checkoutdate 
            print(checkindate,checkoutdate)
            status = True
            rooms_list = []
            for check in roomdata:
                roomcatname = check.roomno.room_type.category_name
                if  Rooms.objects.filter(vendor=user,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                    available_rooms = Rooms.objects.filter(
                                vendor=user,
                                room_type__category_name=roomcatname
                                ).exclude(
                                    id__in=rooms_list
                                ).exclude(
                                    id__in=Booking.objects.filter(
                                    Q(check_in_date__lt=checkoutdate) &
                                    Q(check_out_date__gt=checkindate)
                                ).values_list('room_id', flat=True)
                                )
                    room = available_rooms.first()
                                    
                    if not room:
                        status=False
                    else:
                        rooms_list.append(room.id)

            if status == True:
                print(rooms_list,"jab chle tb ye ")
                count = 0
                for room in roomdata:
                    id = rooms_list[count]
                    newroom = Rooms.objects.filter(vendor=user,id=id).first()

                    print(newroom.room_name,'check this one')

                    RoomBookAdvance.objects.filter(vendor=user,id=room.id).update(
                        roomno=newroom
                    )
                    noon_time_str = "12:00 PM"
                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                    Booking.objects.create(
                            vendor=user,
                            room=newroom,
                            guest_name=checkdatas.bookingguest,
                            check_in_date=checkindate,
                            check_out_date=checkoutdate,
                            check_in_time=noon_time,
                            check_out_time=noon_time,
                            segment=checkdatas.channal.channalname,
                            totalamount=0.0,
                            totalroom=1,
                            gueststay=None,
                            advancebook=checkdatas,
                            status="BOOKING"
                            )
                    catdatas = RoomsCategory.objects.get(vendor=user,id=newroom.room_type.id)
                                    # inventory code
                                    # Convert date strings to date objects
                    checkindate = str(checkindate)
                    checkoutdate = str(checkoutdate)
                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                    checkoutdates = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                                    # Generate the list of all dates between check-in and check-out (inclusive)
                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                    existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category=catdatas, date__in=all_dates)

                    roomcount = Rooms.objects.filter(vendor=user,room_type=catdatas).count()
                                   
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
                    count +=1
                roomdatacount = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=checkdatas).count()
                Booking.objects.filter(vendor=user,advancebook=checkdatas).update(
                            totalroom=roomdatacount,totalamount=checkdatas.total_amount
                )

                actionss = 'Booking Revoked'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook=checkdatas,description=f'Booking Revoked in PMS')

                if VendorCM.objects.filter(vendor=user):
                    start_date = str(checkdatas.bookingdate)
                    end_date = str(checkdatas.checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()
                    
                checkdatas.action='modify'
                checkdatas.is_hold=False
                checkdatas.save()
                messages.success(request,'booking Revoked')
                return redirect('notification')
                    
                # messages.error(request, "This Service is not available yet!")
            else:
                messages.error(request, "Some rooms are not available in guest selected rooms category!")


        else:
            messages.error(request, "The guest's checkout date has already passed.")
            print("date ja chuke hai ")
        return redirect('notification')

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models.functions import ExtractMonth
def cm(request):
    if request.user.is_authenticated:
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor 

        if True:
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
                last_day_of_month = today + timedelta(days=6)
            else:
                # last_day_of_month = now.replace(month=now.month + 1, day=1) - timezone.timedelta(days=20)
                last_day_of_month = today + timedelta(days=6)
        


            # ye pahle ka code hai 
            # monthbookdata  = SaveAdvanceBookGuestData.objects.filter(
            #     vendor=user,
            #     bookingdate__range=(first_day_of_month, last_day_of_month)
            #         ).order_by('bookingdate')

            # ye new code hai
            from django.db.models import Prefetch
            from collections import Counter

            # room_prefetch = Prefetch(
            #     'roombookadvance_set',
            #     queryset=RoomBookAdvance.objects.select_related('roomno__room_type'),
            #     to_attr='booked_rooms'
            # )

            # monthbookdata = SaveAdvanceBookGuestData.objects.filter(
            #     vendor=user,
            #     bookingdate__range=(first_day_of_month, last_day_of_month)
            # ).prefetch_related(room_prefetch).order_by('bookingdate')

            # for guest in monthbookdata:
            #     category_names = [
            #         room.roomno.room_type.category_name
            #         for room in guest.booked_rooms
            #     ]
            #     category_counts = Counter(category_names)

            #     guest.room_categories_summary = ", ".join(
            #         f"({count}) {cat}" for cat, count in category_counts.items()
            #     )
            room_prefetch = Prefetch(
                'roombookadvance_set',
                queryset=RoomBookAdvance.objects.select_related('roomno__room_type'),
                to_attr='booked_rooms'
            )

            # Prefetch for Cm_RoomBookAdvance
            cm_room_prefetch = Prefetch(
                'cm_roombookadvance_set',
                queryset=Cm_RoomBookAdvance.objects.select_related('room_category'),
                to_attr='cm_booked_rooms'
            )

            # Query main guest data with both prefetches
            monthbookdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,
                bookingdate__range=(first_day_of_month, last_day_of_month)).prefetch_related(
                room_prefetch,
                cm_room_prefetch
            )

            # If no matching records
            if not monthbookdata.exists():
                messages.error(request, "No matching guests found.")

            # Process each guest's room summary
            for guest in monthbookdata:
                category_names = []

                # From RoomBookAdvance
                for room in getattr(guest, 'booked_rooms', []):
                    if room.roomno and room.roomno.room_type:
                        category_names.append(room.roomno.room_type.category_name)

                # From Cm_RoomBookAdvance
                for room in getattr(guest, 'cm_booked_rooms', []):
                    if room.room_category:
                        category_names.append(room.room_category.category_name)

                # Count and summarize
                category_counts = Counter(category_names)
                guest.room_categories_summary = ", ".join(
                    f"({count}) {cat}" for cat, count in category_counts.items()
                )


            return render(request,'cm_booking_history.html',{'filtered_orders':filtered_orders,'advanceroomdata':advanceroomdata,'active_page': 'cmadvancebookhistory','monthbookdata':monthbookdata
                                                            ,'first_day_of_month':first_day_of_month,'last_day_of_month':last_day_of_month})
    else:
        return redirect('loginpage')
    
        
        # return render(request,'cm_booking_history.html')
from django.db.models import F

def editinvoiceitemamt(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            itemsids = request.POST.get('itemsids')
            itemsmtname = request.POST.get('itemsmtname')

            if InvoiceItem.objects.filter(vendor=user,id=itemsids):
                items = InvoiceItem.objects.get(vendor=user,id=itemsids)
                price = items.price
                qty = items.quantity_likedays
                items = InvoiceItem.objects.get(vendor=user, id=itemsids)
                price = float(items.price)  # price per 1 qty (per day)
                qty = items.quantity_likedays
                tax_percent = float(items.cgst_rate * 2)

                # Original calculated
                base_price = price * qty
                tax_amount = base_price * (tax_percent / 100)
                total_with_tax = base_price + tax_amount

                # User amount
                try:
                    user_final_amount = float(itemsmtname)
                    base_settled = user_final_amount / (1 + tax_percent / 100)
                    tax_settled = user_final_amount - base_settled
                    per_day_price = base_settled / qty

                    result = {
                        'original_total': total_with_tax,
                        'base_amount': float(base_settled),
                        'tax_amount': float(tax_settled),
                        'per_day_price': float(per_day_price),
                        'final_amount': user_final_amount
                    }
                    if tax_percent==0 or tax_percent==0.0:
                        oldmainwithouttaxamt = float(items.totalwithouttax)
                        oldgrandtotalamt = float(items.total_amount)
                        Invoice.objects.filter(vendor=user,id=items.invoice.id).update(
                            total_item_amount=F('total_item_amount')-oldmainwithouttaxamt,
                            subtotal_amount = F('subtotal_amount')-oldmainwithouttaxamt,
                            grand_total_amount=F('grand_total_amount')-oldgrandtotalamt,
                        )

                        Invoice.objects.filter(vendor=user,id=items.invoice.id).update(
                            total_item_amount=F('total_item_amount')+user_final_amount,
                            subtotal_amount = F('subtotal_amount')+user_final_amount,
                            grand_total_amount=F('grand_total_amount')+user_final_amount,
                        )


                        InvoiceItem.objects.filter(vendor=user,id=items.id).update(
                            price=round(per_day_price, 2),total_amount=user_final_amount,
                            totalwithouttax=user_final_amount,
                        )

                        maininvcwork = Invoice.objects.get(vendor=user,id=items.invoice.id)
                        paidamt = maininvcwork.accepted_amount
                        mainrdtamt = maininvcwork.grand_total_amount
                        duramtmain = mainrdtamt-paidamt
                        maininvcwork.Due_amount=duramtmain
                        maininvcwork.save()
                        CustomGuestLog.objects.create(vendor=user,customer=items.invoice.customer,
                                by=request.user,action=f'Amount Changed For {items.id}',
                                description=f'Amount Changed For {items.id}, from {total_with_tax} to {user_final_amount} '
                                )
                    else:
                        totaloldstaxamt = float(items.cgst_rate_amount)
                        oldmaintotalamt = float(items.total_amount)
                        oldmainwithouttaxamt = float(items.totalwithouttax)
                        oldgrandtotalamt = float(items.total_amount)
                        Invoice.objects.filter(vendor=user,id=items.invoice.id).update(
                            total_item_amount=F('total_item_amount')-oldmainwithouttaxamt,
                            subtotal_amount = F('subtotal_amount')-oldmainwithouttaxamt,
                            gst_amount = F('gst_amount')-totaloldstaxamt,
                            sgst_amount = F('sgst_amount')-totaloldstaxamt,
                            grand_total_amount=F('grand_total_amount')-oldgrandtotalamt,
                            taxable_amount=F('taxable_amount')-oldmainwithouttaxamt
                        )

                        netxper = str(int(tax_percent))
                        netxper = "GST"+netxper
                        if taxSlab.objects.filter(invoice_id=items.invoice.id,tax_rate_name=netxper).exists():
                            taxSlab.objects.filter(invoice_id=items.invoice.id,tax_rate_name=netxper).update(
                                cgst_amount=F('cgst_amount')-float(items.cgst_rate_amount),
                                sgst_amount=F('sgst_amount')-float(items.cgst_rate_amount),
                                total_amount = F('total_amount')-float(items.cgst_rate_amount*2)
                            )

                        item_total_finalamt = float(base_settled)
                        item_final_tax_amt = float(tax_settled)/2

                        InvoiceItem.objects.filter(vendor=user,id=items.id).update(
                            price=float(per_day_price),total_amount=user_final_amount,
                            totalwithouttax=float(per_day_price)*qty,cgst_rate_amount=item_final_tax_amt,
                            sgst_rate_amount=item_final_tax_amt
                        )

                        Invoice.objects.filter(vendor=user,id=items.invoice.id).update(
                                total_item_amount=F('total_item_amount')+item_total_finalamt,
                                subtotal_amount = F('subtotal_amount')+item_total_finalamt,
                                gst_amount = F('gst_amount')+item_final_tax_amt,
                                sgst_amount = F('sgst_amount')+item_final_tax_amt,
                                grand_total_amount=F('grand_total_amount')+user_final_amount,
                                taxable_amount=F('taxable_amount')+item_total_finalamt
                            )
                        
                        if taxSlab.objects.filter(invoice_id=items.invoice.id,tax_rate_name=netxper).exists():
                            taxSlab.objects.filter(invoice_id=items.invoice.id,tax_rate_name=netxper).update(
                                cgst_amount=F('cgst_amount')+float(item_final_tax_amt),
                                sgst_amount=F('sgst_amount')+float(item_final_tax_amt),
                                total_amount = F('total_amount')+float(item_final_tax_amt*2)
                            )
                        else:
                            taxSlab.objects.create(vendor=user,invoice=items.invoice,tax_rate_name=netxper,
                                cgst_amount=float(item_final_tax_amt),
                                sgst_amount=float(item_final_tax_amt),
                                total_amount = float(item_final_tax_amt*2),
                                cgst=items.cgst_rate,sgst=items.cgst_rate)
                            
                        CustomGuestLog.objects.create(vendor=user,customer=items.invoice.customer,
                                by=request.user,action=f'Amount Changed For {items.id}',
                                description=f'Amount Changed For {items.id}, from {total_with_tax} to {user_final_amount} '
                                )
                        maininvcwork = Invoice.objects.get(vendor=user,id=items.invoice.id)
                        paidamt = maininvcwork.accepted_amount
                        mainrdtamt = maininvcwork.grand_total_amount
                        duramtmain = mainrdtamt-paidamt
                        maininvcwork.Due_amount=duramtmain
                        maininvcwork.save()

                except ValueError:
                    messages.error(request,'Invalid amount entered')
                    return redirect('invoicepage',items.invoice.id)
                messages.success(request,'Amount Changed')
                return redirect('invoicepage',items.invoice.id)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def delteroominbook(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            if RoomBookAdvance.objects.filter(vendor=user,id=id):
                roombook = RoomBookAdvance.objects.get(vendor=user,id=id)
                booking = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=roombook.saveguestdata.id).first()

                if booking.action=='cancel':
                    messages.error(request,"This Booking is cancelled not remove any room from here")
                    return redirect('advancebookingdetails',booking.id)
                bookcounts = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=booking).count()
                if bookcounts==1:
                    messages.error(request,"Only one room left please canclled full booking!")
                    return redirect('advancebookingdetails',booking.id)

                if booking.checkinstatus==False:
                    sellprice = roombook.sell_rate
                    if sellprice>7500:
                        tax = 18
                    else:
                        tax=12
                    days = booking.staydays

                    base_amount = (sellprice*days)
                    tax_amount = base_amount*tax/100
                    total_amount = float(base_amount) + float(tax_amount)
                    print(base_amount,tax_amount,total_amount)
                    
                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=roombook.saveguestdata.id).update(
                        action="modify",
                        tax=F('tax')-tax_amount,
                        amount_after_tax=F('amount_after_tax')- total_amount,
                        amount_before_tax=F('amount_before_tax')-base_amount,
                        total_amount=F('total_amount')-total_amount,
                        noofrooms=F('noofrooms')-1
                    )
                    newbooking = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=roombook.saveguestdata.id).first()
                    Booking.objects.filter(vendor=user,advancebook=newbooking,room=roombook.roomno).delete()
                    Booking.objects.filter(vendor=user,advancebook=newbooking).update(
                        totalamount=newbooking.total_amount,
                        totalroom=newbooking.noofrooms,
                    )
                    print("checkamounts",newbooking.reamaining_amount,total_amount)
                    if newbooking.reamaining_amount > total_amount or newbooking.reamaining_amount == total_amount:
                        print(total_amount,'check here')
                        newbooking.reamaining_amount = newbooking.reamaining_amount - float(total_amount)
                        newbooking.save()
                    else:
                        print("if nhi chaal",newbooking.reamaining_amount,total_amount)

                    Rooms.objects.filter(vendor=user,id=roombook.roomno.id).update(checkin=0)
                    checkindate = roombook.bookingdate
                    checkoutdate = roombook.checkoutdate
                    while checkindate < checkoutdate:
                        roomscat = Rooms.objects.get(vendor=user,id=roombook.roomno.id)
                        invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                                            
                        invtavaible = invtdata.total_availibility + 1
                        invtabook = invtdata.booked_rooms - 1
                        total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                        occupancy = invtabook * 100//total_rooms
                                                                                    

                        RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                    total_availibility=invtavaible,occupancy=occupancy)
                                
                        checkindate += timedelta(days=1)

                    if VendorCM.objects.filter(vendor=user):
                        start_date = str(roombook.bookingdate)
                        end_date = str(roombook.checkoutdate)
                        thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                        thread.start()
                    actionss = 'Modify Booking Delete Room'
                    CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                        advancebook=newbooking,description=f"Room booking for Room No. {roombook.roomno.room_name} has been deleted, and the booking amount of {total_amount} has been removed.")
                    roombook.delete()
                    messages.success(request,"Room Deleted")
                else:
                    messages.error(request,"Guest Checkin Complete Room Cant Be Delete!")

                return redirect('advancebookingdetails',booking.id)
            
            else:
                messages.error(request,"Id Not Found!")
                return redirect('advanceroomhistory')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def editbookingdates(request):
    # try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            checkin = request.POST.get('checkin')
            checkout = request.POST.get('checkout')
            id = request.POST.get('id')
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id):
                booking = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
            
                if str(booking.bookingdate)==checkin and str(booking.checkoutdate)==checkout:
                    messages.error(request,"Check-in and check-out are on the same date, and both are old dates.")
                else:
                    if checkin < checkout:
                        checkindate = datetime.strptime(checkin, "%Y-%m-%d").date()
                        checkoutdate = datetime.strptime(checkout, "%Y-%m-%d").date()
                        roombooks = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=booking).all()

                        if checkindate==booking.bookingdate:
                            available = False
                            for books in roombooks:
                                roomcatname = books.roomno
                                Booking.objects.filter(Q(vendor=user),
                                        Q(check_in_date__lt=checkoutdate) &
                                        Q(check_out_date__gte=checkindate))
                                

                        else:

                            available = False
                            for books in roombooks:
                                print(books.roomno.room_type)
                                roomcatname=books.roomno.room_type
                                if  Rooms.objects.filter(vendor=user,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                                    available_rooms = Rooms.objects.filter(
                                                    vendor=user,
                                                    room_type__category_name=roomcatname
                                                ).exclude(
                                                    id__in=Booking.objects.filter(
                                                        Q(check_in_date__lt=checkoutdate) &
                                                        Q(check_out_date__gte=checkindate)
                                                    ).values_list('room_id', flat=True)
                                                )
                                    room = available_rooms.first()
                                    if not room:
                                        break
                                    else:
                                        available=True
                            print(available)

                        

                    else:
                        messages.error(request,"Checkout date is earlier than check-in date — please enter a valid date.")

            return redirect('advancebookingdetails',id)

def searchdateweek(request):
    date_str = request.POST.get('searchdate')  # e.g. "2025-07-02"

    if date_str:
        form_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.now().date()

        difference = (form_date - today).days  # positive, negative, or 0


        # Redirect with calculated index in query string
        return redirect(f'/weekviews/?index={difference}')

    return redirect('weekviews')  # default fallback

def addmorerooms(request,id):
        if request.user.is_authenticated :
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id):
                booking = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                today = datetime.today().date()
                if booking.segment=="OTA":
                    messages.error(request,'This Booking From OTA. Not Added Another Room Please Create A New Booking')
                    return redirect('advancebookingdetails',id)
                if booking.checkoutdate>today:
                    checkindate=booking.bookingdate
                    checkoutdate=booking.checkoutdate
                    available_rooms = Rooms.objects.filter(
                                        vendor=user,
                                        ).exclude(
                                        id__in=Booking.objects.filter(
                                                Q(check_in_date__lt=checkoutdate) &
                                                Q(check_out_date__gte=checkindate)
                                                ).values_list('room_id', flat=True)
                                        )
                    room = available_rooms
                    for i in room:
                        print(i.room_name,i.id)
                    return render(request,"addroombooking.html",{'availableroomdata':room,'booking':booking})
                else:
                    messages.error(request,'Guest Checkout Date is Less Then To Current Date')
                
            else:
                messages.error(request,'Id not found!')
                return redirect('advancebookingdetails',id)

        return redirect('advancebookingdetails',id)

def addroomsinbooking(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookingid = request.POST.get('bookingid')
            final_amount = float(request.POST.get('final_amount'))
            booking = SaveAdvanceBookGuestData.objects.get(vendor=user,id=bookingid)
            checkindate=booking.bookingdate
            checkoutdate=booking.checkoutdate

            # Step 3: Extract selected room IDs from POST data
            room_ids_raw = request.POST.get('selected_rooms')  # e.g. "8,9"
            room_ids_list = []
            if room_ids_raw:
                room_ids_list = [int(x) for x in room_ids_raw.split(',') if x.strip().isdigit()]

            rooms = Rooms.objects.filter(id__in=room_ids_list)
            available_rooms = Rooms.objects.filter(
                                        vendor=user,
                                        ).exclude(
                                        id__in=Booking.objects.filter(
                                                Q(check_in_date__lt=checkoutdate) &
                                                Q(check_out_date__gte=checkindate)
                                                ).values_list('room_id', flat=True)
                                        )
            

            # Step 4: Get available room IDs
            available_ids = list(available_rooms.values_list('id', flat=True))

            # Step 5: Check if all selected rooms are actually available
            somebook = not set(room_ids_list).issubset(set(available_ids))
            

            

            if somebook==True:
                messages.error(request,'Some Rooms Are Booked In Your Selected Rooms!')
                return redirect('addmorerooms',bookingid)
            else:
                alldayoneroomamt = final_amount/len(room_ids_list)
                onedayprice = alldayoneroomamt/booking.staydays
                if onedayprice<= 8400: 
                    baseprice = onedayprice/1.12
                    taxamt = onedayprice-baseprice
                elif 8400 < onedayprice <= 8850:
                    baseprice = onedayprice/1.18
                    taxamt = onedayprice-baseprice
                else:
                    baseprice = onedayprice/1.12
                    taxamt = onedayprice-baseprice

                total_tax_Amt = taxamt*len(room_ids_list)*booking.staydays
                total_base_amt = baseprice*len(room_ids_list)*booking.staydays
                grand_total_amt = total_tax_Amt+total_base_amt
                print(total_base_amt,total_tax_Amt,grand_total_amt)
                rooms = []
                print(room_ids_raw,'checkids')
                for room in room_ids_list:
                        print(room,'check this')
                        room=int(room)
                        newroom = Rooms.objects.get(vendor=user,id=room)
                        rooms.append(newroom.room_name)
                        rbk = RoomBookAdvance.objects.create(
                                vendor=user,
                                saveguestdata=booking,
                                bookingdate=checkindate,
                                roomno_id=newroom.id,
                                bookingguest=booking.bookingguest,
                                bookingguestphone=0,
                                checkoutdate=checkoutdate,
                                bookingstatus=True,
                                channal=booking.channal,
                                totalguest=newroom.max_person,
                                rateplan_code='EP',
                                rateplan_code_main='add more room',
                                guest_name='',
                                adults=newroom.max_person,
                                children=0,
                                sell_rate=baseprice
                                )
                                  

                                    


                        # Handling check-in and check-out times
                        noon_time_str = "12:00 PM"
                        noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
                        # Create the Booking entry for the room
                        Booking.objects.create(
                                        vendor=user,
                                        room=newroom,
                                        guest_name=booking.bookingguest,
                                        check_in_date=checkindate,
                                        check_out_date=checkoutdate,
                                        check_in_time=noon_time,
                                        check_out_time=noon_time,
                                        segment=booking.channal.channalname,
                                        totalamount=0.0,
                                        totalroom=1,
                                        gueststay=None,
                                        advancebook=booking,
                                        status="BOOKING"
                                    )

                                    

                        catdatas = RoomsCategory.objects.get(vendor=user,category_name=newroom.room_type)
                                    # inventory code
                                    # Convert date strings to date objects
                        checkindate = str(checkindate)
                        checkoutdate = str(checkoutdate)
                        checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                        checkoutdates = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                                    # Generate the list of all dates between check-in and check-out (inclusive)
                        all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                        existing_inventory = RoomsInventory.objects.filter(vendor=user,room_category=catdatas, date__in=all_dates)

                                    # Get the list of dates that already exist in the inventory
                        existing_dates = set(existing_inventory.values_list('date', flat=True))

                                    # Identify the missing dates by comparing all_dates with existing_dates
                        missing_dates = [date for date in all_dates if date not in existing_dates]

                                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                        roomcount = Rooms.objects.filter(vendor=user,room_type=catdatas).count()
                                   
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
                        totalrooms = Rooms.objects.filter(vendor=user,room_type=catdatas).count()
                        occupancccy = (1 *100 //totalrooms)
                        if missing_dates:
                                for missing_date in missing_dates:
                                        
                                                RoomsInventory.objects.create(
                                                    vendor=user,
                                                    date=missing_date,
                                                    room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
                                                    total_availibility=roomcount-1,       # Set according to your logic
                                                    booked_rooms=1,    
                                                    occupancy=occupancccy,
                                                    price=catdatas.catprice
                                                                            # Set according to your logic
                                                )
                                print(f"Missing dates have been created for: {missing_dates}")
                        else:
                                print("All dates already exist in the inventory.")

                roomcounts = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=booking).count()
                Booking.objects.filter(vendor=user,advancebook=booking).update(
                    totalamount = booking.total_amount + grand_total_amt,
                    totalroom = roomcounts
                )

                booking.amount_after_tax=F('amount_after_tax')+ grand_total_amt
                booking.amount_before_tax=F('amount_before_tax')+total_base_amt
                booking.total_amount=F('total_amount')+grand_total_amt
                booking.tax=F('tax')+total_tax_Amt
                booking.reamaining_amount=F('reamaining_amount')+grand_total_amt
                booking.noofrooms=roomcounts
                booking.action='modify'
                booking.save()

                actionss = 'Edit Booking Add Rooms'
                CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook=booking,description=f'Add some room in booking, room numbers {rooms} ')

                if VendorCM.objects.filter(vendor=user):
                    start_date = str(booking.bookingdate)
                    end_date = str(booking.checkoutdate)
                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                    thread.start()
                    

                messages.success(request,'Room Added')
                return redirect('advancebookingdetails',booking.id)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

from .manageQR import changeroomadvance 
from django.http import QueryDict
def bookingchangeroom(request,id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=403)
    user=request.user
    subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
    if subuser:
        user = subuser.vendor 
    savebook = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).first()
    bookmodel=Booking.objects.filter(vendor=user,advancebook=savebook).first()
    new_request = request
    new_request.method = "POST"  # Simulate a POST request
    new_request.POST = QueryDict(mutable=True)
    new_request.POST.update({
        'bookingmodelid': bookmodel.id,
        })

          
    return changeroomadvance(new_request)