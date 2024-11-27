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






