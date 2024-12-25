from celery import shared_task
from .models import User, RoomsCategory, RoomsInventory, Rooms
from datetime import datetime, timedelta
import requests
import json

@shared_task
def update_inventory_task(user_id, start_date_str, end_date_str):
    print("run calery")
    # Your task logic here
    user = User.objects.get(id=user_id)
    room_categories = RoomsCategory.objects.filter(vendor=user)
    inventory_updates = []

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    date_range = (end_date - start_date).days
    for day in range(date_range + 1):
        current_date = start_date + timedelta(days=day)

        for category in room_categories:
            inventory = RoomsInventory.objects.filter(vendor=user, room_category=category, date=current_date).first()
            roomcount = Rooms.objects.filter(vendor=user, room_type=category).count()

            if not inventory:
                available_rooms = roomcount
            else:
                available_rooms = inventory.total_availibility

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
            inventory_updates.append({
                "startDate": str(current_date),
                "endDate": str(current_date),
                "rooms": [room_data]
            })

    data = {
        "hotelCode": "SANDBOX-PMS",
        "updates": inventory_updates
    }

    url = "https://live.aiosell.com/api/v2/cm/update/sample-pms"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response_data = response.json()

        if response.status_code == 200 and response_data.get("success"):
            return "Inventory Updated Successfully"
        else:
            return f"Failed: {response_data.get('message')}"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


