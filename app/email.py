
from django.core.mail import send_mass_mail
from django.shortcuts import render, redirect,HttpResponse 
from . models import *
from time import gmtime, strftime
from django.shortcuts import render,redirect
from django.conf import settings
import textwrap

def sent_success_email(userids, channel, cmBookingId,guestname,savidmain):
        user = User.objects.get(id=userids)
        if not user.is_authenticated:
            print("User is not authenticated.")
            return
        hp = HotelProfile.objects.filter(vendor=user).first()
        hotelemail = hp.email
        # subject = 'New Booking Received'

        import time
        subject = f'New Booking Received - {cmBookingId} - {time.strftime("%Y%m%d%H%M%S")}'

        message = textwrap.dedent(f"""
            Hey {hp.name},

            You have received a new booking from {channel}.

            Booking ID: {cmBookingId}  
            Guest Name: {guestname}  
            Booking Voucher: https://live.billzify.com/receipt/?cd={savidmain}

            Please log in to your Billzify panel to view full booking details.

            Thanks & Regards,  
            Team Billzify
        """)

        email_from = settings.EMAIL_HOST_USER
        recipient_list = [hotelemail]  # ✅ ensure this is a list

        messages = [
            (subject, message, email_from, recipient_list)
        ]

        send_mass_mail(messages)


def sent_cancel_email(userids,channel,cmBookingId,guestname,savidmain):
        user = User.objects.get(id=userids)
        if not user.is_authenticated:
            print("User is not authenticated.")
            return
        hp = HotelProfile.objects.filter(vendor=user).first()
        hotelemail = hp.email

        import time
        subject = f'Booking Cancelled - {cmBookingId} - {time.strftime("%Y%m%d%H%M%S")}'

        message = textwrap.dedent(f"""
            Hey {hp.name},

            A booking from {channel} has been cancelled.

            Booking ID: {cmBookingId}  
            Guest Name: {guestname}  
            Cancelled Voucher: https://live.billzify.com/receipt/?cd={savidmain}

            Please log in to your Billzify panel to view full cancellation details.

            Thanks & Regards,  
            Team Billzify
        """)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [hotelemail]  # ✅ ensure this is a list

        messages = [
            (subject, message, email_from, recipient_list)
        ]

        send_mass_mail(messages)

def error_message_email(userids,channel,cmBookingId,guestname):
        hotelemail = 'ckhajwan@gmail.com'

        import time
        subject = f'Booking Creation Error {userids} - {cmBookingId} - {time.strftime("%Y%m%d%H%M%S")}'

        message = textwrap.dedent(f"""
            yha error aaye hai user hai {userids},

            A booking from {channel} has been cancelled.

            Booking ID: {cmBookingId}  
            Guest Name: {guestname}  

        """)
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [hotelemail]  # ✅ ensure this is a list

        messages = [
            (subject, message, email_from, recipient_list)
        ]

        send_mass_mail(messages)