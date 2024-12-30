from django.shortcuts import render, redirect
from . models import *
import datetime
from datetime import  timedelta
from django.contrib import messages
from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models import OuterRef, Subquery
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from django.shortcuts import render, get_object_or_404
import json
import requests
from django.conf import settings
import urllib.parse
from django.db.models import F, ExpressionWrapper, DurationField, Avg, Case, When, Value, DateTimeField, OuterRef, Subquery
from django.db.models import Count


def employee(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            empdata = Employee.objects.filter(vendor=user).all()
            return render(request,'employeepage.html',{'active_page': 'employee','empdata':empdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def addemployee(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            firstname = request.POST.get('firstname')
            lastname = request.POST.get('lastname')
            dob = request.POST.get('dob')
            joindate = request.POST.get('joindate')
            Position = request.POST.get('Position')
            Department = request.POST.get('Department')
            phone = request.POST.get('phone')
            salarybyday = request.POST.get('salarybyday')
            workinghour = request.POST.get('workinghour')
            Employee.objects.create(vendor=user,first_name=firstname,last_name=lastname,date_of_birth=dob,
                    date_of_joining=joindate,position=Position,department=Department,employee_contact=phone,salarybyday=salarybyday
                    ,working_hours=workinghour)
            empdata = Employee.objects.filter(vendor=user).all()
            return render(request,'employeepage.html',{'active_page': 'employee','empdata':empdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def deleteemployee(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            if Employee.objects.filter(vendor=user,id=id).exists():
                Employee.objects.filter(vendor=user,id=id).delete()
                empdata = Employee.objects.filter(vendor=user).all()
                return render(request,'employeepage.html',{'active_page': 'employee','empdata':empdata})
            else:
                empdata = Employee.objects.filter(vendor=user).all()
                return render(request,'employeepage.html',{'active_page': 'employee','empdata':empdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
             
def updateemployee(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            # Employee.objects.filter(vendor=user,id=id).update()
            empdata = Employee.objects.filter(vendor=user).all()
            return render(request,'employeepage.html',{'active_page': 'employee','empdata':empdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
    

def dailyattendance(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            current_date = datetime.now().date()
           
            
            current_datetime = datetime.now()
            subtracted_time = current_datetime - timedelta(hours=24)
            # Find the most recent date that has data
            most_recent_date = Employee.objects.filter(
                vendor=user
            ).aggregate(
                max_date=Max('dailymanagement__date')
            )['max_date']
            
            
            
            
            # new chat gpt code jo chal raha hai
            current_datetime = datetime.now()
            subtracted_time = current_datetime - timedelta(hours=24)
            lastday = current_datetime - timedelta(days=1)

            

            if most_recent_date:
                employees_not_checked_out = Employee.objects.filter(
                    Q(vendor=user) &
                    Q(dailymanagement__check_out_time=None) &
                    Q( Q(Q(dailymanagement__date=lastday) & Q(dailymanagement__check_out_time=None))) &
                    Q(dailymanagement__check_in_time__gte=subtracted_time)
                ).distinct()
            else:
                employees_not_checked_out = Employee.objects.none()  # No data found

            employees_current_date_not_checked_out = Employee.objects.filter(
                    Q(vendor=user) &
                    Q(dailymanagement__check_out_time=None) &
                    Q( dailymanagement__date=current_date ) 
                ).distinct()
            employees_not_checked_out = employees_not_checked_out | employees_current_date_not_checked_out
            employees_not_checked_in = Employee.objects.filter(
                vendor=user
            ).exclude(id__in=employees_not_checked_out.values('id'))
            return render(request,'dailyattendance.html',{'active_page': 'dailyattendance',
                        'employees_not_checked_in':employees_not_checked_in,'employees_not_checked_out':employees_not_checked_out,})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     



    
def employeecheckin(request,dsd):
    try:
        if request.user.is_authenticated:
            user=request.user
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            if DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).exists():
                messages.error(request,"Employees completed their jobs today and will check in again tomorrow.")
                return redirect('dailyattendance')
            else:
                DailyManagement.objects.create(vendor=user,employee_id=dsd,date=current_date,check_in_time=current_time)
                messages.success(request,"Employees successfully checked in.")
                return redirect('dailyattendance')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def employeecheckout(request,dsd):
    try:
        if request.user.is_authenticated:
            user=request.user
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            lastday = current_date - timedelta(days=1)
            if DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).exists():
                DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).update(check_out_time=current_time)
                messages.success(request,"Employees successfully checked Out.")
                return redirect('dailyattendance')
            
            elif DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=lastday).exists() and  not DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).exists():
                DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=lastday).update(check_out_time=current_time)
                messages.success(request,"Employees successfully checked Out.")
                return redirect('dailyattendance')
            else:
                return redirect('dailyattendance')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def employeehalfday(request,dsd):
    try:
        if request.user.is_authenticated:
            user=request.user
            current_date = datetime.now().date()
            current_time = datetime.now().time()
            if DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).exists():
                DailyManagement.objects.filter(vendor=user,employee_id=dsd,date=current_date).update(halfday=True,check_out_time=current_time)
                messages.success(request,"Employees successfully checked Out in Halfday.")
                return redirect('dailyattendance')
            else:
                return redirect('dailyattendance')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     

def attendancepage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            current_date = datetime.now().date()
            empsdata = DailyManagement.objects.filter(vendor=user).all()
            datas = Employee.objects.annotate(attendance_count=Count('dailymanagement')).filter(vendor=user,dailymanagement__date__lt=current_date).values()
            return render(request,'attencancepage.html',{'empdata':datas,'active_page': 'attendancepage',})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def employeereport(request,eid):
    try:
        if request.user.is_authenticated:
            user=request.user
            empattendancedata = DailyManagement.objects.filter(vendor=user,employee_id=eid).order_by('date')
            start_date = DailyManagement.objects.filter(vendor=user,employee_id=eid).earliest('date').date
            last_date = DailyManagement.objects.filter(vendor=user,employee_id=eid).latest('date').date
            
            s=str(start_date)
            e=str(last_date)
            start_date =  datetime.strptime(s, '%Y-%m-%d').date()
            end_date = datetime.strptime(e, '%Y-%m-%d').date()
            # Calculate the difference in days and add 1
            dayscount = (end_date - start_date).days + 1
            
            all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
            present_dates = DailyManagement.objects.filter(vendor=user,employee_id=eid,date__range=[start_date, end_date]).values_list('date', flat=True)
        
            present_dates_set = set(present_dates)
            lost_days = [d for d in all_dates if d not in present_dates_set]
            leavsday = len(lost_days)
            
            comeday = dayscount - leavsday
            halfdaycount = DailyManagement.objects.filter(vendor=user,employee_id=eid,halfday=True).count()
            fulldaycount = DailyManagement.objects.filter(vendor=user,employee_id=eid,halfday=False).count()
            # create salary function start
            employe = Employee.objects.get(vendor=user,id=eid)
            salary = employe.salarybyday
            halfdaysalcount = halfdaycount/2
            totalsalaryday = comeday - halfdaysalcount
            totalsalary = totalsalaryday * salary
            
        

            # Get the specific employee
            employee = get_object_or_404(Employee, id=eid)
            

            # Fetch all DailyManagement entries for this employee
            daily_management_entries = DailyManagement.objects.filter(vendor=user, employee=employee)

            # Initialize variables for calculating total working time
            total_working_seconds = 0
            valid_entries_count = 0

            for entry in daily_management_entries:
                check_in_datetime = datetime.combine(entry.date, entry.check_in_time)

                if entry.check_out_time:
                    # Determine the checkout date (same date or next day)
                    check_out_date = entry.date if entry.check_out_time >= entry.check_in_time else entry.date + timedelta(days=1)
                    check_out_datetime = datetime.combine(check_out_date, entry.check_out_time)

                    # Calculate working duration
                    working_duration = check_out_datetime - check_in_datetime
                    total_working_seconds += working_duration.total_seconds()
                    valid_entries_count += 1

            if valid_entries_count > 0:
                avg_working_seconds = total_working_seconds / valid_entries_count
                avg_working_hours = avg_working_seconds / 3600
                avg_working_time_in_hours = round(avg_working_hours, 2)
            else:
                avg_working_time_in_hours = 0
            return render(request,'attendancereportpage.html',{'empattendancedata':empattendancedata,'active_page': 'attendancepage','start_date':s,'last_date':e,'dayscount':dayscount,'leavsday':leavsday,'comeday':comeday
                                                            ,'avg_working_time_in_hours':avg_working_time_in_hours,'fulldaycount':fulldaycount,'salary':salary,'halfdaycount':halfdaycount,'totalsalaryday':totalsalaryday,'totalsalary':totalsalary})
        
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def addsalary(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            employeeid = request.POST.get('employeeid')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            salarytotalday = request.POST.get('salarytotalday')
            salary = request.POST.get('salary')
            bonus = request.POST.get('bonus')
            descount = request.POST.get('descount')
            start_date_obj = datetime.strptime(startdate, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(enddate, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            SalaryManagement.objects.create(vendor=user,employee_id=employeeid,salary_date=today,start_date=start_date_obj,
                                end_date=end_date_obj,salary_days=salarytotalday,basic_salary=salary,bonus=bonus,deductions=descount)
            
            if DailyManagement.objects.filter(vendor=user,employee_id=employeeid).exists():
                DailyManagement.objects.filter(vendor=user,employee_id=employeeid).delete()
                usermsglimit = Messgesinfo.objects.get(vendor=user)
                empdata = Employee.objects.get(vendor=user,id=employeeid)
                empphone = empdata.employee_contact
                empname = empdata.first_name
                hoteldata = HotelProfile.objects.get(vendor=user)
                hotelname = hoteldata.name
                if usermsglimit.defaultlimit > usermsglimit.changedlimit :
                        addmsg = usermsglimit.changedlimit + 2
                        Messgesinfo.objects.filter(vendor=user).update(changedlimit=addmsg)
                        profilename = HotelProfile.objects.get(vendor=user)
                        mobile_number = empphone
                        user_name = empname
                        val = 5
                        message_content = f"Hello {empname}, your salary for {salary} has been successfully credited. We value your ongoing efforts and contributions. Best regards, {hotelname} - Billzify"
                            
                        base_url = "http://control.yourbulksms.com/api/sendhttp.php"
                        params = {
                            'authkey': settings.YOURBULKSMS_API_KEY,
                            'mobiles': empphone,
                            'sender':  'BILZFY',
                            'route': '2',
                            'country': '0',
                            'DLT_TE_ID': '1707171992237495364'
                        }
                        encoded_message = urllib.parse.urlencode({'message': message_content})
                        url = f"{base_url}?authkey={params['authkey']}&mobiles={params['mobiles']}&sender={params['sender']}&route={params['route']}&country={params['country']}&DLT_TE_ID={params['DLT_TE_ID']}&{encoded_message}"
                        
                        try:
                            response = requests.get(url)
                            if response.status_code == 200:
                                try:
                                    response_data = response.json()
                                    if response_data.get('Status') == 'success':
                                        messages.success(request, 'SMS sent successfully.')
                                    else:
                                        messages.success(request, response_data.get('Description', 'Failed to send SMS'))
                                except ValueError:
                                    messages.success(request, 'Failed to parse JSON response')
                            else:
                                messages.success(request, f'Failed to send SMS. Status code: {response.status_code}')
                        except requests.RequestException as e:
                            messages.success(request, f'Error: {str(e)}')
                else:
                    messages.error(request,'Ooooops! Looks like your message balance is depleted. Please recharge to keep sending SMS notifications to your guests.CLICK HERE TO RECHARGE!')
                
                return redirect('attendancepage')
            else:
                return redirect('attendancepage')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def payslippage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            empdata = SalaryManagement.objects.filter(vendor=user)
            return render(request,'payslippage.html',{'empdata':empdata,'active_page': 'payslippage',})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def showpayslip(request,eid):
    try:
        if request.user.is_authenticated:
            user=request.user
            empdata = SalaryManagement.objects.filter(vendor=user)
            employeedata = SalaryManagement.objects.filter(vendor=user,id=eid)
            return render(request,'payslippage.html',{'empdata':empdata,'employeedata':employeedata,'active_page': 'payslippage',})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def eventpackage(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            eventdata = Events.objects.filter(vendor=user)
            tax = Taxes.objects.filter(vendor=user).all()
            return render(request,'eventpackagepage.html',{'active_page': 'eventpackage','tax':tax,'eventdata':eventdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def createevent(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            eventname = request.POST.get('eventname')
            price = request.POST.get('price')
            taxcategory = request.POST.get('taxcategory')
            description = request.POST.get('description')
            termscondition = request.POST.get('termscondition')
            hsncode = request.POST.get('hsncode')
            Events.objects.create(vendor=user,eventname=eventname,eventprice=price,eventax_id=taxcategory,description=description,termscondition=termscondition,Hsn_sac=hsncode)
            eventdata = Events.objects.filter(vendor=user)
            tax = Taxes.objects.filter(vendor=user).all()
            return render(request,'eventpackagepage.html',{'active_page': 'eventpackage','tax':tax,'eventdata':eventdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def searchdateevent(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            dataid = request.POST.get('dataid')
            start_date = datetime.strptime(startdate, '%Y-%m-%d').date()
            end_date=datetime.strptime(enddate, '%Y-%m-%d').date()
            eventdata = Events.objects.filter(vendor=user,id=dataid)
            if EventBookGuest.objects.filter(vendor=user,event_id=dataid,start_date__lte=end_date,end_date__gte=start_date).exists():
                errordata = EventBookGuest.objects.filter(vendor=user,event_id=dataid,start_date__lte=end_date,end_date__gte=start_date)
                for i in errordata:
                    stdate = i.start_date
                    edate = i.end_date

                messages.error(request,f'This Event Booked For this date    STARTDATE:{stdate}  TO   ENDDATE:{edate}')
                return redirect('eventpackage')
            else:
                return render(request,'bookeventpage.html',{'eventdata':eventdata,'active_page': 'eventpackage','startdate':startdate,'enddate':enddate})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
        

def billingplanpage(request):
    try:
        if request.user.is_authenticated:
            user = request.user

            # Get the latest subscription for the user
            subscription = Subscription.objects.filter(user=user).order_by('-id').first()
        
            if subscription:
                startdate = subscription.start_date
                enddate = subscription.end_date

                # Calculate the necessary date ranges
                bookingdate = startdate
                checkoutdate = enddate
                today = datetime.now().date()
                totalday = (checkoutdate - bookingdate).days
                completed_days = (today - bookingdate).days

                dayswidth = (completed_days / totalday) * 100 if totalday != 0 else 0

                # Calculate the remaining days until checkout
                remaining_days = (checkoutdate - today).days

                # Get message info for the user, or set default values
                msgdata = Messgesinfo.objects.filter(vendor=user).first()
                if msgdata:
                    totalmsg = msgdata.defaultlimit
                    usemsg = msgdata.changedlimit
                else:
                    totalmsg = 1
                    usemsg = 0

                remainmsg = totalmsg - usemsg
                totalwidthmsg = (usemsg / totalmsg) * 100 if totalmsg != 0 else 0

                fiftyper = 50
                planname = subscription.plan.name
                planenddate = subscription.end_date
                return render(request, 'billingplanpage.html', {
                    'planname':planname,
                    'planenddate':planenddate,
                    'totalday': totalday,
                    'completedays': completed_days,
                    'dayswidth': dayswidth,
                    'fiftyper': fiftyper,
                    'reaminday': remaining_days,
                    'totalmsg': totalmsg,
                    'usemsg': usemsg,
                    'remainmsg': remainmsg,
                    'totalwidthmsg': totalwidthmsg
                })
            else:
                return render(request, 'index.html')

        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     

def createeventbooking(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            customername = request.POST.get('customername')
            customeremail = request.POST.get('customeremail')
            customerphone = request.POST.get('customerphone')
            customeraddress = request.POST.get('customeraddress')
            customergstin = request.POST.get('customergstin')
            totalamount = request.POST.get('totalamount')
            discountamount = request.POST.get('discountamount')
            subtotal = request.POST.get('subtotal')
            taxamount = request.POST.get('taxamount')
            advanceamount = request.POST.get('advanceamount')
            reamainingamount = request.POST.get('reamainingamount')
            eventid = request.POST.get('eventid')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            state = request.POST.get('STATE')
            userstatedata = HotelProfile.objects.get(vendor=user)
            userstate = userstatedata.zipcode
            if userstate == state:
                taxtypes = "GST"
            else:
                taxtypes = "IGST"
            grandstotal = float(subtotal) + float(taxamount)
            EventBookGuest.objects.create(vendor=user,customername=customername,guestemail=customeremail,customer_contact=customerphone,
                        customeraddress=customeraddress,customergst=customergstin,total=totalamount,discount=discountamount,
                            subtotal=subtotal,taxamount=taxamount,advanceamount=advanceamount,reamainingamount=reamainingamount,event_id=eventid,
                            start_date=startdate,end_date=enddate,taxtype=taxtypes,Grand_total_amount= grandstotal)
            return render(request,'upcomingevents.html')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def upcomingevent(request):
    try:
        if request.user.is_authenticated:
            user=request.user
            eventdata = EventBookGuest.objects.filter(vendor=user)
            return render(request,'upcomingevents.html',{'active_page': 'upcomingevent','eventdata':eventdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def deleteupcomingevent(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            eventdata = EventBookGuest.objects.filter(vendor=user)
            if EventBookGuest.objects.filter(vendor=user,id=id).exists():
                EventBookGuest.objects.filter(vendor=user,id=id).delete()
                return render(request,'upcomingevents.html',{'active_page': 'upcomingevent','eventdata':eventdata})
            else:
                return render(request,'upcomingevents.html',{'active_page': 'upcomingevent','eventdata':eventdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def showeventinvoice(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            if EventBookGuest.objects.filter(vendor=user,id=id).exists():
                eventdata = EventBookGuest.objects.filter(vendor=user,id=id).all()
                events = Events.objects.filter(vendor=user)
                profiledata = HotelProfile.objects.filter(vendor=user).all()
                return render(request,'eventinvoice.html',{'profiledata':profiledata,'eventdata': eventdata,'events':events,})
            else:
                eventdata = EventBookGuest.objects.filter(vendor=user)
                return render(request,'upcomingevents.html',{'active_page': 'upcomingevent','eventdata':eventdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
from django.db.models import Max
def createeventinvoice(request,id):
    try:
        if request.user.is_authenticated:
            user=request.user
            if EventBookGuest.objects.filter(vendor=user,id=id,status=False):
                current_date = datetime.now().date()
                # Get the current date
                invccurrentdate = datetime.now().date()

                # Update the EventBookGuest object with status and invoice date
                event_obj = EventBookGuest.objects.filter(vendor=user, id=id).first()
                if event_obj:
                    event_obj.status = True
                    event_obj.invoice_date = invccurrentdate
                    event_obj.reamainingamount = 0
                    event_obj.save()

                # Fetch the maximum invoice number for today for the given user
                max_invoice_today = EventBookGuest.objects.filter(
                    vendor=user,
                    invoice_date=invccurrentdate
                ).aggregate(max_invoice_number=Max('invoice_number'))['max_invoice_number']

                # Determine the next invoice number
                if max_invoice_today is not None:
                    # Extract the numeric part of the latest invoice number and increment it
                    try:
                        current_number = int(max_invoice_today.split('-')[-1])
                        next_invoice_number = current_number + 1
                    except (ValueError, IndexError):
                        # Handle the case where the invoice number format is unexpected
                        next_invoice_number = 1
                else:
                    next_invoice_number = 1

                # Generate the invoice number
                invoice_number = f"EVENT-INV-{invccurrentdate}-{next_invoice_number}"
                
                # Check if the generated invoice number already exists
                while EventBookGuest.objects.filter(vendor=user,invoice_number=invoice_number).exists():
                    next_invoice_number += 1
                    invoice_number = f"EVENT-INV-{invccurrentdate}-{next_invoice_number}"

                EventBookGuest.objects.filter(vendor=user,id=id).update(invoice_number=invoice_number)
                previous_url = request.META.get('HTTP_REFERER', 'showeventinvoice')
                # Redirect to the previous page
                return redirect(previous_url)
            else:
                previous_url = request.META.get('HTTP_REFERER', 'showeventinvoice')
                # Redirect to the previous page
                return redirect(previous_url)
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def roomclean(request,user):
    try:
            user = user 
            today = datetime.now().date()
            lastday = datetime.now().date()
            lastday -= timedelta(days=1)

            roomdata = Rooms.objects.filter(vendor=user).order_by('room_name')
            cleanrooms = RoomCleaning.objects.filter(vendor=user, current_date=today, status=True)
            hotelnames = HotelProfile.objects.get(vendor=user)
            hotelname = hotelnames.name
            return render(request, 'roomclean.html', {
                'active_page': 'roomclean',
                'rooms': roomdata,
                'hotelname':hotelnames
            })
       
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    

         
def cleanroom(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            roomid = request.POST.get('roomno')
            today = datetime.now().date()
            # today += timedelta(days=1)
            if RoomCleaning.objects.filter(vendor=user,rooms_id=roomid,current_date=today,status=True).exists():
         
                return redirect('roomclean')
            else:
                RoomCleaning.objects.create(vendor=user,rooms_id=roomid,current_date=today,status=True)
               
                return redirect('roomclean')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         

    
     
       
     
def pos(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            # room = Rooms.objects.filter(vendor=user)
            # for i in room:
            #     Rooms.objects.filter(vendor=user,id=i.id).update(checkin=0)
            tax = Taxes.objects.filter(vendor=user)
            folio = Invoice.objects.filter(vendor=user,foliostatus=False)
            iteams = Items.objects.filter(vendor=user)
            laundry = LaundryServices.objects.filter(vendor=user)
            return render(request,'pospage.html',{'active_page': 'pos','tax':tax,'folio':folio,'iteams':iteams,'laundry':laundry})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def Product(request):
    try:
        if request.user.is_authenticated:
            user = request.user
            tax = Taxes.objects.filter(vendor=user)
            folio = Invoice.objects.filter(vendor=user,foliostatus=False)
            iteams = Items.objects.filter(vendor=user)
            laundry = LaundryServices.objects.filter(vendor=user)
            return render(request,'product.html',{'active_page': 'Product','tax':tax,'folio':folio,'iteams':iteams,'laundry':laundry})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def deleteproduct(request,id):
    try:
        if request.user.is_authenticated:
            user = request.user
            if Items.objects.filter(vendor=user,id=id).exists():
                Items.objects.filter(vendor=user,id=id).delete()
            else:
                pass
            return redirect('Product')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
     
def additems(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            description = request.POST.get('description')
            category_tax = request.POST.get('category_tax')
            hsncode = request.POST.get('hsncode')
            price = request.POST.get('price')
            if Items.objects.filter(vendor=user,description=description).exists():
                messages.error(request,'ITEMS already exists.')
                return redirect('Product')
            else:
                Items.objects.create(vendor=user,description=description,category_tax_id=category_tax,hsncode=hsncode,price=price)
                messages.success(request,'ITEMS added succesfully')
                return redirect('Product')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
         
def updateitems(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            itemid = request.POST.get('itemid')
            description = request.POST.get('description')
            category_tax = request.POST.get('category_tax')
            hsncode = request.POST.get('hsncode')
            price = request.POST.get('price')
            if Items.objects.filter(vendor=user,id=itemid).exists():
                Items.objects.filter(vendor=user,id=itemid).update(description=description,category_tax_id=category_tax,hsncode=hsncode,price=price)
                messages.success(request,'ITEMS Update succesfuly')
                return redirect('Product')
            else:
                messages.success(request,'Wrong Data Enter')
                return redirect('Product')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
from django.urls import reverse
# add items to pos 
def additemstofolio(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            foliocustomer = request.POST.get('invoiceid')
            qty = request.POST.get('qty')
            itemid = request.POST.get('iteamid')
            if Invoice.objects.filter(vendor=user,id=foliocustomer).exists():
                if qty==0:
                    qty = 1
                else:
                    pass
                iteams = Items.objects.get(vendor=user,id=itemid)
            
                taxes = iteams.category_tax
                price = iteams.price
                total = price * int(qty)
                if taxes is not None:
                    taxrate = iteams.category_tax.taxrate
                    taxamt = total * taxrate /100
                    totalamt = taxamt + total
                    hsccode = iteams.hsncode
                    individualtax = taxrate / 2
                    inditaxamt = taxamt/2
               
                    current_date = datetime.now().date()
                    current_date = str(current_date)
                    InvoiceItem.objects.create(vendor=user,invoice_id=foliocustomer,description=iteams.description +" "+ current_date,price=iteams.price,
                                        quantity_likedays=qty,cgst_rate=individualtax,sgst_rate=individualtax,
                                        hsncode=hsccode,total_amount=totalamt)
                    invc = Invoice.objects.get(vendor=user,id=foliocustomer)
                    totalamtinvc = invc.total_item_amount + total
                    subtotalinvc = total + invc.subtotal_amount
                    grandtotal = float(invc.grand_total_amount) + totalamt 
                    sgsttotal = float(invc.sgst_amount) + inditaxamt
                    gsttotal = float(invc.gst_amount) + inditaxamt
                    dueamount = float(invc.Due_amount) + totalamt
                    Invoice.objects.filter(vendor=user,id=foliocustomer).update(total_item_amount=totalamtinvc,subtotal_amount=subtotalinvc,
                                                                                grand_total_amount =grandtotal,sgst_amount=sgsttotal,gst_amount=gsttotal,
                                                                                Due_amount=dueamount)
                    messages.success(request,'Invoice Item added succesfully')
                    # return redirect('pos')
                    userid = invc.customer.id
                    url = reverse('invoicepage', args=[userid])
                    return redirect(url)
                else:
                    current_date = datetime.now().date()
                    current_date = str(current_date)
                    InvoiceItem.objects.create(vendor=user,invoice_id=foliocustomer,description=iteams.description+" "+ current_date,price=iteams.price,
                                        quantity_likedays=qty,total_amount=total,cgst_rate=0.0,sgst_rate=0.0)
                    invc = Invoice.objects.get(vendor=user,id=foliocustomer)
                    totalamtinvc = invc.total_item_amount + total
                    subtotalinvc = total + invc.subtotal_amount
                    grandtotal = invc.grand_total_amount + total
                    dueamount = float(invc.Due_amount) + total
                    Invoice.objects.filter(vendor=user,id=foliocustomer).update(total_item_amount=totalamtinvc,subtotal_amount=subtotalinvc,
                                                                                grand_total_amount =grandtotal,Due_amount=dueamount)
                    messages.success(request,'Invoice Item added succesfully')
                    # return redirect('pos')
                    userid = invc.customer.id
                    url = reverse('invoicepage', args=[userid])
                    return redirect(url)
            else:
                return redirect('pos')
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
            
def addlaundryitems(request):
    try:
        if request.user.is_authenticated and request.method=="POST":
            user=request.user
            foliocustomer = request.POST.get('foliocustomer')
            qty = request.POST.get('qty')
            itemid = request.POST.get('iteamid')
            if Invoice.objects.filter(vendor=user,id=foliocustomer).exists():
                if qty==0:
                    qty = 1
                else:
                    pass
                laundry = LaundryServices.objects.get(vendor=user,id=itemid)
                price = laundry.price
                current_date = datetime.now().date()
                current_date = str(current_date)
                name = laundry.gencategory + " " + laundry.name +" "+ laundry.sercategory+" "+current_date
                total = price * int(qty)
                
                
                InvoiceItem.objects.create(vendor=user,invoice_id=foliocustomer,description=name,price=price,
                                        quantity_likedays=qty,total_amount=total,cgst_rate=0.0,sgst_rate=0.0)
                invc = Invoice.objects.get(vendor=user,id=foliocustomer)
                totalamtinvc = invc.total_item_amount + total
                subtotalinvc = total + invc.subtotal_amount
                grandtotal = invc.grand_total_amount + total
                dueamount = invc.Due_amount + total
                Invoice.objects.filter(vendor=user,id=foliocustomer).update(total_item_amount=totalamtinvc,subtotal_amount=subtotalinvc,
                                                                            grand_total_amount =grandtotal,Due_amount=dueamount)
                messages.success(request,'Invoice Item added succesfully')
                # return redirect('pos')
                userid = invc.customer.id
                url = reverse('invoicepage', args=[userid])
                return redirect(url)
            else:
                return redirect('pos')
            
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
    

def userdatacheckbychandanbillsteam(request):
    try:
        if request.user.is_superuser:
            current_date = datetime.now().date()
            userdata = Subscription.objects.order_by('user', 'end_date')
            
            return render(request,'usersdatabybills.html',{'userdata':userdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    
    
def searchuserdata(request):
    try:
        if request.user.is_superuser and request.method=="POST":
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            userdata = Subscription.objects.filter(end_date__range=[startdate,enddate]).all()
            return render(request,'usersdatabybills.html',{'userdata':userdata})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  


from django.db.models import Sum
def finddatevisesales(request):
    try:
        if request.user.is_authenticated  and request.method=="POST":
            user=request.user
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')

            if Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate]).exists():

                total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate],
                    foliostatus=True
                ).aggregate(total_amount=Sum('grand_total_amount'))

                try:
                    # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                    sattle_total_amount = float(total_grand_total_amount['total_amount'])
                
                except (TypeError, ValueError):
                    sattle_total_amount = 0.00

                folio_total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate],
                    foliostatus=False
                ).aggregate(total_amount=Sum('grand_total_amount'))

                try:
                    # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                    folio_total_amount = folio_total_grand_total_amount['total_amount']
                
                except (TypeError, ValueError):
                    folio_total_amount = 0.00
                            
                # Aggregate the sum of `gst_amount`
                gst_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_gst_amount=Sum('gst_amount'))

                total_gst_amount = float(gst_amount_sum['total_gst_amount'])
                if total_gst_amount == None:
                    pass
                else:
                    total_gst_amount = total_gst_amount * 2
                

                grand_total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_amount=Sum('grand_total_amount'))

                # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                grand_total_amount = float(grand_total_grand_total_amount['total_amount'])
               

                # Aggregate the sum of `cash_amount`
                cash_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_cash_amount=Sum('Due_amount'))

                # # Access the correct key 'total_cash_amount'
                total_cash_amount =float( cash_amount_sum['total_cash_amount'])
               

                online_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_online_amount=Sum('accepted_amount'))

                # Access the correct key 'total_online_amount'
                total_online_amount = float(online_amount_sum['total_online_amount'])
                
                
            # Query to get the data with totals for each channel
                # Query to get the data with totals for each channel
                channel_data = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).values('customer__channel').annotate(
                    total_grand_total=Sum('grand_total_amount'),
                    total_gst_amount=Sum('gst_amount'),
                    total_sgst_amount=Sum('sgst_amount'),
                    total_invoices=Count('id'),
                    total_tax_amount=Sum(F('gst_amount') + F('sgst_amount')),  # Sum of GST and SGST as tax amount
                    net_profit=Sum(F('grand_total_amount') - (F('gst_amount') + F('sgst_amount')))  # Net Profit
                )

                # Calculate the total sums across all channels (Grand total sum, Tax sum, Net Profit)
                total_grand_total_sum = channel_data.aggregate(Sum('total_grand_total'))['total_grand_total__sum'] or 0
                total_tax_amount_sum = channel_data.aggregate(Sum('total_tax_amount'))['total_tax_amount__sum'] or 0
                net_profit_sum = total_grand_total_sum - total_tax_amount_sum  # Calculate net profit for the entire period

                # Calculate total invoices count
                total_invoices_count = sum(data['total_invoices'] for data in channel_data)

                return render(request,'datewisesale.html',{'active_page':'index','sattle_total_amount':sattle_total_amount,
                                                    'channel_data': channel_data,
                                                    'total_grand_total_sum': total_grand_total_sum,
                                                    'total_tax_amount_sum': total_tax_amount_sum,
                                                    'net_profit_sum': net_profit_sum,
                                                    'total_invoices_count': total_invoices_count,'total_cash_amount':total_cash_amount,'total_online_amount':total_online_amount,'grand_total_amount':grand_total_amount,'startdate':startdate,'enddate':enddate,'folio_total_amount':folio_total_amount,'total_gst_amount':total_gst_amount})
            else:
                return render(request,'datewisesale.html',{'active_page':'index','startdate':startdate,'enddate':enddate,
                                        'erroe':"NO DATA FIND ON THIS DATES"})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  



def todaysales(request):
    try:
        if request.user.is_authenticated  :
            user=request.user

            today = datetime.now().date()
            yestarday = today - timedelta(days=1)

            startdate = yestarday
            enddate = today
            
            if Invoice.objects.filter(vendor=user,invoice_date__range=[startdate,enddate]).exists():

                total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate],
                    foliostatus=True
                ).aggregate(total_amount=Sum('grand_total_amount'))

                try:
                    # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                    sattle_total_amount = float(total_grand_total_amount['total_amount'])
                    
                except (TypeError, ValueError):
                    sattle_total_amount = 0.00

                folio_total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate],
                    foliostatus=False
                ).aggregate(total_amount=Sum('grand_total_amount'))

                try:
                    # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                    folio_total_amount = folio_total_grand_total_amount['total_amount']
                    
                except (TypeError, ValueError):
                    folio_total_amount = 0.00
                            
                # Aggregate the sum of `gst_amount`
                gst_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_gst_amount=Sum('gst_amount'))

                total_gst_amount = float(gst_amount_sum['total_gst_amount'])
                if total_gst_amount == None:
                    pass
                else:
                    total_gst_amount = total_gst_amount * 2
               

                grand_total_grand_total_amount = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_amount=Sum('grand_total_amount'))

                # `total_grand_total_amount` is a dictionary with the sum under the key 'total_amount'
                grand_total_amount = float(grand_total_grand_total_amount['total_amount'])
          

                # Aggregate the sum of `cash_amount`
                cash_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_cash_amount=Sum('Due_amount'))

                # # Access the correct key 'total_cash_amount'
                total_cash_amount =float( cash_amount_sum['total_cash_amount'])
               

                online_amount_sum = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).aggregate(total_online_amount=Sum('accepted_amount'))

                # Access the correct key 'total_online_amount'
                total_online_amount = float(online_amount_sum['total_online_amount'])
                
                
            # Query to get the data with totals for each channel
                # Query to get the data with totals for each channel
                channel_data = Invoice.objects.filter(
                    vendor=user,
                    invoice_date__range=[startdate, enddate]
                ).values('customer__channel').annotate(
                    total_grand_total=Sum('grand_total_amount'),
                    total_gst_amount=Sum('gst_amount'),
                    total_sgst_amount=Sum('sgst_amount'),
                    total_invoices=Count('id'),
                    total_tax_amount=Sum(F('gst_amount') + F('sgst_amount')),  # Sum of GST and SGST as tax amount
                    net_profit=Sum(F('grand_total_amount') - (F('gst_amount') + F('sgst_amount')))  # Net Profit
                )

                # Calculate the total sums across all channels (Grand total sum, Tax sum, Net Profit)
                total_grand_total_sum = channel_data.aggregate(Sum('total_grand_total'))['total_grand_total__sum'] or 0
                total_tax_amount_sum = channel_data.aggregate(Sum('total_tax_amount'))['total_tax_amount__sum'] or 0
                net_profit_sum = total_grand_total_sum - total_tax_amount_sum  # Calculate net profit for the entire period

                # Calculate total invoices count
                total_invoices_count = sum(data['total_invoices'] for data in channel_data)
                today
                
                bookingdata=SaveAdvanceBookGuestData.objects.filter(vendor=user,
                                            bookingdate__lte=today,
                                            checkoutdate__gt=today,
                                            checkinstatus=False ).all()
                
              

                return render(request,'datewisesale.html',{'active_page':'todaysales','sattle_total_amount':sattle_total_amount,
                                                    'channel_data': channel_data,
                                                    'total_grand_total_sum': total_grand_total_sum,
                                                    'total_tax_amount_sum': total_tax_amount_sum,
                                                    'net_profit_sum': net_profit_sum,
                                                    'bookingdata':bookingdata,
                                                    'total_invoices_count': total_invoices_count,'total_cash_amount':total_cash_amount,'total_online_amount':total_online_amount,'grand_total_amount':grand_total_amount,'startdate':startdate,'enddate':enddate,'folio_total_amount':folio_total_amount,'total_gst_amount':total_gst_amount})
            else:
                today = datetime.now().date()
                bookingdata=SaveAdvanceBookGuestData.objects.filter(vendor=user,
                                            bookingdate=today).all()
                return render(request,'datewisesale.html',{'bookingdata':bookingdata,'active_page':'todaysales','startdate':startdate,'enddate':enddate,
                                        'erroe':"NO DATA FIND ON THIS DATES"})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)  










from django.shortcuts import render
from datetime import datetime, timedelta

def mobileview(request, user):
    try:
        # Check if the hotel profile exists
        if not HotelProfile.objects.filter(vendor__username=user).exists():
            return render(request, '404.html', {'error_message': "Profile Not Created!"}, status=300)
        checkdata = bestatus.objects.get(vendor__username=user)
        if checkdata.is_active is True:

            profile = HotelProfile.objects.get(vendor__username=user)
            rooms = RoomsCategory.objects.filter(vendor__username=user).prefetch_related('images')
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)

            daysdiff = 1
            adults = 2
            child = 0

            # Fetch inventory for today
            inventory_today = RoomsInventory.objects.filter(vendor__username=user, date=today)

            profiledata = HotelProfile.objects.filter(vendor__username=user)
            imagedata = HoelImage.objects.filter(vendor__username=user)
            rateplanmaxuser = RatePlan.objects.filter(vendor__username=user, max_persons__gte=1)
            offers = OfferBE.objects.filter(vendor__username=user).last()

            # Initialize cheapest room tracking
            cheapest_room = None
            cheapest_rate_plan = None
            lowest_price = float('inf')

            users = User.objects.get(username=user)

            # Store availability data with room objects
            for room in rooms:
                room_inventory = inventory_today.filter(room_category=room)
                if room_inventory.exists():
                    inventory = room_inventory.first()
                    room.available_rooms = inventory.total_availibility

                    # Calculate prices with offers
                    if offers:
                        OFFERAMOUNT = inventory.price * offers.discount_percentage // 100
                        room.uprice = inventory.price - OFFERAMOUNT
                        room.delprice = inventory.price
                        room.offeramount = OFFERAMOUNT
                    else:
                        room.uprice = inventory.price
                        room.delprice = inventory.price + 1000
                        room.offeramount = 0

                    room.tax = room.category_tax.taxrate
                else:
                    room.available_rooms = Rooms.objects.filter(vendor__username=user, room_type=room).count()
                    # room.uprice = room.catprice
                    # room.delprice = room.catprice+1000
                    # room.offeramount = 0
                    # Calculate prices with offers
                    if offers:
                        OFFERAMOUNT = room.catprice * offers.discount_percentage // 100
                        room.uprice = room.catprice - OFFERAMOUNT
                        room.delprice = room.catprice
                        room.offeramount = OFFERAMOUNT
                    else:
                        room.uprice = room.catprice
                        room.delprice = room.catprice + 1000
                        room.offeramount = 0
                    room.tax = room.category_tax.taxrate

                # Check all rate plans for the cheapest option
                for plan in rateplanmaxuser.filter(room_category=room):
                    total_price = room.uprice + plan.base_price

                    # Update the cheapest room and rate plan if found
                    if total_price < lowest_price and room.available_rooms > 0:
                        cheapest_room = room
                        cheapest_rate_plan = plan
                        lowest_price = total_price

            hoteldatas = HotelProfile.objects.get(vendor__username=user)
            terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
            aminities = beaminities.objects.filter(vendor__username=user)
            prfmcdata = becallemail.objects.filter(vendor__username=user)
            cpolicy = cancellationpolicy.objects.filter(vendor__username=user).last()
            return render(request, 'website.html', {
                'aminities':aminities,
                'prfmcdata':prfmcdata,
                'profile': profile,
                'imagedata': imagedata,
                'profiledata': profiledata,
                'today': today,
                'tomorrow': tomorrow,
                'rooms': rooms,
                'rateplanmaxuser': rateplanmaxuser,
                'offer': offers,
                'daysdiff': daysdiff,
                'adults': adults,
                'child': child,
                'cheapest_room': cheapest_room,
                'cheapest_rate_plan': cheapest_rate_plan,
                'lowest_price': lowest_price,
                'user':users.id,
                'terms_lines':terms_lines,
                'cpolicy':cpolicy
            })
        
        else:
            return render(request, 'website.html',{'emptydata':'Online bookings are currently unavailable. Please try booking offline instead.'} )
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

from datetime import datetime, timedelta
from django.shortcuts import render
from .models import HotelProfile, RoomsCategory, RoomsInventory, RatePlan, OfferBE, HoelImage, User

from django.http import HttpResponseRedirect


def searchwebsitedata(request):
    try:
        if request.method=="POST":
            # Get user data from request
            userid = request.POST.get('userid')
            users = User.objects.get(id=userid)
            user = users.username
            
            # Check if the hotel profile exists
            if not HotelProfile.objects.filter(vendor__username=user).exists():
                return render(request, '404.html', {'error_message': "Profile Not Created!"}, status=300)

            profile = HotelProfile.objects.get(vendor__username=user)
            rooms = RoomsCategory.objects.filter(vendor__username=user).prefetch_related('images')

            # Get check-in and check-out dates from the request
            checkin_date = request.POST.get('checkin_date')  # Example: '2024-12-04'
            checkout_date = request.POST.get('checkout_date')  # Example: '2024-12-06'

            # Parse the dates
            checkin_date = datetime.strptime(checkin_date, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout_date, '%Y-%m-%d').date()

            # Check if any of the dates are in the past
            today = datetime.now().date()
            if checkin_date < today or checkout_date < today or (checkin_date == today and  checkout_date==today) or (checkin_date == checkin_date and  checkout_date==checkin_date) or (checkin_date == checkout_date and  checkout_date==checkout_date):
                # If the check-in or checkout date is in the past, call the URL with the username
                # Example: make a URL call to a page with the username parameter
                # url = f"http://127.0.0.1:8000/mobileview/{user}/"
                url = f"https://live.billzify.com/mobileview/{user}/"
                return HttpResponseRedirect(url)

            # Initialize variables
            daysdiff = (checkout_date - checkin_date).days
            adults = 2
            child = 0

            # Fetch all inventory for the date range
            inventory_data = RoomsInventory.objects.filter(vendor__username=user, date__range=[checkin_date, checkout_date])

            profiledata = HotelProfile.objects.filter(vendor__username=user)
            imagedata = HoelImage.objects.filter(vendor__username=user)
            rateplanmaxuser = RatePlan.objects.filter(vendor__username=user, max_persons__gte=1)
            offers = OfferBE.objects.filter(vendor__username=user).last()

            # Initialize cheapest room tracking
            cheapest_room = None
            cheapest_rate_plan = None
            lowest_price = float('inf')

            users = User.objects.get(username=user)

            # Fetch the inventory for the specific date range
            inventory_today = RoomsInventory.objects.filter(vendor__username=user, date__range=[checkin_date, checkout_date])

            # Store availability data with room objects
            for room in rooms:
                room_inventory = inventory_today.filter(room_category=room)
                if room_inventory.exists():
                    inventory = room_inventory.first()

                    # Loop through all days in the check-in and check-out date range to find minimum availability
                    available_rooms_per_day = []  # List to store availability for each day

                    current_date = checkin_date
                    while current_date < checkout_date:
                        # Filter inventory for the current room and date
                        room_inventory = inventory_data.filter(room_category=room, date=current_date).first()

                        if room_inventory:
                            # If inventory exists, use the availability for that date
                            available_rooms_per_day.append(room_inventory.total_availibility)
                        else:
                            # If no inventory exists for the date, assume all rooms are available (fallback to total rooms)
                            available_rooms_per_day.append(Rooms.objects.filter(vendor__username=user, room_type=room).count())

                        current_date += timedelta(days=1)

                    # If available_rooms_per_day is not empty, find the minimum availability, otherwise set a default value
                    if available_rooms_per_day:
                        min_available_rooms = min(available_rooms_per_day)
                        room.available_rooms = min_available_rooms
                        
                    else:
                        room.available_rooms = 0  # Default to 0 if no availability data is found

                    # Calculate prices with offers
                    if offers:
                        OFFERAMOUNT = inventory.price * offers.discount_percentage // 100
                        room.uprice = inventory.price - OFFERAMOUNT
                        room.delprice = inventory.price
                        room.offeramount = OFFERAMOUNT
                    else:
                        room.uprice = inventory.price
                        room.delprice = inventory.price + 1000
                        room.offeramount = 0

                    room.tax = room.category_tax.taxrate
                else:
                    room.available_rooms = Rooms.objects.filter(vendor__username=user, room_type=room).count()

                    if offers:
                        OFFERAMOUNT = room.catprice * offers.discount_percentage // 100
                        room.uprice = room.catprice - OFFERAMOUNT
                        room.delprice = room.catprice
                        room.offeramount = OFFERAMOUNT
                    else:
                        room.uprice = room.catprice
                        room.delprice = room.catprice + 1000
                        room.offeramount = 0
                    room.tax = room.category_tax.taxrate

            hoteldatas = HotelProfile.objects.get(vendor__username=user)
            terms_lines = hoteldatas.termscondition.splitlines() if hoteldatas else []
            aminities = beaminities.objects.filter(vendor__username=user)
            prfmcdata = becallemail.objects.filter(vendor__username=user)
            cpolicy = cancellationpolicy.objects.filter(vendor__username=user).last()
            return render(request, 'website.html', {
                'aminities':aminities,
                'prfmcdata':prfmcdata,
                'profile': profile,
                'imagedata': imagedata,
                'profiledata': profiledata,
                'today': checkin_date,
                'tomorrow': checkout_date,
                'rooms': rooms,
                'rateplanmaxuser': rateplanmaxuser,
                'offer': offers,
                'daysdiff': daysdiff,
                'adults': adults,
                'child': child,
                'cheapest_room': cheapest_room,
                'lowest_price': lowest_price,
                'user': users.id,
                'terms_lines':terms_lines,
                'cpolicy':cpolicy
            })
        else:
            return redirect('mobileview')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)



from django.contrib.auth.forms import UserCreationForm
def handleuser(request):
    try:
        if request.user.is_superuser:
            form = UserCreationForm()
            users= User.objects.all()
            subplan = SubscriptionPlan.objects.all()
            return render(request,'usercreatsbillpos.html',{'form': form,'users':users,'subplan':subplan})
        else:
            return redirect('loginpage')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    


def createsubplan(request):
    try:
        if request.user.is_superuser and request.method=="POST":
            user = request.POST.get('user')
            plans = request.POST.get('plans')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
            if User.objects.filter(id=user).exists():
                userid = User.objects.get(id=user)
                if SubscriptionPlan.objects.filter(id=plans).exists():
                    subid = SubscriptionPlan.objects.get(id=plans)
                    Subscription.objects.create(
                        user=userid,
                        plan=subid,
                        start_date=startdate,
                        end_date=enddate
                    )
                    if onlinechannls.objects.filter(vendor=userid,channalname="self").exists():
                        pass
                    else:
                        onlinechannls.objects.create(vendor=userid,channalname="self")

                    messages.success(request,'Plan created!')

                else:
                    messages.error(request,'Plan not found')
            else:
                    messages.error(request,'user not found')

            return redirect('handleuser')


        else:
            return redirect('handleuser')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    


def addmsgtouser(request):
    try:
        if request.user.is_superuser and request.method=="POST":
            user = request.POST.get('user')
            msglimit = int(request.POST.get('msglimit'))
            Messgesinfo
            if User.objects.filter(id=user).exists():
                userid = User.objects.get(id=user)
                if Messgesinfo.objects.filter(vendor=userid).exists():
                    msgdata = Messgesinfo.objects.get(vendor=userid)
                    defaludatas = msgdata.defaultlimit
                    changeslmt = msglimit+defaludatas
                    Messgesinfo.objects.filter(vendor=userid).update(defaultlimit=changeslmt)

                else:
                    Messgesinfo.objects.create(vendor=userid,
                                     defaultlimit=msglimit, changedlimit=0  )
                    
                messages.success(request,'messages added!')
                return redirect('handleuser')

            else:
                    messages.error(request,'msg Plan not found')
                    return redirect('handleuser')

        else:
                messages.error(request,'user not found')
                return redirect('handleuser')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    
    


def bulkupdate(request):
    try:    
        if request.user.is_authenticated:
            user=request.user
            roomcat = RoomsCategory.objects.filter(vendor=user)
            today = datetime.now().date()
            return render(request,'bulkpage.html',{'roomcat':roomcat,'active_page':'bulkupdate','today':today})

        else:
            return redirect('loginpage')
        
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)

from django.http import HttpResponse
from .newcode import *
# Create your views here.
from .dynamicrates import *
import threading






def bulkinventoryform(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            # Get the selected category IDs
            user = request.user
            selected_ids = request.POST.getlist('selected_categories')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
           

            # Query the selected categories from the database
            selected_categories = RoomsCategory.objects.filter(vendor=user, id__in=selected_ids)
        
          

            # Prepare category_data with availability values
            category_data = {}
            for category_id in selected_categories:
                # Check if availability input exists for this category
                availability_key = f'catavaibility_{category_id.id}'
                availability_value = request.POST.get(availability_key, None)

                if availability_value:  # Ensure value is not None or empty
                    category_data[category_id.id] = int(availability_value)  # Store as integer

            # अब category_data में IDs और उनकी availability वैल्यू हैं
      

            # Parse the start and end dates
            checkindate = datetime.strptime(startdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(enddate, '%Y-%m-%d').date()

            # Generate the list of all dates between check-in and check-out (inclusive)
            all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

            for roomtype in selected_categories:  # Iterate through all selected categories
                # Query the RoomsInventory model to check if records exist for all those dates
                existing_inventory = RoomsInventory.objects.filter(
                    vendor=user, room_category_id=roomtype.id, date__in=all_dates
                )

                # Get the list of dates that already exist in the inventory
                existing_dates = set(existing_inventory.values_list('date', flat=True))
                

                # Identify the missing dates by comparing all_dates with existing_dates
                missing_dates = [date for date in all_dates if date not in existing_dates]

                # Get the total room count for the current category
                roomcount = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()

                # Get availability value for the current category from category_data
                availability_value = category_data.get(roomtype.id, roomcount)  # Default to roomcount if not provided

                # Deduct availability and update bookings for existing inventory
                for inventory in existing_inventory:
                    trms = inventory.booked_rooms
                    if trms==0:
                        trms=1
                    else:
                        pass
                    occupncies = (trms*100//availability_value)
                    inventory.total_availibility = availability_value  # Update with the provided value
                    inventory.occupancy=occupncies
                    inventory.save()

                # Fetch category data
                catdatas = RoomsCategory.objects.get(vendor=user, id=roomtype.id)
                totalrooms = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()
                occupancy = (1 * 100 // totalrooms) if totalrooms else 0

                # Create missing inventory entries
                if missing_dates:
                    for missing_date in missing_dates:
                        RoomsInventory.objects.create(
                            vendor=user,
                            date=missing_date,
                            room_category_id=roomtype.id,
                            total_availibility=availability_value,  # Use availability from category_data
                            booked_rooms=0,  # Set according to your logic
                            price=catdatas.catprice,
                            occupancy=occupancy
                        )
                    print(f"Missing dates have been created for category {roomtype}: {missing_dates}")
                else:
                    print(f"All dates already exist in the inventory for category {roomtype}.")

            # Trigger background API tasks for the user
            start_date = str(checkindate)
            end_date = str(checkoutdate)
            if VendorCM.objects.filter(vendor=user):
                start_date = str(checkindate)
                end_date = str(checkoutdate)
                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                thread.start()
                # for dynamic pricing
                if VendorCM.objects.filter(vendor=user, dynamic_price_active=True):
                    thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                    thread.start()
                else:
                    pass
            else:
                pass

            messages.success(request, "Inventory Updated Successfully!")
            
            # Do whatever processing is needed, then return a response
            return redirect('bulkupdate')
        
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)    




def bulkformprice(request):
    try:
        if request.user.is_authenticated and request.method == "POST":
            # Get the selected category IDs
            user = request.user
            selected_ids = request.POST.getlist('selected_categories')
            startdate = request.POST.get('startdate')
            enddate = request.POST.get('enddate')
          

            # Query the selected categories from the database
            selected_categories = RoomsCategory.objects.filter(vendor=user, id__in=selected_ids)
           

            # Prepare category_data with availability values
            category_data = {}
            for category_id in selected_categories:
                # Check if availability input exists for this category
                availability_key = f'catavaibility_{category_id.id}'
                availability_value = request.POST.get(availability_key, None)

                if availability_value:  # Ensure value is not None or empty
                    category_data[category_id.id] = int(availability_value)  # Store as integer

            # अब category_data में IDs और उनकी availability वैल्यू हैं
           

            # Parse the start and end dates
            checkindate = datetime.strptime(startdate, '%Y-%m-%d').date()
            checkoutdate = datetime.strptime(enddate, '%Y-%m-%d').date()

            # Generate the list of all dates between check-in and check-out (inclusive)
            all_dates = [checkindate + timedelta(days=x) for x in range((checkoutdate - checkindate).days + 1)]

            for roomtype in selected_categories:  # Iterate through all selected categories
                # Query the RoomsInventory model to check if records exist for all those dates
                existing_inventory = RoomsInventory.objects.filter(
                    vendor=user, room_category_id=roomtype.id, date__in=all_dates
                )

                # Get the list of dates that already exist in the inventory
                existing_dates = set(existing_inventory.values_list('date', flat=True))
               

                # Identify the missing dates by comparing all_dates with existing_dates
                missing_dates = [date for date in all_dates if date not in existing_dates]

                # Get the total room count for the current category
                roomcount = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()

                # Get availability value for the current category from category_data
                availability_value = category_data.get(roomtype.id, roomcount)  # Default to roomcount if not provided

                # Deduct availability and update bookings for existing inventory
                for inventory in existing_inventory:
                    inventory.price = float(availability_value)  # Update with the provided value
                    
                    inventory.save()

                # Fetch category data
                catdatas = RoomsCategory.objects.get(vendor=user, id=roomtype.id)
                totalrooms = Rooms.objects.filter(vendor=user, room_type_id=roomtype.id).exclude(checkin=6).count()
                occupancy = (1 * 100 // totalrooms) if totalrooms else 0

                # Create missing inventory entries
                if missing_dates:
                    for missing_date in missing_dates:
                        RoomsInventory.objects.create(
                            vendor=user,
                            date=missing_date,
                            room_category_id=roomtype.id,
                            total_availibility=totalrooms,  # Use availability from category_data
                            booked_rooms=0,  # Set according to your logic
                            price=float(availability_value),
                            occupancy=occupancy
                            
                        )
                    print(f"Missing dates have been created for category {roomtype}: {missing_dates}")
                else:
                    print(f"All dates already exist in the inventory for category {roomtype}.")

            # Trigger background API tasks for the user
            start_date = str(checkindate)
            end_date = str(checkoutdate)
            if VendorCM.objects.filter(vendor=user):
                start_date = str(checkindate)
                end_date = str(checkoutdate)
                thread = threading.Thread(target=update_inventory_task, args=(user.id, start_date, end_date))
                thread.start()
                # for dynamic pricing
                # if VendorCM.objects.filter(vendor=user, dynamic_price_active=True):
                thread = threading.Thread(target=rate_hit_channalmanager, args=(user.id, start_date, end_date))
                thread.start()
                # else:
                #     pass
            else:
                pass

            messages.success(request, "Price Updated Successfully!")
            
            # Do whatever processing is needed, then return a response
            return redirect('bulkupdate')
   
        else:
            return render(request, 'login.html')
    except Exception as e:
        return render(request, '404.html', {'error_message': str(e)}, status=500)