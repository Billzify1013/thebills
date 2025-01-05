# import datetime
# from django.utils.deprecation import MiddlewareMixin
# from django.shortcuts import render, redirect, HttpResponse
# from django.contrib.sessions.models import Session
# from django.utils import timezone
# from django.core.exceptions import SuspiciousOperation


# class DailySessionExpiryMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         try:
#             if request.user.is_authenticated:
#                 now = datetime.datetime.now()
#                 tomorrow = now + datetime.timedelta(days=1)
#                 midnight = datetime.datetime.combine(tomorrow, datetime.time.min)
#                 seconds_until_midnight = (midnight - now).seconds
#                 request.session.set_expiry(seconds_until_midnight)

#         except Exception as e:
#             # Optionally log the error if needed
#             pass

import datetime
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from app.models import Subuser
from django.utils import timezone

class UserSessionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            
            if request.user.is_authenticated:
                # Handle session expiry at midnight
                now = datetime.datetime.now()
                tomorrow = now + datetime.timedelta(days=1)
                midnight = datetime.datetime.combine(tomorrow, datetime.time.min)
                seconds_until_midnight = (midnight - now).seconds
                request.session.set_expiry(seconds_until_midnight)  # Set session expiry to midnight
              
                # Check if permissions are already set in session to avoid querying DB again
                if 'permissions' not in request.session:
                    
                    try:
                        # Try to fetch the subuser and their permissions
                        subuser = Subuser.objects.get(user=request.user)
                        request.session['is_subuser'] = True
                        request.session['permissions'] = subuser.permissions  # Store subuser permissions in session
                    except Subuser.DoesNotExist:
                        # If user is not a subuser, consider them a main user with full permissions
                        request.session['is_subuser'] = False
                        request.session['permissions'] = {
                            'TSel': True, 'Attd': True, 'cln': True, 'psle': True,
                            'si': True, 'saa': True, 'ext': True, 'emp': True,
                            'pdt': True, 'set': True, 'ups': True
                        }
                       
            else:
                # For unauthenticated users, clear permissions in the session
                request.session['is_subuser'] = False
                request.session['permissions'] = {}

        except Exception as e:
            # Optionally log the error if needed
            pass






