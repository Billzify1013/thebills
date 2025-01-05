from django.shortcuts import render, redirect,HttpResponse 
from . models import *
import datetime
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.urls import reverse

def comaypage(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            companydata= Companies.objects.filter(vendor=user)
            return render(request,'companypage.html',{'active_page':'comaypage','companydata':companydata})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)




def add_company(request):
    if request.user.is_authenticated:
        user = request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor 
        if request.method == "POST":
            # Get form data from the POST request
            companyname = request.POST.get("companyname")
            pname = request.POST.get("pname")  # Contact person name
            phone = request.POST.get("phone")
            emails = request.POST.get("emails")
            address = request.POST.get("address")
            gstno = request.POST.get("gstno")

            # Validate data (optional, but good practice)
            if not companyname or not pname or not phone or not address:
                messages.error(request, "Please fill in all required fields!")
                return redirect("comaypage")  # Redirect back to the form

            try:
                # Create and save the company instance
                company = Companies.objects.create(
                    vendor=user,  # The logged-in user
                    companyname=companyname,
                    contactpersonname=pname,
                    contact=phone,
                    email=emails,
                    address=address,
                    customergst=gstno,
                )
                company.save()
                messages.success(request, "Company added successfully!")
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")

        # Render the page (form will be shown again)
        return redirect('comaypage')
    else:
            return render(request, 'login.html')
    

def deletecompany(request,id):
    try:
        id =id
        if Companies.objects.filter(id=id).exists():
            Companies.objects.filter(id=id).delete()
            messages.success(request, "Company Delete successfully!")
        else:
            pass

        return redirect('comaypage')
    
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)


def get_companies(request):
    if request.user.is_authenticated:
        user=request.user
        subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
        if subuser:
            user = subuser.vendor 
        companies = Companies.objects.filter(vendor=user).values('id', 'companyname', 'contact')
        return JsonResponse(list(companies), safe=False)
    return JsonResponse({'error': 'Unauthorized'}, status=401)



def submit_form(request):
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        invoice_id = request.POST.get('invoice_id')
        value = request.POST.get('value', 'N/A')  # Default to 'N/A' if no value is provided

    
        if not company_id or not invoice_id:
            messages.error(request, 'Company and Invoice are required fields.')
            return JsonResponse({'status': 'error', 'message': 'Company and Invoice are required fields.'})

        try:
            user=request.user
            subuser = Subuser.objects.select_related('vendor').filter(user=user).first()
            if subuser:
                user = subuser.vendor 
            company = Companies.objects.get(id=company_id, vendor=user)
            invoice = Invoice.objects.get(id=invoice_id)
            
            val = invoice.grand_total_amount
            today = datetime.now().date()
            if companyinvoice.objects.filter(Invoicedata=invoice).exists():
                messages.success(request, 'Company invoice Already Exists !')
                return JsonResponse({'status': 'success', 'message': 'Company invoice Already Exists !'})
            else:
                # Create a new companyinvoice record
                company_invoice = companyinvoice.objects.create(
                    vendor=user,
                    company=company,
                    Invoicedata=invoice,
                    Value=val,
                    date=today,
                    is_paid=False
                )

                Invoice.objects.filter(id=invoice_id).update(customer_gst_number=company.customergst)

                messages.success(request, 'Company invoice created successfully!')
                return JsonResponse({'status': 'success', 'message': 'Company invoice created successfully!'})
            
        except Companies.DoesNotExist:
            messages.error(request, 'Company not found.')
            return JsonResponse({'status': 'error', 'message': 'Company not found.'})

        except Invoice.DoesNotExist:
            messages.error(request, 'Invoice not found.')
            return JsonResponse({'status': 'error', 'message': 'Invoice not found.'})

        except Exception as e:
            # Log unexpected errors for debugging
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred. Please try again.'})

    messages.error(request, 'Invalid request method.')
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def gotocmpbills(request,id):
    try:
        if request.user.is_authenticated:
            cmpinvcdata  = companyinvoice.objects.filter(company_id=id).all()
            a=1
            cname = ''
            for i in cmpinvcdata:
                if a>1:
                    break
                else:
                    cname = i.company.companyname
                    a=a+1

            return render(request,'cmpinvc.html',{'cmpinvcdata':cmpinvcdata,'active_page':'comaypage','cname':cname})
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)
