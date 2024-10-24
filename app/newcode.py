from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from datetime import datetime, timedelta, date
import calendar

# def gridview(request):
#     if request.user.is_authenticated:
#         user = request.user
#         items = Items.objects.filter(vendor=user)
#         return render(request,'gridviews.html',{'active_page':'gridview','items':items})
    
def gridview(request):
    if request.user.is_authenticated:
        user = request.user
        
        # Step 1: Get the current month and year
        today = datetime.today()
        current_year = today.year
        current_month = today.month
        room_cat = RoomsCategory.objects.filter(vendor=user).last()
        room_type = room_cat.id
        cat_name = room_cat.category_name
        

        # Step 2: Get the number of days in the current month and first weekday
        num_days_in_month = calendar.monthrange(current_year, current_month)[1]  # e.g., 31 for October
        first_weekday_of_month = calendar.monthrange(current_year, current_month)[0]  # 0 = Monday, 6 = Sunday

        # Generate a list of all dates in the current month
        all_dates = [datetime(current_year, current_month, day).date() for day in range(1, num_days_in_month + 1)]

        # Step 3: Query the RateInventory model for the current month and room type
        room_inventory_data = RoomsInventory.objects.filter(
            room_category_id=room_type,
            date__year=current_year,
            date__month=current_month
        )

        # Create a dictionary to store the data by date
        room_data_by_date = {inventory.date: inventory for inventory in room_inventory_data}

        # Prepare data for the template (inventory for each date)
        inventory_for_template = []
        for date in all_dates:
            if date in room_data_by_date:
                inventory = room_data_by_date[date]
                inventory_for_template.append({
                    'date': date,
                    'available_rooms': inventory.total_availibility,
                    'booked_rooms': inventory.booked_rooms
                })
            else:
                # If no data exists for that date, just show empty availability
                inventory_for_template.append({
                    'date': date,
                    'available_rooms': None,  # or 0
                    'booked_rooms': None  # or 0
                })

        # Add empty slots at the beginning based on the first day of the month
        empty_slots = first_weekday_of_month  # Number of empty days at the start of the month
        room_categorys = RoomsCategory.objects.filter(vendor=user)
        context = {
            'inventory_for_template': inventory_for_template,
            'empty_slots': empty_slots,  # Pass the empty slots to the template
            'room_type': cat_name,
            'current_month': today.strftime('%B'),  # e.g., 'October'
            'current_year': current_year,
            'weekdays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],  # Weekdays
            'room_categorys':room_categorys
        }

        return render(request, 'gridviews.html', context)
    

def gridviewviasearch(request):
    if request.user.is_authenticated and request.method == 'POST':
        user = request.user
        month_year_str = request.POST.get('monthyear')
        categry = request.POST.get('category')
        year, month = map(int, month_year_str.split('-'))

            # Now you can use `year` and `month` separately
        print(f"Year: {year}, Month: {month} by form")
        # Step 1: Get the current month and year
        today = datetime.today()
        current_year = year
        current_month = month
        room_cat = RoomsCategory.objects.get(vendor=user,id=categry)
        room_type = room_cat.id
        cat_name = room_cat.category_name
        

        # Step 2: Get the number of days in the current month and first weekday
        num_days_in_month = calendar.monthrange(current_year, current_month)[1]  # e.g., 31 for October
        first_weekday_of_month = calendar.monthrange(current_year, current_month)[0]  # 0 = Monday, 6 = Sunday

        # Generate a list of all dates in the current month
        all_dates = [datetime(current_year, current_month, day).date() for day in range(1, num_days_in_month + 1)]

        # Step 3: Query the RateInventory model for the current month and room type
        room_inventory_data = RoomsInventory.objects.filter(
            room_category_id=room_type,
            date__year=current_year,
            date__month=current_month
        )

        # Create a dictionary to store the data by date
        room_data_by_date = {inventory.date: inventory for inventory in room_inventory_data}

        # Prepare data for the template (inventory for each date)
        inventory_for_template = []
        for date in all_dates:
            if date in room_data_by_date:
                inventory = room_data_by_date[date]
                inventory_for_template.append({
                    'date': date,
                    'available_rooms': inventory.total_availibility,
                    'booked_rooms': inventory.booked_rooms
                })
            else:
                # If no data exists for that date, just show empty availability
                inventory_for_template.append({
                    'date': date,
                    'available_rooms': None,  # or 0
                    'booked_rooms': None  # or 0
                })

        # Add empty slots at the beginning based on the first day of the month
        empty_slots = first_weekday_of_month  # Number of empty days at the start of the month
        room_categorys = RoomsCategory.objects.filter(vendor=user)
        context = {
            'inventory_for_template': inventory_for_template,
            'empty_slots': empty_slots,  # Pass the empty slots to the template
            'room_type': cat_name,
            'current_month': today.strftime('%B'),  # e.g., 'October'
            'current_year': current_year,
            'weekdays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],  # Weekdays
            'room_categorys':room_categorys
        }

        return render(request, 'gridviews.html', context)



import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt




# chandan starts here

import threading
import time
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.models import User

def inventory_push(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            user = request.user
            start_date = request.POST.get('startDate', '2024-10-22')
            end_date = request.POST.get('endDate', '2024-10-30')
            print(start_date,end_date,'by chandan sir')
            # Start the long-running task in a separate thread
            thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
            thread.start()
            
            # Redirect to the desired page immediately
            return redirect('homepage')  # Replace 'homepage' with your actual URL name
        else:
            return JsonResponse({"success": False, "message": "User is not authenticated."}, status=403)

    return JsonResponse({"success": False, "message": "Only POST requests are allowed."}, status=405)


def update_inventory_task(user_id, start_date_str, end_date_str):
    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        try:
            user = User.objects.get(id=user_id)  # Ensure the user exists
            if not user.is_authenticated:
                print("User is not authenticated.")
                return
            
            # Your existing logic for updating inventory goes here
            print(f"Attempt {attempt + 1}: Updating inventory for user {user.username}")

            # Call your inventory update function
            success = update_inventory(user, start_date_str, end_date_str)
            
            if success:
                print("Inventory updated successfully.")
                break  # Exit loop if successful
            else:
                print("Failed to update inventory, will retry...")
        
        except Exception as e:
            print(f"Error occurred: {str(e)}")
        
        attempt += 1
        time.sleep(2)  # Wait before retrying

    if attempt == max_attempts:
        print("Max attempts reached. Inventory update failed.")




def update_inventory(user, start_date_str, end_date_str):
    try:
        # Fetch room categories for the vendor
        room_categories = RoomsCategory.objects.filter(vendor=user)
        inventory_updates = []

        # Parse start and end dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Loop through each day in the range
        date_range = (end_date - start_date).days
        for day in range(date_range + 1):
            current_date = start_date + timedelta(days=day)
            
            # Loop through each room category and build the inventory data
            for category in room_categories:
                inventory = RoomsInventory.objects.filter(vendor=user, room_category=category, date=current_date).first()
                
                if not inventory:
                    # If no inventory is found, use total rooms of the category
                    room_count = Rooms.objects.filter(vendor=user, room_type=category).count()
                    available_rooms = room_count
                else:
                    available_rooms = inventory.total_availibility
                
                # Build the room inventory data for this category for the specific date
                room_data = {
                    "available": available_rooms,
                    "roomCode": category.category_name,
                    "restrictions": {
                        "stopSell": False,
                        "minimumStay": 1,
                        "closeOnArrival": False,
                        "closeOnDeparture": False
                    }
                }

                # Add the inventory update for this specific date and room category
                inventory_updates.append({
                    "startDate": str(current_date),
                    "endDate": str(current_date),
                    "rooms": [room_data]
                })

        # Prepare the data to send to the external API
        vndorcms = VendorCM.objects.get(vendor=user)
        hotelscodecm = vndorcms.hotelcode
        data = {
            "hotelCode": hotelscodecm,  # Update this with your actual hotel code
            "updates": inventory_updates
        }
        
        # Send the request to the external API
        url = "https://live.aiosell.com/api/v2/cm/update/sample-pms"  # Update with the actual API endpoint
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success"):
            print("Inventory updated successfully.last function")
            return True  # Indicate that the update was successful
        else:
            print(f"Failed to update inventory: {response_data.get('message', 'Unknown error')}")
            return False  # Indicate that the update failed

    except Exception as e:
        print(f"Error occurred while updating inventory: {str(e)}")
        return False  # Indicate that an error occurred
    






from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime
from .models import MainBooking, MBRoom, User, onlinechannls

@csrf_exempt
def booking_webhook(request):
    if request.user.is_authenticated and request.method=="POST":
            
        try:
            user=request.user
            # Parse the incoming JSON data
            data = json.loads(request.body)

            # Fetch the vendor using the provided hotelCode (Assuming you have a field in User for hotelCode)
            vendor = user  # Adjust this query based on your model

            # Fetch the channel (for example, 'Goingo')
            if onlinechannls.objects.get(channalname=data['channel']):
                channel = onlinechannls.objects.get(channalname=data['channel'])
            else:
                channel = onlinechannls.objects.create(channalname=data['channel'],channal_img='')

            # Create the main booking
            booking = MainBooking.objects.create(
                vendor=vendor,
                guest_name=f"{data['guest']['firstName']} {data['guest']['lastName']}",
                email=data['guest']['email'],
                phone=data['guest']['phone'],
                address_city=data['guest']['address']['city'],
                state=data['guest']['address']['state'],
                country=data['guest']['address']['country'],
                action=data['action'],
                channal=channel,
                booking_id=data['bookingId'],
                cm_booking_id=data['cmBookingId'],
                booked_on=datetime.strptime(data['bookedOn'], '%Y-%m-%d %H:%M:%S'),
                checkin=datetime.strptime(data['checkin'], '%Y-%m-%d').date(),
                checkout=datetime.strptime(data['checkout'], '%Y-%m-%d').date(),
                segment=data['segment'],
                special_requests=data.get('specialRequests', ''),
                pah=data['pah'],
                amount_after_tax=data['amount']['amountAfterTax'],
                amount_before_tax=data['amount']['amountBeforeTax'],
                tax=data['amount']['tax'],
                currency=data['amount']['currency'],
            )

            # Loop through rooms and store each room's data
            for room_data in data['rooms']:
                for price in room_data['prices']:
                    MBRoom.objects.create(
                        vendor=vendor,
                        main_booking=booking,
                        room_code=room_data['roomCode'],
                        rateplan_code=room_data['rateplanCode'],
                        guest_name=room_data['guestName'],
                        adults=room_data['occupancy']['adults'],
                        children=room_data['occupancy']['children'],
                        date=datetime.strptime(price['date'], '%Y-%m-%d').date(),
                        sell_rate=price['sellRate'],
                    )

            return JsonResponse({"success": True, "message": "Booking saved successfully"}, status=201)

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": False, "message": "Only POST method allowed"}, status=405)



import requests
from datetime import datetime
from .models import MainBooking, MBRoom, User, onlinechannls

def fetch_and_save_bookings(request):
    url = "https://sample-pms.com/update_reservation"  # API endpoint
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_KEY",  # Include API key if required
    }
    

    response = requests.get(url, headers=headers)
    data = response.json()

    # Process and store the booking data
    try:
        if request.user.is_authenticated :
            
       
            user=request.user
            vendor = user
            channel = onlinechannls.objects.get(name=data['channel'])

            booking = MainBooking.objects.create(
                vendor=vendor,
                guest_name=f"{data['guest']['firstName']} {data['guest']['lastName']}",
                email=data['guest']['email'],
                phone=data['guest']['phone'],
                address_city=data['guest']['address']['city'],
                state=data['guest']['address']['state'],
                country=data['guest']['address']['country'],
                action=data['action'],
                channal=channel,
                booking_id=data['bookingId'],
                cm_booking_id=data['cmBookingId'],
                booked_on=datetime.strptime(data['bookedOn'], '%Y-%m-%d %H:%M:%S'),
                checkin=datetime.strptime(data['checkin'], '%Y-%m-%d').date(),
                checkout=datetime.strptime(data['checkout'], '%Y-%m-%d').date(),
                segment=data['segment'],
                special_requests=data.get('specialRequests', ''),
                pah=data['pah'],
                amount_after_tax=data['amount']['amountAfterTax'],
                amount_before_tax=data['amount']['amountBeforeTax'],
                tax=data['amount']['tax'],
                currency=data['amount']['currency'],
            )

            for room_data in data['rooms']:
                for price in room_data['prices']:
                    MBRoom.objects.create(
                        vendor=vendor,
                        main_booking=booking,
                        room_code=room_data['roomCode'],
                        rateplan_code=room_data['rateplanCode'],
                        guest_name=room_data['guestName'],
                        adults=room_data['occupancy']['adults'],
                        children=room_data['occupancy']['children'],
                        date=datetime.strptime(price['date'], '%Y-%m-%d').date(),
                        sell_rate=price['sellRate'],
                    )
    except Exception as e:
        print(f"Error: {e}")
