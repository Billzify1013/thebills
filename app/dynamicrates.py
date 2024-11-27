from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from datetime import datetime, timedelta, date
import calendar
import threading
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages

def rate_push(request):
        if request.user.is_authenticated:
            user = request.user
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
            return redirect('homepage')  # Replace 'homepage' with your actual URL name
        else:
            return JsonResponse({"success": False, "message": "User is not authenticated."}, status=403)




# def rate_hit_channalmanager(user_id, start_date_str, end_date_str):
#     try:
#             user = User.objects.get(id=user_id)  # Ensure the user exists
#             if not user.is_authenticated:
#                 print("User is not authenticated.")
#                 return
#             current_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#             while current_date <= end_date:
#                 print(f"Processing date: {current_date}")

#                 current_date += timedelta(days=1)

#             print("succesfully dynamic rate",user)
#             # print(start_date_str)
#             # roomscat = RoomsCategory.objects.filter(vendor=user)
#             # current_date = datetime.now().date() + timedelta(days=2)

#             # roomsdata = []
#             # for category in roomscat:
#             #     if RoomsInventory.objects.filter(vendor=user,date=current_date,room_category=category):
#             #         roomdata = RoomsInventory.objects.get(vendor=user,date=current_date,room_category=category)
#             #         roomcount = Rooms.objects.filter(vendor=user,room_type=category).exclude(checkin=6).count()
#             #         print(roomcount)

#             #         occupancy = (roomdata.booked_rooms* 100//roomcount)
#             #         print(occupancy,"occupany in category",category)

#             # print(type(roomsdata))
                  
#             # Your existing logic for updating inventory goes here

#             # Call your inventory update function
#             success = update_rates_cm(user, start_date_str, end_date_str)
            
           
#     except Exception as e:
#             print(f"Error occurred: {str(e)}")


# def update_rates_cm(user, start_date_str, end_date_str):
#     # try:
#         # Fetch room categories for the vendor
#         room_categories = RoomsCategory.objects.filter(vendor=user)
#         inventory_updates = []
#         print("succesfully ru by chandan dynamic rate",user)

from decimal import Decimal
import requests

# def rate_hit_channalmanager(user_id, start_date_str, end_date_str):
#     try:
#         user = User.objects.get(id=user_id)  # Ensure the user exists
#         if not user.is_authenticated:
#             print("User is not authenticated.")
#             return
        
#         print("Starting dynamic rate update for user:", user)
#         start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#         end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

#         roomscat = RoomsCategory.objects.filter(vendor=user)
        
#         # Loop over each day in the date range
#         current_date = start_date
#         while current_date <= end_date:
            
#             print(f"Processing date: {current_date}")
#             for category in roomscat:
#                 total_rooms = Rooms.objects.filter(vendor=user, room_type=category).exclude(checkin=6).count()
#                 # Try to fetch the inventory record for this date and category
#                 room_inventory = RoomsInventory.objects.filter(
#                     vendor=user, 
#                     date=current_date, 
#                     room_category=category
#                 ).first()
                
#                 # If no inventory record exists, create one with default values
#                 if not room_inventory:
                    
#                     room_inventory = RoomsInventory.objects.create(
#                         vendor=user,
#                         room_category=category,
#                         date=current_date,
#                         total_availibility=total_rooms,
#                         booked_rooms=0,
#                         price=category.catprice,  # Assume `default_price` is a field in `RoomsCategory`
#                         occupancy=0  # Since no rooms are booked
#                     )
#                     print(f"Created new inventory record for {category} on {current_date} with {total_rooms} total rooms available.")
#                 print(category.catprice,'cat price')
#                 # Calculate occupancy based on available data
#                 if room_inventory.total_availibility > 0:
#                     occupancy = (room_inventory.booked_rooms * 100 // total_rooms)
#                     room_inventory.occupancy = occupancy
#                     print(f"Occupancy for {category} on {current_date}: {occupancy}%")
                
#                     # Apply dynamic pricing rules based on occupancy and conditions
#                     if occupancy > 90:
#                         # High demand, high occupancy - Premium pricing
#                         room_inventory.price = category.catprice * Decimal('1.3')  # Increase rate by 30%
#                     elif occupancy > 80:
#                         # Moderate-high demand - Moderate premium pricing
#                         room_inventory.price = category.catprice* Decimal('1.2')  # Increase rate by 20%
#                     elif occupancy > 60:
#                         # Moderate demand - Standard rate with minor increase
#                         room_inventory.price = category.catprice * Decimal('1.15')  # Increase rate by 10%
#                     elif occupancy > 50:
#                         # Moderate demand - Standard rate with minor increase
#                         room_inventory.price = category.catprice * Decimal('1.1')  # Increase rate by 10%
#                     elif occupancy < 30:
#                         # Low occupancy - Last-minute discount to encourage bookings
#                         room_inventory.price = category.catprice * Decimal('0.85')  # Decrease rate by 15%
#                         print('decreaseby 20 per')
#                     elif occupancy < 50:
#                         # Below average occupancy - Light discount
#                         room_inventory.price = category.catprice  # category price
#                         print('decreaseby 10 per')
                    
#                     # Additional conditions for date-based pricing adjustments
#                     days_to_date = (current_date - datetime.now().date()).days
#                     if days_to_date < 7 and occupancy < 40:
#                         print('decreaseby 15 per')
#                         # Last-minute pricing, less than a week away, and low occupancy
#                         room_inventory.price = category.catprice * Decimal('0.85')  # Decrease by 15%
#                     elif days_to_date > 30 and occupancy < 50:
#                         # Early bird pricing for dates over a month away and low occupancy
#                         room_inventory.price = category.catprice * Decimal('0.9')  # Decrease by 10%
#                         print('decreaseby 10 per')
                    

#                     # occupancy update
#                     room_inventory.occupancy = occupancy
#                     # Save the updated inventory
#                     room_inventory.save()
#                     print(f"Updated price for {category} on {current_date}: {room_inventory.price}")
#                 else:
#                     print(f"Total availability for {category} on {current_date} is zero. No occupancy calculation.")
            
#             # Move to the next date
#             current_date += timedelta(days=1)
        
#         # Call your inventory update function for external channel manager integration
#         success = update_rates_cm(user, start_date_str, end_date_str)
#         if success:
#             print("Rates successfully updated in the channel manager.")
#         else:
#             print("Failed to update rates in the channel manager.")
        
#     except Exception as e:
#         print(f"Error occurred: {str(e)}")

# def update_rates_cm(user, start_date_str, end_date_str):
#     try:
#         room_categories = RoomsCategory.objects.filter(vendor=user)
#         inventory_updates = []
#         print("Successfully executed dynamic rate update to channel manager for:", user)
        
#         # Implement any additional logic needed for external channel manager integration here
#         return True
#     except Exception as e:
#         print(f"Error occurred in channel manager update: {str(e)}")
#         return False





# def rate_hit_channalmanager(user_id, start_date_str, end_date_str):
#     try:
#         user = User.objects.get(id=user_id)
#         if not user.is_authenticated:
#             print("User is not authenticated.")
#             return
        
#         print("Starting dynamic rate update for user:", user)
#         start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#         end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
#         roomscat = RoomsCategory.objects.filter(vendor=user)
        
#         vendorcmdata = VendorCM.objects.get(vendor=user)
#         chooseplannumber = vendorcmdata.dynamic_price_plan
#         # Loop over each day in the date range
#         current_date = start_date
#         while current_date <= end_date:
#             for category in roomscat:
#                 total_rooms = Rooms.objects.filter(vendor=user, room_type=category).exclude(checkin=6).count()
#                 room_inventory = RoomsInventory.objects.filter(
#                     vendor=user, date=current_date, room_category=category
#                 ).first()
                
#                 if not room_inventory:
#                     room_inventory = RoomsInventory.objects.create(
#                         vendor=user,
#                         room_category=category,
#                         date=current_date,
#                         total_availibility=total_rooms,
#                         booked_rooms=0,
#                         price=category.catprice,
#                         occupancy=0
#                     )
#                     print(f"Created inventory record for {category} on {current_date} with {total_rooms} rooms.")
                
#                 if room_inventory.total_availibility > 0:
#                     occupancy = (room_inventory.booked_rooms * 100 // total_rooms)
#                     room_inventory.occupancy = occupancy
#                     print(f"Occupancy for {category} on {current_date}: {occupancy}%")
                    
#                     if occupancy > 90:
#                         room_inventory.price = category.catprice * Decimal('1.3')
#                     elif occupancy > 80:
#                         room_inventory.price = category.catprice * Decimal('1.2')
#                     elif occupancy > 60:
#                         room_inventory.price = category.catprice * Decimal('1.15')
#                     elif occupancy > 50:
#                         room_inventory.price = category.catprice * Decimal('1.1')
#                     elif occupancy < 30:
#                         room_inventory.price = category.catprice * Decimal('0.85')
#                     elif occupancy < 50:
#                         room_inventory.price = category.catprice
                    
#                     days_to_date = (current_date - datetime.now().date()).days
#                     if days_to_date < 7 and occupancy < 40:
#                         room_inventory.price = category.catprice * Decimal('0.85')
#                     elif days_to_date > 30 and occupancy < 50:
#                         room_inventory.price = category.catprice * Decimal('0.9')

#                     room_inventory.occupancy = occupancy
#                     room_inventory.save()
#                     print(f"Updated price for {category} on {current_date}: {room_inventory.price}")
#                 else:
#                     room_inventory.occupancy = 100
#                     room_inventory.save()
#             current_date += timedelta(days=1)
        
#         # Call to send updated rates to channel manager
#         success = update_rates_cm(user, start_date, end_date)
#         if success:
#             print("Rates successfully updated in the channel manager.")
#         else:
#             print("Failed to update rates in the channel manager.")
        
#     except Exception as e:
#         print(f"Error occurred: {str(e)}")


def rate_hit_channalmanager(user_id, start_date_str, end_date_str):
    try:
        user = User.objects.get(id=user_id)
        if not user.is_authenticated:
            print("User is not authenticated.")
            return
        
        print("Starting dynamic rate update for user:", user)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        roomscat = RoomsCategory.objects.filter(vendor=user)
        
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
                    occupancy = (room_inventory.booked_rooms * 100 // total_rooms)
                    room_inventory.occupancy = occupancy
                    print(f"Occupancy for {category} on {current_date}: {occupancy}%")
                    
                    days_to_date = (current_date - datetime.now().date()).days

                    # Advanced dynamic pricing strategies
                    

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

# 1st workingcode ike bad rate planpr kam kre kelie new banaya
# def update_rates_cm(user, start_date, end_date):
#     try:
#         room_categories = RoomsCategory.objects.filter(vendor=user)
#         inventory_updates = []
        
#         current_date = start_date
#         while current_date <= end_date:
#             daily_update = {
#                 "startDate": current_date.strftime('%Y-%m-%d'),
#                 "endDate": current_date.strftime('%Y-%m-%d'),
#                 "rates": []
#             }
            
#             for category in room_categories:
#                 inventory = RoomsInventory.objects.filter(
#                     vendor=user, 
#                     room_category=category, 
#                     date=current_date
#                 ).first()
#                 RatePlan.objects.filter(vendor=user,room_category=category)
#                 if inventory:
#                     rate_data = {
#                         "roomCode": category.category_name,
#                         "rate": float(inventory.price),
#                         "rateplanCode": f"{category.category_name}-S-101",
#                         "restrictions": {
#                             "stopSell": False,
#                             "minimumStay": 1,
#                             "closeOnArrival": False,
#                             "closeOnDeparture": False,
#                         }
#                     }
#                     daily_update["rates"].append(rate_data)
            
#             inventory_updates.append(daily_update)
#             current_date += timedelta(days=1)
        
#         # API payload
#         payload = {
#             "hotelCode": "SANDBOX-PMS",
#             "updates": inventory_updates
#         }
        
#         # API request
#         response = requests.post(
#             "https://live.aiosell.com/api/v2/cm/update-rates/sample-pms",
#             json=payload
#         )
        
#         if response.status_code == 200:
#             print("Successfully sent rate update to API.")
#             return True
#         else:
#             print("Failed to send rate update to API:", response.status_code, response.text)
#             return False
        
#     except Exception as e:
#         print(f"Error in channel manager update: {str(e)}")
#         return False
    


# rate plan work ke liye new code
def update_rates_cm(user, start_date, end_date):
    try:
        room_categories = RoomsCategory.objects.filter(vendor=user)
        inventory_updates = []
        
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
                            "restrictions": {
                                "stopSell": False,
                                "minimumStay": 1,
                                "closeOnArrival": False,
                                "closeOnDeparture": False,
                            }
                        }
                        daily_update["rates"].append(rate_data)
            
            # Only add the update if rates data is present
            if daily_update["rates"]:
                inventory_updates.append(daily_update)
            
            current_date += timedelta(days=1)
        
        # API payload
        payload = {
            "hotelCode": "SANDBOX-PMS",
            "updates": inventory_updates
        }
        
        # API request
        response = requests.post(
            "https://live.aiosell.com/api/v2/cm/update-rates/sample-pms",
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
























































# Here's an easy-to-understand explanation of each plan (1–6) to help you choose the best strategy to increase your hotel revenue:

# 1. Early Bird Advantage
# Overview: This plan rewards early bookings by giving discounts on bookings made well in advance.
# How It Works: Prices drop by 10-15% for bookings made over 30 days in advance. It also raises prices as occupancy rises, so if occupancy is above 80%, prices go up by 20-30%.
# Best For: Hotels that want to fill rooms early and secure bookings in advance.
# Benefit: Helps you secure guests early and set high rates for last-minute bookings.
# Consideration: May reduce flexibility for last-minute bookings, as early bookings can fill up rooms faster.
# 2. Seasonal Demand Boost
# Overview: Adjusts rates based on seasonal demands and weekday occupancy patterns.
# How It Works: Prices automatically increase during peak seasons or high-demand periods. Weekdays have corporate discounts, and weekends see rate increases of 10-20%.
# Best For: Hotels in areas with clear high and low seasons, or hotels that see a lot of business travelers on weekdays.
# Benefit: Maximizes profit during high seasons and weekends while keeping rates attractive on weekdays.
# Consideration: Might need careful monitoring to avoid overly high rates during off-peak times.
# 3. Family & Group Discounts
# Overview: Encourages group bookings with flexible discounts for families or multiple rooms.
# How It Works: Prices are discounted by 5-15% for bookings with multiple rooms or family bookings, while maintaining regular prices for single-room bookings. Occupancy adjustments increase rates as rooms fill up.
# Best For: Hotels catering to family or group travelers who book multiple rooms at once.
# Benefit: Attracts larger groups, boosting overall occupancy and revenue.
# Consideration: Can lead to smaller individual margins but fills multiple rooms faster.
# 4. Flexible Last-Minute Offers
# Overview: Balances early-bird and last-minute offers for flexible pricing based on booking time.
# How It Works: Prices drop by 10-15% for bookings made last minute if occupancy is low. Early-booking discounts apply for reservations over 30 days out, with price increases based on occupancy.
# Best For: Hotels that want to maximize revenue from both early and last-minute bookings.
# Benefit: Keeps rooms occupied by balancing early and late bookings.
# Consideration: Requires adjustments if occupancy fluctuates, to avoid overbooking or underpricing.
# 5. High-Occupancy Surge
# Overview: Targets maximum revenue on high-occupancy days with strong price increases.
# How It Works: Prices increase by 20-30% if occupancy is above 80%, while low-occupancy days have slight discounts.
# Best For: Hotels that regularly reach high occupancy and want to maximize profits on these days.
# Benefit: Drives high revenue on days when demand is already strong.
# Consideration: May reduce affordability for certain guests during peak periods.
# 6. High Occupancy and Flexible Pricing
# Overview: Balances high-occupancy pricing with last-minute offers to attract guests even when occupancy is low.
# How It Works: Rates increase up to 30% with high occupancy, while last-minute bookings have up to a 15% discount if occupancy is low. Early-booking discounts are also available for guests booking over 30 days ahead.
# Best For: Hotels looking for maximum flexibility and to fill rooms last-minute.
# Benefit: Provides flexibility for both early and late bookings, maximizing revenue based on occupancy trends.
# Consideration: Can lead to high price swings; requires careful monitoring of booking patterns.
# Choosing the Right Plan
# Each of these plans offers unique ways to boost revenue:

# For early bookings: Plan 1 (Early Bird Advantage).
# For seasonal demand: Plan 2 (Seasonal Demand Boost).
# For family/group bookings: Plan 3 (Family & Group Discounts).
# For both early and last-minute flexibility: Plan 4 (Flexible Last-Minute Offers).
# For high occupancy periods: Plan 5 (High-Occupancy Surge).
# For occupancy-based flexibility: Plan 6 (High Occupancy and Flexible Pricing).
# Choose the strategy that best fits your hotel’s needs and booking patterns to increase revenue effectively.



def dynamicformpage(request):
    if request.user.is_authenticated:
        user=request.user
        if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
            datas = VendorCM.objects.filter(vendor=user,admin_dynamic_active=True).first()
            return render(request,'dynamicformpage.html',{'datas':datas})
        
def dynamicformdata(request):
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
    

def rateplanpage(request):
    if request.user.is_authenticated :
        user = request.user 
        bookingplan = RatePlanforbooking.objects.filter(vendor=user)
        roomcat = RoomsCategory.objects.filter(vendor=user)
        roomsdata = RatePlan.objects.filter(vendor=user)
        return render(request,'rateplanpage.html',{'bookingplan':bookingplan,'roomcat':roomcat,'roomsdata':roomsdata})
    

def addbookingrateplan(request):
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


def deleteplanbookingcode(request,id):
    if request.user.is_authenticated :
        user = request.user 
        id=id
        if RatePlanforbooking.objects.filter(vendor=user,id=id).exists():
            RatePlanforbooking.objects.filter(vendor=user,id=id).delete()
            messages.success(request,"Rate Plan Deleted")
        else:
            pass

        return redirect('rateplanpage')
    
 
   
def addrateplan(request):
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


def deleteplanratecode(request,id):
    if request.user.is_authenticated :
        user = request.user 
        id=id
        if RatePlan.objects.filter(vendor=user,id=id).exists():
            RatePlan.objects.filter(vendor=user,id=id).delete()
            messages.success(request,"Main Rate Plan Deleted")
        else:
            pass

        return redirect('rateplanpage')
    

def guestplans(request):
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