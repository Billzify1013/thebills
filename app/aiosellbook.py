import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.db.models import Q
from datetime import datetime,timedelta
import threading
from .newcode import *
# Create your views here.
from .dynamicrates import *
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore
import re

# Logging setup
logger = logging.getLogger(__name__)

@csrf_exempt
def aiosell_new_reservation(request):
    # if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Log incoming data for verification
            logger.info("Received new reservation data: %s", data)

           
            action = data['action']
            hotelCode = data['hotelCode']
            if VendorCM.objects.filter(hotelcode=hotelCode).exists():
                bookingId = data['bookingId']

                if action == 'book' or action=='modify': 
                    cmBookingId = data['cmBookingId']
                    channel = data['channel']
                    bookingdate = data['bookedOn']
                    if bookingId=='null':
                         bookingId=None
                    else:
                         pass
                    if cmBookingId=='null':
                        cmBookingId=None
                    else:
                        pass
                    # Parse the date and time string into a datetime object
                    booking_datetime = datetime.strptime(bookingdate, '%Y-%m-%d %H:%M:%S')

                    # Format it to just the date (YYYY-MM-DD)
                    bookingdates = booking_datetime.date()
                    checkindate = data['checkin']
                    checkoutdate = data['checkout']
                    segment = data['segment']
                    specialRequests = data['specialRequests']
                    pah = str(data['pah'])
                    checkpah = pah.lower()
                    mcheckoutdate=checkoutdate

                    # Convert string dates to datetime objects
                    checkin_date = datetime.strptime(data['checkin'], '%Y-%m-%d')
                    checkout_date = datetime.strptime(data['checkout'], '%Y-%m-%d')

                    day_difference = (checkout_date - checkin_date).days

                    # Example 2: Access nested keys (amount details)
                    amount_details = data['amount']
                    
                    amountbeforetax = amount_details['amountBeforeTax']
                    amountaftertax =  amount_details['amountAfterTax']
                    taxamount = amount_details['tax']
                    currency = amount_details['currency']

                    # Example 3: Access guest details
                    guest = data['guest']
                    guestname = str(guest['firstName']) + " " + str(guest['lastName'])
                    guetemail =  guest['email']
                    guestphone =  guest['phone']

                    

                    # Remove spaces from the string
                    if not guestphone:
                         guestphone=0
                    else:
                        guestphone = re.sub(r'\s+', '', guestphone)  # Removes all spaces

                        # Extract the last 10 characters
                        guestphone = guestphone[-10:]

                    print(guestphone)
                    guestaddress =  str(guest['address']['line1']) + " " + str(guest['address']['city']) + " " + str(guest['address']['zipCode'])
                    
                    state = str(guest['address']['state'])
                    country = str(guest['address']['country'])

                    if checkpah=='true':
                        pahr = True
                        advanceamounts = 0
                        remainamounts = int(amountaftertax)
                        paymenttype = 'postpaid'
                    else:
                        pahr=False
                        advanceamounts = int(amountaftertax)
                        remainamounts = 0
                        paymenttype = 'prepaid'

                    # Example 4: Iterate over rooms
                    # print("\nRoom Details:")
                    totalguest = 0
                    roomcount = 0
                    for room in data['rooms']:
                        # print("  Room Code:", room['roomCode'])
                        # print("  Guest Name:", room['guestName'])
                        totalguest = totalguest + int(room['occupancy']['adults']) +  int(room['occupancy']['children'])

                        # print("  Prices:")
                        for price in room['prices']:
                            print("    Date:", price['date'], "| Rate:", price['sellRate'])

                        roomcount = roomcount + 1
                        


                    # if VendorCM.objects.filter(hotelcode=hotelCode).exists():
                    vendordata = VendorCM.objects.get(hotelcode=hotelCode)
                    if onlinechannls.objects.filter(vendor=vendordata.vendor, channalname=channel).exists():
                            pass
                    else:
                            onlinechannls.objects.create(vendor=vendordata.vendor, channalname=channel)

                if action == 'book':
                        if SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor, booking_id=bookingId, cm_booking_id=cmBookingId).exists():
                            return JsonResponse({'success': True, 'message': 'Reservation Already Exists! '})
                        else:
                            cnalledata = onlinechannls.objects.get(vendor=vendordata.vendor, channalname=channel)
                            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.create(
                                vendor=vendordata.vendor,
                                booking_id=bookingId,
                                cm_booking_id=cmBookingId,
                                channal=cnalledata,  
                                action=action,
                                checkin=bookingdates,
                                bookingdate=checkindate,
                                checkoutdate=checkoutdate,
                                segment=segment,
                                special_requests=specialRequests,
                                pah=pahr,
                                amount_before_tax=amountbeforetax,
                                amount_after_tax=amountaftertax,
                                tax=taxamount,
                                currency=currency,
                                total_amount=int(amountaftertax),
                                advance_amount=advanceamounts,
                                reamaining_amount=remainamounts,
                                discount=0,
                                checkinstatus=False,
                                Payment_types=paymenttype,
                                is_selfbook=False,
                                staydays=day_difference,
                                bookingguest=guestname,
                                bookingguestphone=guestphone,
                                email=guetemail,
                                address_city=guestaddress,
                                state = state,
                                country = country,
                                totalguest=totalguest,
                                noofrooms=roomcount,
                            )

                            if pahr==False:
                                InvoicesPayment.objects.create(vendor=vendordata.vendor,
                                                advancebook= Saveadvancebookdata,
                                                payment_amount= amountaftertax,
                                                payment_date=bookingdates,
                                                payment_mode='BankTransfer', 
                                                transaction_id='',
                                                descriptions='This Amount From OTA'  )
                            
                            for room in data['rooms']:
                                roomcatname = room['roomCode']
                                rateplanCode = room['rateplanCode']
                                GuestName = room['guestName']
                                adults =  int(room['occupancy']['adults']) 
                                children = int(room['occupancy']['children'])
                                rateplanname=''
                                if rateplanCode == 'null':
                                    rateplanCode=None
                                else:
                                    if RatePlan.objects.filter(vendor=vendordata.vendor,rate_plan_code=rateplanCode).exists():
                                        plandatas = RatePlan.objects.get(vendor=vendordata.vendor,rate_plan_code=rateplanCode)
                                        rateplanname = plandatas.rate_plan_name
                                    else:
                                        pass
                                
                                # print("  Prices:")
                                # totalsell = 0.0
                                # for price in room['prices']:
                                #     totalsell = totalsell + price['sellRate']

                                totalsell = 0.0
                                for price in room['prices']:
                                    totalsell =  price['sellRate']

                                if  Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                                    available_rooms = Rooms.objects.filter(
                                                vendor=vendordata.vendor,
                                                room_type__category_name=roomcatname
                                            ).exclude(
                                                id__in=Booking.objects.filter(
                                                    Q(check_in_date__lt=checkoutdate) &
                                                    Q(check_out_date__gt=checkindate)
                                                ).values_list('room_id', flat=True)
                                            )
                                    room = available_rooms.first()
                                    if not room:
                                        room = Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname,checkin=0).exclude(checkin=6).first()
                                    else:
                                        pass
                                    RoomBookAdvance.objects.create(
                                                vendor=vendordata.vendor,
                                                saveguestdata=Saveadvancebookdata,
                                                bookingdate=checkindate,
                                                roomno_id=room.id,
                                                bookingguest=guestname,
                                                bookingguestphone=guestphone,
                                                checkoutdate=checkoutdate,
                                                bookingstatus=True,
                                                channal=cnalledata,
                                                totalguest=adults + children,
                                                rateplan_code=rateplanname,
                                                rateplan_code_main=rateplanCode,
                                                guest_name=GuestName,
                                                adults=adults,
                                                children=children,
                                                sell_rate=totalsell
                                            )

                                                # Handling check-in and check-out times
                                    noon_time_str = "12:00 PM"
                                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()

                                    # Create the Booking entry for the room
                                    Booking.objects.create(
                                        vendor=vendordata.vendor,
                                        room=room,
                                        guest_name=guestname,
                                        check_in_date=checkindate,
                                        check_out_date=checkoutdate,
                                        check_in_time=noon_time,
                                        check_out_time=noon_time,
                                        segment=segment,
                                        totalamount=amountbeforetax,
                                        totalroom=roomcount,
                                        gueststay=None,
                                        advancebook=Saveadvancebookdata,
                                        status="BOOKING"
                                    )

                                    

                                    catdatas = RoomsCategory.objects.get(vendor=vendordata.vendor,category_name=roomcatname)
                                    # inventory code
                                    # Convert date strings to date objects
                                    checkindate = str(checkindate)
                                    checkoutdate = str(checkoutdate)
                                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                                    checkoutdates = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                                    # Generate the list of all dates between check-in and check-out (inclusive)
                                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                                    existing_inventory = RoomsInventory.objects.filter(vendor=vendordata.vendor,room_category=catdatas, date__in=all_dates)

                                    # Get the list of dates that already exist in the inventory
                                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                                    # Identify the missing dates by comparing all_dates with existing_dates
                                    missing_dates = [date for date in all_dates if date not in existing_dates]

                                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                                    roomcount = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).exclude(checkin=6).count()
                                   
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
                                    totalrooms = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).exclude(checkin=6).count()
                                    occupancccy = (1 *100 //totalrooms)
                                    if missing_dates:
                                        for missing_date in missing_dates:
                                        
                                                RoomsInventory.objects.create(
                                                    vendor=vendordata.vendor,
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
                                            
                                    
                            userids = vendordata.vendor.id
                            if VendorCM.objects.filter(vendor=vendordata.vendor,):
                                        start_date = str(checkindate)
                                        end_date = str(checkoutdates)
                                        thread = threading.Thread(target=update_inventory_task, args=(userids, start_date, end_date))
                                        thread.start()
                                        # for dynamic pricing
                                        if  VendorCM.objects.filter(vendor=vendordata.vendor,dynamic_price_active=True):
                                            thread = threading.Thread(target=rate_hit_channalmanager, args=(userids, start_date, end_date))
                                            thread.start()
                                        else:
                                            pass
                            else:
                                        pass  
                              
                            

                            user = vendordata.vendor
                            
                            # Fetch all sessions
                            sessions = Session.objects.filter(expire_date__gte=timezone.now())

                            # Iterate over active sessions to find the user's session
                            for session in sessions:
                                session_store = SessionStore(session_key=session.session_key)
                                data = session_store.load()  # Load session data
                                
                                if str(user.id) == str(data.get('_auth_user_id')):  # Match user ID with session data
                                    # Check if the user is a subuser
                                    if hasattr(user, 'subuser_profile'):
                                        subuser = user.subuser_profile
                                        if not subuser.is_cleaner:
                                            # Get the main user (vendor) of this subuser
                                            main_user = subuser.vendor
                                            if main_user:
                                                # Update main user's session
                                                for main_session in sessions:
                                                    main_session_store = SessionStore(session_key=main_session.session_key)
                                                    main_session_data = main_session_store.load()
                                                    if str(main_user.id) == str(main_session_data.get('_auth_user_id')):
                                                        main_session_data['notification'] = True
                                                        main_session_store.update(main_session_data)
                                                        main_session_store.save()

                                            # Update subuser's session
                                            data['notification'] = True
                                            session_store.update(data)
                                            session_store.save()

                                    else:
                                        # Update the main user's session
                                        data['notification'] = True
                                        session_store.update(data)
                                        session_store.save()

                            return JsonResponse({'success': True, 'message': 'Reservation Updated Successfully'})
                            
                
                elif action=='modify':
                        # i am work here
                        cnalledata = onlinechannls.objects.get(vendor=vendordata.vendor, channalname=channel)
                        if SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor,booking_id=bookingId,channal=cnalledata).exists():
                            
                            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.get(vendor=vendordata.vendor,booking_id=bookingId,channal=cnalledata)
                            SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor,booking_id=bookingId,channal=cnalledata).update(
                                booking_id=bookingId,
                                cm_booking_id=cmBookingId,
                                channal=cnalledata,  
                                action=action,
                                checkin=bookingdates,
                                bookingdate=checkindate,
                                checkoutdate=checkoutdate,
                                segment=segment,
                                special_requests=specialRequests,
                                pah=pahr,
                                amount_before_tax=amountbeforetax,
                                amount_after_tax=amountaftertax,
                                tax=taxamount,
                                currency=currency,
                                total_amount=int(amountaftertax),
                                advance_amount=advanceamounts,
                                reamaining_amount=remainamounts,
                                discount=0,
                                checkinstatus=False,
                                Payment_types=paymenttype,
                                is_selfbook=False,
                                staydays=day_difference,
                                bookingguest=guestname,
                                bookingguestphone=guestphone,
                                email=guetemail,
                                address_city=guestaddress,
                                state = state,
                                country = country,
                                totalguest=totalguest,
                                noofrooms=roomcount,
                            )

                            if pahr==False:
                                if InvoicesPayment.objects.filter(vendor=vendordata.vendor,advancebook= Saveadvancebookdata).exists():
                                    pass
                                else:
                                    InvoicesPayment.objects.create(vendor=vendordata.vendor,
                                                advancebook= Saveadvancebookdata,
                                                payment_amount= amountaftertax,
                                                payment_date=bookingdates,
                                                payment_mode='BankTransfer', 
                                                transaction_id='',
                                                descriptions='This Amount From OTA'  )
                            
                            roombookadvance_data = list(RoomBookAdvance.objects.filter(
                                vendor=vendordata.vendor,
                                saveguestdata=Saveadvancebookdata
                            ))

                            # Create an iterator from the queryset
                            roombookadvance_iterator = iter(roombookadvance_data)
                            count=0
                            for room in data['rooms']:
                                roomcatname = room['roomCode']
                                rateplanCode = room['rateplanCode']
                                GuestName = room['guestName']
                                adults =  int(room['occupancy']['adults']) 
                                children = int(room['occupancy']['children'])
                                rateplanname=''
                                roombookadvance = next(roombookadvance_iterator)
                                print(roombookadvance.id,"next data id ")
                                if rateplanCode == 'null':
                                    rateplanCode=None
                                else:
                                    if RatePlan.objects.filter(vendor=vendordata.vendor,rate_plan_code=rateplanCode).exists():
                                        plandatas = RatePlan.objects.get(vendor=vendordata.vendor,rate_plan_code=rateplanCode)
                                        rateplanname = plandatas.rate_plan_name
                                    else:
                                        pass
                                
                                # print("  Prices:")
                                totalsell = 0.0
                                for price in room['prices']:
                                    totalsell =  price['sellRate']
                                
                                if  Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                                    available_rooms = Rooms.objects.filter(
                                                vendor=vendordata.vendor,
                                                room_type__category_name=roomcatname
                                            ).exclude(
                                                id__in=Booking.objects.filter(
                                                    Q(check_in_date__lt=checkoutdate) &
                                                    Q(check_out_date__gt=checkindate)
                                                ).values_list('room_id', flat=True)
                                            )
                                    room = available_rooms.first()
                                    
                                    if not room:
                                        room = Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname,checkin=0).exclude(checkin=6).first()
                                    else:
                                        pass
                                    
                                    if roombookadvance.roomno.room_type.category_name==roomcatname:
                                        
                                        roomid = roombookadvance.roomno.id
                                    else:
                                     
                                        roomid = room.id
                                    
                                    RoomBookAdvance.objects.filter(id=roombookadvance.id).update(
                                                saveguestdata=Saveadvancebookdata,
                                                bookingdate=checkindate,
                                                roomno_id=roomid,
                                                bookingguest=guestname,
                                                bookingguestphone=guestphone,
                                                checkoutdate=checkoutdate,
                                                bookingstatus=True,
                                                channal=cnalledata,
                                                totalguest=adults + children,
                                                rateplan_code=rateplanname,
                                                rateplan_code_main=rateplanCode,
                                                guest_name=GuestName,
                                                adults=adults,
                                                children=children,
                                                sell_rate=totalsell
                                            )

                                                # Handling check-in and check-out times
                                    noon_time_str = "12:00 PM"
                                    noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()

                                    # Create the Booking entry for the room
                                    
                                    bdata = Booking.objects.filter(vendor=vendordata.vendor,advancebook=Saveadvancebookdata)
                                    idsb = []
                                    for i in bdata:
                                         idsb.append(i.id)
                                    bids = idsb[count]
                                    Booking.objects.filter(vendor=vendordata.vendor,id=bids).update(
                                        vendor=vendordata.vendor,
                                        room_id=roomid,
                                        guest_name=guestname,
                                        check_in_date=checkindate,
                                        check_out_date=checkoutdate,
                                        check_in_time=noon_time,
                                        check_out_time=noon_time,
                                        segment=segment,
                                        totalamount=amountbeforetax,
                                        totalroom=roomcount,
                                        gueststay=None,
                                        advancebook=Saveadvancebookdata,
                                        status="BOOKING"
                                    )
                                    count+=1

                                    

                                    try:
                                        catdatas = RoomsCategory.objects.get(vendor_id=vendordata.vendor.id,category_name=roomcatname)
                                        # Convert check-in and check-out dates to date objects if they are strings
                                        checkindate = datetime.strptime(str(checkindate), '%Y-%m-%d').date()
                                        checkoutdate = datetime.strptime(str(checkoutdate), '%Y-%m-%d').date()
                                        mcheckoutdate = datetime.strptime(str(mcheckoutdate), '%Y-%m-%d').date()
                                        checkoutdates = checkoutdate - timedelta(days=1)  # Exclude the last day for range

                                        print(Saveadvancebookdata.bookingdate , checkindate , Saveadvancebookdata.checkoutdate , mcheckoutdate , roombookadvance.roomno.room_type.id,catdatas.id)
                                        if Saveadvancebookdata.bookingdate == checkindate and Saveadvancebookdata.checkoutdate == mcheckoutdate and roombookadvance.roomno.room_type.id==catdatas.id:
                                            pass
                                            
                                        else:
                                            oldcheckoutdate = Saveadvancebookdata.checkoutdate - timedelta(days=1) 
                                            olds_inventory = RoomsInventory.objects.filter(
                                                vendor=vendordata.vendor,
                                                room_category=roombookadvance.roomno.room_type,
                                                date__range=[Saveadvancebookdata.bookingdate, oldcheckoutdate]
                                            )

                                            
                                            for inventory in olds_inventory:
                                                if inventory.booked_rooms > 0:  # Ensure there is at least 1 booked room to remove
                                                    # Remove old booking data for this date
                                                    inventory.booked_rooms -= 1
                                                    inventory.total_availibility += 1  # Restore availability
                                                    
                                                    # Recalculate occupancy safely
                                                    if (inventory.booked_rooms + inventory.total_availibility) > 0:
                                                        inventory.occupancy = (inventory.booked_rooms * 100) // (inventory.booked_rooms + inventory.total_availibility)
                                                    else:
                                                        inventory.occupancy = 0  # If no rooms are booked or available, set occupancy to 0

                                                    inventory.save()

                                            all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                            # Query the RoomsInventory model to check if records exist for all those dates
                                            existing_inventory = RoomsInventory.objects.filter(vendor=vendordata.vendor,room_category=catdatas, date__range=[checkindate,checkoutdates])
                                            print(existing_inventory,"check here chandan")
                                            # Get the list of dates that already exist in the inventory
                                            existing_dates = set(existing_inventory.values_list('date', flat=True))

                                            # Identify the missing dates by comparing all_dates with existing_dates
                                            missing_dates = [date for date in all_dates if date not in existing_dates]

                                            # If there are missing dates, create new entries for those dates in the RoomsInventory model
                                            
                                            for inventory in existing_inventory:
                                                if inventory.total_availibility > 0:  # Ensure there's at least 1 room available
                                                    inventory.total_availibility -= 1  # Decrease available rooms
                                                    inventory.booked_rooms += 1  # Increase booked rooms
                                                    
                                                    # Calculate occupancy dynamically
                                                    inventory.occupancy = (inventory.booked_rooms * 100) // (inventory.booked_rooms + inventory.total_availibility)
                                                    
                                                    inventory.save()
                                            
                                            
                                            
                                            totalrooms = Rooms.objects.filter(vendor=vendordata.vendor, room_type=catdatas).exclude(checkin=6).count()

                                            # Handle division by zero
                                            if totalrooms > 0:
                                                occupancccy = (1 * 100) // totalrooms  # Assuming 1 room booked
                                            else:
                                                occupancccy = 0  # No rooms available, so occupancy is 0%

                                            mrooms = totalrooms - 1
                                            print(all_dates,"all dates here")
                                            print(missing_dates,"missind dates")
                                            if missing_dates:
                                                for missing_date in missing_dates:
                                                        print(missing_date,"missing date")
                                                        RoomsInventory.objects.create(
                                                            vendor=vendordata.vendor,
                                                            date=missing_date,
                                                            room_category=catdatas,  # Use the appropriate `roomtype` or other identifier here
                                                            total_availibility=mrooms,       # Set according to your logic
                                                            booked_rooms=1,    
                                                            occupancy=occupancccy,
                                                            price=catdatas.catprice
                                                                                    # Set according to your logic
                                                        )

                                                print(f"Missing dates have been created for: {missing_dates}")
                                            else:
                                                print("All dates already exist in the inventory.")
                                            



                                        

                                    except Exception as e:
                                        print(f"An error occurred: {str(e)}")
                                        pass
                                    
                            userids = vendordata.vendor.id
                            if VendorCM.objects.filter(vendor=vendordata.vendor):
                                        start_date = str(checkindate)
                                        end_date = str(checkoutdates)
                                        thread = threading.Thread(target=update_inventory_task, args=(userids, start_date, end_date))
                                        thread.start()
                                        # for dynamic pricing
                                        if  VendorCM.objects.filter(vendor=vendordata.vendor,dynamic_price_active=True):
                                            thread = threading.Thread(target=rate_hit_channalmanager, args=(userids, start_date, end_date))
                                            thread.start()
                                        else:
                                            pass
                            else:
                                        pass
                            return JsonResponse({'success': True, 'message': 'Reservation Modified Successfully'})
                        else:
                             return JsonResponse({'success': True, 'message': 'Reservation Not Found!'})
                        
                        
                elif action=='cancel':
                        hotelCode = data['hotelCode']
                        bookingIds = data['bookingId']
                        vendordata = VendorCM.objects.get(hotelcode=hotelCode)
                        channel = data['channel']
                        cnalledata = onlinechannls.objects.get(vendor=vendordata.vendor, channalname=channel)
                        
                        exists = SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor,booking_id=bookingIds,channal=cnalledata).exclude(action='cancel').exists()

                        if exists:
                                
                                user = vendordata.vendor
                                saveguestid=SaveAdvanceBookGuestData.objects.get(vendor=vendordata.vendor,booking_id=bookingIds,channal=cnalledata)
                                roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid).all()
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

                                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel')
                                    Booking.objects.filter(vendor=user,advancebook_id=saveguestid.id).delete()
                                    return JsonResponse({'success': True, 'message': 'Reservation Cancelled Successfully'})
                        else:
                            return JsonResponse({'success': True, 'message': 'Reservation Cancelled Already'})
                        
                            
                       
            else:
                 
                return JsonResponse({'success': True, 'message': 'Hotel Code Not Exists!'})

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format: %s", e)
            return JsonResponse({'success': False, 'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            logger.error("Error in new reservation function: %s", e)
            return JsonResponse({'success': False, 'message': 'An error occurred.'}, status=500)


