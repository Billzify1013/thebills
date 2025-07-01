from django.shortcuts import render, redirect,HttpResponse , get_object_or_404
from . models import *
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
import threading
import datetime
from .dynamicrates import *
from .newcode import *
from datetime import date
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db.models import F
from django.urls import reverse

from django.db.models import IntegerField
from django.db.models.functions import Cast
from datetime import datetime, timedelta
from .email import *


def priceshow_new_cm(request):
    """ Display inventory prices dynamically based on selected date """

    if not request.user.is_authenticated:
        return redirect('loginpage')

    user = request.user

    # Handle subuser case
    subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
    if subuser:
        user = subuser.vendor  

    # Get selected start date (default: today)
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.now().date()  # Fallback if invalid date format
    else:
        selected_date = datetime.now().date()

    # Generate date range (10 days from selected date)
    date_range = [selected_date + timedelta(days=i) for i in range(10)]

    # Fetch inventory data for the selected date range
    inventory_data = RoomsInventory.objects.filter(
        vendor=user,
        date__range=(selected_date, date_range[-1])
    ).order_by('room_category', 'date')

    # Get all room categories
    categories = RoomsCategory.objects.filter(vendor=user)

    # Prepare data to display in the template
    inventory_list = []
    for category in categories:
        row = {'category': category.category_name, 'price_data': {}}
        for date in date_range:
            # Find existing price in the inventory
            existing_price = next(
                (item.price for item in inventory_data if item.room_category == category and item.date == date),
                None
            )
            row['price_data'][date] = existing_price if existing_price is not None else category.catprice
        inventory_list.append(row)

    context = {
        'date_range': date_range,
        'inventory_list': inventory_list,
        'selected_date': selected_date,
        'today': datetime.now().date(),  # Ensure 'min' in date picker works properly
        'active_page':'priceshow_new'
    }

    return render(request, 'webratedate_cm.html', context)


def change_date_new_cm(request):
    """ Handles date picker selection """
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            datetime.strptime(selected_date_str, "%Y-%m-%d")  # Validate date format
            return redirect(f"/priceshow_new_cm/?start_date={selected_date_str}")
        except ValueError:
            pass  # Invalid date, fallback to default
    return redirect("/priceshow_new_cm/")

def next_day_new_cm(request):
    """ Handles 'Next Day' button click """

    # Ensure we get a valid date, fallback to today if missing
    selected_date_str = request.GET.get('start_date')
    if not selected_date_str:
        selected_date = datetime.now().date()
    else:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.now().date()

    next_date = selected_date + timedelta(days=1)
    return redirect(f"/priceshow_new_cm/?start_date={next_date.strftime('%Y-%m-%d')}")


# inventory work start

def inventory_view_cm(request):
    if not request.user.is_authenticated:
        return redirect('loginpage')

    user = request.user

    # Handle subuser case
    subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
    if subuser:
        user = subuser.vendor  

    # Get selected start date (default: today)
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.now().date()  # Fallback if invalid date format
    else:
        selected_date = datetime.now().date()

    # Generate date range (7 days from selected date)
    date_range = [selected_date + timedelta(days=i) for i in range(10)]

    # Fetch inventory data for the selected date range
    inventory_data = RoomsInventory.objects.filter(
        vendor=user,
        date__range=(selected_date, date_range[-1])
    ).order_by('room_category', 'date')

    # Get all room categories
    categories = RoomsCategory.objects.filter(vendor=user)

    # Prepare data to display in the template
    inventory_list = []
    for category in categories:
        row = {'category': category.category_name, 'availability_data': {}}
        for date in date_range:
            # Find existing availability in the inventory
            existing_availability = next(
                (item.total_availibility for item in inventory_data if item.room_category == category and item.date == date),
                None
            )
            roomct = Rooms_count.objects.filter(vendor=user, room_type=category).values_list('total_room_numbers', flat=True).first() or 0
            row['availability_data'][date] = existing_availability if existing_availability is not None else roomct
        inventory_list.append(row)

    context = {
        'date_range': date_range,
        'inventory_list': inventory_list,
        'selected_date': selected_date,
        'today': datetime.now().date(),  # Ensure 'min' in date picker works properly
        'active_page':'inventory_view'
    }

    return render(request, 'webinventory_cm.html', context)


def next_day_inventory_cm(request):
    """ Handles 'Next Day' button click """

    # Ensure we get a valid date, fallback to today if missing
    selected_date_str = request.GET.get('start_date')
    if not selected_date_str:
        selected_date = datetime.now().date()
    else:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = datetime.now().date()

    next_date = selected_date + timedelta(days=1)
    return redirect(f"/inventory_view_cm/?start_date={next_date.strftime('%Y-%m-%d')}")

def change_date_inventory_cm(request):
    """ Handles date picker selection """
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            datetime.strptime(selected_date_str, "%Y-%m-%d")  # Validate date format
            return redirect(f"/inventory_view_cm/?start_date={selected_date_str}")
        except ValueError:
            pass  # Invalid date, fallback to default
    return redirect("/inventory_view_cm/")





# tds commision work
def ota_Commission_cm(request):
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
            print(booking)
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

        return render(request, 'otacommisioon_cm.html', context)
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


# save rates

def save_prices_new_cm(request):
    """ Save inventory prices submitted from the form """

    if not request.user.is_authenticated:
        return redirect('loginpage')

    if request.method == "POST":
        user = request.user

        # Handle subuser case
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  

        

        # Get selected start date from the form
        selected_date_str = request.POST.get('selected_date')
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format!")
                return redirect('priceshow_new_cm')
        else:
            selected_date = datetime.now().date()

        


        # Generate date range (Fix: Use form-submitted date)
        date_range = [selected_date + timedelta(days=i) for i in range(10)]

        enddate = selected_date + timedelta(days=9)
        print("check this dates",selected_date,enddate)

        # Fetch all categories
        categories = RoomsCategory.objects.filter(vendor=user)

        # Process form data and update inventory
        for category in categories:
            for date in date_range:
                price_key = f"price_{category.category_name}_{date.strftime('%Y-%m-%d')}"
                price = request.POST.get(price_key, "").strip()

                if price:  # Ensure price is not empty
                    try:
                        price = float(price)
                    except ValueError:
                        continue  # Skip invalid price values
                
                    # Update or create inventory entry
                    if RoomsInventory.objects.filter(vendor=user,room_category=category,date=date).exists():
                        RoomsInventory.objects.filter(
                            vendor=user,
                            room_category=category,
                            date=date
                        ).update(
                            price = price
                        )

                    else:
                        # rcount=Rooms_count.objects.filter(vendor=user,room_type=category)
                        rcount = Rooms_count.objects.filter(vendor=user, room_type=category).values_list('total_room_numbers', flat=True).first() or 0



                        RoomsInventory.objects.create(
                            vendor=user,
                            room_category=category,
                            date=date,
                            booked_rooms=0,
                            total_availibility=rcount,
                            price=price,
                            occupancy=0
                        )
                        


                    # Debugging Output
                    # print(f"Updated: {date} | Category: {category.category_name} | Price: {price}")
        if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                start_date = str(selected_date)
                end_date = str(enddate)
                    
                    # for dynamic pricing
                if  VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                        thread = threading.Thread(target=rate_hit_channalmanager_cm, args=(user.id, start_date, end_date))
                        thread.start()
                else:
                        pass
        else:
            messages.error(request, "Your Permission is Denied via Admin,but booking Engine prices changed succesfully!")
            return redirect(f"/priceshow_new_cm/?start_date={selected_date.strftime('%Y-%m-%d')}")
        start_date = str(selected_date)
        end_date = str(enddate)
        logsdesc = f"Update Rates For All Category, From {start_date} To {end_date}"
        bulklogs.objects.create(vendor=user,by=request.user,action="Update Rates",
                    description = logsdesc)
        messages.success(request, "Prices updated successfully!")
        return redirect(f"/priceshow_new_cm/?start_date={selected_date.strftime('%Y-%m-%d')}")

    return redirect('priceshow_new_cm')




def rate_hit_channalmanager_cm(user_id, start_date_str, end_date_str):
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
                # total_rooms = Rooms.objects.filter(vendor=user, room_type=category).exclude(checkin=6).count()
                total_rooms = Rooms_count.objects.filter(vendor=user, room_type=category).values_list('total_room_numbers', flat=True).first() or 0
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








def create_roomcount(request):
        if not request.user.is_authenticated:
            return render(request, 'login.html')

        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor
        roomdata = Rooms_count.objects.filter(vendor=user)
        category = RoomsCategory.objects.filter(vendor=user)
        total_rooms = Rooms_count.objects.filter(vendor=user).aggregate(total=Sum('total_room_numbers'))['total'] or 0
        return render(request,'create_roomcount.html',{'roomdata':roomdata,'category':category,
                      'total_rooms':total_rooms})

def addroomcount(request):
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            category_id = request.POST.get('category')
            rooms = request.POST.get('rooms')
            if RoomsCategory.objects.filter(vendor=user,id=category_id).exists():
                category = RoomsCategory.objects.get(vendor=user,id=category_id)
                if Rooms_count.objects.filter(vendor=user,room_type=category).exists():
                    Rooms_count.objects.filter(vendor=user,room_type=category).update(
                        total_room_numbers=rooms
                    )
                    messages.success(request,'Category Already Exists! But changed the room count ')

                else:
                    Rooms_count.objects.create(vendor=user,room_type=category,
                        total_room_numbers=rooms
                    )
                    messages.success(request,'Data Created ')
            else:
                messages.error(request,'Category is not found ')

            return redirect('create_roomcount')
        
        else:
            return render(request, 'login.html')
        



def save_inventory_new_cm(request):
    """ Save inventory prices submitted from the form """

    if not request.user.is_authenticated:
        return redirect('loginpage')

    if request.method == "POST":
        user = request.user

        # Handle subuser case
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  

        # Get selected start date
        selected_date_str = request.POST.get('selected_date')
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date() if selected_date_str else datetime.now().date()
        except ValueError:
            messages.error(request, "Invalid date format!")
            return redirect('inventory_view_cm')

        # Check if vendor has permission
        if not VendorCM.objects.filter(vendor=user, inventory_active=True).exists():
            messages.error(request, "Your Permission is Denied via Admin")
            return redirect(f"/inventory_view_cm/?start_date={selected_date.strftime('%Y-%m-%d')}")

        # Generate date range (7 days)
        date_range = [selected_date + timedelta(days=i) for i in range(10)]
        enddate = selected_date + timedelta(days=9)

        # Fetch all categories
        categories = RoomsCategory.objects.filter(vendor=user).all()

        # Process form data and update inventory
        for category in categories:
            category_name_safe = category.category_name.replace(" ", "_")  # Remove spaces
            for date in date_range:
                price_key = f"availability_{category_name_safe}_{date.strftime('%Y-%m-%d')}"
                price = request.POST.get(price_key, "").strip()
                print(price)
                if price:
                    try:
                        price = int(price)  # Convert to integer
                    except ValueError:
                        continue  # Skip invalid values

                    # Check if inventory exists
                    inventory_item = RoomsInventory.objects.filter(
                        vendor=user, room_category=category, date=date
                    ).first()

                    if inventory_item:
                        inventory_item.total_availibility = price
                        inventory_item.save()
                        print(f"Updated: {category.category_name} | Date: {date} | Availability: {price}")
                    else:
                        RoomsInventory.objects.create(
                            vendor=user,
                            room_category=category,
                            date=date,
                            booked_rooms=0,
                            total_availibility=price,
                            price=category.catprice,
                            occupancy=0
                        )
                        print(f"Created: {category.category_name} | Date: {date} | Availability: {price}")

        if VendorCM.objects.filter(vendor=user):
                start_date = str(selected_date)
                end_date = str(enddate)
                thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                thread.start()
                    # for dynamic pricing
               
        else:
            pass

        start_date = str(selected_date)
        end_date = str(enddate)
        logsdesc = f"Update Inventory For All Category, From {start_date} To {end_date}"
        bulklogs.objects.create(vendor=user,by=request.user,action="Update Inventory",
                    description = logsdesc)

        messages.success(request, "Inventory updated successfully!")
        return redirect(f"/inventory_view_cm/?start_date={selected_date.strftime('%Y-%m-%d')}")

    else:
        messages.error(request, "Method Not Exists!")
        return redirect('inventory_view_cm')
    


def sync_inventory_cm(request):
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
                thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                thread.start()
                print(start_date, end_date)
                # Add a success message
                messages.success(request, "Inventory sync has been started successfully.") 
                bulklogs.objects.create(vendor=user,by=request.user,action="sync inventory",
                        description=f"Inventory Update From {start_date} to {end_date} ")
                return redirect('inventory_view_cm') 
            else:
                rinvdata=None
            return redirect('inventory_view_cm')
        return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

 
def update_inventory_task_cm(user_id, start_date_str, end_date_str):
    max_attempts = 1
    attempt = 0
    print("haan cm chala")
    while attempt < max_attempts:
        try:
            user = User.objects.get(id=user_id)  # Ensure the user exists
            if not user.is_authenticated:
                print("User is not authenticated.")
                return
            
            # Your existing logic for updating inventory goes here
            print(f"Attempt {attempt + 1}: Updating inventory for user {user.username}")

            # Call your inventory update function
            success = update_inventory_cm(user, start_date_str, end_date_str)
            
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




def update_inventory_cm(user, start_date_str, end_date_str):
    print("haan 2nd cm chala")
    try:
        # Fetch room categories for the vendor
        room_categories = RoomsCategory.objects.filter(vendor=user,is_not_active=False)
        inventory_updates = []
        print(room_categories,'check category in cm')
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
                    room_count = Rooms_count.objects.filter(vendor=user, room_type=category).values_list('total_room_numbers', flat=True).first() or 0
                    
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
        if VendorCM.objects.filter(vendor=user,inventory_active=True).exists():
            vndorcms = VendorCM.objects.get(vendor=user)
            hotelscodecm = vndorcms.hotelcode
            data = {
                "hotelCode": hotelscodecm,  # Update this with your actual hotel code
                "updates": inventory_updates
            }
            
            # Send the request to the external testing API
            # url = "https://live.aiosell.com/api/v2/cm/update/sample-pms"  # Update with the actual API endpoint
            # headers = {
            #     "Content-Type": "application/json"
            # }

            # main live url on aiosell
            url = "https://live.aiosell.com/api/v2/cm/update/billzify"  # Update with the actual API endpoint
            headers = {
                "Content-Type": "application/json"
            }

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
    


def bulkinventoryform_cm(request):
    # try:
        if request.user.is_authenticated and request.method == "POST":
            # Get the selected category IDs
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            selected_ids = request.POST.getlist('selected_categories')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
           

            # Query the selected categories from the database
            selected_categories = RoomsCategory.objects.filter(vendor=user, id__in=selected_ids)
        
          

            # Prepare category_data with availability values
            category_data = {}
            categoryogs = []
            for category_id in selected_categories:
                # Check if availability input exists for this category
                availability_key = f'catavaibility_{category_id.id}'
                availability_value = request.POST.get(availability_key, None)

                if availability_value:  # Ensure value is not None or empty
                    category_data[category_id.id] = int(availability_value)  # Store as integer
                    categoryogs.append(f"{category_id.category_name} {int(availability_value)} ")

            # अब category_data में IDs और उनकी availability वैल्यू हैं
      

            # Parse the start and end dates
            checkindate = datetime.strptime(startdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(enddate, '%Y-%m-%d').date()

            # Generate the list of all dates between check-in and check-out (inclusive)
            all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

            

            for roomtype in selected_categories:  # Iterate through all selected categories
                # Query the RoomsInventory model to check if records exist for all those dates
                existing_inventory = RoomsInventory.objects.filter(
                    vendor=user, room_category_id=roomtype.id, date__in=all_dates
                )

                

                # Get the list of dates that already exist in the inventory
                existing_dates = set(existing_inventory.values_list('date', flat=True))
                

                # Identify the missing dates by comparing all_dates with existing_dates
                missing_dates = [date for date in all_dates if date not in existing_dates]

                # Get the total room count for the current category
                # roomcount = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()
                roomcount = Rooms_count.objects.filter(vendor=user, room_type_id=roomtype.id).values_list('total_room_numbers', flat=True).first() or 0

                # Get availability value for the current category from category_data
                availability_value = category_data.get(roomtype.id, roomcount)  # Default to roomcount if not provided
                print(availability_value,'check this')
                # Deduct availability and update bookings for existing inventory
                for inventory in existing_inventory:
                    trms = inventory.booked_rooms
                    if trms==0:
                        trms=1
                    else:
                        pass
                    if availability_value==0:
                        occupncies=100
                    else:
                        occupncies = (trms*100//availability_value)
                    inventory.total_availibility = availability_value  # Update with the provided value
                    inventory.occupancy=occupncies
                    inventory.save()

                # Fetch category data
                catdatas = RoomsCategory.objects.get(vendor=user, id=roomtype.id)
                # totalrooms = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()
                totalrooms = Rooms_count.objects.filter(vendor=user, room_type_id=roomtype.id).values_list('total_room_numbers', flat=True).first() or 0
                occupancy = (1 * 100 // totalrooms) if totalrooms else 0

                # Create missing inventory entries
                if missing_dates:
                    for missing_date in missing_dates:
                        RoomsInventory.objects.create(
                            vendor=user,
                            date=missing_date,
                            room_category_id=roomtype.id,
                            total_availibility=availability_value,  # Use availability from category_data
                            booked_rooms=0,  # Set according to your logic
                            price=catdatas.catprice,
                            occupancy=occupancy
                        )
                    print(f"Missing dates have been created for category {roomtype}: {missing_dates}")
                else:
                    print(f"All dates already exist in the inventory for category {roomtype}.")

            # Trigger background API tasks for the user
            start_date = str(checkindate)
            end_date = str(checkoutdate)
            logsdesc = f"Update inventory For {categoryogs}, From {start_date} To {end_date}"
            bulklogs.objects.create(vendor=user,by=request.user,action="Update Inventory",
                    description = logsdesc)

            if VendorCM.objects.filter(vendor=user):
                start_date = str(checkindate)
                end_date = str(checkoutdate)
                thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                thread.start()
                
            else:
                pass

            messages.success(request, "Inventory Updated Successfully!")
            
            # Do whatever processing is needed, then return a response
            return redirect('bulkupdatecm')
        
        else:
            return render(request, 'login.html')
    # except Exception as e:
    #     return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def bulkformprice_cm(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor

            selected_ids = request.POST.getlist('selected_categories')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            mon = request.POST.get('mon')
            tues = request.POST.get('tues')
            wed = request.POST.get('wed')
            thur = request.POST.get('thur')
            fri = request.POST.get('fri')
            sat = request.POST.get('sat')
            sun = request.POST.get('sun')

            # Check if at least one day is selected
            if not any([mon, tues, wed, thur, fri, sat, sun]):
                messages.error(request, "Please select at least one day.")
                return redirect('bulkupdatecm')

            # Get selected categories
            selected_categories = RoomsCategory.objects.filter(vendor=user, id__in=selected_ids)

            # Prepare category_data with availability values
            category_data = {}
            categoryogs = []
            for category_id in selected_categories:
                availability_key = f'catavaibility_{category_id.id}'
                availability_value = request.POST.get(availability_key, None)
                if availability_value:
                    category_data[category_id.id] = int(availability_value)
                    categoryogs.append(f"{category_id.category_name} {int(availability_value)}")

            # Parse date range
            checkindate = datetime.strptime(startdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(enddate, '%Y-%m-%d').date()

            # Weekday filter map (0=Monday, ..., 6=Sunday)
            weekday_map = {
                0: mon,
                1: tues,
                2: wed,
                3: thur,
                4: fri,
                5: sat,
                6: sun,
            }

            # Generate filtered list of dates based on selected days
            all_dates = []
            for x in range((checkoutdate - checkindate).days + 1):
                current_date = checkindate + timedelta(days=x)
                if weekday_map.get(current_date.weekday()) == "on":
                    all_dates.append(current_date)

            # If no dates match selected days
            if not all_dates:
                messages.warning(request, "No matching dates found for selected weekdays.")
                return redirect('bulkupdatecm')

            # Loop through each selected category
            for roomtype in selected_categories:
                existing_inventory = RoomsInventory.objects.filter(
                    vendor=user, room_category_id=roomtype.id, date__in=all_dates
                )
                existing_dates = set(existing_inventory.values_list('date', flat=True))
                missing_dates = [date for date in all_dates if date not in existing_dates]

                # roomcount = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()
                roomcount = Rooms_count.objects.filter(vendor=user, room_type_id=roomtype.id).values_list('total_room_numbers', flat=True).first() or 0
                availability_value = category_data.get(roomtype.id, roomcount)

                # Update existing inventory
                for inventory in existing_inventory:
                    inventory.price = float(availability_value)
                    inventory.save()

                # Create inventory for missing dates
                totalrooms = roomcount
                occupancy = (1 * 100 // totalrooms) if totalrooms else 0

                for missing_date in missing_dates:
                    RoomsInventory.objects.create(
                        vendor=user,
                        date=missing_date,
                        room_category_id=roomtype.id,
                        total_availibility=totalrooms,
                        booked_rooms=0,
                        price=float(availability_value),
                        occupancy=occupancy
                    )
                    print(f"Created inventory for {missing_date} - {roomtype}")

            # Logging
            logsdesc = f"Update Rates For {categoryogs}, From {startdate} To {enddate}"
            bulklogs.objects.create(
                vendor=user,
                by=request.user,
                action="Update Rates",
                description=logsdesc
            )

            # Background threads for channel manager
            if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                start_date = str(checkindate)
                end_date = str(checkoutdate)
                threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date)).start()
                threading.Thread(target=rate_hit_channalmanager_cm, args=(user.id, start_date, end_date)).start()

                messages.success(request, "Price Updated Successfully!")
            else:
                messages.error(request, "Your Permission is Denied via Admin,but booking Engine prices changed succesfully!")
            return redirect('bulkupdatecm')

        else:
            return render(request, 'login.html')

    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)






def searchguestdataadvance_cm(request):
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
            # advancersoomdata = guests.filter(filters)

            # # If no results found
            # if not advancersoomdata.exists():
            #     messages.error(request, "No matching guests found.")

            from django.db.models import Prefetch
            from collections import Counter
            # new code 
            # ⬇️ Prefetch related room bookings
            # room_prefetch = Prefetch(
            #     'roombookadvance_set',
            #     queryset=RoomBookAdvance.objects.select_related('roomno__room_type'),
            #     to_attr='booked_rooms'
            # )

            # # ⬇️ Apply filters and prefetch
            # advancersoomdata = SaveAdvanceBookGuestData.objects.filter(filters, vendor=user).prefetch_related(room_prefetch)

            # if not advancersoomdata.exists():
            #     messages.error(request, "No matching guests found.")

            # # ⬇️ Attach room summary to each guest
            # for guest in advancersoomdata:
            #     category_names = [
            #         room.roomno.room_type.category_name
            #         for room in guest.booked_rooms
            #     ]
            #     category_counts = Counter(category_names)

            #     guest.room_categories_summary = ", ".join(
            #         f"({count}) {cat}" for cat, count in category_counts.items()
            #     )
            # Prefetch for RoomBookAdvance
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
            advancersoomdata = SaveAdvanceBookGuestData.objects.filter(filters, vendor=user).prefetch_related(
                room_prefetch,
                cm_room_prefetch
            )

            # If no matching records
            if not advancersoomdata.exists():
                messages.error(request, "No matching guests found.")

            # Process each guest's room summary
            for guest in advancersoomdata:
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

            # Return results
            return render(request, 'cm_booking_history.html', {
                'monthbookdata': advancersoomdata,
                'first_day_of_month': checkindate,
                'last_day_of_month': checkoutdate,
                'active_page': 'cmadvancebookhistory',
            })
        else:
            return redirect('loginpage')

    except Exception as e:
        # Handle unexpected errors
        return render(request, '404.html', {'error_message': str(e)}, status=500)



# advance details function
def advancebookingdetails_cm(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            guestdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id)
            roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=id).all()
            bookdatesdata = bookpricesdates.objects.filter(roombook__saveguestdata__id=id).all()
            tdscomm = tds_comm_model.objects.filter(roombook_id=id).first()
            if roomdata:
                pass
            else:
                roomdata=Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=id).all()
            if bookdatesdata:
                pass
            else:
                bookdatesdata = Cm_bookpricesdates.objects.filter(roombook__saveguestdata__id=id).all()
            advancepayment = InvoicesPayment.objects.filter(vendor=user,advancebook_id=id).all()
            return render(request,'advancebookingdetailspage_cm.html',{'roomdata':roomdata,'guestdata':guestdata,'active_page': 'cmadvancebookhistory',
                        'tdscomm':tdscomm,'advancepayment':advancepayment,'bookdatesdata':bookdatesdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def addpaymenttobooking_cm(request,booking_id):
    try:
        if request.user.is_authenticated:
            user=request.user 
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            bookingdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,id=booking_id)
            return render(request,'advanceamt_cm.html',{'bookingdata':bookingdata})
        else:
            return redirect('loginpage')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def addpymenttoboking_cm(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                bokkingid = request.POST.get('bokkingid')
                amount = int(float(request.POST.get('amount')))
                paymentmode = request.POST.get('paymentmode')
                paymntdetails = request.POST.get('paymntdetails')
                comment = request.POST.get('comment')
                today = datetime.now()
                invoicedata = SaveAdvanceBookGuestData.objects.get(vendor=user,id=bokkingid)

                advanceamount = int(invoicedata.advance_amount)
                reaminingamount =int(invoicedata.reamaining_amount)
                
                
                if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid,checkinstatus=False):
                    if amount == reaminingamount:
                        dueamount = reaminingamount - amount
                        acceptamount = advanceamount + amount

                        InvoicesPayment.objects.create(vendor=user,invoice_id=None,payment_amount=amount,
                                    payment_date=today,payment_mode=paymentmode,transaction_id=paymntdetails,
                                    descriptions=comment,advancebook=invoicedata)
                        
                        SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid).update(
                            advance_amount=acceptamount,reamaining_amount=dueamount,Payment_types='prepaid'
                        )

                        actionss = 'Add Payment Advance'
                        CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook_id=bokkingid,description=f'Payment Added As Advance {amount} ')

                        messages.success(request,"Payment added succesfully!")
                        url = reverse('advancebookingdetails_cm', args=[bokkingid])
                        return redirect(url)
            
                    elif amount > reaminingamount:
                        
                        messages.error(request,"amount graterthen to billing amount!")
                        url = reverse('addpaymenttobooking_cm', args=[bokkingid])
                        return redirect(url)
                    
                    else:

                        dueamount = reaminingamount - amount
                        acceptamount = advanceamount + amount
                        InvoicesPayment.objects.create(vendor=user,invoice_id=None,payment_amount=amount,
                                    payment_date=today,payment_mode=paymentmode,transaction_id=paymntdetails,
                                    descriptions=comment,advancebook=invoicedata)
                        
                        SaveAdvanceBookGuestData.objects.filter(vendor=user,id=bokkingid).update(
                            advance_amount=acceptamount,reamaining_amount=dueamount,Payment_types='partially'
                        )

                        actionss = 'Add Payment Advance'
                        CustomGuestLog.objects.create(vendor=user,by=request.user,action=actionss,
                                            advancebook_id=bokkingid,description=f'Payment Added As Advance {amount} ')

                        messages.success(request,"Payment added succesfully!")
                        url = reverse('advancebookingdetails_cm', args=[bokkingid])
                        return redirect(url)

                    
                else:
                    
                    messages.error(request,"Guest are checked in add payment to folio page")
                    return redirect('cm')          
                
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



def edittotalbookingamount_cm(request):
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
                all_rooms = Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=main_guest)
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


                    # extraBookingAmount.objects.filter(vendor=user, bookdata__in=all_rooms).delete()
                    messages.success(request,'Booking amount changed!')
            else:
                messages.error(request,'id not found!')
            return redirect('advancebookingdetails_cm',bid)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def cmnotification(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if hasattr(user, 'subuser_profile'):
                    subuser = user.subuser_profile
                    if not subuser.is_cleaner:
                        # Update main user's notification (for subuser)
                        main_user = subuser.vendor
                        if main_user.is_authenticated:
                            request.session['notification'] = False  # Update main user's session
                            request.session.modified = True
                        # Update subuser's own notification
                        request.session['notification'] = False  # Update subuser's session
                        request.session.modified = True
            else:
                        # If it's a main user, update their notification
                        request.session['notification'] = False
                        request.session.modified = True
            # Get today's date
            # today = timezone.now().date()
           

            
            # advanceroomdata = RoomBookAdvance.objects.filter(vendor=user).all().order_by('bookingdate')
            # old code
            saveadvancebookdata = SaveAdvanceBookGuestData.objects.filter(vendor=user,checkinstatus=False).all().order_by('-id')[:25]
            
            # new code updates
            from collections import Counter
            from django.db.models import Prefetch

            # Prefetch related room data with room type
            # room_prefetch = Prefetch(
            #     'roombookadvance_set',
            #     queryset=RoomBookAdvance.objects.select_related('roomno__room_type'),
            #     to_attr='booked_rooms'
            # )

            # # Apply prefetch
            # saveadvancebookdata = SaveAdvanceBookGuestData.objects.filter(
            #     vendor=user,
            #     checkinstatus=False
            # ).prefetch_related(room_prefetch).order_by('-id')[:25]

            # # Add room category summary to each guest
            # for guest in saveadvancebookdata:
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
            saveadvancebookdata = SaveAdvanceBookGuestData.objects.filter(
                vendor=user,
                checkinstatus=False
            ).prefetch_related(
                room_prefetch,
                cm_room_prefetch
            ).order_by('-id')[:25]

            # If no matching records
            if not saveadvancebookdata.exists():
                messages.error(request, "No matching guests found.")

            # Process each guest's room summary
            for guest in saveadvancebookdata:
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
           
            return render(request,'notify_cm.html',{'saveadvancebookdata':saveadvancebookdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def dashboardcm(request):
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            today =  datetime.now().date()
            total_available = RoomsInventory.objects.filter(
                vendor=user,
                date=today
            ).aggregate(total=Sum('total_availibility'))['total'] or 0

            checkoutids = SaveAdvanceBookGuestData.objects.filter(vendor=user,checkoutdate=today).exclude(action='cancel')
            checout_roombok = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id__in=checkoutids).count()
            checout_roombok += Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id__in=checkoutids).count()

            checkinids = SaveAdvanceBookGuestData.objects.filter(vendor=user,bookingdate=today).exclude(action='cancel')
            checin_roombok = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id__in=checkinids).count()
            checin_roombok += Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id__in=checkinids).count()

            
            return render(request,'bookcmdashboard.html',{'active_page':'dashboardcm','total_available':total_available
                            ,'checout_roombok':checout_roombok,'checin_roombok':checin_roombok,'checkinids':checkinids})

def salescm(request):
        if request.user.is_authenticated:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 

            return render(request,'salescm.html',{'active_page':'salescm'})
# aiosell cmbooking get work here

import json
import logging
import re
from .dynamicrates import *
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore

# Logging setup
logger = logging.getLogger(__name__)
@csrf_exempt
def channel_manager_aiosell_new_reservation(request):
    # if request.method == 'POST':
        try:
            data = json.loads(request.body)  
            print("mera walachala")
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
                    if segment is None:
                         segment ='OTA'
                    else:
                         pass
                    specialRequests = data['specialRequests']
                    pah = str(data['pah'])
                    checkpah = pah.lower()
                    mcheckoutdate=checkoutdate


                    # Convert string dates to datetime objects
                    checkin_date = datetime.strptime(data['checkin'], '%Y-%m-%d')
                    checkout_date = datetime.strptime(data['checkout'], '%Y-%m-%d')

                    day_difference = (checkout_date - checkin_date).days
                    if day_difference==0:
                        day_difference=1
                    else:
                        pass
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
                        # for price in room['prices']:
                        #     print("    Date:", price['date'], "| Rate:", price['sellRate'])

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
                            cnalledata = onlinechannls.objects.filter(vendor=vendordata.vendor, channalname=channel).first()
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
                                is_noshow=False,
                                is_hold=False,
                            )
                            print("yha tk to chal gaya ")
                            # commission = amount_details['commission']
                            # tds = amount_details['tds']
                            # tcs = amount_details['tcs']
                            # if commission=='null':
                            #     commission=0.0
                            # else:
                            #     commission = float(commission)
                            # if tds=='null':
                            #     tds=None
                            # if tcs=='null':
                            #     tcs=None

                            commission = amount_details.get('commission')
                            tds = amount_details.get('tds')
                            tcs = amount_details.get('tcs')

                            # Handle commission
                            if commission is None:
                                commission = 0.0
                            else:
                                commission = float(commission)

                            # Handle tds and tcs
                            tds = float(tds) if tds is not None else None
                            tcs = float(tcs) if tcs is not None else None

                            agodataxamt = taxamount
                            print("yha tk bhi chal gaya ")
                            # commisiion calculation here
                            if channel == "MakeMyTrip" or channel == "Goibibo":
                                extra_mmt_commison = 0
                                extra_mmt_commison = commission * 18/100
                                commission = commission + extra_mmt_commison

                            if channel == "booking.com" :
                                extra_bcom_tds = 0
                                extra_bcom_tds = amountbeforetax * 0.1/100
                                tds = extra_bcom_tds
                            
                            if channel == "AirBNB" :
                                extra_bnb_tds = 0
                                extra_bnb_tds = amountbeforetax * 5/100
                                tds = extra_bnb_tds

                            tdscreate = tds_comm_model.objects.create(roombook=Saveadvancebookdata,
                                        commission=commission,tds=tds,tcs=tcs  )

                            if pahr==False:
                                invcpaymentdata = InvoicesPayment.objects.create(vendor=vendordata.vendor,
                                                advancebook= Saveadvancebookdata,
                                                payment_amount= amountaftertax,
                                                payment_date=bookingdates,
                                                payment_mode='BankTransfer', 
                                                transaction_id='',
                                                descriptions='This Amount From OTA'  )
                            total_tax_amount_main = 0.0
                            total_after_taxamt_bnb = 0.0
                            total_before_taxamt_bnb = 0.0
                            for room in data['rooms']:
                                roomcatname = room['roomCode']
                                rateplanCode = room['rateplanCode']
                                GuestName = room['guestName']
                                adults =  int(room['occupancy']['adults']) 
                                children = int(room['occupancy']['children'])
                                # new
                                newtestroom=room
                                # new end
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
                                    totalsell =  totalsell + price['sellRate']

                                print(totalsell,'total sell for ',room)

                                totalsell = totalsell / int(day_difference)

                                if taxamount == 0.0:
                                    if channel == "AirBNB" :
                                        newtaxamount = 0.0
                                        if totalsell >7500:
                                            newtaxamount = totalsell*18/100
                                            # totalsell = totalsell - newtaxamount
                                        else:
                                            newtaxamount = totalsell*12/100
                                            # totalsell = totalsell - newtaxamount

                                        # checkamtsbnb = (newtaxamount * int(day_difference)) + amountaftertax
                                        total_after_taxamt_bnb = total_after_taxamt_bnb + (newtaxamount * int(day_difference)) + amountaftertax
                                        # checkbeforbnbamt = totalsell * int(day_difference)
                                        total_before_taxamt_bnb = total_before_taxamt_bnb + totalsell * int(day_difference)
                                        total_tax_amount_main = total_tax_amount_main + (newtaxamount * int(day_difference))
                                        newbookmodeltotalamt = total_after_taxamt_bnb
                                        # newtotaltaxamount = newtaxamount * int(day_difference)

                                        # SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_after_tax=checkamtsbnb,
                                        #             total_amount=int(checkamtsbnb),amount_before_tax=checkbeforbnbamt,
                                        #             tax=(newtaxamount * int(day_difference)))
                                        # invcpaymentdata.payment_amount=checkamtsbnb
                                        # invcpaymentdata.save()
                                    
                                         
                                    else:
                                        if totalsell >8851:
                                            totalsell = float(totalsell) / (1 + (18) / 100)

                                        elif totalsell <=8400:
                                            totalsell = float(totalsell) / (1 + (12) / 100)
                                        
                                        newtaxamount = 0.0
                                        if totalsell >7500:
                                            newtaxamount = totalsell*18/100
                                            # totalsell = totalsell - newtaxamount
                                        else:
                                            newtaxamount = totalsell*12/100
                                            # totalsell = totalsell - newtaxamount

                                        newtotaltaxamount = newtaxamount * int(day_difference)
                                        print(newtotaltaxamount,'checkthis amount')
                                        # amountbeforetax = amountbeforetax - newtotaltaxamount
                                        newbookmodeltotalamt = amountaftertax
                                        agodataxamt = newtotaltaxamount
                                        # totaltax amount calculation
                                        total_tax_amount_main = total_tax_amount_main + newtotaltaxamount
                                        # SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(tax=newtotaltaxamount
                                                        # ,amount_before_tax=amountbeforetax)
                                
                                else:
                                    newbookmodeltotalamt = amountaftertax

                                # if  Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname).exclude(checkin=6).exists():
                                #     available_rooms = Rooms.objects.filter(
                                #                 vendor=vendordata.vendor,
                                #                 room_type__category_name=roomcatname
                                #             ).exclude(
                                #                 id__in=Booking.objects.filter(
                                #                     Q(check_in_date__lt=checkoutdate) &
                                #                     Q(check_out_date__gt=checkindate)
                                #                 ).values_list('room_id', flat=True)
                                #             )
                                #     room = available_rooms.first()
                                #     if not room:
                                #         room = Rooms.objects.filter(vendor=vendordata.vendor,room_type__category_name=roomcatname,checkin=0).exclude(checkin=6).first()
                                #     else:
                                #         pass
                                if True:
                                    catdatas = RoomsCategory.objects.get(vendor=vendordata.vendor,category_name=roomcatname)
                                    rbk = Cm_RoomBookAdvance.objects.create(
                                                vendor=vendordata.vendor,
                                                saveguestdata=Saveadvancebookdata,
                                                room_category=catdatas,
                                                bookingguest=guestname,
                                                bookingguestphone=guestphone,
                                                totalguest=adults + children,
                                                rateplan_code=rateplanname,
                                                rateplan_code_main=rateplanCode,
                                                guest_name=GuestName,
                                                adults=adults,
                                                children=children,
                                                sell_rate=totalsell
                                            )
                                    
                                    # for checknew in data['rooms']:
                                    for ckprice in newtestroom['prices']:
                                            date = ckprice['date']
                                            # new work here
                                            if Cm_bookpricesdates.objects.filter(roombook=rbk,date=str(ckprice['date'])):
                                                        pass
                                            else:                      
                                                Cm_bookpricesdates.objects.create(
                                                    roombook=rbk,date=str(ckprice['date']),
                                                    price = float(ckprice['sellRate'])
                                                )

                                    


                                    # Handling check-in and check-out times
                                    # noon_time_str = "12:00 PM"
                                    # noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()

                                    # # Create the Booking entry for the room
                                    # Booking.objects.create(
                                    #     vendor=vendordata.vendor,
                                    #     room=room,
                                    #     guest_name=guestname,
                                    #     check_in_date=checkindate,
                                    #     check_out_date=checkoutdate,
                                    #     check_in_time=noon_time,
                                    #     check_out_time=noon_time,
                                    #     segment=channel,
                                    #     totalamount=newbookmodeltotalamt,
                                    #     totalroom=roomcount,
                                    #     gueststay=None,
                                    #     advancebook=Saveadvancebookdata,
                                    #     status="BOOKING"
                                    # )

                                    
                                
                                    
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
                                    # roomcount = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).count()
                                    roomcount = Rooms_count.objects.filter(vendor=vendordata.vendor, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
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
                                    # totalrooms = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).count()
                                    totalrooms =Rooms_count.objects.filter(vendor=vendordata.vendor, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
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
                            # tax 0 hoto yah update ho total krke 
                            if taxamount == 0.0:
                                if channel == "AirBNB":
                                        SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_after_tax=total_after_taxamt_bnb,
                                                    total_amount=int(total_after_taxamt_bnb),amount_before_tax=total_before_taxamt_bnb,
                                                    tax=total_tax_amount_main,advance_amount=int(total_after_taxamt_bnb))
                                        if invcpaymentdata:
                                            invcpaymentdata.payment_amount=total_after_taxamt_bnb
                                            invcpaymentdata.save()
                                else:
                                    amountbeforetax = amountbeforetax - total_tax_amount_main
                                    SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(tax=total_tax_amount_main
                                                            ,amount_before_tax=amountbeforetax)
                            # agoda commsion checking
                            if channel == 'agoda':
                                # checkagodacomm = total_tax_amount_main + commission + amountaftertax
                                # print(amountaftertax,checkagodacomm,commission)
                                # if amountaftertax < checkagodacomm:
                                #         agodacommissionamt = commission - total_tax_amount_main
                                # elif amountaftertax >= checkagodacomm:
                                agodacommissionamt = commission
                                         
                                tdscreate.commission=agodacommissionamt
                                tdscreate.save()


                            userids = vendordata.vendor.id
                            savidmain = Saveadvancebookdata.id
                            emailthread = threading.Thread(target=sent_success_email, args=(userids, channel, bookingId,guestname,savidmain))
                            emailthread.start()
                            if VendorCM.objects.filter(vendor=vendordata.vendor,):
                                        start_date = str(checkindate)
                                        end_date = str(checkoutdates)
                                        print(end_date)
                                        thread = threading.Thread(target=update_inventory_task_cm, args=(userids, start_date, end_date))
                                        thread.start()
                                        # for dynamic pricing
                                        # if  VendorCM.objects.filter(vendor=vendordata.vendor,dynamic_price_active=True):
                                        #     thread = threading.Thread(target=rate_hit_channalmanager, args=(userids, start_date, end_date))
                                        #     thread.start()
                                        # else:
                                        #     pass
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

                            actionss = 'Create Booking'
                            CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=Saveadvancebookdata,description=f'Booking Created for {Saveadvancebookdata.bookingguest}, This Booking From OTA ')


                            return JsonResponse({'success': True, 'message': 'Reservation Updated Successfully'})
                            
                
                elif action=='modify':
                        # i am work here
                        cnalledata = onlinechannls.objects.filter(vendor=vendordata.vendor, channalname=channel).first()
                        if SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor,booking_id=bookingId,channal=cnalledata).exists():
                            
                            Saveadvancebookdata = SaveAdvanceBookGuestData.objects.get(vendor=vendordata.vendor,booking_id=bookingId,channal=cnalledata)
                            oldcheckindatemainmodel=Saveadvancebookdata.bookingdate
                            oldcheckoutdatemainmodel=Saveadvancebookdata.checkoutdate
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
                            commission = amount_details.get('commission')
                            tds = amount_details.get('tds')
                            tcs = amount_details.get('tcs')

                            # Handle commission
                            if commission is None:
                                commission = 0.0
                            else:
                                commission = float(commission)

                            # Handle tds and tcs
                            tds = float(tds) if tds is not None else None
                            tcs = float(tcs) if tcs is not None else None

                            agodataxamt = taxamount
                            print('yha tk chal gaya')
                            # commisiion calculation here
                            if channel == "MakeMyTrip" or channel == "Goibibo":
                                extra_mmt_commison = 0
                                extra_mmt_commison = commission * 18/100
                                commission = commission + extra_mmt_commison

                            if channel == "booking.com" :
                                extra_bcom_tds = 0
                                extra_bcom_tds = amountbeforetax * 0.1/100
                                tds = extra_bcom_tds
                            
                            if channel == "AirBNB" :
                                extra_bnb_tds = 0
                                extra_bnb_tds = amountbeforetax * 5/100
                                tds = extra_bnb_tds

                            if tds_comm_model.objects.filter(roombook=Saveadvancebookdata).exists():
                                 tds_comm_model.objects.filter(roombook=Saveadvancebookdata).update(
                                        commission=commission,tds=tds,tcs=tcs  )
                                 
                            # tdscreate = tds_comm_model.objects.create(roombook=Saveadvancebookdata,
                            #             commission=commission,tds=tds,tcs=tcs  )
                            if pahr==False:
                                if InvoicesPayment.objects.filter(vendor=vendordata.vendor,advancebook= Saveadvancebookdata).exists():
                                    invcpaymentdata = InvoicesPayment.objects.get(vendor=vendordata.vendor,advancebook= Saveadvancebookdata)
                                else:
                                    invcpaymentdata = InvoicesPayment.objects.create(vendor=vendordata.vendor,
                                                advancebook= Saveadvancebookdata,
                                                payment_amount= amountaftertax,
                                                payment_date=bookingdates,
                                                payment_mode='BankTransfer', 
                                                transaction_id='',
                                                descriptions='This Amount From OTA')
                            
                            Cm_bookpricesdates.objects.filter(
                                roombook__saveguestdata=Saveadvancebookdata
                            ).all().delete()

                            # new modify code yha se suru kiya delete wala
                            roomdata = Cm_RoomBookAdvance.objects.filter(saveguestdata=Saveadvancebookdata).all()
                            if roomdata: 
                                    for datain in roomdata:
                                        # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                                        checkindatedlt = oldcheckindatemainmodel
                                        checkoutdatedlt = oldcheckoutdatemainmodel
                                        while checkindatedlt < checkoutdatedlt:
                                            # roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                                            roomcategory = datain.room_category
                                            invtdata = RoomsInventory.objects.get(vendor=vendordata.vendor,date=checkindatedlt,room_category=roomcategory)
                                            invtavaible = invtdata.total_availibility + 1
                                            invtabook = invtdata.booked_rooms - 1
                                            # total_rooms = Rooms.objects.filter(vendor=user, room_type=roomcategory).exclude(checkin=6).count()
                                            total_rooms = Rooms_count.objects.filter(vendor=vendordata.vendor, room_type=roomcategory).values_list('total_room_numbers', flat=True).first() or 0
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=vendordata.vendor,date=checkindatedlt,room_category=roomcategory).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindatedlt += timedelta(days=1)
                            Cm_RoomBookAdvance.objects.filter(saveguestdata=Saveadvancebookdata).delete()
                            print("yaha dekh yh atkaaya kya ")
                            # Create an iterator from the queryset
                            # roombookadvance_iterator = iter(roombookadvance_data)
                            count=0
                            total_tax_amount_main = 0.0
                            total_after_taxamt_bnb = 0.0
                            total_before_taxamt_bnb = 0.0
                            for room in data['rooms']:
                                roomcatname = room['roomCode']
                                rateplanCode = room['rateplanCode']
                                GuestName = room['guestName']
                                adults =  int(room['occupancy']['adults']) 
                                children = int(room['occupancy']['children'])
                                rateplanname=''
                                # roombookadvance = next(roombookadvance_iterator)
                                newtestroom=room
                                # print(roombookadvance.id,"next data id ")
                                if rateplanCode == 'null':
                                    rateplanCode=None
                                else:
                                    if RatePlan.objects.filter(vendor=vendordata.vendor,rate_plan_code=rateplanCode).exists():
                                        plandatas = RatePlan.objects.get(vendor=vendordata.vendor,rate_plan_code=rateplanCode)
                                        rateplanname = plandatas.rate_plan_name
                                    else:
                                        pass
                                print('yha tk bhi new chal gaya')
                                # print("  Prices:")
                                # totalsell = 0.0
                                # for price in room['prices']:
                                #     totalsell =  price['sellRate']

                                totalsell = 0.0
                                for price in room['prices']:
                                    totalsell =  totalsell + price['sellRate']



                                totalsell = totalsell / int(day_difference)

                                if taxamount == 0.0:
                                    if channel == "AirBNB" :
                                        newtaxamount = 0.0
                                        if totalsell >7500:
                                            newtaxamount = totalsell*18/100
                                        else:
                                            newtaxamount = totalsell*12/100

                                        total_after_taxamt_bnb = total_after_taxamt_bnb + (newtaxamount * int(day_difference)) + amountaftertax
                                        
                                        total_before_taxamt_bnb = total_before_taxamt_bnb + totalsell * int(day_difference)
                                        total_tax_amount_main = total_tax_amount_main + (newtaxamount * int(day_difference))
                                        newbookmodeltotalamt = total_after_taxamt_bnb
                                        
                                    
                                         
                                    else:
                                        if totalsell >8851:
                                            totalsell = float(totalsell) / (1 + (18) / 100)

                                        elif totalsell <=8400:
                                            totalsell = float(totalsell) / (1 + (12) / 100)
                                        
                                        newtaxamount = 0.0
                                        if totalsell >7500:
                                            newtaxamount = totalsell*18/100
                                        else:
                                            newtaxamount = totalsell*12/100

                                        newtotaltaxamount = newtaxamount * int(day_difference)
                                        print(newtotaltaxamount,'checkthis amount')
                                        newbookmodeltotalamt = amountaftertax
                                        agodataxamt = newtotaltaxamount
                                        # totaltax amount calculation
                                        total_tax_amount_main = total_tax_amount_main + newtotaltaxamount
                                
                                else:
                                    newbookmodeltotalamt = amountaftertax

                                print('yha tk bhi chal gaya')
                                if True:    
                                    roomcatname
                                    roomcategry = RoomsCategory.objects.filter(vendor=vendordata.vendor,category_name=roomcatname).first()
                                    
                                    rbk=Cm_RoomBookAdvance.objects.create(
                                                vendor=vendordata.vendor,
                                                saveguestdata=Saveadvancebookdata,
                                                room_category=roomcategry,
                                                bookingguest=guestname,
                                                bookingguestphone=guestphone,
                                                totalguest=adults + children,
                                                rateplan_code=rateplanname,
                                                rateplan_code_main=rateplanCode,
                                                guest_name=GuestName,
                                                adults=adults,
                                                children=children,
                                                sell_rate=totalsell
                                            )
                                    # rbk=Cm_RoomBookAdvance.objects.get(id=roombookadvance.id)
                                   # for checknew in data['rooms']:
                                    for ckprice in newtestroom['prices']:
                                            date = ckprice['date']
                                            # new work here
                                            if Cm_bookpricesdates.objects.filter(roombook=rbk,date=str(ckprice['date'])):
                                                        pass
                                            else:                      
                                                Cm_bookpricesdates.objects.create(
                                                    roombook=rbk,date=str(ckprice['date']),
                                                    price = float(ckprice['sellRate'])
                                                )

                                    # Handling check-in and check-out times
                                    # noon_time_str = "12:00 PM"
                                    # noon_time = datetime.strptime(noon_time_str, "%I:%M %p").time()

                                    checkindate = str(checkindate)
                                    checkoutdate = str(checkoutdate)
                                    checkindate = datetime.strptime(checkindate, '%Y-%m-%d').date()
                                    checkoutdates = (datetime.strptime(checkoutdate, '%Y-%m-%d').date() - timedelta(days=1))
                                    catdatas=roomcategry
                                    # Generate the list of all dates between check-in and check-out (inclusive)
                                    all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdates - checkindate).days + 1)]

                                    # Query the RoomsInventory model to check if records exist for all those dates
                                    existing_inventory = RoomsInventory.objects.filter(vendor=vendordata.vendor,room_category=catdatas, date__in=all_dates)

                                    # Get the list of dates that already exist in the inventory
                                    existing_dates = set(existing_inventory.values_list('date', flat=True))

                                    # Identify the missing dates by comparing all_dates with existing_dates
                                    missing_dates = [date for date in all_dates if date not in existing_dates]

                                    # If there are missing dates, create new entries for those dates in the RoomsInventory model
                                    # roomcount = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).count()
                                    roomcount = Rooms_count.objects.filter(vendor=vendordata.vendor, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
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
                                    # totalrooms = Rooms.objects.filter(vendor=vendordata.vendor,room_type=catdatas).count()
                                    totalrooms =Rooms_count.objects.filter(vendor=vendordata.vendor, room_type=catdatas).values_list('total_room_numbers', flat=True).first() or 0
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

                                    
                            # tax 0 hoto yah update ho total krke 
                            if taxamount == 0.0:
                                if channel == "AirBNB":
                                        SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(amount_after_tax=total_after_taxamt_bnb,
                                                    total_amount=int(total_after_taxamt_bnb),amount_before_tax=total_before_taxamt_bnb,
                                                    tax=total_tax_amount_main,advance_amount=int(total_after_taxamt_bnb))
                                        if invcpaymentdata:
                                            invcpaymentdata.payment_amount=total_after_taxamt_bnb
                                            invcpaymentdata.save()
                                else:
                                    amountbeforetax = amountbeforetax - total_tax_amount_main
                                    SaveAdvanceBookGuestData.objects.filter(id=Saveadvancebookdata.id).update(tax=total_tax_amount_main
                                                            ,amount_before_tax=amountbeforetax)
                            # agoda commsion checking
                            if channel == 'agoda':
                                # checkagodacomm = total_tax_amount_main + commission + amountaftertax
                                # print(amountaftertax,checkagodacomm,commission)
                                # if amountaftertax < checkagodacomm:
                                #         agodacommissionamt = commission - total_tax_amount_main
                                # elif amountaftertax >= checkagodacomm:
                                agodacommissionamt = commission
                                         
                                tds_comm_model.objects.filter(roombook=Saveadvancebookdata).update(
                                        commission=agodacommissionamt  )


                            userids = vendordata.vendor.id
                            if VendorCM.objects.filter(vendor=vendordata.vendor):
                                        start_date = str(checkindate)
                                        end_date = str(checkoutdates)
                                        print(start_date,end_date)
                                        thread = threading.Thread(target=update_inventory_task_cm, args=(userids, start_date, end_date))
                                        thread.start()
                                        # for dynamic pricing
                                        if  VendorCM.objects.filter(vendor=vendordata.vendor,dynamic_price_active=True):
                                            thread = threading.Thread(target=rate_hit_channalmanager_cm, args=(userids, start_date, end_date))
                                            thread.start()
                                        else:
                                            pass
                            else:
                                        pass
                            
                            actionss = 'Edit Booking'
                            user=Saveadvancebookdata.vendor
                            CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=Saveadvancebookdata,description=f'Booking Edited for {Saveadvancebookdata.bookingguest}, This Booking From OTA ')

                            return JsonResponse({'success': True, 'message': 'Reservation Modified Successfully'})
                        else:
                             return JsonResponse({'success': True, 'message': 'Reservation Not Found!'})
                        
                        
                elif action=='cancel':
                        hotelCode = data['hotelCode']
                        bookingIds = data['bookingId']
                        vendordata = VendorCM.objects.get(hotelcode=hotelCode)
                        channel = data['channel']
                        cnalledata = onlinechannls.objects.filter(vendor=vendordata.vendor, channalname=channel).first()
                        
                        exists = SaveAdvanceBookGuestData.objects.filter(vendor=vendordata.vendor,booking_id=bookingIds,channal=cnalledata).exclude(action='cancel').exists()

                        if exists:
                                savedata = SaveAdvanceBookGuestData.objects.get(vendor=vendordata.vendor,booking_id=bookingIds,channal=cnalledata)
                                user = vendordata.vendor
                                saveguestid=SaveAdvanceBookGuestData.objects.get(vendor=vendordata.vendor,booking_id=bookingIds,channal=cnalledata)
                                roomdata = Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=saveguestid).all()
                                InvoicesPayment.objects.filter(vendor=user,advancebook=saveguestid).update(
                                    payment_mode="Refund"
                                )
                                if roomdata: 
                                    for data in roomdata:
                                        # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                                        checkindate = savedata.bookingdate
                                        checkoutdate = savedata.checkoutdate
                                        while checkindate < checkoutdate:
                                            # roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                                            roomcategory = data.room_category
                                            invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomcategory)
                                            invtavaible = invtdata.total_availibility + 1
                                            invtabook = invtdata.booked_rooms - 1
                                            # total_rooms = Rooms.objects.filter(vendor=user, room_type=roomcategory).exclude(checkin=6).count()
                                            total_rooms = Rooms_count.objects.filter(vendor=user, room_type=roomcategory).values_list('total_room_numbers', flat=True).first() or 0
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomcategory).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindate += timedelta(days=1)

                                    if VendorCM.objects.filter(vendor=user):
                                        start_date = str(savedata.bookingdate)
                                        end_date = str(savedata.checkoutdate)
                                        thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                                        thread.start()
                                    userids=user.id
                                    channel=saveguestid.channal.channalname
                                    cmBookingId=bookingIds
                                    print(cmBookingId)
                                    guestname=saveguestid.bookingguest
                                    savidmain=saveguestid.id
                                    emailthread = threading.Thread(target=sent_cancel_email, args=(userids,channel,cmBookingId,guestname,savidmain))
                                    emailthread.start()
                                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel')
                                    # Booking.objects.filter(vendor=user,advancebook_id=saveguestid.id).delete()
                                    actionss = 'Cancel Booking'
                                    CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=saveguestid,description=f'Booking Cancel for {saveguestid.bookingguest}, This Booking From OTA ')

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


def noshowcme(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            print(yesterday,today)
            # alldata = SaveAdvanceBookGuestData.objects.filter(vendor=user,bookingdate=yesterday,channal__channalname='booking.com').all()
            alldata = SaveAdvanceBookGuestData.objects.filter(
                    vendor=user,
                    bookingdate=yesterday,
                    channal__channalname='booking.com'
                ).filter(
                    Q(~Q(action='cancel')) | Q(action='cancel', is_hold=True)
                )
            return render(request,'noshowcm.html',{'alldata':alldata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)   
        


def marknoshowcm(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id,is_noshow=True).exists():
                messages.success(request,"Booking marked as no-show Already")
                return redirect('noshowcme')
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                    booking = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                    url = "https://live.aiosell.com/api/v2/cm/noshow"
                    vendordata = VendorCM.objects.filter(vendor=user).first()
                    hotelcode = vendordata.hotelcode
                    payload = {
                        "hotelId": hotelcode,
                        "bookingId": booking.booking_id,
                        "partner": "booking.com"
                    }
                    
                    try:
                        response = requests.post(url, json=payload)
                        result = response.json()

                        if result.get("success") is True:
                            # Handle success response
                            if booking.action == 'book' or booking.action == 'modify':
                                roomdata = Cm_RoomBookAdvance.objects.filter(vendor=user,saveguestdata=booking).all()
                                savedata=booking
                                saveguestid=booking
                                if roomdata: 
                                    for data in roomdata:
                                        # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                                        checkindate = savedata.bookingdate
                                        checkoutdate = savedata.checkoutdate
                                        while checkindate < checkoutdate:
                                            # roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                                            roomcategory = data.room_category
                                            invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomcategory)
                                            invtavaible = invtdata.total_availibility + 1
                                            invtabook = invtdata.booked_rooms - 1
                                            # total_rooms = Rooms.objects.filter(vendor=user, room_type=roomcategory).exclude(checkin=6).count()
                                            total_rooms = Rooms_count.objects.filter(vendor=user, room_type=roomcategory).values_list('total_room_numbers', flat=True).first() or 0
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomcategory).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindate += timedelta(days=1)

                                    if VendorCM.objects.filter(vendor=user):
                                        start_date = str(savedata.bookingdate)
                                        end_date = str(savedata.checkoutdate)
                                        thread = threading.Thread(target=update_inventory_task_cm, args=(user.id, start_date, end_date))
                                        thread.start()

                                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel',
                                                                    is_noshow=True)
                                    # Booking.objects.filter(vendor=user,advancebook_id=saveguestid.id).delete()
                                    actionss = 'No Show And Cancel Booking'
                                    CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=saveguestid,description=f'Booking No Show And Cancel for {saveguestid.bookingguest}, This Booking From OTA ')
                            else:
                                saveguestid=booking
                                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel',
                                                    is_noshow=True)
                                actionss = 'No Show Booking'
                                CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=saveguestid,description=f'Booking No Show for {saveguestid.bookingguest}, This Booking From OTA ')
                            messages.success(request,"Booking marked as no-show successfully.")
                            return redirect('noshowcme')
                        
                        else:
                            messages.error(request,f'Failed to mark booking as no-show.{booking.bookingguest} Booking id: {booking.booking_id}')
                            # Handle failure response
                            return redirect('noshowcme')

                    except requests.exceptions.RequestException as e:
                        messages.error(request,f'Failed to mark booking as no-show.')
                        return redirect('noshowcme')
                        # Handle request errors (e.g., timeout, connection error)
            else:
                    messages.error(request,f'Failed to mark booking as no-show.')
                    return redirect('noshowcme')
                
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    

def noshowcmemain(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            print(yesterday,today)
            # alldata = SaveAdvanceBookGuestData.objects.filter(vendor=user,bookingdate=yesterday,channal__channalname='booking.com').all()
            alldata = SaveAdvanceBookGuestData.objects.filter(
                    vendor=user,
                    bookingdate=yesterday,
                    channal__channalname='booking.com'
                ).filter(
                    Q(~Q(action='cancel')) | Q(action='cancel', is_hold=True)
                )
            return render(request,'noshowcmmain.html',{'alldata':alldata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  

def marknoshowmain(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id,is_noshow=True).exists():
                messages.success(request,"Booking marked as no-show Already")
                return redirect('noshowcmemain')
            if SaveAdvanceBookGuestData.objects.filter(vendor=user,id=id).exists():
                    booking = SaveAdvanceBookGuestData.objects.get(vendor=user,id=id)
                    url = "https://live.aiosell.com/api/v2/cm/noshow"
                    vendordata = VendorCM.objects.filter(vendor=user).first()
                    hotelcode = vendordata.hotelcode
                    payload = {
                        "hotelId": hotelcode,
                        "bookingId": booking.booking_id,
                        "partner": "booking.com"
                    }
                    
                    try:
                        response = requests.post(url, json=payload)
                        result = response.json()

                        if result.get("success") is True:
                            # Handle success response
                            if booking.action == 'book' or booking.action == 'modify':
                                roomdata = RoomBookAdvance.objects.filter(vendor=user,saveguestdata=booking).all()
                                savedata=booking
                                saveguestid=booking
                                if roomdata: 
                                    for data in roomdata:
                                        # Rooms.objects.filter(vendor=user,id=data.roomno.id).update(checkin=0)
                                        checkindate = savedata.bookingdate
                                        checkoutdate = savedata.checkoutdate
                                        while checkindate < checkoutdate:
                                            # roomscat = Rooms.objects.get(vendor=user,id=data.roomno.id)
                                            roomcategory = data.roomno.room_type
                                            invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomcategory)
                                            invtavaible = invtdata.total_availibility + 1
                                            invtabook = invtdata.booked_rooms - 1
                                            total_rooms = Rooms.objects.filter(vendor=user, room_type=roomcategory).exclude(checkin=6).count()
                                            # total_rooms = Rooms_count.objects.filter(vendor=user, room_type=roomcategory).values_list('total_room_numbers', flat=True).first() or 0
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomcategory).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindate += timedelta(days=1)

                                    if VendorCM.objects.filter(vendor=user):
                                        start_date = str(savedata.bookingdate)
                                        end_date = str(savedata.checkoutdate)
                                        thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                        thread.start()

                                    SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel',
                                                                    is_noshow=True)
                                    # Booking.objects.filter(vendor=user,advancebook_id=saveguestid.id).delete()
                                    actionss = 'No Show And Cancel Booking'
                                    CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=saveguestid,description=f'Booking No Show And Cancel for {saveguestid.bookingguest}, This Booking From OTA ')
                            else:
                                saveguestid=booking
                                SaveAdvanceBookGuestData.objects.filter(vendor=user,id=saveguestid.id).update(action='cancel',
                                                    is_noshow=True)
                                actionss = 'No Show Booking'
                                CustomGuestLog.objects.create(vendor=user,by='system Assign',action=actionss,
                                            advancebook=saveguestid,description=f'Booking No Show for {saveguestid.bookingguest}, This Booking From OTA ')
                            messages.success(request,"Booking marked as no-show successfully.")
                            return redirect('noshowcmemain')
                        
                        else:
                            messages.error(request,f'Failed to mark booking as no-show.{booking.bookingguest} Booking id: {booking.booking_id}')
                            # Handle failure response
                            return redirect('noshowcmemain')

                    except requests.exceptions.RequestException as e:
                        messages.error(request,f'Failed to mark booking as no-show.')
                        return redirect('noshowcmemain')
                        # Handle request errors (e.g., timeout, connection error)
            else:
                    messages.error(request,f'Failed to mark booking as no-show.')
                    return redirect('noshowcmemain')
                
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    

from django.db.models.functions import ExtractYear
from django.db.models import Sum, Count
def cm_sales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor

            current_year = datetime.now().year

            # Filter booking data (excluding cancel)
            bookings = (
                SaveAdvanceBookGuestData.objects
                .filter(vendor=user)
                .exclude(action='cancel')
                .annotate(year=ExtractYear('bookingdate'))
                .filter(year=current_year)
            )

            # Channel-wise aggregation
            channel_data = (
                bookings
                .values('channal__channalname')
                .annotate(
                    total_sales=Sum('total_amount'),
                    booking_count=Count('id'),
                    total_nights=Sum('staydays')
                )
                .order_by('-total_sales')
            )

            # Rooms from related table
            cm_room_data = Cm_RoomBookAdvance.objects.filter(
                vendor=user,
                saveguestdata__in=bookings
            ).values('saveguestdata__channal__channalname') \
            .annotate(room_count=Count('id'))

            # Mapping rooms per channel
            room_count_map = {
                item['saveguestdata__channal__channalname']: item['room_count']
                for item in cm_room_data
            }

            # Prepare lists for chart
            channels = []
            sales = []
            bookings_list = []
            nights = []
            rooms = []

            for item in channel_data:
                name = item['channal__channalname']
                channels.append(name)
                sales.append(item['total_sales'] or 0)
                bookings_list.append(item['booking_count'])
                nights.append(item['total_nights'] or 0)
                rooms.append(room_count_map.get(name, 0))

            sum_bookings = (
                    SaveAdvanceBookGuestData.objects
                    .filter(vendor=user)
                    .exclude(action='cancel')
                    .annotate(year=ExtractYear('bookingdate'))
                    .filter(year=current_year)
                )
            sum_cmroombook_count = Cm_RoomBookAdvance.objects.filter(
                    vendor=user,
                    saveguestdata__in=sum_bookings
                ).count()
            total_amount_sum = sum_bookings.aggregate(total=Sum('total_amount'))['total'] or 0

            sum_cancel_bookings = (
                    SaveAdvanceBookGuestData.objects
                    .filter(vendor=user,action='cancel')
                    .annotate(year=ExtractYear('bookingdate'))
                    .filter(year=current_year)
                )
            total_cancel_amount_sum = sum_cancel_bookings.aggregate(total=Sum('total_amount'))['total'] or 0
            if sum_cmroombook_count > 0:
                adr = total_amount_sum / sum_cmroombook_count
            else:
                adr = 0
            print("Total Room Book Count:", sum_cmroombook_count)
            print("Total Amount Sum:", total_amount_sum)
            print("ADR (Average Daily Rate):", adr)
            print(total_cancel_amount_sum,'cancel sale')
            context = {
                'channels': json.dumps(channels),
                'sales': json.dumps(sales),
                'bookings': json.dumps(bookings_list),
                'nights': json.dumps(nights),
                'rooms': json.dumps(rooms),
                'active_page': 'cm_sales',
                'showdates': f'{current_year} Full Year',
                'sum_cmroombook_count':sum_cmroombook_count,
                'total_amount_sum':total_amount_sum,
                'adr':adr,'total_cancel_amount_sum':total_cancel_amount_sum

            }

            return render(request, 'cmsales.html', context)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    
def searchcmsales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            print("FILTERING: ", startdate, enddate)

            start = datetime.strptime(startdate, "%Y-%m-%d").date()
            end = datetime.strptime(enddate, "%Y-%m-%d").date()

            if start <= end:
                # Default fallback if no dates
                if startdate and enddate:
                    bookings = (
                        SaveAdvanceBookGuestData.objects
                        .filter(vendor=user)
                        .exclude(action='cancel')
                        .filter(bookingdate__range=[startdate, enddate])
                    )
                    show_range = f"{startdate} to {enddate}"
                
                    # Channel-wise aggregation
                    channel_data = (
                        bookings
                        .values('channal__channalname')
                        .annotate(
                            total_sales=Sum('total_amount'),
                            booking_count=Count('id'),
                            total_nights=Sum('staydays')
                        )
                        .order_by('-total_sales')
                    )

                    # Rooms from related table
                    cm_room_data = Cm_RoomBookAdvance.objects.filter(
                        vendor=user,
                        saveguestdata__in=bookings
                    ).values('saveguestdata__channal__channalname') \
                    .annotate(room_count=Count('id'))

                    room_count_map = {
                        item['saveguestdata__channal__channalname']: item['room_count']
                        for item in cm_room_data
                    }

                    channels = []
                    sales = []
                    bookings_list = []
                    nights = []
                    rooms = []

                    for item in channel_data:
                        name = item['channal__channalname']
                        channels.append(name)
                        sales.append(item['total_sales'] or 0)
                        bookings_list.append(item['booking_count'])
                        nights.append(item['total_nights'] or 0)
                        rooms.append(room_count_map.get(name, 0))

                    context = {
                        'channels': json.dumps(channels),
                        'sales': json.dumps(sales),
                        'bookings': json.dumps(bookings_list),
                        'nights': json.dumps(nights),
                        'rooms': json.dumps(rooms),
                        'active_page': 'cm_sales',
                        'showdates': show_range,
                    }
                    return render(request, 'cmsales.html', context)
                else:
                    messages.error(request,'please select correct dates')
                    return render(request, 'cmsales.html')

            else:
                messages.error(request,'please select correct dates')
                return render(request, 'cmsales.html')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



from django.db.models import Sum, Count, F, ExpressionWrapper, DurationField
from datetime import timedelta
def pm_cm_sales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor

            current_year = datetime.now().year

            # Step 1: Filter PMS data for the current year
            pms_data = Gueststay.objects.filter(
                vendor=user,
                channel="PMS",
                checkindate__date__year=current_year
            )

            # Step 2: Annotate duration (checkout - checkin)
            pms_data = pms_data.annotate(
                duration=ExpressionWrapper(
                    F('checkoutdate') - F('checkindate'),
                    output_field=DurationField()
                )
            )

            # Step 3: Calculate total values
            total_sales = pms_data.aggregate(total_sales=Sum('total'))['total_sales'] or 0
            booking_count = pms_data.count()
            total_nights = sum([int(item.duration.days) for item in pms_data])
            room_count = booking_count  # As each booking = 1 room


            # Filter booking data (excluding cancel)
            bookings = (
                SaveAdvanceBookGuestData.objects
                .filter(vendor=user)
                .exclude(action='cancel')
                .annotate(year=ExtractYear('bookingdate'))
                .filter(year=current_year)
            )

            # Channel-wise aggregation
            channel_data = (
                bookings
                .values('channal__channalname')
                .annotate(
                    total_sales=Sum('total_amount'),
                    booking_count=Count('id'),
                    total_nights=Sum('staydays')
                )
                .order_by('-total_sales')
            )

            # Rooms from related table
            cm_room_data = Cm_RoomBookAdvance.objects.filter(
                vendor=user,
                saveguestdata__in=bookings
            ).values('saveguestdata__channal__channalname') \
            .annotate(room_count=Count('id'))

            # Mapping rooms per channel
            room_count_map = {
                item['saveguestdata__channal__channalname']: item['room_count']
                for item in cm_room_data
            }

            # Prepare lists for chart
            channels = []
            sales = []
            bookings_list = []
            nights = []
            rooms = []

            for item in channel_data:
                name = item['channal__channalname']
                channels.append(name)
                sales.append(item['total_sales'] or 0)
                bookings_list.append(item['booking_count'])
                nights.append(item['total_nights'] or 0)
                rooms.append(room_count_map.get(name, 0))

            # Step 4: Append to lists
            channels.append("PMS")
            sales.append(total_sales)
            bookings_list.append(booking_count)
            nights.append(total_nights)
            rooms.append(room_count)

            sum_bookings = (
                    SaveAdvanceBookGuestData.objects
                    .filter(vendor=user)
                    .exclude(action='cancel')
                    .annotate(year=ExtractYear('bookingdate'))
                    .filter(year=current_year)
                )
            sum_cmroombook_count = Cm_RoomBookAdvance.objects.filter(
                    vendor=user,
                    saveguestdata__in=sum_bookings
                ).count()
            total_amount_sum = sum_bookings.aggregate(total=Sum('total_amount'))['total'] or 0

            sum_cancel_bookings = (
                    SaveAdvanceBookGuestData.objects
                    .filter(vendor=user,action='cancel')
                    .annotate(year=ExtractYear('bookingdate'))
                    .filter(year=current_year)
                )
            total_cancel_amount_sum = sum_cancel_bookings.aggregate(total=Sum('total_amount'))['total'] or 0
            if sum_cmroombook_count > 0:
                adr = total_amount_sum / sum_cmroombook_count
            else:
                adr = 0
            print("Total Room Book Count:", sum_cmroombook_count)
            print("Total Amount Sum:", total_amount_sum)
            print("ADR (Average Daily Rate):", adr)
            print(total_cancel_amount_sum,'cancel sale')
            context = {
                'channels': json.dumps(channels),
                'sales': json.dumps(sales),
                'bookings': json.dumps(bookings_list),
                'nights': json.dumps(nights),
                'rooms': json.dumps(rooms),
                'active_page': 'pm_cm_sales',
                'showdates': f'{current_year} Full Year',
                'sum_cmroombook_count':sum_cmroombook_count,
                'total_amount_sum':total_amount_sum,
                'adr':adr,'total_cancel_amount_sum':total_cancel_amount_sum

            }

            return render(request, 'cmsalespm.html', context)
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def pmsearchcmsales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            start = datetime.strptime(startdate, "%Y-%m-%d").date()
            end = datetime.strptime(enddate, "%Y-%m-%d").date()

            if start <= end:
                # Default fallback if no dates
                if startdate and enddate:

                    # Step 1: Filter PMS data for the current year
                    pms_data = Gueststay.objects.filter(
                        vendor=user,
                        channel="PMS",
                        checkindate__date__range=[startdate, enddate]
                    )

                    # Step 2: Annotate duration (checkout - checkin)
                    pms_data = pms_data.annotate(
                        duration=ExpressionWrapper(
                            F('checkoutdate') - F('checkindate'),
                            output_field=DurationField()
                        )
                    )

                    # Step 3: Calculate total values
                    total_sales = pms_data.aggregate(total_sales=Sum('total'))['total_sales'] or 0
                    booking_count = pms_data.count()
                    total_nights = sum([int(item.duration.days) for item in pms_data])
                    room_count = booking_count  # As each booking = 1 room



                    bookings = (
                        SaveAdvanceBookGuestData.objects
                        .filter(vendor=user)
                        .exclude(action='cancel')
                        .filter(bookingdate__range=[startdate, enddate])
                    )
                    show_range = f"{startdate} to {enddate}"
                
                    # Channel-wise aggregation
                    channel_data = (
                        bookings
                        .values('channal__channalname')
                        .annotate(
                            total_sales=Sum('total_amount'),
                            booking_count=Count('id'),
                            total_nights=Sum('staydays')
                        )
                        .order_by('-total_sales')
                    )

                    # Rooms from related table
                    cm_room_data = Cm_RoomBookAdvance.objects.filter(
                        vendor=user,
                        saveguestdata__in=bookings
                    ).values('saveguestdata__channal__channalname') \
                    .annotate(room_count=Count('id'))

                    room_count_map = {
                        item['saveguestdata__channal__channalname']: item['room_count']
                        for item in cm_room_data
                    }

                    channels = []
                    sales = []
                    bookings_list = []
                    nights = []
                    rooms = []

                    for item in channel_data:
                        name = item['channal__channalname']
                        channels.append(name)
                        sales.append(item['total_sales'] or 0)
                        bookings_list.append(item['booking_count'])
                        nights.append(item['total_nights'] or 0)
                        rooms.append(room_count_map.get(name, 0))

                    # Step 4: Append to lists
                    channels.append("PMS")
                    sales.append(total_sales)
                    bookings_list.append(booking_count)
                    nights.append(total_nights)
                    rooms.append(room_count)

                    context = {
                        'channels': json.dumps(channels),
                        'sales': json.dumps(sales),
                        'bookings': json.dumps(bookings_list),
                        'nights': json.dumps(nights),
                        'rooms': json.dumps(rooms),
                        'active_page': 'cm_sales',
                        'showdates': show_range,
                    }
                    return render(request, 'cmsalespm.html', context)
                else:
                    messages.error(request,'please select correct dates')
                    return render(request, 'cmsalespm.html')

            else:
                messages.error(request,'please select correct dates')
                return render(request, 'cmsalespm.html')
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
