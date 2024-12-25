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
                    print(data)

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
                            
                            for room in data['rooms']:
                                roomcatname = room['roomCode']
                                rateplanCode = room['rateplanCode']
                                GuestName = room['guestName']
                                adults =  int(room['occupancy']['adults']) 
                                children = int(room['occupancy']['children'])

                                if rateplanCode == 'null':
                                    rateplanCode=None
                                else:
                                    # if RatePlan.objects.filter(vendor=vendordata.vendor,rate_plan_code=rateplanCode).exists():
                                    #     plandatas = RatePlan.objects.filter(vendor=vendordata.vendor,rate_plan_code=rateplanCode)
                                    #     planname = ''
                                    #     for i in plandatas:
                                    #          planname=i.rate_plan_name
                                    #     rateplanCode = planname +", "+rateplanCode
                                    # else:
                                        pass
                                
                                # print("  Prices:")
                                totalsell = 0.0
                                for price in room['prices']:
                                    totalsell = totalsell + price['sellRate']

                                if  Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname).exists():
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
                                        room = Rooms.objects.filter(vendor=vendordata.vendor,room_type_category_name=roomcatname,checkin=0).first()
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
                                                rateplan_code=rateplanCode,
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
                                    checkoutdate = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))

                                    # Generate the list of all dates between check-in and check-out (inclusive)
                                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                                    existing_inventory = RoomsInventory.objects.filter(vendor=vendordata.vendor,room_category=catdatas, date__in=all_dates)

                                    # Get the list of dates that already exist in the inventory
                                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                                    # Identify the missing dates by comparing all_dates with existing_dates
                                    missing_dates = [date for date in all_dates if date not in existing_dates]

                                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                                    roomcount = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).exclude(checkin=6).count()
                                    print(roomcount,'total room')
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
                                        end_date = str(checkoutdate)
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
                           

                            return JsonResponse({'success': True, 'message': 'Reservation Updated Successfully'})
                            
                
                elif action=='modify':
                        
                        return JsonResponse({'success': True, 'message': 'Reservation Modified Successfully'})
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
                                            print(checkindate)
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


