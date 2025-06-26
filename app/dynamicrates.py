from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from datetime import datetime, timedelta, date
import calendar
import threading
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages

def rate_push(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            start_date = datetime.now().date()
            end_date = start_date +  timedelta(days=10)
            start_date=str(start_date)
            end_date = str(end_date)
            # start_date = request.POST.get('startDate', '2024-10-22')
            # end_date = request.POST.get('endDate', '2024-10-30')
            if VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                # Start the long-running task in a separate thread
                thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                thread.start()
            
            # Redirect to the desired page immediately
            messages.success(request,"Rates has been started successfully.")
            return redirect('homepage')  # Replace 'homepage' with your actual URL name
        else:
            messages.success(request,"User is not authenticated.")
            return redirect('loginpage')
      
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)





from decimal import Decimal
import requests



def rate_hit_channalmanager(user_id, start_date_str, end_date_str):
    try:
        user = User.objects.get(id=user_id)
        if not user.is_authenticated:
            print("User is not authenticated.")
            return
        
        print("Starting dynamic rate update for user:", user)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        roomscat = RoomsCategory.objects.filter(vendor=user,is_not_active=False)
        
        vendorcmdata = VendorCM.objects.get(vendor=user)
        chooseplannumber = vendorcmdata.dynamic_price_plan

        current_date = start_date
        while current_date <= end_date:
            for category in roomscat:
                total_rooms = Rooms.objects.filter(vendor=user, room_type=category).exclude(checkin=6).count()
                room_inventory = RoomsInventory.objects.filter(
                    vendor=user, date=current_date, room_category=category
                ).first()
                
                if not room_inventory:
                    room_inventory = RoomsInventory.objects.create(
                        vendor=user,
                        room_category=category,
                        date=current_date,
                        total_availibility=total_rooms,
                        booked_rooms=0,
                        price=category.catprice,
                        occupancy=0
                    )
                    print(f"Created inventory record for {category} on {current_date} with {total_rooms} rooms.")
                
                if room_inventory.total_availibility > 0:
                    # occupancy = (room_inventory.booked_rooms * 100 // total_rooms)
                    # room_inventory.occupancy = occupancy
                    # print(f"Occupancy for {category} on {current_date}: {occupancy}%")
                    # Check to avoid division by zero
                    if total_rooms > 0:
                        occupancy = (room_inventory.booked_rooms * 100 // total_rooms)
                    else:
                        occupancy = 0  # Default occupancy when total_rooms is zero

                    room_inventory.occupancy = occupancy
                    print(f"Occupancy for {category} on {current_date}: {occupancy}%")

                    
                    days_to_date = (current_date - datetime.now().date()).days

                    # Advanced dynamic pricing strategies
                    
                    if VendorCM.objects.filter(vendor=user,dynamic_price_active=True).exists():
                        if chooseplannumber == 1:
                            print("Plan 7: Maximum Price with Decreasing Adjustments")

                            # Set the maximum price based on the room category
                            max_price = category.catprice

                            # Apply decreasing adjustments to the price based on occupancy levels
                            if occupancy > 90:
                                room_inventory.price = max_price  # Highest price (no change)
                            elif occupancy > 70:
                                room_inventory.price = max_price * Decimal('0.9')  # 10% discount
                            elif occupancy > 50:
                                room_inventory.price = max_price * Decimal('0.8')  # 20% discount
                            elif occupancy > 30:
                                room_inventory.price = max_price * Decimal('0.7')  # 30% discount
                            else:
                                room_inventory.price = max_price * Decimal('0.6')  # 40% discount for very low occupancy

                        elif chooseplannumber == 2:
                            print("Plan 7: Maximum Price with Decreasing Adjustments")

                            # Set the maximum price based on the room category
                            max_price = category.catprice

                            # Apply decreasing adjustments to the price based on occupancy levels
                            if occupancy > 90:
                                room_inventory.price = max_price  # Highest price (no change)
                            elif occupancy > 70:
                                room_inventory.price = max_price * Decimal('0.9')  # 10% discount
                            elif occupancy > 50:
                                room_inventory.price = max_price * Decimal('0.8')  # 20% discount
                            elif occupancy > 30:
                                room_inventory.price = max_price * Decimal('0.7')  # 30% discount
                            else:
                                room_inventory.price = max_price * Decimal('0.6')  # 40% discount for very low occupancy

                            

                            # Apply weekend increase
                            if current_date.weekday() >= 5:
                                currentprice = room_inventory.price 
                                currentprice *= Decimal('1.2')  
                                if  currentprice>max_price:
                                    room_inventory.price = max_price 
                                else:
                                    room_inventory.price  *= Decimal('1.2') #current price pr 20% ka amount add kiya

                        elif chooseplannumber == 3:
                            print("Plan 7: Maximum Price with Decreasing Adjustments")

                            # Set the maximum price based on the room category
                            max_price = category.catprice

                            # Apply decreasing adjustments to the price based on occupancy levels
                            if occupancy > 90:
                                room_inventory.price = max_price  # Highest price (no change)
                            elif occupancy > 70:
                                room_inventory.price = max_price * Decimal('0.95')  # 5% discount
                            elif occupancy > 50:
                                room_inventory.price = max_price * Decimal('0.9')  # 10% discount
                            elif occupancy > 30:
                                room_inventory.price = max_price * Decimal('0.85')  # 15% discount
                            else:
                                room_inventory.price = max_price * Decimal('0.8')  # 20% discount for very low occupancy


                        elif chooseplannumber == 4:
                            print("Plan 7: Maximum Price with Decreasing Adjustments")

                            # Set the maximum price based on the room category
                            max_price = category.catprice

                            # Apply decreasing adjustments to the price based on occupancy levels
                            if occupancy > 90:
                                room_inventory.price = max_price  # Highest price (no change)
                            elif occupancy > 70:
                                room_inventory.price = max_price * Decimal('0.95')  # 5% discount
                            elif occupancy > 50:
                                room_inventory.price = max_price * Decimal('0.9')  # 10% discount
                            elif occupancy > 30:
                                room_inventory.price = max_price * Decimal('0.85')  # 15% discount
                            else:
                                room_inventory.price = max_price * Decimal('0.8')  # 20% discount for very low occupancy

                            # Apply weekend increase
                            if current_date.weekday() >= 5:
                                currentprice = room_inventory.price 
                                currentprice *= Decimal('1.1')  
                                if  currentprice>max_price:
                                    room_inventory.price = max_price 
                                else:
                                    room_inventory.price  *= Decimal('1.1') #current pr 10% amountadd kiya

                        room_inventory.save()
                    else:
                        pass
                    print(f"Updated price for {category} on {current_date}: {room_inventory.price}")
                else:
                    room_inventory.occupancy = 100
                    room_inventory.save()
            current_date += timedelta(days=1)
        
        # Call to send updated rates to channel manager
        success = update_rates_cm(user, start_date, end_date)
        if success:
            print("Rates successfully updated in the channel manager.")
        else:
            print("Failed to update rates in the channel manager.")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")




# rate plan work ke liye new code
def update_rates_cm(user, start_date, end_date):
    try:
        room_categories = RoomsCategory.objects.filter(vendor=user,is_not_active=False)
        inventory_updates = []
        print(end_date,"en date")
        
        current_date = start_date
        while current_date <= end_date:
            daily_update = {
                "startDate": current_date.strftime('%Y-%m-%d'),
                "endDate": current_date.strftime('%Y-%m-%d'),
                "rates": []
            }
            
            for category in room_categories:
                inventory = RoomsInventory.objects.filter(
                    vendor=user, 
                    room_category=category, 
                    date=current_date
                ).first()
                
                # Fetch all rate plans for the current room category
                rate_plans = RatePlan.objects.filter(vendor=user, room_category=category)
                
                # If there are no rate plans, skip this category
                if not rate_plans.exists():
                    continue
                
                # Loop through each rate plan and prepare rate data
                for rate_plan in rate_plans:
                    if inventory:
                        
                        rate_data = {
                            "roomCode": category.category_name,
                            "rate": float(inventory.price+rate_plan.base_price),
                            "rateplanCode": rate_plan.rate_plan_code,
                           
                        }
                        daily_update["rates"].append(rate_data)
            
            # Only add the update if rates data is present
            if daily_update["rates"]:
                inventory_updates.append(daily_update)
            
            current_date += timedelta(days=1)
        
        vdrcode = VendorCM.objects.get(vendor=user)
        hotelcode = vdrcode.hotelcode
        # API payload
        payload = {
            "hotelCode": hotelcode,
            "updates": inventory_updates
        }
        
        # API request and its testing api
        # response = requests.post(
        #     "https://live.aiosell.com/api/v2/cm/update-rates/sample-pms",
        #     json=payload
        # )

        # its workingon local thats why abhi band krde
        response = requests.post(
            "https://live.aiosell.com/api/v2/cm/update-rates/billzify",
            json=payload
        )
        
        if response.status_code == 200:
            print("Successfully sent rate update to API.")
            return True
        else:
            print("Failed to send rate update to API:", response.status_code, response.text)
            return False
        
    except Exception as e:
        print(f"Error in channel manager update: {str(e)}")
        return False

























































def dynamicformpage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                datas = VendorCM.objects.filter(vendor=user,admin_dynamic_active=True).first()
                return render(request,'dynamicformpage.html',{'datas':datas})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def dynamicformdata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            planname = int(request.POST.get('planname', 0))
            
            # Check if the checkbox data is present in the POST request
            checkboxs = request.POST.get('checkboxs', None)

            # If the checkbox is present (checked), update the field to True
            if checkboxs:
                VendorCM.objects.filter(vendor=user).update(
                    dynamic_price_active=True,
                    dynamic_price_plan=planname
                )
                print("Checkbox is checked and dynamic_price_active is set to True")
                
            else:
                VendorCM.objects.filter(vendor=user).update(
                    dynamic_price_active=False,
                    dynamic_price_plan=planname
                )
                print("Checkbox is unchecked and dynamic_price_active is set to False")

            return redirect('dynamicformpage')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def rateplanpage(request):
    try:
        if request.user.is_authenticated :
            user = request.user 
            bookingplan = RatePlanforbooking.objects.filter(vendor=user)
            roomcat = RoomsCategory.objects.filter(vendor=user)
            roomsdata = RatePlan.objects.filter(vendor=user)
            return render(request,'rateplanpage.html',{'bookingplan':bookingplan,'roomcat':roomcat,'roomsdata':roomsdata})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    

def addbookingrateplan(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            planname = request.POST.get('planname')
            plancode = request.POST.get('plancode')
            planprice = float(request.POST.get('planprice'))

            if RatePlanforbooking.objects.filter(vendor=user,rate_plan_name=planname).exists():
                messages.error(request,"Rate Plan Already exists")
            else:
                RatePlanforbooking.objects.create(
                    vendor=user,
                    rate_plan_name=planname,
                    rate_plan_code=plancode,
                    base_price=planprice
                )
                messages.success(request,"Rate Plan Created")

            return redirect('rateplanpage')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def deleteplanbookingcode(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user 
            id=id
            if RatePlanforbooking.objects.filter(vendor=user,id=id).exists():
                RatePlanforbooking.objects.filter(vendor=user,id=id).delete()
                messages.success(request,"Rate Plan Deleted")
            else:
                pass

            return redirect('rateplanpage')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
 
   
def addrateplan(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            selectcat = request.POST.get('selectcat')
            planname = request.POST.get('planname')
            plancode = request.POST.get('plancode')
            planprice = float(request.POST.get('planprice'))
            maxperson = request.POST.get('maxperson')
            maxhild = request.POST.get('maxhild')
            addprice = float(request.POST.get('addprice'))
            description = request.POST.get('description')
            roomscat=RoomsCategory.objects.get(id=selectcat)
            if RatePlan.objects.filter(vendor=user,rate_plan_code=plancode,room_category=roomscat).exists():
                messages.error(request,"Rate Plan Already exists")
            else:
                RatePlan.objects.create(
                    vendor=user,
                    room_category=roomscat,
                    rate_plan_name=planname,
                    rate_plan_code=plancode,
                    base_price=planprice,
                    additional_person_price=addprice,
                    max_persons=maxperson,
                    childmaxallowed=maxhild,
                    rate_plan_description=description,
                )
                messages.success(request,"Main Rate Plan Created")

            return redirect('rateplanpage')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def deleteplanratecode(request,id):
    try:
        if request.user.is_authenticated :
            user = request.user 
            id=id
            if RatePlan.objects.filter(vendor=user,id=id).exists():
                RatePlan.objects.filter(vendor=user,id=id).delete()
                messages.success(request,"Main Rate Plan Deleted")
            else:
                pass

            return redirect('rateplanpage')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    

def guestplans(request):
    try:
        if request.user.is_authenticated :
            user = request.user 
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            today = datetime.now().date()
            query1 = Gueststay.objects.filter(
                vendor=user,
                checkindate__lte=today_end,
                checkoutdate__gte=today_start,
                checkoutdone=False,

            )

        

            room_advance_data = {}
            for guest in query1:
                if guest.saveguestid:
                    room_advance = RoomBookAdvance.objects.filter(saveguestdata__id=guest.saveguestid)
                    room_names = [room.roomno.room_name for room in room_advance]
                    room_advance_data[guest.id] = room_names
            print(room_advance_data)

            guestdata = Gueststay.objects.filter(
                vendor=user,
                checkindate__lte=today_end,
                checkoutdate__gte=today_start,
                checkoutdone=False,
                saveguestid__isnull=True
            )
            print(guestdata,'filter null')

            saveguest_ids = query1.values_list('saveguestid', flat=True)

            # Filter RoomBookAdvance based on the list of saveguest_ids
            room_advance = RoomBookAdvance.objects.filter(saveguestdata__id__in=saveguest_ids,checkinstatus=True)
            print(room_advance,'bokroms data')

            return render(request,'rateplancheckin.html',{'query1':query1,'active_page': 'guestplans',
                    'room_advance_data':room_advance_data,'today':today,'room_advance':room_advance,
                    'guestdata':guestdata
                    
                    })  
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)