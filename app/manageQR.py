from . models import *
from django.conf import settings
from django.shortcuts import render, redirect
import re




def laundrysrvs(request,id):
    try:
        numbers = re.findall(r'\d+', id)
        number = int(numbers[0]) if numbers else None
        laundrydatamen =  LaundryServices.objects.filter(vendor=number,sercategory='laundry',gencategory='mens').all()
        laundrydatawomen =  LaundryServices.objects.filter(vendor=number,sercategory='laundry',gencategory='womens').all()
        drydatawomen =  LaundryServices.objects.filter(vendor=number,sercategory='drycleaning',gencategory='womens').all()
        drydatamen =  LaundryServices.objects.filter(vendor=number,sercategory='drycleaning',gencategory='mens').all()
        return render(request,'laundryservicepage.html',{'id':id,'laundrydatamen':laundrydatamen,'laundrydatawomen':laundrydatawomen,'drydatawomen':drydatawomen,'drydatamen':drydatamen})
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def addlaundrypage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            laundrydata =  LaundryServices.objects.filter(vendor=user).all()
            return render(request,'laundrypage.html',{'active_page': 'addlaundrypage','laundrydata':laundrydata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def addlaundryitem(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            itemname = request.POST.get('itemname')
            servicecategory = request.POST.get('servicecategory')
            itemprice = request.POST.get('itemprice')
            gendercategory = request.POST.get('gendercategory')
            LaundryServices.objects.create(vendor=user,sercategory=servicecategory,price=itemprice,name=itemname,gencategory=gendercategory)
            laundrydata =  LaundryServices.objects.filter(vendor=user).all()
            return render(request,'laundrypage.html',{'laundrydata':laundrydata})
        else:
            return redirect('loginpage') 
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

def deletelaundryitem(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            LaundryServices.objects.filter(vendor=user,id=id).delete()
            laundrydata =  LaundryServices.objects.filter(vendor=user).all()
            return render(request,'laundrypage.html',{'laundrydata':laundrydata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


def changeroompage(request,id):
    # try:
        if request.user.is_authenticated:
            user=request.user
            invoice_id = id
            # invcitemdata = InvoiceItem.objects.filter(vendor=user,invoice_id=invoice_id)
            # for i in invcitemdata:
            #     roomname = i.description
            #     Rooms.objects.filter(vendor=user,room_name=roomname)
            valid_room_names = Rooms.objects.filter(vendor=user).values_list('room_name', flat=True)
            # Filter InvoiceItem records where the description matches a valid room name
            invcitemdata = InvoiceItem.objects.filter(vendor=user, invoice_id=invoice_id, description__in=valid_room_names)
            
            avlrooms = Rooms.objects.filter(vendor=user,checkin=0)
            return render(request,'changerom.html',{'avlrooms':avlrooms,'invcitemdata':invcitemdata,'invoice_id':invoice_id})
           


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Rooms, InvoiceItem

@csrf_exempt
def change_rooms(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        invoice_id = data.get('invoice_id')
        current_rooms = data.get('current_rooms', [])
        available_rooms = data.get('available_rooms', [])

        if len(current_rooms) != len(available_rooms):
            return JsonResponse({'success': False, 'message': 'Room count mismatch'})
        print(current_rooms,available_rooms,"js data")
        # Process the room changes
        try:
            for current_room, available_room in zip(current_rooms, available_rooms):
                current_room_id = current_room['id']
                available_room_id = available_room['id']
                current_description = current_room['description']
                available_room_name = available_room['room_name']
                print(current_room_id,"current roomid")

               
                orginvc = Invoice.objects.get(id=invoice_id)
                gustfirstroom = Gueststay.objects.get(id=orginvc.customer.id)
                checks = False
                if int(gustfirstroom.roomno) == int(current_description):
                        print("haan main room liya hai ")
                        changeroomno = int(available_room_name)
                        
                        if Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,room_name=current_description):
                            roomcolourdata = Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,room_name=current_description)
                            for i in roomcolourdata:
                                colourcode = i.checkin
                                Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,id=available_room_id).update(checkin=colourcode)
                            
                            Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,room_name=current_description).update(checkin=0)
                            InvoiceItem.objects.filter(id=current_room_id).update(description=changeroomno)
                            checks=True
                            Gueststay.objects.filter(id=orginvc.customer.id).update(roomno=changeroomno)

                            
                else:
                        changeroomno = int(available_room_name)
                        print("current room alag hai ")
                        roomcolourdata = Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,room_name=current_description)
                        for i in roomcolourdata:
                            colourcode = i.checkin
                            Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,id=available_room_id).update(checkin=colourcode)
                        Rooms.objects.filter(vendor_id=gustfirstroom.vendor.id,room_name=current_description).update(checkin=0)
                        InvoiceItem.objects.filter(vendor_id=gustfirstroom.vendor.id,id=current_room_id).update(description=changeroomno)
                        checks=True
                       
                roomobj = Rooms.objects.get(vendor_id=gustfirstroom.vendor.id,room_name=current_description)
                Booking.objects.filter(vendor=gustfirstroom.vendor,gueststay=gustfirstroom,room=roomobj).update(
                     room_id=available_room_id
                )

                saveguestdatsid = gustfirstroom.saveguestid
                if saveguestdatsid:
                    chcksdatas = RoomBookAdvance.objects.filter(vendor=gustfirstroom.vendor,saveguestdata_id=saveguestdatsid,
                                roomno=roomobj)
                    if chcksdatas:
                         RoomBookAdvance.objects.filter(vendor=gustfirstroom.vendor,saveguestdata_id=saveguestdatsid,
                                roomno=roomobj).update(
                                     roomno_id=available_room_id
                                )
                    else:
                         pass
                else:
                     pass
                         
                         

                
                if checks==True:
                    roomcsdata = Rooms.objects.get(vendor_id=gustfirstroom.vendor.id,room_name=current_description)
                    avlblsrid = Rooms.objects.get(vendor_id=gustfirstroom.vendor.id,id=available_room_id)
                    
                    if roomcsdata.room_type == avlblsrid.room_type:
                            pass
                    else:
                        saveguestdata = Gueststay.objects.get(id=orginvc.customer.id)
                        checkindate = saveguestdata.checkindate
                        checkoutdate = saveguestdata.checkoutdate

                        current_date = checkindate
                        while current_date < checkoutdate:
                                    avaiblecategory = RoomsInventory.objects.get(room_category=avlblsrid.room_type,date=current_date)
                                    currentcategory = RoomsInventory.objects.get(room_category=roomcsdata.room_type,date=current_date)

                                    # availbable data
                                    totalavlbb = avaiblecategory.total_availibility -1
                                    totalbookbb = avaiblecategory.booked_rooms +1
                                    RoomsInventory.objects.filter(room_category=avlblsrid.room_type,date=current_date).update(
                                        total_availibility = totalavlbb,
                                        booked_rooms= totalbookbb
                                    )

                                    

                                    # current book data
                                    totalavalcc = currentcategory.total_availibility+1
                                    totalbookcc = currentcategory.booked_rooms-1
                                    RoomsInventory.objects.filter(room_category=roomcsdata.room_type,date=current_date).update(
                                        total_availibility = totalavalcc,
                                        booked_rooms= totalbookcc
                                    )
                                    
                                    current_date += timedelta(days=1)   
                        user = gustfirstroom.vendor  

                        if VendorCM.objects.filter(vendor=user):
                                start_date = str(checkindate.date())
                                end_date = str(checkoutdate.date())
                                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                print("vendorcm run")
                                thread.start()
                                # for dynamic pricing
                                if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                    thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                    print("vendorcm rate run")
                                    thread.start()
                                else:
                                    pass
                        else:
                                pass      
                
                        

            return JsonResponse({'success': True, 'message': 'Rooms changed successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})



def changeroombooking(request,id):
      if request.user.is_authenticated:
            user=request.user
            roombook_id = id
            # invcitemdata = InvoiceItem.objects.filter(vendor=user,invoice_id=invoice_id)
            # for i in invcitemdata:
            #     roomname = i.description
            #     Rooms.objects.filter(vendor=user,room_name=roomname)
            valid_room_names = Rooms.objects.filter(vendor=user).values_list('room_name', flat=True)
            # Filter InvoiceItem records where the description matches a valid room name
            # invcitemdata = InvoiceItem.objects.filter(vendor=user, invoice_id=invoice_id, description__in=valid_room_names)
            if RoomBookAdvance.objects.filter(vendor=user,id=roombook_id).exists():
                rombokdata = RoomBookAdvance.objects.get(vendor=user,id=roombook_id)
                saveguestid = rombokdata.saveguestdata.id
                Bookedrooms = RoomBookAdvance.objects.filter(vendor=user,saveguestdata_id=saveguestid)


            
            avlrooms = Rooms.objects.filter(vendor=user,checkin=0)
            return render(request,'changerombook.html',{'avlrooms':avlrooms,'invcitemdata':Bookedrooms,'invoice_id':saveguestid})
           
from datetime import timedelta
import threading
from .newcode import *
# Create your views here.
from .dynamicrates import *

# def change_rooms_book_url(request):
#     if request.method == 'POST':
#             data = json.loads(request.body)

#             invoice_id = data.get('invoice_id')
#             current_rooms = data.get('current_rooms', [])
#             available_rooms = data.get('available_rooms', [])

#             if len(current_rooms) != len(available_rooms):
#                 return JsonResponse({'success': False, 'message': 'Room count mismatch'})

#             # Process the room changes
#             try:
#                 for current_room, available_room in zip(current_rooms, available_rooms):
#                     current__room_book_id = current_room['id']
#                     available_room_id = available_room['id']
#                     current_description = current_room['description']
#                     available_room_name = available_room['room_name']

#                     # print('savguestid',invoice_id)
#                     rbadvc = RoomBookAdvance.objects.get(id=current__room_book_id)
#                     roomcsdata = Rooms.objects.get(id=rbadvc.roomno.id)
#                     colorcode = roomcsdata.checkin
#                     if colorcode == 0 or colorcode == 4:
#                         Rooms.objects.filter(id=rbadvc.roomno.id).update(checkin=0)
#                     avlblsrid = Rooms.objects.get(id=available_room_id)
#                     RoomBookAdvance.objects.filter(id=current__room_book_id).update(
#                          roomno=avlblsrid
#                     )
                    
#                     Booking.objects.filter(advancebook=invoice_id,room_id=rbadvc.roomno.id).update(
#                          room_id=available_room_id
#                     )

#                     if roomcsdata.room_type == avlblsrid.room_type:
#                          pass
#                     else:
#                         saveguestdata = SaveAdvanceBookGuestData.objects.get(id=invoice_id)
#                         checkindate = saveguestdata.bookingdate
#                         checkoutdate = saveguestdata.checkoutdate

#                         current_date = checkindate
#                         while current_date < checkoutdate:
#                             avaiblecategory = RoomsInventory.objects.get(room_category=avlblsrid.room_type,date=current_date)
#                             currentcategory = RoomsInventory.objects.get(room_category=roomcsdata.room_type,date=current_date)

#                             # availbable data
#                             totalavlbb = avaiblecategory.total_availibility -1
#                             totalbookbb = avaiblecategory.booked_rooms +1
#                             RoomsInventory.objects.filter(room_category=avlblsrid.room_type,date=current_date).update(
#                                 total_availibility = totalavlbb,
#                                 booked_rooms= totalbookbb
#                             )

                            

#                             # current book data
#                             totalavalcc = currentcategory.total_availibility+1
#                             totalbookcc = currentcategory.booked_rooms-1
#                             RoomsInventory.objects.filter(room_category=roomcsdata.room_type,date=current_date).update(
#                                 total_availibility = totalavalcc,
#                                 booked_rooms= totalbookcc
#                             )
                            
#                             current_date += timedelta(days=1)
                        
#                         # call dynamic rate functon
#                         user = currentcategory.vendor
#                         if VendorCM.objects.filter(vendor=user):
#                                 start_date = str(checkindate)
#                                 end_date = str(checkoutdate)
#                                 thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                                 print("vendorcm run")
#                                 thread.start()
#                                 # for dynamic pricing
#                                 if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
#                                     thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                                     print("vendorcm rate run")
#                                     thread.start()
#                                 else:
#                                     pass
#                         else:
#                                 pass
                            
                    
                            

#                 return JsonResponse({'success': True, 'message': 'Rooms changed successfully'})
#             except Exception as e:
#                 return JsonResponse({'success': False, 'message': str(e)})

#     return JsonResponse({'success': False, 'message': 'Invalid request method'})


from django.http import JsonResponse
from django.db.models import F
from datetime import timedelta
import json
import threading

# def change_rooms_book_url(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)

#         invoice_id = data.get('invoice_id')
#         current_rooms = data.get('current_rooms', [])
#         available_rooms = data.get('available_rooms', [])

#         if len(current_rooms) != len(available_rooms):
#             return JsonResponse({'success': False, 'message': 'Room count mismatch'})

#         # Process the room changes
#         try:
#             for current_room, available_room in zip(current_rooms, available_rooms):
#                 current__room_book_id = current_room['id']
#                 available_room_id = available_room['id']
#                 current_description = current_room['description']
#                 available_room_name = available_room['room_name']

#                 # Get current room booking and details
#                 rbadvc = RoomBookAdvance.objects.get(id=current__room_book_id)
#                 roomcsdata = Rooms.objects.get(id=rbadvc.roomno.id)
#                 colorcode = roomcsdata.checkin

#                 # Reset check-in status for the current room
#                 if colorcode == 0 or colorcode == 4:
#                     Rooms.objects.filter(id=rbadvc.roomno.id).update(checkin=0)

#                 # Update the new room in RoomBookAdvance
#                 avlblsrid = Rooms.objects.get(id=available_room_id)
#                 RoomBookAdvance.objects.filter(id=current__room_book_id).update(
#                     roomno=avlblsrid
#                 )

#                 # Update the Booking table with the new room
#                 Booking.objects.filter(advancebook=invoice_id, room_id=rbadvc.roomno.id).update(
#                     room_id=available_room_id
#                 )

#                 # Check if room types are different, then update inventory
#                 if roomcsdata.room_type != avlblsrid.room_type:
#                     saveguestdata = SaveAdvanceBookGuestData.objects.get(id=invoice_id)
#                     checkindate = saveguestdata.bookingdate
#                     checkoutdate = saveguestdata.checkoutdate

#                     current_date = checkindate
#                     while current_date < checkoutdate:
#                         # Fetch inventory records for the current date
#                         try:
#                             avaiblecategory = RoomsInventory.objects.select_for_update().get(room_category=avlblsrid.room_type, date=current_date)
#                             currentcategory = RoomsInventory.objects.select_for_update().get(room_category=roomcsdata.room_type, date=current_date)
#                         except RoomsInventory.DoesNotExist:
#                             return JsonResponse({'success': False, 'message': f'Inventory record not found for date {current_date}'})

#                         # Update the available room category
#                         if avaiblecategory.total_availibility > 0:
#                             avaiblecategory.total_availibility = F('total_availibility') - 1
#                             avaiblecategory.booked_rooms = F('booked_rooms') + 1
#                             avaiblecategory.save()

#                         # Update the current room category
#                         if currentcategory.booked_rooms > 0:
#                             currentcategory.total_availibility = F('total_availibility') + 1
#                             currentcategory.booked_rooms = F('booked_rooms') - 1
#                             currentcategory.save()

#                         # Move to the next date
#                         current_date += timedelta(days=1)

#                     # Call dynamic rate update function if VendorCM exists
#                     user = saveguestdata.vendor
#                     if VendorCM.objects.filter(vendor=user).exists():
#                         start_date = str(checkindate)
#                         end_date = str(checkoutdate)

#                         # Start a thread for updating inventory
#                         thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
#                         thread.start()

#                         # Start a thread for dynamic pricing if active
#                         if VendorCM.objects.filter(vendor=user, dynamic_price_active=True).exists():
#                             rate_thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
#                             rate_thread.start()

#             return JsonResponse({'success': True, 'message': 'Rooms changed successfully'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'message': str(e)})

#     return JsonResponse({'success': False, 'message': 'Invalid request method'})



from django.db import transaction

def change_rooms_book_url(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        invoice_id = data.get('invoice_id')
        current_rooms = data.get('current_rooms', [])
        available_rooms = data.get('available_rooms', [])

        if len(current_rooms) != len(available_rooms):
            return JsonResponse({'success': False, 'message': 'Room count mismatch'})

        try:
            # Using atomic transaction for consistency
            with transaction.atomic():
                for current_room, available_room in zip(current_rooms, available_rooms):
                    current__room_book_id = current_room['id']
                    available_room_id = available_room['id']

                    # Fetch current RoomBookAdvance and room details
                    rbadvc = RoomBookAdvance.objects.select_related('roomno').get(id=current__room_book_id)
                    roomcsdata = rbadvc.roomno

                    # Reset check-in status for the current room if necessary
                    if roomcsdata.checkin in [0, 4]:
                        Rooms.objects.filter(id=roomcsdata.id).update(checkin=0)

                    # Update the new room in RoomBookAdvance
                    RoomBookAdvance.objects.filter(id=current__room_book_id).update(roomno_id=available_room_id)

                    # Update the Booking table with the new room
                    Booking.objects.filter(advancebook=invoice_id, room_id=roomcsdata.id).update(room_id=available_room_id)

                    # If room types are different, update inventory
                    avlblsrid = Rooms.objects.get(id=available_room_id)
                    if roomcsdata.room_type != avlblsrid.room_type:
                        saveguestdata = SaveAdvanceBookGuestData.objects.get(id=invoice_id)
                        checkindate = saveguestdata.bookingdate
                        checkoutdate = saveguestdata.checkoutdate

                        current_date = checkindate
                        while current_date < checkoutdate:
                            try:
                                # Fetch and update inventory using atomic updates
                                RoomsInventory.objects.filter(room_category=avlblsrid.room_type, date=current_date).update(
                                    total_availibility=F('total_availibility') - 1,
                                    booked_rooms=F('booked_rooms') + 1
                                )

                                RoomsInventory.objects.filter(room_category=roomcsdata.room_type, date=current_date).update(
                                    total_availibility=F('total_availibility') + 1,
                                    booked_rooms=F('booked_rooms') - 1
                                )

                            except RoomsInventory.DoesNotExist:
                                return JsonResponse({'success': False, 'message': f'Inventory record not found for date {current_date}'})

                            current_date += timedelta(days=1)

                        # Start background tasks for inventory and pricing updates
                        user = saveguestdata.vendor

                        if VendorCM.objects.filter(vendor=user):
                                start_date = str(checkindate)
                                end_date = str(checkoutdate)
                                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                print("vendorcm run")
                                thread.start()
                                # for dynamic pricing
                                if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                    thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                    print("vendorcm rate run")
                                    thread.start()
                                else:
                                    pass
                        else:
                                pass
            return JsonResponse({'success': True, 'message': 'Rooms changed successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Failed to change rooms: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})