from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from datetime import datetime, timedelta, date
import calendar

    

def gridview(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            
            # Get the current month and year
            today = datetime.today()
            current_year = today.year
            current_month = today.month
            


            
            room_cat = RoomsCategory.objects.filter(vendor=user).last()
            room_type = room_cat.id
            cat_name = room_cat.category_name
            
        
            # Get the selected room category
            room_cat = RoomsCategory.objects.get(vendor=user, id=room_type)
            room_type = room_cat.id
            cat_name = room_cat.category_name

            # Get number of days and first weekday of the selected month and year
            num_days_in_month = calendar.monthrange(current_year, current_month)[1]
            first_weekday_of_month = calendar.monthrange(current_year, current_month)[0]  # 0=Monday, 6=Sunday

            # Generate a list of dates in the selected month
            all_dates = [datetime(current_year, current_month, day).date() for day in range(1, num_days_in_month + 1)]

            # Query the RoomsInventory model based on selected month and room type
            room_inventory_data = RoomsInventory.objects.filter(
                room_category_id=room_type,
                date__year=current_year,
                date__month=current_month
            )

            # Create a dictionary to store inventory data by date
            room_data_by_date = {inventory.date: inventory for inventory in room_inventory_data}

            # Prepare data for each date, filling missing dates with default values
            inventory_for_template = []
            for date in all_dates:
                if date in room_data_by_date:
                    inventory = room_data_by_date[date]
                    inventory_for_template.append({
                        'date': date,
                        'available_rooms': inventory.total_availibility,
                        'booked_rooms': inventory.booked_rooms,
                        'price': inventory.price,
                        'occupancy': inventory.occupancy,
                    
                    })
                else:
                    inventory_for_template.append({
                        'date': date,
                        'available_rooms': None,
                        'booked_rooms': None,
                        'price': None,
                        'occupancy': None,
                        
                    })

            # Adjust the first weekday to align with a Sunday start
            empty_slots = (first_weekday_of_month + 1) % 7  # Shift to match a Sunday start

            # Get room categories for the dropdown or other purposes
            room_categorys = RoomsCategory.objects.filter(vendor=user)

            # Prepare context for the template
            context = {
                'active_page':'gridview',
                'inventory_for_template': inventory_for_template,
                'empty_slots_range': range(empty_slots),  # Use range directly for empty slots
                'room_type': cat_name,
                'current_month': calendar.month_name[current_month],  # Display selected month name
                'current_year': current_year,
                'weekdays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'room_categorys': room_categorys
            }

            return render(request, 'gridviews.html', context)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def gridviewviasearch(request):
    try:
        if request.user.is_authenticated and request.method == 'POST':
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            month_year_str = request.POST.get('monthyear')
            categry = request.POST.get('category')

            # Extract year and month from the user's input
            year, month = map(int, month_year_str.split('-'))

       

            # Use the year and month from the input
            current_year = year
            current_month = month

            # Get the selected room category
            room_cat = RoomsCategory.objects.get(vendor=user, id=categry)
            room_type = room_cat.id
            cat_name = room_cat.category_name

            # Get number of days and first weekday of the selected month and year
            num_days_in_month = calendar.monthrange(current_year, current_month)[1]
            first_weekday_of_month = calendar.monthrange(current_year, current_month)[0]  # 0=Monday, 6=Sunday

            # Generate a list of dates in the selected month
            all_dates = [datetime(current_year, current_month, day).date() for day in range(1, num_days_in_month + 1)]

            # Query the RoomsInventory model based on selected month and room type
            room_inventory_data = RoomsInventory.objects.filter(
                room_category_id=room_type,
                date__year=current_year,
                date__month=current_month
            )

            # Create a dictionary to store inventory data by date
            room_data_by_date = {inventory.date: inventory for inventory in room_inventory_data}

            # Prepare data for each date, filling missing dates with default values
            inventory_for_template = []
            for date in all_dates:
                if date in room_data_by_date:
                    inventory = room_data_by_date[date]
                    inventory_for_template.append({
                        'date': date,
                        'available_rooms': inventory.total_availibility,
                        'booked_rooms': inventory.booked_rooms,
                        'price': inventory.price,
                        'occupancy': inventory.occupancy,
                    
                    })
                else:
                    inventory_for_template.append({
                        'date': date,
                        'available_rooms': None,
                        'booked_rooms': None,
                        'price': None,
                        'occupancy': None,
                        
                    })

            # Adjust the first weekday to align with a Sunday start
            empty_slots = (first_weekday_of_month + 1) % 7  # Shift to match a Sunday start

            # Get room categories for the dropdown or other purposes
            room_categorys = RoomsCategory.objects.filter(vendor=user)

            # Prepare context for the template
            context = {
                'active_page':'gridview',
                'inventory_for_template': inventory_for_template,
                'empty_slots_range': range(empty_slots),  # Use range directly for empty slots
                'room_type': cat_name,
                'current_month': calendar.month_name[current_month],  # Display selected month name
                'current_year': current_year,
                'weekdays': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
                'room_categorys': room_categorys
            }

            return render(request, 'gridviews.html', context)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages



# chandan starts here

import threading
import time
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib.auth.models import User




def inventory_push(request):
    try:
        if request.method == 'POST':
            if request.user.is_authenticated:
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                start_date = datetime.now().date()
                end_date = start_date +  timedelta(days=10)
                start_date=str(start_date)
                end_date = str(end_date)
                print(end_date,start_date,"dates")
                # start_date = request.POST.get('startDate', '2024-10-22')
                # end_date = request.POST.get('endDate', '2024-10-30')
                
                # Start the long-running task in a separate thread
                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                thread.start()
                
                # Add a success message
                messages.success(request, "Inventory sync has been started successfully.")
                return redirect('homepage')  # Replace 'homepage' with your actual URL name
            else:
                messages.error(request, "User is not authenticated.")
                return redirect('loginpage')

        messages.error(request, "Only POST requests are allowed.")
        return redirect('homepage')
       
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
    
def update_inventory_task(user_id, start_date_str, end_date_str):
    max_attempts = 1
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
                    room_count = Rooms.objects.filter(vendor=user, room_type=category).exclude(checkin=6).count()
                    available_rooms = room_count
                else:
                    available_rooms = inventory.total_availibility
                
                # Build the room inventory data for this category for the specific date
                
                room_data = {
                    "available": available_rooms,
                    "roomCode": category.category_name,
                    
                }

                # Add the inventory update for this specific date and room category
                inventory_updates.append({
                    "startDate": str(current_date),
                    "endDate": str(current_date),
                    "rooms": [room_data]
                })

        # Prepare the data to send to the external API
        if VendorCM.objects.filter(vendor=user).exists():
            vndorcms = VendorCM.objects.get(vendor=user)
            hotelscodecm = vndorcms.hotelcode
            data = {
                "hotelCode": hotelscodecm,  # Update this with your actual hotel code
                "updates": inventory_updates
            }
            
            # Send the request to the external testing API
            url = "https://live.aiosell.com/api/v2/cm/update/sample-pms"  # Update with the actual API endpoint
            headers = {
                "Content-Type": "application/json"
            }

            # main live url on aiosell
            # url = "https://live.aiosell.com/api/v2/cm/update/billzify"  # Update with the actual API endpoint
            # headers = {
            #     "Content-Type": "application/json"
            # }

            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()
            print(response_data,'response data')
            if response.status_code == 200 and response_data.get("success"):
                print("Inventory updated successfully.last function")
                return True  # Indicate that the update was successful
            else:
                print(f"Failed to update inventory: {response_data.get('message', 'Unknown error')}")
                return False  # Indicate that the update failed
        else:
            return False

    except Exception as e:
        print(f"Error occurred while updating inventory: {str(e)}")
        return False  # Indicate that an error occurred
    



