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







def priceshow_new(request):
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

    return render(request, 'webratedate.html', context)




def change_date_new(request):
    """ Handles date picker selection """
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            datetime.strptime(selected_date_str, "%Y-%m-%d")  # Validate date format
            return redirect(f"/priceshow-new/?start_date={selected_date_str}")
        except ValueError:
            pass  # Invalid date, fallback to default
    return redirect("/priceshow-new/")




def next_day_new(request):
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
    return redirect(f"/priceshow-new/?start_date={next_date.strftime('%Y-%m-%d')}")





def save_prices_new(request):
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
                return redirect('priceshow_new')
        else:
            selected_date = datetime.now().date()

        if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
            pass
        else:
            messages.error(request, "Your Permission is Denied via Admin")
            return redirect(f"/priceshow-new/?start_date={selected_date.strftime('%Y-%m-%d')}")


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
                        rcount=Rooms.objects.filter(vendor=user,room_type=category).exclude(checkin=6).count()
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
        if VendorCM.objects.filter(vendor=user):
                start_date = str(selected_date)
                end_date = str(enddate)
                    
                    # for dynamic pricing
                if  VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                        thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                        thread.start()
                else:
                        pass

        else:
                    pass
        start_date = str(selected_date)
        end_date = str(enddate)
        logsdesc = f"Update Rates For All Category, From {start_date} To {end_date}"
        bulklogs.objects.create(vendor=user,by=request.user,action="Update Rates",
                    description = logsdesc)
        messages.success(request, "Prices updated successfully!")
        return redirect(f"/priceshow-new/?start_date={selected_date.strftime('%Y-%m-%d')}")

    return redirect('priceshow_new')











def inventory_view(request):
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
            roomct = Rooms.objects.filter(vendor=user,room_type=category).exclude(checkin=6).count()
            row['availability_data'][date] = existing_availability if existing_availability is not None else roomct
        inventory_list.append(row)

    context = {
        'date_range': date_range,
        'inventory_list': inventory_list,
        'selected_date': selected_date,
        'today': datetime.now().date(),  # Ensure 'min' in date picker works properly
        'active_page':'inventory_view'
    }

    return render(request, 'webinventory.html', context)


def next_day_inventory(request):
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
    return redirect(f"/inventory_view/?start_date={next_date.strftime('%Y-%m-%d')}")

def change_date_inventory(request):
    """ Handles date picker selection """
    selected_date_str = request.GET.get('start_date')
    if selected_date_str:
        try:
            datetime.strptime(selected_date_str, "%Y-%m-%d")  # Validate date format
            return redirect(f"/inventory_view/?start_date={selected_date_str}")
        except ValueError:
            pass  # Invalid date, fallback to default
    return redirect("/inventory_view/")




def save_inventory_new(request):
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
                return redirect('priceshow_new')
        else:
            selected_date = datetime.now().date()

        if VendorCM.objects.filter(vendor=user,inventory_active=True):
            pass
        else:
            messages.error(request, "Your Permission is Denied via Admin")
            return redirect(f"/inventory_view/?start_date={selected_date.strftime('%Y-%m-%d')}")


        # Generate date range (Fix: Use form-submitted date)
        date_range = [selected_date + timedelta(days=i) for i in range(7)]

        enddate = selected_date + timedelta(days=6)
        print("check this dates",selected_date,enddate)

        # Fetch all categories
        categories = RoomsCategory.objects.filter(vendor=user)
    
        # Process form data and update inventory
        for category in categories:
            for date in date_range:
                price_key = f"price_{category.category_name}_{date.strftime('%Y-%m-%d')}"
                price = request.POST.get(price_key, "").strip()

                if price:  # Ensure inventory is not empty
                    try:
                        price = price
                    except ValueError:
                        continue  # Skip invalid price values
                
                    # Update or create inventory entry
                    if RoomsInventory.objects.filter(vendor=user,room_category=category,date=date).exists():
                        RoomsInventory.objects.filter(
                            vendor=user,
                            room_category=category,
                            date=date
                        ).update(
                            total_availibility = price #this is actual inventory
                        )

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
                        


                    # Debugging Output
                    print(f"Updated: {date} | Category: {category.category_name} | avaibility: {price}")
        if VendorCM.objects.filter(vendor=user):
                start_date = str(selected_date)
                end_date = str(enddate)
                    
                    # for dynamic pricing
               
        else:
                    pass
        start_date = str(selected_date)
        end_date = str(enddate)
        logsdesc = f"Update Inventory For All Category, From {start_date} To {end_date}"
        bulklogs.objects.create(vendor=user,by=request.user,action="Update Inventory",
                    description = logsdesc)
        messages.success(request, "Inventory updated successfully!")
        return redirect(f"/inventory_view/?start_date={selected_date.strftime('%Y-%m-%d')}")
    
    else:
        messages.error(request, "Method Not Exists!")
    return redirect('inventory_view')







def save_inventory_new(request):
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
            return redirect('priceshow_new')

        # Check if vendor has permission
        if not VendorCM.objects.filter(vendor=user, inventory_active=True).exists():
            messages.error(request, "Your Permission is Denied via Admin")
            return redirect(f"/inventory_view/?start_date={selected_date.strftime('%Y-%m-%d')}")

        # Generate date range (7 days)
        date_range = [selected_date + timedelta(days=i) for i in range(10)]
        enddate = selected_date + timedelta(days=9)

        # Fetch all categories
        categories = RoomsCategory.objects.filter(vendor=user)

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
                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
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
        return redirect(f"/inventory_view/?start_date={selected_date.strftime('%Y-%m-%d')}")

    else:
        messages.error(request, "Method Not Exists!")
        return redirect('inventory_view')
