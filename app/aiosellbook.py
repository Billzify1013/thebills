import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Logging setup
logger = logging.getLogger(__name__)

@csrf_exempt
def aiosell_new_reservation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Log incoming data for verification
            logger.info("Received new reservation data: %s", data)

            # Verify required fields before proceeding
            required_fields = ["bookingId", "hotelCode", "channel", "checkin", "checkout", "guest", "rooms"]
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'success': False, 'message': f'Missing required field: {field}'}, status=400)

            # For testing, send a response without saving data
            return JsonResponse({'success': True, 'message': 'Function is working, data received successfully.'})

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format: %s", e)
            return JsonResponse({'success': False, 'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            logger.error("Error in new reservation function: %s", e)
            return JsonResponse({'success': False, 'message': 'An error occurred.'}, status=500)


