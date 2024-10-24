from . models import *
import qrcode
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
import re
from PIL import Image, ImageDraw, ImageFont



def Website(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            qr=reviewQr.objects.filter(vendor=user).all()
            roomdata = Rooms.objects.filter(vendor=user).order_by('room_name')
            linkdatacount = websitelinks.objects.filter(vendor=user).count()
            linkdata = websitelinks.objects.filter(vendor=user)
            return render(request,'qrindex.html',{'qr':qr,'roomdata':roomdata,'active_page': 'qrindex','linkdatacount':linkdatacount,'linkdata':linkdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

# def Showqr(request,id):
#     try:
#         if request.user.is_authenticated:
#             user = request.user
#             checkdata = reviewQr.objects.filter(vendor=user, room_no=id).exists()
#             if checkdata is True:
#                 qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#                 return render(request, 'qr_code.html', {'qrdata':qrdata})
#             else:
#                 roomid = Rooms.objects.get(vendor=user, id=id)
#                 # url pattern
#                 url = f"https://www.billzify.com/IGfKg/{roomid.id}lskgyh"  
#                 # Generate the QR code
#                 qr = qrcode.QRCode(
#                     version=1,
#                     error_correction=qrcode.constants.ERROR_CORRECT_H,  # Use high error correction to allow for logo
#                     box_size=10,
#                     border=4,
#                 )
#                 qr.add_data(url)
#                 qr.make(fit=True)
                
#                 qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

#                 # Get the logo image path from the static files
#                 logo_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'img', 'newshadowlogo.png')
#                 print(f"Logo path: {logo_path}")  # Debug statement to print the logo path

#                 if not os.path.exists(logo_path):
#                     print(f"Logo file not found at: {logo_path}")
#                     return HttpResponseNotFound("Logo image not found.")
                
#                 try:
#                     # Open the logo image
#                     logo = Image.open(logo_path).convert("RGBA")

#                     # Calculate logo size and position
#                     qr_width, qr_height = qr_image.size
#                     logo_size = qr_width // 5
#                     logo = logo.resize((logo_size, logo_size), Image.ANTIALIAS)
#                     logo_position = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

#                     # Paste the logo onto the QR code
#                     qr_image.paste(logo, logo_position, logo)
#                     print("Logo pasted successfully")  # Debug statement to indicate logo was pasted

#                     # Add text (room number) to the QR code
#                     draw = ImageDraw.Draw(qr_image)
#                     font_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'fonts', 'arial.ttf')  # Ensure you have a font file
#                     font_size = 10
#                     font = ImageFont.truetype(font_path, font_size)
#                     print(f"Font loaded: {font_path}")  # Debug statement to indicate font loaded

#                     text = f"Room {roomid.room_name}"
#                     text_width, text_height = draw.textsize(text, font=font)
#                     text_position = ((qr_width - text_width) // 2, qr_height - text_height - 10)  # Positioning text at the bottom

#                     draw.text(text_position, text, font=font, fill="black")
#                     print("Text added successfully")  # Debug statement to indicate text was added

#                 except Exception as e:
#                     print(f"Error processing the logo or adding text: {e}")
#                     return HttpResponse("Error processing the logo or adding text.", status=500)
                
#                 # Continue processing the QR code and saving it to the model
#                 buffer = BytesIO()
#                 qr_image.save(buffer, format="PNG")
#                 buffer.seek(0)

#                 # Create a Django file from the in-memory file
#                 file_name = f'user_{user.id}_qr.png'
#                 file_content = ContentFile(buffer.read(), name=file_name)

#                 reviewQr.objects.create(vendor=user, room_no=roomid, qrimage=file_content)

#                 response = HttpResponse(content_type="image/png")
#                 qr_image.save(response, "PNG")
#                 qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#                 return render(request, 'qr_code.html', {'qrdata':qrdata})
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)
    
# try this code in which remove billzify logo in center and its working properly
# def Showqr(request,id):
#     try:
#         if request.user.is_authenticated:
#             user = request.user
#             checkdata = reviewQr.objects.filter(vendor=user, room_no=id).exists()
#             if checkdata is True:
#                 qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#                 return render(request, 'qr_code.html', {'qrdata': qrdata})
#             else:
#                 roomid = Rooms.objects.get(vendor=user, id=id)
#                 # URL pattern
#                 url = f"http://172.20.10.3:8000/IGfKg/{roomid.id}lskgyh"
#                 # Generate the QR code
#                 qr = qrcode.QRCode(
#                     version=1,
#                     error_correction=qrcode.constants.ERROR_CORRECT_H,
#                     box_size=10,
#                     border=4,
#                 )
#                 qr.add_data(url)
#                 qr.make(fit=True)

#                 qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

#                 try:
#                     # Add text (room number) to the QR code
#                     draw = ImageDraw.Draw(qr_image)
#                     font_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'fonts', 'arial.ttf')  # Ensure you have a font file
#                     font_size = 20  # Adjust font size as needed
#                     font = ImageFont.truetype(font_path, font_size)

#                     text = f"Room {roomid.room_name}"
#                     text_width, text_height = draw.textsize(text, font=font)
#                     qr_width, qr_height = qr_image.size
#                     text_position = ((qr_width - text_width) // 2, qr_height - text_height - 10)  # Positioning text at the bottom

#                     draw.text(text_position, text, font=font, fill="black")

#                 except Exception as e:
#                     print(f"Error adding text: {e}")
#                     return HttpResponse("Error adding text.", status=500)

#                 # Continue processing the QR code and saving it to the model
#                 buffer = BytesIO()
#                 qr_image.save(buffer, format="PNG")
#                 buffer.seek(0)

#                 # Create a Django file from the in-memory file
#                 file_name = f'user_{user.id}_qr.png'
#                 file_content = ContentFile(buffer.read(), name=file_name)

#                 reviewQr.objects.create(vendor=user, room_no=roomid, qrimage=file_content)

#                 response = HttpResponse(content_type="image/png")
#                 qr_image.save(response, "PNG")
#                 qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#                 return render(request, 'qr_code.html', {'qrdata': qrdata})
#         else:
#             return redirect('loginpage')
#     except Exception as e:
#         return render(request, '404.html', {'error_message': str(e)}, status=500)
    

# new code remove all the try and except

# def Showqr(request, id):
#     if request.user.is_authenticated:
#         user = request.user
        
#         # Check if reviewQr exists for the vendor and room_no
#         if reviewQr.objects.filter(vendor=user, room_no=id).exists():
#             qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#             return render(request, 'qr_code.html', {'qrdata': qrdata})
        
#         # If reviewQr does not exist, try to get the room details
#         roomid = None
#         try:
#             roomid = Rooms.objects.get(vendor=user, id=id)
#         except Rooms.DoesNotExist:
#             return render(request, '404.html', {'error_message': 'Room not found'}, status=404)
        
#         # URL pattern
#         url = f"https://www.billzify.com/IGfKg/{roomid.id}lskgyh"
#         # Generate the QR code
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_H,
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(url)
#         qr.make(fit=True)

#         qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

#         # Add text (room number) to the QR code
#         draw = ImageDraw.Draw(qr_image)
#         font_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'fonts', 'arial.ttf')  # Ensure you have a font file
#         font_size = 20  # Adjust font size as needed
#         font = ImageFont.truetype(font_path, font_size)

#         text = f"Room {roomid.room_name}"
#         text_width, text_height = draw.textsize(text, font=font)
#         qr_width, qr_height = qr_image.size
#         text_position = ((qr_width - text_width) // 2, qr_height - text_height - 10)  # Positioning text at the bottom

#         draw.text(text_position, text, font=font, fill="black")

#         # Continue processing the QR code and saving it to the model
#         buffer = BytesIO()
#         qr_image.save(buffer, format="PNG")
#         buffer.seek(0)

#         # Create a Django file from the in-memory file
#         file_name = f'user_{user.id}_qr.png'
#         file_content = ContentFile(buffer.read(), name=file_name)

#         # Save the QR code image to reviewQr model
#         reviewQr.objects.create(vendor=user, room_no=roomid, qrimage=file_content)

#         # Return the QR code image as HTTP response
#         response = HttpResponse(content_type="image/png")
#         qr_image.save(response, "PNG")
#         qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
#         return render(request, 'qr_code.html', {'qrdata': qrdata})

#     else:
#         return redirect('loginpage')


def Showqr(request, id):
    if request.user.is_authenticated:
        user = request.user
        
        # Check if reviewQr exists for the vendor and room_no
        if reviewQr.objects.filter(vendor=user, room_no=id).exists():
            qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
            return render(request, 'qr_code.html', {'qrdata': qrdata})
        
        # If reviewQr does not exist, try to get the room details
        try:
            roomid = Rooms.objects.get(vendor=user, id=id)
        except Rooms.DoesNotExist:
            return render(request, '404.html', {'error_message': 'Room not found'}, status=404)
        
        # URL pattern
        url = f"https://www.billzify.com/IGfKg/{roomid.id}lskgyh"
        
        # Generate the QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Add text (room number) to the QR code
        draw = ImageDraw.Draw(qr_image)
        text = f"Room {roomid.room_name}"
        font_size = 30
        font = ImageFont.truetype("arial.ttf", font_size)  # Load Arial font with larger size
        
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        qr_width, qr_height = qr_image.size
        text_position = ((qr_width - text_width) // 2, qr_height - text_height - 20)  # Positioning text at the bottom with larger margin

        draw.text(text_position, text, font=font, fill="black")

        
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Create a Django file from the in-memory file
        file_name = f'user_{user.id}_qr.png'
        file_content = ContentFile(buffer.read(), name=file_name)

        # Save the QR code image to reviewQr model
        reviewQr.objects.create(vendor=user, room_no=roomid, qrimage=file_content)

        # Return the QR code image as HTTP response
        response = HttpResponse(content_type="image/png")
        qr_image.save(response, "PNG")
        qrdata = reviewQr.objects.filter(vendor=user, room_no=id)
        return render(request, 'qr_code.html', {'qrdata': qrdata})

    else:
        return redirect('loginpage')




def IGfKg(request,id):
    try:
        numbers = re.findall(r'\d+', id)
        number = int(numbers[0]) if numbers else None
        roomdata = reviewQr.objects.filter(room_no=number)
        roomsdata = Rooms.objects.filter(id=number) 
        print(roomsdata)
        for i in roomsdata:
            user =i.vendor
        linkdata=websitelinks.objects.filter(vendor = user )
        return render(request,'IGfKg.html',{'id':id,'roomdata':roomdata,'linkdata':linkdata})
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def yourwebpage(request,rid):
    try:
        if request.user.is_authenticated:
            user=request.user
            roomdata = Rooms.objects.filter(vendor=user,id=rid)
            return render(request,'manageqrbuttons.html',{'roomdata':roomdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def addwebsitedata(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            checkdata = websitelinks.objects.filter(vendor=user).exists()
            if checkdata is False:
                logoname = request.POST.get('logoname')
                googlelink = request.POST.get('googlelink')
                Websitelink = f"https://www.billzify.com/mobileview/{user}"  
                laundryserviceurl = f"https://www.billzify.com/laundrysrvs/{user.id}lskgyh10"  
                websitelinks.objects.create(vendor=user,logoname=logoname,googlelink=googlelink,websitelink=Websitelink,laundryurl=laundryserviceurl)
                qr=reviewQr.objects.filter(vendor=user).all()
                roomdata = Rooms.objects.filter(vendor=user)
                return render(request,'qrindex.html',{'qr':qr,'roomdata':roomdata,'active_page': 'qrindex'})
            else:
                qr=reviewQr.objects.filter(vendor=user).all()
                roomdata = Rooms.objects.filter(vendor=user)
                return render(request,'qrindex.html',{'qr':qr,'roomdata':roomdata,'active_page': 'qrindex'})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def updatewebsitedata(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            logoname = request.POST.get('logoname')
            googlelink = request.POST.get('googlelink')
            checkdata = websitelinks.objects.filter(vendor=user).update(vendor=user,logoname=logoname,googlelink=googlelink)
            qr=reviewQr.objects.filter(vendor=user).all()
            roomdata = Rooms.objects.filter(vendor=user)
            linkdata = websitelinks.objects.filter(vendor=user)
            return render(request,'qrindex.html',{'qr':qr,'roomdata':roomdata,'active_page': 'qrindex','linkdata':linkdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

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
    

def addfoodurlbyqr(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            dataid = request.POST.get('dataid')
            FoodWebsitelink = request.POST.get('FoodWebsitelink')
            reviewQr.objects.filter(vendor=user,room_no=dataid).update(foodurl=FoodWebsitelink)
            qr=reviewQr.objects.filter(vendor=user).all()
            roomdata = Rooms.objects.filter(vendor=user)
            linkdata = websitelinks.objects.filter(vendor=user)
            return render(request,'qrindex.html',{'qr':qr,'roomdata':roomdata,'active_page': 'qrindex','linkdata':linkdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def deleteroomoffersweb(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            offerwebsitevendor.objects.filter(vendor=user,id=id).delete()
            return redirect('websetting')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)