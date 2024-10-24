import datetime
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render, redirect, HttpResponse
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.exceptions import SuspiciousOperation

class DailySessionExpiryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            if request.user.is_authenticated:
                now = datetime.datetime.now()
                tomorrow = now + datetime.timedelta(days=1)
                midnight = datetime.datetime.combine(tomorrow, datetime.time.min)
                seconds_until_midnight = (midnight - now).seconds
                request.session.set_expiry(seconds_until_midnight)
            
        except Exception as e:
            # Optionally log the error if needed
            pass

class OneSessionPerUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if request.user.is_authenticated:
                current_session_key = request.session.session_key
                user_sessions = Session.objects.filter(expire_date__gte=timezone.now())
                
                for session in user_sessions:
                    session_data = session.get_decoded()
                    if session_data.get('_auth_user_id') == str(request.user.id) and session.session_key != current_session_key:
                        session.delete()
        except Exception as e:
            # Optionally log the error if needed
            pass

        return response


