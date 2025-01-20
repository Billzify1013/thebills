from django.shortcuts import render, redirect, HttpResponse
from .models import *
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import datetime
from datetime import datetime, timedelta
from django.db.models import Max
import requests
from django.conf import settings
import urllib.parse
from django.db.models import Sum
from django.urls import reverse
import threading
from .newcode import *
# Create your views here.
from .dynamicrates import *


def setting(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            loyltydata = loylty_data.objects.filter(vendor=user)
            taxdata = Taxes.objects.filter(vendor=user)
            category = RoomsCategory.objects.filter(vendor=user)
            vendorcms = VendorCM.objects.none()
            if VendorCM.objects.filter(vendor=user,admin_dynamic_active=True):
                vendorcms = VendorCM.objects.filter(vendor=user,admin_dynamic_active=True)
            return render(
                request,
                "settings.html",
                {
                    "active_page": "setting",
                    "category": category,
                    "loyltydata": loyltydata,
                    "taxdata": taxdata,
                    'vendorcms':vendorcms
                },
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def activeloylty(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            loyltypersantage = request.POST.get("loyltypersantage")
            loylty_data.objects.create(
                vendor=user, loylty_rate_prsantage=loyltypersantage, Is_active=True
            )
            messages.success(request, "Loylty Activated")
            return redirect("setting")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def updateloylty(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            loyltypersantage = request.POST.get("loyltypersantage")
            checkbox = request.POST.get("checkbox")
     
            if checkbox is None:
                loylty_data.objects.filter(vendor=user).update(
                    loylty_rate_prsantage=loyltypersantage, Is_active=False
                )

            else:
                loylty_data.objects.filter(vendor=user).update(
                    loylty_rate_prsantage=loyltypersantage, Is_active=True
                )
            messages.success(request, "Loylty updates Succesfully")
            return redirect("setting")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def deletetaxitem(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if Taxes.objects.filter(vendor=user, id=id).exists():
                Taxes.objects.filter(vendor=user, id=id).delete()
                messages.success(request, "Item Delete Succesfully")
            else:
                messages.error(request, "Item note matched")
            return redirect("setting")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def deletecategory(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            if RoomsCategory.objects.filter(vendor=user, id=id).exists():
                RoomsCategory.objects.filter(vendor=user, id=id).delete()
                messages.success(request, "Category Delete Succesfully")
            else:
                messages.error(request, "Category note matched")
            return redirect("setting")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




# ajax book date all rooms data
@csrf_exempt
def getloyltydataajax(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            Mobile = request.POST["Mobile"]
            data = loylty_Guests_Data.objects.filter(
                Q(vendor=user, guest_contact=Mobile)
            ).all()
            if data.exists():
                return JsonResponse(
                    list(
                        data.values("id", "guest_name", "guest_contact", "loylty_point")
                    ),
                    safe=False,
                )
            else:
                return JsonResponse(
                    {"error": "No data found matching the query"}, status=404
                )
        else:
            return JsonResponse(
                {"error": "User not authenticated or invalid request method"},
                status=400,
            )
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


@csrf_exempt
def deleteloyltyajaxdata(request):
    try:
        if request.method == "POST":
            if request.user.is_authenticated:
                user = request.user
                subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
                if subuser:
                    user = subuser.vendor  
                Mobile = request.POST.get("Mobile")
                try:
                    # Update loyalty points to 0 for the given vendor and guest contact
                    data = loylty_Guests_Data.objects.filter(
                        vendor=user, guest_contact=Mobile
                    ).update(loylty_point=0)

                    if data > 0:  # Check if any records were updated
                        updated_data = loylty_Guests_Data.objects.filter(
                            vendor=user, guest_contact=Mobile
                        )
                        return JsonResponse(
                            list(
                                updated_data.values(
                                    "id", "guest_name", "guest_contact", "loylty_point"
                                )
                            ),
                            safe=False,
                        )
                    else:
                        return JsonResponse(
                            {"error": "No data found matching the query"}, status=404
                        )

                except loylty_Guests_Data.DoesNotExist:
                    return JsonResponse(
                        {"error": "No data found matching the query"}, status=404
                    )

            else:
                return JsonResponse({"error": "User not authenticated"}, status=401)

        else:
            return JsonResponse({"error": "Invalid request method"}, status=405)
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


@csrf_exempt
def getguestdatabyajaxinform(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            Mobile = request.POST["Mobile"]
            data = Gueststay.objects.filter(Q(vendor=user, guestphome=Mobile))
            if data.exists():
                return JsonResponse(
                    list(
                        data.values(
                            "guestname",
                            "guestemail",
                            "guestcity",
                            "guestcountry",
                            "gueststates",
                            "guestidtypes",
                            "guestsdetails",
                            "ar",
                            "dp"
                        )
                    ),
                    safe=False,
                )
            else:
                return JsonResponse(
                    {"error": "No data found matching the query"}, status=404
                )
        else:
            return JsonResponse(
                {"error": "User not authenticated or invalid request method"},
                status=400,
            )
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


@csrf_exempt
def getrateplandata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            Rateplanid = request.POST["Rateplanid"]

            data = RatePlan.objects.filter(Q(vendor=user, id=Rateplanid))

            if data.exists():
                return JsonResponse(
                    list(
                        data.values(
                            "base_price",
                            "max_persons",
                            "additional_person_price",
                            "rate_plan_name",
                            "rate_plan_code",
                        )
                    ),
                    safe=False,
                )
            else:
                return JsonResponse(
                    {"error": "No data found matching the query"}, status=404
                )
        else:
            return JsonResponse(
                {"error": "User not authenticated or invalid request method"},
                status=400,
            )
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def creditmanage(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            customerdata = CustomerCredit.objects.filter(vendor=user)
            total_amount = CustomerCredit.objects.filter(vendor=user).aggregate(
                total=Sum("amount")
            )["total"]
            return render(
                request,
                "showcredit.html",
                {
                    "customerdata": customerdata,
                    "active_page": "creditmanage",
                    "total_amount": total_amount,
                },
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def addpaymentininvoice(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcid = id
            if Invoice.objects.filter(vendor=user, id=invcid).exists():
                invcdata = Invoice.objects.get(vendor=user, id=invcid)
                dueamount = invcdata.Due_amount
                creditid = CustomerCredit.objects.get(vendor=user, invoice_id=invcid)
                creditid_id = creditid.id
            return render(
                request,
                "showcreditaddpayment.html",
                {
                    "active_page": "creditmanage",
                    "dueamount": dueamount,
                    "creditid": creditid_id,
                    "invcid": invcid,
                },
            )
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

def addcreditcustomer(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            amount = request.POST.get("amount")
            duedate = request.POST.get("duedate")
            if CustomerCredit.objects.filter(
                vendor=user,
                customer_name=name,
                phone=phone,
                amount=amount,
                due_date=duedate,
            ).exists():
                return redirect("creditmanage")
            else:
                CustomerCredit.objects.create(
                    vendor=user,
                    customer_name=name,
                    phone=phone,
                    amount=amount,
                    due_date=duedate,
                    invoice=None,
                )
                messages.success(request, "Data Added Succesfully!")
                return redirect("creditmanage")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def saveinvoicetocredit(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            dataid = id
            if CustomerCredit.objects.filter(vendor=user, id=dataid).exists():
                # Get the current date
                invccurrentdate = datetime.now().date()

                # Fetch the maximum invoice number for today for the given user
                max_invoice_today = Invoice.objects.filter(
                    vendor=user, invoice_date=invccurrentdate, foliostatus=True
                ).aggregate(max_invoice_number=Max("invoice_number"))[
                    "max_invoice_number"
                ]

                # Determine the next invoice number
                if max_invoice_today is not None:
                    # Extract the numeric part of the latest invoice number and increment it
                    try:
                        current_number = int(max_invoice_today.split("-")[-1])
                        next_invoice_number = current_number + 1
                    except (ValueError, IndexError):
                        # Handle the case where the invoice number format is unexpected
                        next_invoice_number = 1
                else:
                    next_invoice_number = 1

                # Generate the invoice number
                invoice_number = f"INV-{invccurrentdate}-{next_invoice_number}"

                # Check if the generated invoice number already exists
                while Invoice.objects.filter(
                    vendor=user, invoice_number=invoice_number
                ).exists():
                    next_invoice_number += 1
                    invoice_number = f"INV-{invccurrentdate}-{next_invoice_number}"

                invcdata = CustomerCredit.objects.get(vendor=user, id=dataid)
                if invcdata.invoice is None:
                    CustomerCredit.objects.filter(vendor=user, id=dataid).delete()
                    messages.success(request, "Credit Sattle done Succesfully!")
                    return redirect("creditmanage")
                else:
                    invoiceid = invcdata.invoice.id
                    if Invoice.objects.filter(vendor=user, id=invoiceid).exists():

                        grandtotalamt = invcdata.invoice.grand_total_amount
                        Invoice.objects.filter(vendor=user, id=invoiceid).update(
                            invoice_number=invoice_number,
                            invoice_status=True,
                            modeofpayment="cash",
                            cash_amount=grandtotalamt,
                            online_amount=0.00,
                        )
                        CustomerCredit.objects.filter(vendor=user, id=dataid).delete()
                        messages.success(request, "Invoice Sattle done Succesfully!")
                        return redirect("creditmanage")
            else:
                return redirect("creditmanage")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def searchcredit(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            name = request.POST.get("name", "").strip()
            phone = request.POST.get("phone", "").strip()
            date = request.POST.get("date", "").strip()

            if not name and not phone and not date:
                messages.error(request, "Please provide at least one search criterion.")
                return redirect("creditmanage")

            # Start with all records for the current vendor
            queryset = CustomerCredit.objects.filter(vendor=user)

            # Apply filters if any field is provided
            if name:
                queryset = queryset.filter(customer_name__icontains=name)
            elif phone:
                queryset = queryset.filter(phone__icontains=phone)
            elif date:
                queryset = queryset.filter(due_date=date)
            if not queryset.exists():
                messages.error(request, "No data found matching the criteria.")
                return redirect(
                    "creditmanage"
                )  # Replace with your search form view name

            # Return results even if none of the fields were provided (i.e., all records for the vendor)
            return render(
                request,
                "showcredit.html",
                {"customerdata": queryset, "active_page": "creditmanage"},
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def Messages(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            profiledata = HotelProfile.objects.get(vendor=user)
            return render(
                request,
                "messages.html",
                {"active_page": "Messages", "profiledata": profiledata},
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def sendwelcomemsg(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            usermsglimit = Messgesinfo.objects.get(vendor=user)
            if usermsglimit.defaultlimit > usermsglimit.changedlimit:
                addmsg = usermsglimit.changedlimit + 2
                Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                profilename = HotelProfile.objects.get(vendor=user)
                mobile_number = phone
                user_name = "chandan"
                val = 5
                message_content = f"Dear {name}, Welcome to {profilename.name}. We are delighted to have you with us and look forward to making your stay enjoyable. Thank you for choosing us. - Billzify"

                base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                params = {
                    "authkey": settings.YOURBULKSMS_API_KEY,
                    "mobiles": phone,
                    "sender": "BILZFY",
                    "route": "2",
                    "country": "0",
                    "DLT_TE_ID": "1707171889808133640",
                }
                encoded_message = urllib.parse.urlencode({"message": message_content})
                url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"

                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if response_data.get("Status") == "success":
                                messages.success(request, "SMS sent successfully.")
                            else:
                                messages.success(
                                    request,
                                    response_data.get(
                                        "Description", "Failed to send SMS"
                                    ),
                                )
                        except ValueError:
                            messages.success(request, "Failed to parse JSON response")
                    else:
                        messages.success(
                            request,
                            f"Failed to send SMS. Status code: {response.status_code}",
                        )
                except requests.RequestException as e:
                    messages.success(request, f"Error: {str(e)}")
            else:
                messages.error(
                    request,
                    "Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!",
                )

            return redirect("Messages")

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def sendloyaltymsg(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            points = request.POST.get("points")
            phone = request.POST.get("phone")
            usermsglimit = Messgesinfo.objects.get(vendor=user)
            if usermsglimit.defaultlimit > usermsglimit.changedlimit:
                addmsg = usermsglimit.changedlimit + 2
                Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                profilename = HotelProfile.objects.get(vendor=user)
                message_content = f"Dear Guest, you have earned loyalty points worth Rs {points} at {profilename.name}. We look forward to welcoming you back soon. - Billzify"

                base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                params = {
                    "authkey": settings.YOURBULKSMS_API_KEY,
                    "mobiles": phone,
                    "sender": "BILZFY",
                    "route": "2",
                    "country": "0",
                    "DLT_TE_ID": "1707171993560691064",
                }
                encoded_message = urllib.parse.urlencode({"message": message_content})
                url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"

                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if response_data.get("Status") == "success":
                                messages.success(request, "SMS sent successfully.")
                            else:
                                messages.success(
                                    request,
                                    response_data.get(
                                        "Description", "Failed to send SMS"
                                    ),
                                )
                        except ValueError:
                            messages.success(request, "Failed to parse JSON response")
                    else:
                        messages.success(
                            request,
                            f"Failed to send SMS. Status code: {response.status_code}",
                        )
                except requests.RequestException as e:
                    messages.success(request, f"Error: {str(e)}")
            else:
                messages.error(
                    request,
                    "Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!",
                )

            return redirect("Messages")

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def aminityinvoice(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            profiledata = HotelProfile.objects.filter(vendor=user)
            invcdata = AminitiesInvoice.objects.filter(vendor=user, sattle=False).last()
            invpermit = invPermit.objects.filter(vendor=user)
            invoiceitemsdata = AminitiesInvoiceItem.objects.filter(
                vendor=user, invoice=invcdata
            )
            return render(
                request,
                "aminityinvoice.html",
                {
                    "active_page": "aminityinvoice",
                    "profiledata": profiledata,
                    "invcdata": invcdata,
                    "invoiceitemsdata": invoiceitemsdata,
                    'invpermit':invpermit
                },
            )

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def addaminitiesinvoice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            invcdate = request.POST.get("invcdate", "")
            cname = request.POST.get("cname", "")
            contact = request.POST.get("contact", "")
            email = request.POST.get("email", "")
            address = request.POST.get("address", "")
            state = request.POST.get("STATE", "")
            customergstno = request.POST.get("customergstno", "")
            companyname = request.POST.get("companyname", "")
            productname = request.POST.get("productname", "")
            productprice_str = request.POST.get(
                "productprice", "0"
            )  # Default to '0' if not provided
            productqty_str = request.POST.get(
                "productqty", "0"
            )  # Default to '0' if not provided
            producttax_str = request.POST.get("producttax", "0")
            producthsn = request.POST.get("producthsn", "")
            productdiscount_str = request.POST.get("productdiscount", "0")

            # Handle product quantity
            try:
                productqty = int(productqty_str)  # Convert to integer
            except (ValueError, TypeError):
                productqty = 0  # Default or handle error

            # Handle product price
            try:
                productprice = float(productprice_str)  # Convert to float
            except (ValueError, TypeError):
                productprice = 0.0  # Default or handle error

            # Handle product tax
            try:
                producttax = (
                    int(producttax_str)
                    if producttax_str and producttax_str.isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                producttax = 0  # Default or handle error

            # Handle product discount
            try:
                productdiscount = (
                    int(productdiscount_str)
                    if productdiscount_str and productdiscount_str.isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                productdiscount = 0  # Default or handle error

            # Get user's state
            userstatedata = HotelProfile.objects.get(vendor=user)
            userstate = userstatedata.zipcode

            # Determine tax type
            taxtypes = "GST" if userstate == state else "IGST"

            # Calculation
            total_amount = productprice * productqty
            subtotal_amount = total_amount - productdiscount
            tax_amount = 0
            grand_total = 0
            taxamts = 0

            if producttax > 0:
                tax_amount = subtotal_amount * producttax / 100
                grand_total = subtotal_amount + tax_amount
                taxamts = tax_amount / 2
            else:
                grand_total = subtotal_amount

            # Invoice number handling
            invcnumberdata = AminitiesInvoice.objects.filter(vendor=user).last()
            if invcnumberdata and invcnumberdata.invoicenumber:
                try:
                    invcno = int(invcnumberdata.invoicenumber) + 1
                except ValueError:
                    invcno = 1
            else:
                invcno = 1

            # Create invoice
            today = datetime.now().date()
            invoiceid = AminitiesInvoice.objects.create(
                vendor=user,
                customername=cname,
                customercontact=contact,
                customeremail=email,
                customeraddress=address,
                customergst=customergstno,
                customercompany=companyname,
                invoicenumber=invcno,
                invoicedate=invcdate,
                taxtype=taxtypes,
                total_item_amount=float(total_amount),
                discount_amount=float(productdiscount),
                subtotal_amount=float(subtotal_amount),
                gst_amount=float(taxamts),
                sgst_amount=float(taxamts),
                grand_total_amount=float(grand_total),
                modeofpayment="cash",
                cash_amount=float(0),
                online_amount=float(0),
                sattle=False,
            )

            # Create invoice item
            AminitiesInvoiceItem.objects.create(
                vendor=user,
                invoice=invoiceid,
                description=productname,
                quantity=productqty,
                price=productprice,
                total_amount=total_amount,
                tax_rate=producttax,
                hsncode=producthsn,
                discount_amount=productdiscount,
                subtotal_amt=subtotal_amount,
                tax_amt=tax_amount,
                grand_total=grand_total,
            )
            
            if invPermit.objects.filter(vendor=user,pos_billing_active=True).exists():
                if  Items.objects.filter(vendor=user,description=productname).exists():
                    Items.objects.filter(vendor=user,description=productname).update(
                      available_qty=F('available_qty')-productqty  
                    )
                else:
                    pass
            else:
                pass

            messages.success(request, "Invoice created successfully!")
            return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def addmoreaminitiesproductininvoice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            invcid = request.POST.get("invcid")
            productname = request.POST.get("productname", "")
            productprice_str = request.POST.get(
                "productprice", "0"
            )  # Default to '0' if not provided
            productqty_str = request.POST.get(
                "productqty", "0"
            )  # Default to '0' if not provided
            producttax_str = request.POST.get("producttax", "0")
            producthsn = request.POST.get("producthsn", "")
            productdiscount_str = request.POST.get("productdiscount", "0")

            # Handle product quantity
            try:
                productqty = int(productqty_str)  # Convert to integer
            except (ValueError, TypeError):
                productqty = 0  # Default or handle error

            # Handle product price
            try:
                productprice = float(productprice_str)  # Convert to float
            except (ValueError, TypeError):
                productprice = 0.0  # Default or handle error

            # Handle product tax
            try:
                producttax = (
                    int(producttax_str)
                    if producttax_str and producttax_str.isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                producttax = 0  # Default or handle error

            # Handle product discount
            try:
                productdiscount = (
                    int(productdiscount_str)
                    if productdiscount_str and productdiscount_str.isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                productdiscount = 0  # Default or handle error

            # Calculation
            total_amount = productprice * productqty
            subtotal_amount = total_amount - productdiscount
            tax_amount = 0
            grand_total = 0
            taxamts = 0

            if producttax > 0:
                tax_amount = subtotal_amount * producttax / 100
                grand_total = subtotal_amount + tax_amount
                taxamts = tax_amount / 2
            else:
                grand_total = subtotal_amount

            invoicedata = AminitiesInvoice.objects.get(vendor=user, id=invcid)
           

            invctotalamt = float(invoicedata.total_item_amount) + total_amount
            invcsubtotalamt = float(invoicedata.subtotal_amount) + subtotal_amount
            invcdiscountamt = float(invoicedata.discount_amount) + productdiscount
            invcgstamt = float(invoicedata.gst_amount) + taxamts
            invcsgstamt = float(invoicedata.sgst_amount) + taxamts
            invcgrandamt = float(invoicedata.grand_total_amount) + grand_total

            AminitiesInvoice.objects.filter(vendor=user, id=invcid).update(
                total_item_amount=invctotalamt,
                discount_amount=invcdiscountamt,
                subtotal_amount=invcsubtotalamt,
                gst_amount=invcgstamt,
                sgst_amount=invcsgstamt,
                grand_total_amount=invcgrandamt,
            )

            # Create invoice item
            AminitiesInvoiceItem.objects.create(
                vendor=user,
                invoice_id=invcid,
                description=productname,
                quantity=productqty,
                price=productprice,
                total_amount=total_amount,
                tax_rate=producttax,
                hsncode=producthsn,
                discount_amount=productdiscount,
                subtotal_amt=subtotal_amount,
                tax_amt=tax_amount,
                grand_total=grand_total,
            )
            if invPermit.objects.filter(vendor=user,pos_billing_active=True).exists():
                if  Items.objects.filter(vendor=user,description=productname).exists():
                    Items.objects.filter(vendor=user,description=productname).update(
                      available_qty=F('available_qty')-productqty  
                    )
                else:
                    pass
            else:
                pass
            messages.success(request, "Items added successfully!")
            return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def aminitiesitemdelete(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            itemid = id
            if AminitiesInvoiceItem.objects.filter(vendor=user, id=itemid).exists():
                itemsdata = AminitiesInvoiceItem.objects.get(vendor=user, id=itemid)
                itemtotalamt = itemsdata.total_amount
                itemdiscount = itemsdata.discount_amount
                itemsubtotal = itemsdata.subtotal_amt
                itemtaxamt = itemsdata.tax_amt / 2
                itemgrandtotal = itemsdata.grand_total
                invoiceid = itemsdata.invoice.id
                if AminitiesInvoice.objects.filter(vendor=user, id=invoiceid).exists():
                    invoicedata = AminitiesInvoice.objects.get(
                        vendor=user, id=invoiceid
                    )
                    invoicetotalamt = invoicedata.total_item_amount - itemtotalamt
                    invoicediscountamt = invoicedata.discount_amount - itemdiscount
                    invoicesubtotalamt = invoicedata.subtotal_amount - itemsubtotal
                    invoicegstamt = invoicedata.gst_amount - itemtaxamt
                    invoicesgstamt = invoicedata.sgst_amount - itemtaxamt
                    invoicegrandtotalamt = (
                        invoicedata.grand_total_amount - itemgrandtotal
                    )
                    AminitiesInvoice.objects.filter(vendor=user, id=invoiceid).update(
                        total_item_amount=invoicetotalamt,
                        discount_amount=invoicediscountamt,
                        subtotal_amount=invoicesubtotalamt,
                        gst_amount=invoicegstamt,
                        sgst_amount=invoicesgstamt,
                        grand_total_amount=invoicegrandtotalamt,
                    )
                    if invPermit.objects.filter(vendor=user,pos_billing_active=True).exists():
                        if  Items.objects.filter(vendor=user,description=itemsdata.description).exists():
                            Items.objects.filter(vendor=user,description=itemsdata.description).update(
                            available_qty=F('available_qty')+itemsdata.quantity  
                            )
                        else:
                            pass
                    else:
                        pass
                    AminitiesInvoiceItem.objects.filter(vendor=user, id=itemid).delete()
                    messages.success(request, "items delete succesfully!")
                else:
                    messages.error(request, "Please delete this full invoice")
            else:
                messages.error(request, "Items already  deleted ")

            return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def saveaminitiesinvoice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            invoiceid = request.POST.get("invoiceid")
            paymentmode = request.POST.get("paymentmode")
            cashamount = request.POST.get("cashamount")
            onlineamount = request.POST.get("onlineamount")

            datainvc = AminitiesInvoice.objects.get(vendor=user, id=invoiceid)
            totalamt = datainvc.grand_total_amount
            if paymentmode == "cash":
                AminitiesInvoice.objects.filter(vendor=user, id=invoiceid).update(
                    modeofpayment="cash", sattle=True, cash_amount=totalamt
                )
            elif paymentmode == "online":
                AminitiesInvoice.objects.filter(vendor=user, id=invoiceid).update(
                    modeofpayment="online", sattle=True, online_amount=totalamt
                )
            elif paymentmode == "Partly":
                AminitiesInvoice.objects.filter(vendor=user, id=invoiceid).update(
                    modeofpayment="Partly",
                    sattle=True,
                    cash_amount=cashamount,
                    online_amount=onlineamount,
                )
                
            url = reverse('aminitiesinvoice', args=[invoiceid])
            return redirect(url)
            # return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def aminityhistory(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            advanceroomsdata = AminitiesInvoice.objects.filter(vendor=user).order_by(
                "-id"
            )
        
            page = request.GET.get("page", 1)
            paginator = Paginator(advanceroomsdata, 25)
            try:
                advanceroomdata = paginator.page(page)
            except PageNotAnInteger:
                advanceroomdata = paginator.page(1)
            except EmptyPage:
                advanceroomdata = paginator.page(paginator.num_pages)
            return render(
                request,
                "aminityhistory.html",
                {
                    "active_page": "aminityhistory",
                    "advanceroomdata": advanceroomdata,
                    "checkdata": "yes",
                },
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def deleteaminitesinvc(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcid = id
            if AminitiesInvoice.objects.filter(vendor=user, id=invcid).exists():
                if invPermit.objects.filter(vendor=user,pos_billing_active=True).exists():
                    invcdata = AminitiesInvoice.objects.get(vendor=user, id=invcid)
                    loopdata = AminitiesInvoiceItem.objects.filter(vendor=user,invoice=invcdata)
                    for i in loopdata:
                        if  Items.objects.filter(vendor=user,description=i.description).exists():
                            Items.objects.filter(vendor=user,description=i.description).update(
                            available_qty=F('available_qty')+i.quantity  
                            )
                        else:
                            pass
                    else:
                        pass
                AminitiesInvoice.objects.filter(vendor=user, id=invcid).delete()
                messages.success(request, "Invoice delete succesfully!")
                return redirect("aminityinvoice")
            else:
                messages.success(request, "Invoice already deleted!")
                return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def aminitiesinvoice(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            invcid = id
            if AminitiesInvoice.objects.filter(
                vendor=user, id=invcid, sattle=True
            ).exists():
                profiledata = HotelProfile.objects.filter(vendor=user)
                invoice_data = AminitiesInvoice.objects.filter(vendor=user, id=invcid)
                invoiceitemdata = AminitiesInvoiceItem.objects.filter(
                    vendor=user, invoice_id=invcid
                )
                invcheck =  invoiceDesign.objects.get(vendor=user)
                if invcheck.invcdesign==1:
                    return render(
                        request,
                        "aminityinvoicepage.html",
                        {
                            "profiledata": profiledata,
                            "invoice_data": invoice_data,
                            "invoiceitemdata": invoiceitemdata,
                        },
                    )
                elif invcheck.invcdesign==2:
                    return render(
                        request,
                        "aminityinvoicepage2.html",
                        {
                            "profiledata": profiledata,
                            "invoice_data": invoice_data,
                            "invoiceitemdata": invoiceitemdata,
                        },
                    )

            else:
                messages.error(request, "Invoice Not Saved!")
                return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def searchaminitiesdata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            guestname = request.POST.get("guestname", "").strip()
            guestphone = request.POST.get("guestphone", "").strip()
            invnumber = request.POST.get("invnumber", "").strip()
            checkindate = request.POST.get("checkindate", "").strip()
            checkoutdate = request.POST.get("checkoutdate", "").strip()

            # Start with a base queryset
            queryset = AminitiesInvoice.objects.filter(vendor=user).order_by("-id")

            # Apply filters based on provided data
            if guestname:
                queryset = queryset.filter(customername__icontains=guestname)

            if guestphone:
                queryset = queryset.filter(customercontact__icontains=guestphone)

            if invnumber:
                queryset = queryset.filter(invoicenumber__icontains=invnumber)

            if checkindate:
                try:
                    # Ensure checkindate is a string and parse it to a date
                    checkindate = datetime.strptime(checkindate, "%Y-%m-%d").date()
                    queryset = queryset.filter(invoicedate__gte=checkindate)
                except (ValueError, TypeError):
                    # Handle invalid date format if necessary
                    pass

            if checkoutdate:
                try:
                    # Ensure checkoutdate is a string and parse it to a date
                    checkoutdate = datetime.strptime(checkoutdate, "%Y-%m-%d").date()
                    queryset = queryset.filter(invoicedate__lte=checkoutdate)
                except (ValueError, TypeError):
                    # Handle invalid date format if necessary
                    pass

            # Optionally, you can filter between checkindate and checkoutdate
            if checkindate and checkoutdate:
                try:
                    # Ensure both dates are strings and parse them to dates
                    checkindate = datetime.strptime(checkindate, "%Y-%m-%d").date()
                    checkoutdate = datetime.strptime(checkoutdate, "%Y-%m-%d").date()
                    queryset = queryset.filter(
                        invoicedate__range=[checkindate, checkoutdate]
                    )
                except (ValueError, TypeError):
                    # Handle invalid date format if necessary
                    pass

            return render(
                request,
                "aminityhistory.html",
                {"active_page": "aminityhistory", "advanceroomdata": queryset},
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def aminitysales(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Calculate the start and end dates of the current month
            today = datetime.now()
            start_of_month = today.replace(day=1)
            if today.month == 12:
                start_of_next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                start_of_next_month = today.replace(month=today.month + 1, day=1)
            end_of_month = start_of_next_month - timedelta(days=1)

            # Filter invoices for the current month
            monthly_sales = AminitiesInvoice.objects.filter(
                vendor=user, invoicedate__range=[start_of_month, end_of_month]
            ).order_by("-invoicedate")
            # Calculate the total sales for the current month
            total_sales = (
                monthly_sales.aggregate(total_amount=Sum("grand_total_amount"))[
                    "total_amount"
                ]
                or 0
            )
            totals = monthly_sales.aggregate(
                total_amount=Sum("grand_total_amount"),
                total_gst=Sum("gst_amount"),
                total_sgst=Sum("sgst_amount"),
                total_cash=Sum("cash_amount"),
                online_amount=Sum("online_amount"),
            )

            # Retrieve values from the totals dictionary, defaulting to 0 if None
            total_sales = totals["total_amount"] or 0
            total_gst = totals["total_gst"] or 0
            total_sgst = totals["total_sgst"] or 0
            total_cash = totals["total_cash"] or 0
            online_amount = totals["online_amount"] or 0

       
            return render(
                request,
                "aminityhisales.html",
                {
                    "active_page": "aminitysales",
                    "total_sales": total_sales,
                    "total_gst": total_gst,
                    "total_sgst": total_sgst,
                    "total_cash": total_cash,
                    "online_amount": online_amount,
                },
            )

        else:
            return redirect("loginpage")

    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def searchaminitiesinvoicedata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            startdate = request.POST.get("startdate", "").strip()
            enddate = request.POST.get("enddate", "").strip()

            # Filter invoices for the current month
            monthly_sales = AminitiesInvoice.objects.filter(
                vendor=user, invoicedate__range=[startdate, enddate]
            ).order_by("-invoicedate")

            # Calculate the total sales for the current month
            total_sales = (
                monthly_sales.aggregate(total_amount=Sum("grand_total_amount"))[
                    "total_amount"
                ]
                or 0
            )
            totals = monthly_sales.aggregate(
                total_amount=Sum("grand_total_amount"),
                total_gst=Sum("gst_amount"),
                total_sgst=Sum("sgst_amount"),
                total_cash=Sum("cash_amount"),
                online_amount=Sum("online_amount"),
            )

            # Retrieve values from the totals dictionary, defaulting to 0 if None
            total_sales = totals["total_amount"] or 0
            total_gst = totals["total_gst"] or 0
            total_sgst = totals["total_sgst"] or 0
            total_cash = totals["total_cash"] or 0
            online_amount = totals["online_amount"] or 0
            searchdata = "yes"

            return render(
                request,
                "aminityhisales.html",
                {
                    "active_page": "aminitysales",
                    "total_sales": total_sales,
                    "searchdata": searchdata,
                    "startdate": startdate,
                    "enddate": enddate,
                    "total_gst": total_gst,
                    "total_sgst": total_sgst,
                    "total_cash": total_cash,
                    "online_amount": online_amount,
                },
            )

        else:
            return redirect("loginpage")

    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def searchguestexportdta(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            startdate = request.POST.get("startdate", "")
            enddate = request.POST.get("enddate", "")
            if startdate == enddate:
                guestdata = Gueststay.objects.filter(
                    vendor=user, checkindate__date=startdate
                ).order_by("checkindate")
            else:
                guestdata = Gueststay.objects.filter(
                    vendor=user, checkindate__range=[startdate, enddate]
                ).order_by("checkindate")
          
            return render(
                request,
                "guestshowexport.html",
                {"guestdata": guestdata, "startdate": startdate, "enddate": enddate},
            )

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




def policereport(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  

            # Retrieve POST data with default empty string or '0'
            startdate = request.POST.get("startdate", "")
            enddate = request.POST.get("enddate", "")
            
            # Filter guest data based on date range
            if startdate == enddate:
                guestdata = Gueststay.objects.filter(
                    vendor=user, checkindate__date=startdate
                ).order_by("checkindate")
            else:
                guestdata = Gueststay.objects.filter(
                    vendor=user, checkindate__range=[startdate, enddate]
                ).order_by("checkindate")

            hoteldata = HotelProfile.objects.filter(vendor=user)

            return render(
                request,
                "policerpt.html",
                {
                    "guestdata": guestdata, 
                    "startdate": startdate,
                    "enddate": enddate,
                    "hoteldata": hoteldata,
                },
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)

def cleanroombtn(request, id):
    if request.user.is_authenticated:
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  
        data = Rooms.objects.get(vendor=user, room_name=id)
        status = data.is_clean
        if status == True:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=False)
        else:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=True)

        return redirect("homepage")


def cleanroombtnweek(request, id):
    if request.user.is_authenticated:
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
                user = subuser.vendor  
        data = Rooms.objects.get(vendor=user, room_name=id)
        status = data.is_clean
        if status == True:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=False)
        else:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=True)

        return redirect("weekviews")


import json

from django.db.models import F
def sendbulksmsloylty(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            userdata = loylty_Guests_Data.objects.get(vendor=user, id=id)
            usermsglimit = Messgesinfo.objects.get(vendor=user)
            if usermsglimit.defaultlimit > usermsglimit.changedlimit:
                addmsg = usermsglimit.changedlimit + 2
                Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                profilename = HotelProfile.objects.get(vendor=user)
                hotelname = profilename.name
                mobile_number = userdata.guest_contact
                user_name = "chandan"
                val = 5
                totalloyltyamount = userdata.loylty_point
                message_content = f"Dear Guest, you have earned loyalty points worth Rs {totalloyltyamount} at {hotelname}. We look forward to welcoming you back soon. - Billzify"

                base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                params = {
                    "authkey": '34384c5a49465937363974',
                    "mobiles": mobile_number,
                    "sender": "BILZFY",
                    "route": "2",
                    "country": "0",
                    "DLT_TE_ID": "1707171993560691064",
                }
                encoded_message = urllib.parse.urlencode({"message": message_content})
                url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"

                loylty_Guests_Data.objects.filter(vendor=user, id=id).update(smscount=F('smscount')+1)
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        try:
                            response_data = response.json()
                            if response_data.get("Status") == "success":
                                messages.success(request, "SMS sent successfully.")
                            else:
                                messages.success(
                                    request,
                                    response_data.get("Description", "Failed to send SMS"),
                                )
                        except ValueError:
                            messages.success(request, "Failed to parse JSON response")
                    else:
                        messages.success(
                            request,
                            f"Failed to send SMS. Status code: {response.status_code}",
                        )
                except requests.RequestException as e:
                    messages.success(request, f"Error: {str(e)}")
            else:
                messages.error(
                    request,
                    "Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!",
                )

            return redirect('loylty')

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def deleteloylty(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            loylty_Guests_Data.objects.get(vendor=user, id=id).delete()
            messages.success(request, "Deleted Succesfully")
            return redirect('loylty')
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)



        

def search_user(request):
    if request.user.is_authenticated:
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  
        # Get the mobile number from the GET request
        mobile_number = request.GET.get('mobile_number', '').strip()
        profiledata = HotelProfile.objects.get(vendor=user)
        # Validate if the mobile number is provided
        if not mobile_number:
            return JsonResponse({'success': False, 'message': 'Mobile number is required'})

        try:
            # First, check in the AminitiesInvoice model
            invoice = AminitiesInvoice.objects.filter(vendor=user, customercontact=mobile_number).last()  # Adjust field names if necessary

            if invoice:
                # If a matching entry is found in AminitiesInvoice, return those details
                if invoice.taxtype=='GST':
                    statesame = profiledata.zipcode
                else:
                    statesame = 'other'
                guest_details = {
                    'name': invoice.customername,
                    'email': invoice.customeremail,
                    'mobile': invoice.customercontact,
                    'address': invoice.customeraddress,
                    'customercompany': invoice.customercompany,
                    'customergst': invoice.customergst,
                    'state':statesame,

                    
                }
                return JsonResponse({'success': True, 'user': guest_details})

           
            else:
                
                 # If no matching entry in AminitiesInvoice, check in Gueststay
                guest = Gueststay.objects.filter(vendor=user, guestphome=mobile_number).last()  # Adjust field names if necessary
                if guest.gueststates==profiledata.zipcode:
                    statesame = profiledata.zipcode
                else:
                    statesame = 'other'
                # If a matching guest is found in Gueststay, return those details
                guest_details = {
                    'name': guest.guestname,
                    'email': guest.guestemail,
                    'mobile': guest.guestphome,
                    'address': guest.guestcity,
                    'customercompany': 'none',
                    'customergst': 'none',
                    'state':statesame,
                }
                return JsonResponse({'success': True, 'user': guest_details})

           
        except Exception as e:
            # Return a generic error message in case of unexpected issues
            return JsonResponse({'success': False, 'message': str(e)})
        


import re


def check_product(request):
    if request.user.is_authenticated:
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor  
        product_name = request.GET.get('product_name', '').strip()

        if product_name:
            try:
                # Normalize spaces in the input
                normalized_product_name = re.sub(r'\s+', ' ', product_name).strip()
      

                # Search for latest product in AminitiesInvoiceItem
                product3 = AminitiesInvoiceItem.objects.filter(
                    vendor=user,
                    description__icontains=normalized_product_name
                ).order_by('-id').first()  # Fetch the latest entry

                if product3:
               
                    return JsonResponse({
                        'success': True,
                        'products': [{
                            'id': product3.id,
                            'description': product3.description,
                            'price': product3.price,
                            'hsncode': product3.hsncode,
                            'category_tax': product3.tax_rate if product3.tax_rate else None
                        }]
                    })

                # Search for latest product in LaundryServices
                product2 = LaundryServices.objects.filter(
                    vendor=user,
                    name__icontains=normalized_product_name
                ).order_by('-id').first()  # Fetch the latest entry

                if product2:
                    
                    return JsonResponse({
                        'success': True,
                        'products': [{
                            'id': product2.id,
                            'description': product2.name,
                            'price': product2.price,
                        }]
                    })

                # Search for latest product in Items
                product1 = Items.objects.filter(
                    vendor=user,
                    description__icontains=normalized_product_name
                ).order_by('-id').first()  # Fetch the latest entry

                if product1:
                 
                    return JsonResponse({
                        'success': True,
                        'products': [{
                            'id': product1.id,
                            'description': product1.description,
                            'price': product1.price,
                            'hsncode': product1.hsncode,
                            'category_tax': product1.category_tax.taxrate if product1.category_tax else None
                        }]
                    })

               
                return JsonResponse({'success': False, 'message': 'No products found.'})

            except Exception as e:
                
                return JsonResponse({'success': False, 'message': str(e)})

        else:
            return JsonResponse({'success': False, 'message': 'Product name is required.'})




def saveloyltydata(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor  
            # Retrieve POST data with default empty string or '0'
            gname = request.POST.get("gname")
            contact = request.POST.get("contact")
            loyltypts = request.POST.get("loyltypts")

            loylty_Guests_Data.objects.create(vendor=user,
                                guest_name=gname,
                                guest_contact=contact,
                                loylty_point= loyltypts , 
                                smscount=0  )
            messages.success(request,"Guest Added !")
            return redirect('loylty')
   

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def extendscheck(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            
            guestid = request.POST.get("guestid")
            fromdate = request.POST.get("fromdate")
            checkoutdate = request.POST.get("checkoutdate")
            print(checkoutdate,fromdate)

            fromdates = datetime.strptime(fromdate, "%Y-%m-%d")
            checkoutdates = datetime.strptime(checkoutdate, "%Y-%m-%d")

            # Calculate the difference in days
            difference = fromdates - checkoutdates
            days_difference = difference.days 
            print(days_difference,"days")

            invcid = request.POST.get("invcid")
            permission=False
            if Gueststay.objects.filter(vendor=user,id=guestid).exists():
                gestdatas = Gueststay.objects.get(vendor=user,id=guestid)
                roomnumber = gestdatas.roomno

                
                fromdate = datetime.strptime(fromdate, "%Y-%m-%d").date()
                checkoutdate = datetime.strptime(checkoutdate, "%Y-%m-%d").date()
                if Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomnumber).exclude(status='CHECK OUT').exists():

            
                    bookdata = Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomnumber).exclude(status='CHECK OUT')
                    
                    for booking in bookdata:
                        room = booking.room
                        room_type = room.room_type  # Get the category of the room

                        

                    # Find unavaisame_category_rooms = Rooms.objects.filter(room_type=room_type)

                        same_category_rooms = Rooms.objects.filter(vendor=user,room_type=room_type).exclude(checkin=6)

                        # Step 3: Find rooms that are unavailable (i.e., booked between `checkoutdate` and `fromdate`)
                        unavailable_rooms = Booking.objects.filter(vendor=user,
                            room__in=same_category_rooms  # Filter by rooms in the same category
                        ).filter(
                            Q(check_in_date__lt=fromdate) & Q(check_out_date__gt=checkoutdate)  # Room booked during the date range
                        ).values_list('room', flat=True)

                        # Step 4: Find available rooms (exclude the ones that are unavailable)
                        available_rooms = same_category_rooms.exclude(id__in=unavailable_rooms)

                        # Step 5: Check if there are any available rooms
                        # if available_rooms.exists():
                        #     print("Available Rooms in the same category:", available_rooms)
                        #     other_category_available_rooms=None

                        for i in available_rooms:
                            if i.room_name==roomnumber:
                                permission  = True
                    
                      
                        other_categories_rooms = Rooms.objects.filter(vendor=user).exclude(room_type=room_type).exclude(checkin=6).all()
                        other_category_unavailable_rooms = Booking.objects.filter(vendor=user,
                            room__in=other_categories_rooms  # Filter by rooms in other categories
                        ).filter(
                            Q(check_in_date__lt=fromdate) & Q(check_out_date__gt=checkoutdate)  # Room booked during the date range
                        ).values_list('room', flat=True)

                        # Step 8: Find available rooms from other categories (exclude the ones that are unavailable)
                        other_category_available_rooms = other_categories_rooms.exclude(id__in=other_category_unavailable_rooms)

                        # Step 9: Check if there are available rooms from other categories
                        if other_category_available_rooms.exists():
                            print("No rooms available in the selected category. Available rooms from other categories are:", other_category_available_rooms)
                        else:
                            print("No rooms available in the selected or other categories for the given date range.")

            

            # Get the valid room names (room_number) as integers from Rooms model
            valid_room_numbers = Rooms.objects.filter(vendor=user).exclude(checkin=6).values_list('room_name', flat=True)

            # Convert the integers to strings for comparison with the 'description' field
            valid_room_names = [str(room_number) for room_number in valid_room_numbers]

            # Filter InvoiceItem based on description matching valid room names
            
            invcitemdata = InvoiceItem.objects.filter(
                vendor=user,
                invoice_id=invcid,
                description=roomnumber,
                is_room=True,  # 'description' is a string, so valid_room_names should be strings
                is_checkout=False
            ).all()
            totalprice = 0.00
            grandtotal = 0.00
            gstrate = 0.00 
            sgstrate = 0.00
            description = ''
            mdescription = ''
            hsncode = 0
            for i in invcitemdata:
                description = 'EXTEND' + ' ' + i.description 
                hsncode = i.hsncode
                mdescription =  i.mdescription
                totalprice=i.price
                maintotal = i.price * int(days_difference)
                taxamt = 0 
                if i.cgst_rate > 0.00:
                    taxamt = maintotal*i.cgst_rate/100
                    taxamt = taxamt * 2
                    gstrate = i.cgst_rate
                    sgstrate = i.cgst_rate
                grandtotal = float(maintotal + taxamt)

            taxs = sgstrate * 2

            if len(bookdata) == 1:
                pagepermission = True
                print("ek hi hai new")
            else:
                pagepermission = False
                print("jayda hai  ")



            return render(request, 'extnd.html', {
                
                'bookdata': bookdata,
                'invoice_id': invcid,
                'available_rooms':available_rooms,
                'other_category_available_rooms':other_category_available_rooms,
                'fromdate':fromdate,
                'checkoutdate':checkoutdate,
                'invcitemdata':invcitemdata,
                'permission':permission,
                'totalprice':totalprice,
                'grandtotal':grandtotal,
                'taxs':taxs,
                'sgstrate':sgstrate,
                'totaldays':days_difference,
                'pagepermission':pagepermission,
                'description':description,
                'mdescription':mdescription,
                'hsncode':hsncode

            })
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    

        


def checkoutroombyone(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
           
            guestid = request.POST.get("guestid")
            invoiceitemid = request.POST.get("invoiceitemid")
            if Booking.objects.filter(vendor=user,gueststay_id=guestid).exists():
                bookdata = Booking.objects.filter(vendor=user,gueststay_id=guestid).exclude(status='CHECK OUT')
                invcdata = InvoiceItem.objects.get(id=invoiceitemid)
                
                roomname = invcdata.description

               
                checklimit = len(bookdata)
                if checklimit <= 1:
                    messages.error(request,"Please Checkout Full Room Because Is there Only One Room In Folio!")
                else:
                    if Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomname).exists():
                        invccurrentdate = datetime.now().date()
                        ctime = datetime.now().time()
                       
                        bookdataget = Booking.objects.get(vendor=user,gueststay_id=guestid,room__room_name=roomname)
                        if bookdataget.status=='CHECK OUT':
                            messages.error(request,"Room Already Check-Out!")
                        else:
                            checkindate =  invccurrentdate
                            checkoutdate = bookdataget.check_out_date
                            while checkindate < checkoutdate:
                                        roomscat = Rooms.objects.get(vendor=user,id=bookdataget.room.id)
                                        invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                                    
                                        invtavaible = invtdata.total_availibility + 1
                                        invtabook = invtdata.booked_rooms - 1
                                        total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                        occupancy = invtabook * 100//total_rooms
                                                                                

                                        RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                                    total_availibility=invtavaible,occupancy=occupancy)
                            
                                        checkindate += timedelta(days=1)

                            if VendorCM.objects.filter(vendor=user):
                                    start_date = str(invccurrentdate)
                                    end_date = str(checkoutdate)
                                    
                                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                    thread.start()
                                    # for dynamic pricing
                                    if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                        thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                        thread.start()
                                    else:
                                        pass
                            else:
                                    pass

                            Rooms.objects.filter(vendor=user,id=bookdataget.room.id).update(checkin=0,is_clean=False)
                            Booking.objects.filter(vendor=user,id=bookdataget.id).update(status="CHECK OUT",
                                                check_out_time=ctime,check_out_date=invccurrentdate)
                            RoomBookAdvance.objects.filter(vendor=user,roomno_id=bookdataget.room.id,
                                        saveguestdata_id=bookdataget.advancebook.id).update(checkOutstatus=True)
                            booksdatas = Booking.objects.filter(vendor=user,gueststay_id=guestid).exclude(status='CHECK OUT').exclude(id=bookdataget.id)
                            
                            if Gueststay.objects.filter(vendor=user,id=guestid,roomno=bookdataget.room.room_name).exists():
                                roomnumber = 0
                                for i in booksdatas:
                                    roomnumber = i.room.room_name
                                Gueststay.objects.filter(vendor=user,id=guestid,roomno=bookdataget.room.room_name).update(roomno=roomnumber)
                            else:
                                pass
                            invcdata.is_checkout=True
                            invcdata.save()

                            messages.success(request,"Room Check-Out SuccesFully!....")

                       

                        
            return redirect('invoicepage', id=guestid)        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    


from decimal import Decimal, ROUND_HALF_UP

def extednroomform(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
           
            invoiceid = request.POST.get("invoiceid")
            price = request.POST.get("price")
            days = request.POST.get("days")
            tax = request.POST.get("tax")
            adjustableamount = request.POST.get("adjustableamount")
            checkoutdate_str = request.POST.get("checkoutdate")
            description = request.POST.get("description")
            mndescription = request.POST.get("mndescription")
            hsncode = request.POST.get("hsncode")
            print(description,mndescription,hsncode)
            today = datetime.now().date()
            checkoutdatemain = datetime.strptime(checkoutdate_str, "%Y-%m-%d").date()
            new_date = checkoutdatemain - timedelta(days=1)
            if Invoice.objects.filter(vendor=user,id=invoiceid).exists():
                invcdata = Invoice.objects.get(vendor=user,id=invoiceid)
                guestid = invcdata.customer.id
                roomnumer = invcdata.customer.roomno
                print(adjustableamount,tax,days,price)
                
                if Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomnumer).exists():
                        invccurrentdate = datetime.now().date()
                        ctime = datetime.now().time()
                       
                        bookdataget = Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomnumer).last()
                        if bookdataget.status=='CHECK OUT':
                            messages.error(request,"Room Already Check-Out!")
                        else:
                            
                            checkindate =  bookdataget.check_out_date
                            checkoutdate = checkoutdatemain
                            while checkindate < checkoutdate:
                                        roomscat = Rooms.objects.get(vendor=user,id=bookdataget.room.id)
                                        if RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).exists():
                                            invtdata = RoomsInventory.objects.get(vendor=user,date=checkindate,room_category=roomscat.room_type)
                                        
                                            invtavaible = invtdata.total_availibility - 1
                                            invtabook = invtdata.booked_rooms + 1
                                            total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindate += timedelta(days=1)
                                        else:
                                            total_rooms = Rooms.objects.filter(vendor=user, room_type=roomscat.room_type).exclude(checkin=6).count()
                                            invtavaible = total_rooms - 1
                                            invtabook =  1
                                            
                                            occupancy = invtabook * 100//total_rooms
                                                                                    

                                            RoomsInventory.objects.filter(vendor=user,date=checkindate,room_category=roomscat.room_type).update(booked_rooms=invtabook,
                                                        total_availibility=invtavaible,occupancy=occupancy)
                                
                                            checkindate += timedelta(days=1)


                            if VendorCM.objects.filter(vendor=user):
                                    start_date = str(bookdataget.check_out_date)
                                    end_date = str(new_date)
                                    
                                    thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                                    thread.start()
                                    # for dynamic pricing
                                    if  VendorCM.objects.filter(vendor=user,dynamic_price_active=True):
                                        thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                                        thread.start()
                                    else:
                                        pass
                            else:
                                    pass
                            
                            Booking.objects.filter(vendor=user,gueststay_id=guestid,room__room_name=roomnumer).update(check_out_date=checkoutdatemain)
                            Gueststay.objects.filter(id=guestid).update(checkoutstatus=False,checkoutdate=checkoutdatemain)
                                    # Convert inputs to proper types
                                    
                                # Convert inputs to proper types
                            # Convert inputs to proper types
                            price = Decimal(request.POST.get("price")).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)  # Price per day (convert to Decimal)
                            days = int(request.POST.get("days"))  # Number of days (string from form)
                            tax = Decimal(request.POST.get("tax")).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)  # Tax percentage (convert to Decimal)
                            adjustableamount = Decimal(request.POST.get("adjustableamount")).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)  # Total amount user wants to pay (convert to Decimal)

                            # Calculation
                            dividetax = tax / 2  # Dividing tax by 2 (keeping as Decimal)
                            amount_before_tax = adjustableamount / (1 + (tax / 100))  # Calculating amount before tax
                            onedaysell = amount_before_tax / days  # Price per day without tax
                            gst_tax_amount = adjustableamount - amount_before_tax  # Tax amount
                            gst_tax_amount = gst_tax_amount /2
                           
                            adjustableamount = float(adjustableamount)
                            gsttax_amount = float(gst_tax_amount)
                    
                            InvoiceItem.objects.create(vendor=user,invoice_id=invoiceid,description=description,mdescription=mndescription,price=onedaysell,
                                                        quantity_likedays=days,cgst_rate=dividetax,sgst_rate=dividetax,
                                                        hsncode=hsncode,total_amount=adjustableamount,is_room=True)
                            invc = Invoice.objects.get(vendor=user,id=invoiceid)
                            totals = onedaysell * days
                            totalamtinvc = invc.total_item_amount + totals
                            subtotalinvc = totals + invc.subtotal_amount
                            grandtotal = float(invc.grand_total_amount) + adjustableamount 
                            sgsttotal = float(invc.sgst_amount) + gsttax_amount
                            gsttotal = float(invc.gst_amount) + gsttax_amount
                            dueamount = float(invc.Due_amount) + adjustableamount
                            Invoice.objects.filter(vendor=user,id=invoiceid).update(total_item_amount=totalamtinvc,subtotal_amount=subtotalinvc,
                                                                                                grand_total_amount =grandtotal,sgst_amount=sgsttotal,gst_amount=gsttotal,
                                                                                                Due_amount=dueamount)

            return redirect('invoicepage', id=guestid)        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
    




def reviews(request):
    # Get the user_id (vendor ID) from the query parameter
    user_id = request.GET.get('cd')

    # Validate that user_id is provided
    if not user_id:
        return HttpResponse("Error: Missing vendor ID (cd parameter).")

    # Fetch the googleurl for the given vendor
    linkdata = googlereview.objects.filter(vendor_id=user_id).first()

    # Check if a googleurl is found; otherwise, handle gracefully
    if linkdata and linkdata.googleurl:
        url = linkdata.googleurl
    else:
        url = None

    hoteldata = HotelProfile.objects.get(vendor_id=user_id)

    # Pass the URL to the template
    return render(request, 'review.html', {'url': url,'hoteldata':hoteldata})