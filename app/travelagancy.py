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
                  tax=0.00,currency="INR",checkin=current_date,Payment_types='postpaid',is_selfbook=False  )
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
                
            # for i in my_array:
            #         roomid = int(i['id'])
            #         roomsellprice = int(float(i['price']))
            #         roomselltax = int(float(i['tax']))
            #         befortselprice=roomsellprice
            #         totalsellprice = (roomsellprice * roomselltax //100) + roomsellprice
            #         sellingprices = sellingprices + roomsellprice
            #         totaltax = totaltax + (roomsellprice * roomselltax //100)
                   
            #         roomid = Rooms.objects.get(id=roomid)
            #         roomtype = roomid.room_type.id
            #         RoomBookAdvance.objects.create(vendor=user,saveguestdata=Saveadvancebookdata,bookingdate=bookingdate,roomno=roomid,
            #                                         bookingguest=guestname,bookingguestphone=phone
            #                                     ,checkoutdate=bookenddate,bookingstatus=True,channal=channal,totalguest=guestcount,
            #                                    rateplan_code=mealplan,guest_name='',adults=0,children=0,sell_rate=totalsellprice )
            #         noon_time_str = "12:00 PM"
            #         noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()
            #         Booking.objects.create(vendor=user,room=roomid,guest_name=guestname,check_in_date=bookingdate,check_out_date=bookenddate,
            #                     check_in_time=noon_time,check_out_time=noon_time,segment=travelname,totalamount=totalamount,totalroom=noofrooms,
            #                     gueststay=None,advancebook=Saveadvancebookdata,status="BOOKING"           )
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