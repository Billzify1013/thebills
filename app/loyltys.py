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


def setting(request):
    try:
        if request.user.is_authenticated:
            user = request.user
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
            loyltypersantage = request.POST.get("loyltypersantage")
            checkbox = request.POST.get("checkbox")
            print(checkbox)
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
    if request.user.is_authenticated:
        user = request.user
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


def addcreditcustomer(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            user = request.user
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
            profiledata = HotelProfile.objects.filter(vendor=user)
            invcdata = AminitiesInvoice.objects.filter(vendor=user, sattle=False).last()
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
            print(
                "total",
                total_amount,
                "subt",
                subtotal_amount,
                "tax",
                tax_amount,
                "grandt",
                grand_total,
                "disc",
                productdiscount,
            )

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

            return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def aminityhistory(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            advanceroomsdata = AminitiesInvoice.objects.filter(vendor=user).order_by(
                "-id"
            )
            print(advanceroomsdata)
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
            invcid = id
            if AminitiesInvoice.objects.filter(vendor=user, id=invcid).exists():
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
            invcid = id
            if AminitiesInvoice.objects.filter(
                vendor=user, id=invcid, sattle=True
            ).exists():
                profiledata = HotelProfile.objects.filter(vendor=user)
                invoice_data = AminitiesInvoice.objects.filter(vendor=user, id=invcid)
                invoiceitemdata = AminitiesInvoiceItem.objects.filter(
                    vendor=user, invoice_id=invcid
                )
                return render(
                    request,
                    "aminityinvoicepage.html",
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

            print(total_gst, total_sgst)
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
            print(guestdata)
            return render(
                request,
                "guestshowexport.html",
                {"guestdata": guestdata, "startdate": startdate, "enddate": enddate},
            )

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)


def cleanroombtn(request, id):
    if request.user.is_authenticated:
        user = request.user
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
        data = Rooms.objects.get(vendor=user, room_name=id)
        status = data.is_clean
        if status == True:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=False)
        else:
            Rooms.objects.filter(vendor=user, room_name=id).update(is_clean=True)

        return redirect("weekviews")


import json


def sendbulksmsloylty(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            # selected_ids = request.POST.get("selected_ids")
            # Convert from JSON string to Python list
            # Process the IDs, e.g., send SMS to each guest
            # print(selected_ids,'ids')
            # return redirect('loylty')
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
                    "authkey": settings.YOURBULKSMS_API_KEY,
                    "mobiles": mobile_number,
                    "sender": "BILZFY",
                    "route": "2",
                    "country": "0",
                    "DLT_TE_ID": "1707171993560691064",
                }
                encoded_message = urllib.parse.urlencode({"message": message_content})
                url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"

                loylty_Guests_Data.objects.filter(vendor=user, id=id).update(smscount="1")
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
            loylty_Guests_Data.objects.get(vendor=user, id=id).delete()
            messages.success(request, "Deleted Succesfully")
            return redirect('loylty')
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)



# def search_user(request):
#     if request.user.is_authenticated:
#         user = request.user
#         # Get the mobile number from the GET request as a string
#         mobile_number = request.GET.get('mobile_number', '').strip()

#         # Validate if the mobile number is provided
#         if not mobile_number:
#             return JsonResponse({'success': False, 'message': 'Mobile number is required'})

#         try:
#             print("try is worked")
#             # Search for a guest with the given mobile number and vendor
#             # Assuming 'guestphome' is a string field and 'vendor' is the authenticated user
#             guest = Gueststay.objects.filter(vendor=user, guestphome=mobile_number).last()  # Adjust to your actual model fields
#             print(guest)
#             # If a guest is found, return their details
#             guest_details = {
#                 'name': guest.guestname,  # Adjust to your model fields
#                 'email': guest.guestemail,
#                 'mobile': guest.guestphome,
#                 'address': guest.guestcity,  # Adjust if necessary
#             }

#             return JsonResponse({'success': True, 'user': guest_details})
        
#         except Gueststay.DoesNotExist:
#             # If no guest is found, return an error message
#             return JsonResponse({'success': False, 'message': 'No guest found with this mobile number for the current user.'})
        
#         except Exception as e:
#             # Return a generic error message in case of unexpected issues
#             return JsonResponse({'success': False, 'message': str(e)})
        

def search_user(request):
    if request.user.is_authenticated:
        user = request.user
        # Get the mobile number from the GET request
        mobile_number = request.GET.get('mobile_number', '').strip()

        # Validate if the mobile number is provided
        if not mobile_number:
            return JsonResponse({'success': False, 'message': 'Mobile number is required'})

        try:
            # First, check in the AminitiesInvoice model
            invoice = AminitiesInvoice.objects.filter(vendor=user, customercontact=mobile_number).last()  # Adjust field names if necessary

            if invoice:
                # If a matching entry is found in AminitiesInvoice, return those details
                guest_details = {
                    'name': invoice.customername,
                    'email': invoice.customeremail,
                    'mobile': invoice.customercontact,
                    'address': invoice.customeraddress,
                    'customercompany': invoice.customercompany,
                    'customergst': invoice.customergst,
                    
                }
                return JsonResponse({'success': True, 'user': guest_details})

           
            else:
                 # If no matching entry in AminitiesInvoice, check in Gueststay
                guest = Gueststay.objects.filter(vendor=user, guestphome=mobile_number).last()  # Adjust field names if necessary

                # If a matching guest is found in Gueststay, return those details
                guest_details = {
                    'name': guest.guestname,
                    'email': guest.guestemail,
                    'mobile': guest.guestphome,
                    'address': guest.guestcity,
                    'customercompany': 'none',
                    'customergst': 'none',
                }
                return JsonResponse({'success': True, 'user': guest_details})

            # If no guest is found in either model, return an error message
            return JsonResponse({'success': False, 'message': 'No user found with this mobile number for the current user.'})

        except Exception as e:
            # Return a generic error message in case of unexpected issues
            return JsonResponse({'success': False, 'message': str(e)})
        


import re
def check_product(request):
    if request.user.is_authenticated:
        user = request.user
        product_name = request.GET.get('product_name', '').strip()

        if product_name:
            try:
                # Normalize spaces in the input
                normalized_product_name = re.sub(r'\s+', ' ', product_name).strip()

                # Search for products matching the product_name
                products = Items.objects.filter(
                    vendor=user,
                    description__icontains=normalized_product_name
                )

                products2 = LaundryServices.objects.filter(
                            vendor=user,
                            name__icontains=normalized_product_name
                        )
                if products.exists():
                    # Prepare a list of products for suggestions
                    product_suggestions = []
                    for product in products:
                        product_suggestions.append({
                            'id': product.id,
                            'description': product.description,
                            'price': product.price,
                            'hsncode': product.hsncode,
                            'category_tax': product.category_tax.taxrate if product.category_tax else None
                        })

                    return JsonResponse({
                        'success': True,
                        'products': product_suggestions
                    })

                
                elif products2.exists():
                    # Prepare a list of products for suggestions
                    product_suggestions = []
                    for product in products2:
                        product_suggestions.append({
                            'id': product.id,
                            'description': product.name,
                            'price': product.price,
                            # 'hsncode': product.hsncode,
                            # 'category_tax': product.category_tax.taxrate if product.category_tax else None
                        })

                    return JsonResponse({
                        'success': True,
                        'products': product_suggestions
                    })
                else:
                    return JsonResponse({'success': False, 'message': 'No products found.'})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})

        else:
            return JsonResponse({'success': False, 'message': 'Product name is required.'})




