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
from django.db.models import F
from django.urls import reverse

def purchesinvoice(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            profiledata = HotelProfile.objects.filter(vendor=user)
            invcdata = Supplier.objects.filter(vendor=user, sattle=False).last()
            invoiceitemsdata = SupplierInvoiceItem.objects.filter(
                vendor=user, invoice=invcdata
            )

            purchasehsndata = taxSlabpurchase.objects.filter(vendor=user,invoice=invcdata)
            if invcdata:
                 taxtype = invcdata.taxtype
                # taxtype = "ggss"
            else:
                taxtype = None
            print(purchasehsndata)
            return render(
                request,
                "purchesinvoice.html",
                {
                    "active_page": "purchesinvoice",
                    "profiledata": profiledata,
                    "invcdata": invcdata,
                    "invoiceitemsdata": invoiceitemsdata,
                    'purchasehsndata':purchasehsndata,
                    'taxtype':taxtype
                },
            )

        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




def purchesinvoiceform(request):
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
            purchaseinvoicenumber = request.POST.get("purchaseinvoicenumber", "")
            sellinghsn = request.POST.get("sellinghsn", "")
            productprice_str = request.POST.get(
                "productprice", "0"
            )  # Default to '0' if not provided
            productqty_str = request.POST.get(
                "productqty", "0"
            )  # Default to '0' if not provided
            producttax_str = request.POST.get("producttax", "0")
            producthsn = request.POST.get("producthsn", "")
            productdiscount_str = request.POST.get("productdiscount", "0")
            
            isinvtry = request.POST.get("isinvtry")
            
            if isinvtry=="Yes":
                sellrate = request.POST.get("sellrate")
                isivdata = True
            else:
                isivdata = False
                sellrate=0
                pass

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

            

            # Create invoice
            today = datetime.now().date()
            invoiceid = Supplier.objects.create(
                vendor=user,
                customername=cname,
                customercontact=contact,
                customeremail=email,
                customeraddress=address,
                customergst=customergstno,
                companyname=companyname,
                invoicenumber=purchaseinvoicenumber,
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
                state=state
            )

            # Create invoice item
            SupplierInvoiceItem.objects.create(
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
                is_intvntory=isivdata,
                salerate=sellrate,
                sellinghsn=sellinghsn
            )

            if producthsn:
                productstaxbytwo = producttax / 2
                taxamountsbytwo = tax_amount / 2
                taxSlabpurchase.objects.create(vendor=user,invoice=invoiceid,tax_hsnsac_name=producthsn,cgst=productstaxbytwo,
                        sgst=productstaxbytwo,cgst_amount=taxamountsbytwo,sgst_amount=taxamountsbytwo,total_amount=tax_amount,
                        taxableamount=subtotal_amount)


            if isivdata==True:
                if producttax>0:
                        if Taxes.objects.filter(vendor=user,taxrate=producttax).exists():
                            taxdata = Taxes.objects.get(vendor=user,taxrate=producttax)
                        else:
                            if sellinghsn:
                                 taxhsn = sellinghsn
                            else:
                                 taxhsn = None
                            if True:
                                taxname = "GST"+str(producttax)
                                taxdata = Taxes.objects.create(vendor=user,
                                                               taxrate=producttax,
                                                               taxcode=taxhsn,
                                                               taxname=taxname)
                            else:
                                taxdata=None
                else:
                        taxdata=None
                if Items.objects.filter(vendor=user,description=productname).exists():
                    Items.objects.filter(
                        vendor=user,
                        description=productname).update(
                        available_qty=F('available_qty')+productqty,
                        total_qty=F('total_qty') + productqty,
                        price=sellrate,
                        category_tax=taxdata,
                        hsncode=sellinghsn,
                        
                    )
                    itemdata = Items.objects.get(vendor=user,description=productname)
                else:
                    
                    itemdata = Items.objects.create(
                        vendor=user,
                        description=productname,
                        category_tax=taxdata,
                        hsncode=sellinghsn,
                        price=sellrate,
                        available_qty=productqty,
                        total_qty=productqty 
                    )
                
            else:
                pass            
            messages.success(request, "Purches Invoice created successfully!")
            return redirect("purchesinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




def addmorepurchesproductininvoice(request):
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
            sellinghsn = request.POST.get("sellinghsn", "")
            isinvtry = request.POST.get("isinvtry1")
            if isinvtry=="Yes":
                sellrate = request.POST.get("sellrate1")
                isivdata = True
            else:
                isivdata = False
                sellrate=0
                pass

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

            invoicedata = Supplier.objects.get(vendor=user, id=invcid)
            

            invctotalamt = float(invoicedata.total_item_amount) + total_amount
            invcsubtotalamt = float(invoicedata.subtotal_amount) + subtotal_amount
            invcdiscountamt = float(invoicedata.discount_amount) + productdiscount
            invcgstamt = float(invoicedata.gst_amount) + taxamts
            invcsgstamt = float(invoicedata.sgst_amount) + taxamts
            invcgrandamt = float(invoicedata.grand_total_amount) + grand_total

            Supplier.objects.filter(vendor=user, id=invcid).update(
                total_item_amount=invctotalamt,
                discount_amount=invcdiscountamt,
                subtotal_amount=invcsubtotalamt,
                gst_amount=invcgstamt,
                sgst_amount=invcsgstamt,
                grand_total_amount=invcgrandamt,
            )
            print(grand_total,"printed code")
            # Create invoice item
            SupplierInvoiceItem.objects.create(
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
                is_intvntory=isivdata,
                salerate=sellrate,
                sellinghsn=sellinghsn,
                
            )
            
            spdata = Supplier.objects.get(id=invcid)
            productstaxbytwo = producttax / 2
            taxamountsbytwo = tax_amount / 2
            if taxSlabpurchase.objects.filter(vendor=user,invoice=spdata,tax_hsnsac_name=producthsn,cgst=productstaxbytwo).exists():
                taxSlabpurchase.objects.filter(vendor=user,invoice=spdata,tax_hsnsac_name=producthsn).update(cgst_amount=F('cgst_amount')+taxamountsbytwo,sgst_amount=F('sgst_amount')+taxamountsbytwo,total_amount= F('total_amount') + tax_amount,
                        taxableamount=F('taxableamount') + subtotal_amount)
            else:
                taxSlabpurchase.objects.create(vendor=user,invoice=spdata,tax_hsnsac_name=producthsn,cgst=productstaxbytwo,
                        sgst=productstaxbytwo,cgst_amount=taxamountsbytwo,sgst_amount=taxamountsbytwo,total_amount=tax_amount,
                        taxableamount=subtotal_amount)


            # i am working here
            if isivdata==True:
                if producttax>0:
                        if Taxes.objects.filter(vendor=user,taxrate=producttax).exists():
                            taxdata = Taxes.objects.get(vendor=user,taxrate=producttax)
                        else:
                            if True:
                                if sellinghsn:
                                    taccodes = sellinghsn
                                    taxname = "GST"+str(producttax)
                                taxdata = Taxes.objects.create(vendor=user,
                                                               taxrate=producttax,
                                                               taxcode=taccodes,
                                                               taxname=taxname)
                            else:
                                taxdata=None
                else:
                        taxdata=None
                if Items.objects.filter(vendor=user,description=productname).exists():
                    Items.objects.filter(
                        vendor=user,
                        description=productname).update(
                        available_qty=F('available_qty')+productqty,
                        total_qty=F('total_qty') + productqty,
                        price=sellrate,
                        category_tax=taxdata,
                        hsncode=sellinghsn,
                        
                    )
                    itemdata = Items.objects.get(vendor=user,description=productname)
                else:
                    
                    itemdata = Items.objects.create(
                        vendor=user,
                        description=productname,
                        category_tax=taxdata,
                        hsncode=sellinghsn,
                        price=sellrate,
                        available_qty=productqty,
                        total_qty=productqty 
                    )
               
            else:
                pass
            messages.success(request, "Items added successfully!")
            return redirect("purchesinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)



def purchesitemdelete(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            itemid = id
            if SupplierInvoiceItem.objects.filter(vendor=user, id=itemid).exists():
                itemsdata = SupplierInvoiceItem.objects.get(vendor=user, id=itemid)
                itemtotalamt = itemsdata.total_amount
                itemdiscount = itemsdata.discount_amount
                itemsubtotal = itemsdata.subtotal_amt
                itemtaxamt = itemsdata.tax_amt / 2
                itemgrandtotal = itemsdata.grand_total
                invoiceid = itemsdata.invoice.id
                quantity = itemsdata.quantity
                if itemsdata.is_intvntory:
                    
                    if Items.objects.filter(vendor=user,description=itemsdata.description).exists():
                        Items.objects.filter(vendor=user,description=itemsdata.description).update(
                           available_qty=F('available_qty')-quantity,
                           total_qty=F('total_qty')-quantity,
                        )
                        
                    else:
                        pass
                else:
                    pass
                
                if Supplier.objects.filter(vendor=user, id=invoiceid).exists():
                    invoicedata = Supplier.objects.get(
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
                    Supplier.objects.filter(vendor=user, id=invoiceid).update(
                        total_item_amount=invoicetotalamt,
                        discount_amount=invoicediscountamt,
                        subtotal_amount=invoicesubtotalamt,
                        gst_amount=invoicegstamt,
                        sgst_amount=invoicesgstamt,
                        grand_total_amount=invoicegrandtotalamt,
                    )
                    
                    SupplierInvoiceItem.objects.filter(vendor=user, id=itemid).delete()
                    messages.success(request, "items delete succesfully!")
                else:
                    messages.error(request, "Please delete this full invoice")
            else:
                messages.error(request, "Items already  deleted ")

            return redirect("purchesinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




def deletepurchesinvc(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            invcid = id
            if Supplier.objects.filter(vendor=user, id=invcid).exists():
                spdata = Supplier.objects.get(vendor=user, id=invcid)
                spitemdata = SupplierInvoiceItem.objects.filter(vendor=user,invoice=spdata)
                for i in spitemdata:
                    check = i.is_intvntory
                    if check:
                        pname = i.description
                        quantity=i.quantity
                        if Items.objects.filter(vendor=user,description=pname).exists():
                            Items.objects.filter(vendor=user,description=pname).update(
                            available_qty=F('available_qty')-quantity,
                            total_qty=F('total_qty')-quantity,
                            )
                           
                        else:
                            pass
                    
                Supplier.objects.filter(vendor=user, id=invcid).delete()
                messages.success(request, "Invoice delete succesfully!")
                return redirect("purchesinvoice")
            else:
                messages.success(request, "Invoice already deleted!")
                return redirect("purchesinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)



def savepurchesinvoice(request):
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
            today = datetime.now().date()
            datainvc = Supplier.objects.get(vendor=user, id=invoiceid)
            totalamt = datainvc.grand_total_amount
            # if paymentmode == "cash":
            #     Supplier.objects.filter(vendor=user, id=invoiceid).update(
            #         modeofpayment="cash", sattle=True, cash_amount=totalamt
            #     )
            # elif paymentmode == "online":
            #     Supplier.objects.filter(vendor=user, id=invoiceid).update(
            #         modeofpayment="online", sattle=True, online_amount=totalamt
            #     )
            # elif paymentmode == "Partly":
            #     Supplier.objects.filter(vendor=user, id=invoiceid).update(
            #         modeofpayment="Partly",
            #         sattle=True,
            #         cash_amount=cashamount,
            #         online_amount=onlineamount,
            #     )
             
            if paymentmode == "unpaid":
                Supplier.objects.filter(vendor=user, id=invoiceid).update(
                    modeofpayment="unpaid",
                    sattle=True,
                    unpaid=True,
                    due_amount = totalamt,
                    reviced_amount = 0.00,
                )
            
            else:
                PurchasePayment.objects.create(vendor=user,invoice=datainvc,payment_amount=totalamt,payment_date=today,
                                payment_mode= paymentmode,transaction_id='',descriptions='' )
                
                Supplier.objects.filter(vendor=user, id=invoiceid).update(
                    modeofpayment=paymentmode,
                    sattle=True,
                    due_amount=0.00,
                    reviced_amount=totalamt,
                )

            return redirect("purchesinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def purcheshistory(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            advanceroomsdata = Supplier.objects.filter(vendor=user).order_by(
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
                "purcheshistory.html",
                {
                    "active_page": "purcheshistory",
                    "advanceroomdata": advanceroomdata,
                    "checkdata": "yes",
                },
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)



def searchpurchesdata(request):
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
            queryset = Supplier.objects.filter(vendor=user).order_by("-id")

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
                "purcheshistory.html",
                {"active_page": "purcheshistory", "advanceroomdata": queryset},
            )
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




def purchesinvoices(request, id):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            invcid = id
            if Supplier.objects.filter(
                vendor=user, id=invcid, sattle=True
            ).exists():
                invoice_data = Supplier.objects.filter(vendor=user, id=invcid)
                invoiceitemdata = SupplierInvoiceItem.objects.filter(
                    vendor=user, invoice_id=invcid
                )
                invcdata = Supplier.objects.get(vendor=user, id=invcid)
                purchasehsndata = taxSlabpurchase.objects.filter(vendor=user,invoice=invcdata)
                if invcdata:
                    taxtype = invcdata.taxtype
                    # taxtype = "ggss"
                else:
                    taxtype = None
                invcpayments = PurchasePayment.objects.filter(vendor=user,invoice=invcdata)
                return render(
                    request,
                    "purchesinvoicepage.html",
                    {
                        "invoice_data": invoice_data,
                        "invoiceitemdata": invoiceitemdata,
                        'purchasehsndata':purchasehsndata,
                        'taxtype':taxtype,
                        'invcpayments':invcpayments
                    },
                )
            else:
                messages.error(request, "Invoice Not Saved!")
                return redirect("aminityinvoice")
        else:
            return redirect("loginpage")
    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)
    


def purchessales(request):
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
            monthly_sales = Supplier.objects.filter(
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
                "purchessales.html",
                {
                    "active_page": "purchessales",
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


def searpurchesinvoicedata(request):
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
            monthly_sales = Supplier.objects.filter(
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
                "purchessales.html",
                {
                    "active_page": "purchessales",
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

from django.http import HttpResponseRedirect
from .models import Supplier


def channalmanager(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            if VendorCM.objects.filter(vendor=user).exists():
                data =  VendorCM.objects.get(vendor=user)
                url = data.channal_manager_link
                if url:
                    # Return an HTML response that will instruct the browser to open the URL in a new tab
                        return HttpResponse(f'''
                        <html>
                            <body>
                                <script type="text/javascript">
                                    // Open the URL in a new tab
                                    window.open("{url}", "_blank");
                                    // Redirect to another page (replace '/your-redirect-url/' with the actual URL)
                                    window.location.href = '/homepage/';
                                </script>
                            </body>
                        </html>
                    ''')
                else:
                    messages.error(request,"You Are Not Using Channel Manager")
                    return redirect("homepage")

            else:
                return redirect("homepage")


        else:
                return redirect("loginpage")

    except Exception as e:
        return render(request, "404.html", {"error_message": str(e)}, status=500)




from django.http import JsonResponse
from .models import Supplier
from django.db.models import Q


def get_supplier_details(request):
    if request.method == "GET":
        supplier_name = request.GET.get('supplier_name', '').strip()

        # Ensure that the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'User is not authenticated'})

        if supplier_name:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            # Filter suppliers based on the logged-in user and supplier name
            suppliers = Supplier.objects.filter(
                vendor=user,  # Only show suppliers linked to the current logged-in user 
                customercontact__icontains=supplier_name  # Partial match for the supplier name
            )

            if suppliers.exists():
                profiledata = HotelProfile.objects.get(vendor=user)
                supplier = suppliers.last()  # You can modify to return multiple suppliers if needed
                if supplier.taxtype == 'GST':
                     state = profiledata.zipcode
                else:
                     state='other'
                print(state)
                supplier_data = {
                    'customername': supplier.customername,
                    'customercontact': supplier.customercontact,
                    'customeremail': supplier.customeremail,
                    'customeraddress': supplier.customeraddress,
                    'customergst': supplier.customergst,
                    'companyname': supplier.companyname,
                    'invoicenumber': supplier.invoicenumber,
                    'invoicedate': supplier.invoicedate,
                    'taxtype': supplier.taxtype,
                    'total_item_amount': str(supplier.total_item_amount),
                    'discount_amount': str(supplier.discount_amount),
                    'subtotal_amount': str(supplier.subtotal_amount),
                    'gst_amount': str(supplier.gst_amount),
                    'sgst_amount': str(supplier.sgst_amount),
                    'grand_total_amount': str(supplier.grand_total_amount),
                    'modeofpayment': supplier.modeofpayment,
                    'cash_amount': str(supplier.cash_amount),
                    'online_amount': str(supplier.online_amount),
                    'sattle': supplier.sattle,
                    'state':str(state),
                }

                return JsonResponse({'status': 'success', 'data': supplier_data})
            else:
                return JsonResponse({'status': 'error', 'message': 'No supplier found'})

        return JsonResponse({'status': 'error', 'message': 'Supplier name is required'})
    
import json
@csrf_exempt
def fetch_supplier_items(request):
    if request.method == "POST":
        data = json.loads(request.body)
        description = data.get("description", "").strip()

        if description:
            # Filter SupplierInvoiceItem based on the description
            # Fetch all matching items
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor  
            items = SupplierInvoiceItem.objects.filter(
                vendor=user,
                description__icontains=description
            ).values(
                'id', 'description', 'price', 'tax_rate', 'hsncode', 'discount_amount' , 'is_intvntory',
                'salerate','sellinghsn'
            )

            # Remove duplicates using a dictionary to retain the first occurrence
            unique_items = {item['description']: item for item in items}.values()
        
            # Convert to a list for further processing
            items = list(unique_items)
            
            last_item = items[-1] if items else None

            

            # Return the last item in the response
            return JsonResponse({'success': True, 'items': [last_item]}, status=200)
        
        return JsonResponse({'success': False, 'error': 'No description provided.'}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)



def addpaymentpagepurchase(request,id):

    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                    user = subuser.vendor 
            if Supplier.objects.filter(vendor=user,id=id).exists():
                spdata = Supplier.objects.get(vendor=user,id=id)

                return render(request,'purchaseamt.html',{'spdata':spdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def addpaymenttopurchase(request):
    if request.user.is_authenticated and request.method == "POST":
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
                    user = subuser.vendor 
        amount = float(request.POST.get("amount"))
        paymentmode = request.POST.get("paymentmode")
        paymntdetails = request.POST.get("paymntdetails")
        comment = request.POST.get("comment")
        suppilerid = request.POST.get("suppilerid")
        today = datetime.now().date()
        if Supplier.objects.filter(id=suppilerid).exists():
            spdata = Supplier.objects.get(id=suppilerid)
            dueamount = spdata.due_amount
            if float(dueamount) == amount:
                PurchasePayment.objects.create(vendor=user,invoice=spdata,payment_amount=dueamount,payment_date=today,
                                payment_mode= paymentmode,transaction_id=paymntdetails,descriptions=comment )
                
                Supplier.objects.filter(vendor=user, id=suppilerid).update(
                    modeofpayment=paymentmode,
                    sattle=True,
                    due_amount=0.00,
                    unpaid=False,
                    reviced_amount=dueamount,
                )
            else:
                if amount > spdata.due_amount:
                    messages.error(request,"Amount grater then billing amount")
                    return redirect('purcheshistory') 
                
                else:
                    dueamounts = float(spdata.due_amount) - amount
                    PurchasePayment.objects.create(vendor=user,invoice=spdata,payment_amount=amount,payment_date=today,
                                payment_mode= paymentmode,transaction_id=paymntdetails,descriptions=comment )
                    
                    Supplier.objects.filter(vendor=user, id=suppilerid).update(
                    modeofpayment=paymentmode,
                    due_amount=dueamounts,
                    unpaid=True,
                    reviced_amount=F('reviced_amount') + amount,
                    )

                     

            userid = spdata.id
            url = reverse('purchesinvoices', args=[userid])
            return redirect(url)

        else:
            messages.error(request,"data not found")
            return redirect('purcheshistory') 

    else:
            return redirect("loginpage")

        
