from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from decimal import Decimal
# Create your models here.

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15)  # Adjust max_length as per your requirements

    # Specify unique related names for groups and user_permissions fields
    groups = models.ManyToManyField(Group, related_name='custom_users')
    user_permissions = models.ManyToManyField(Permission, related_name='custom_users')

    



class  Taxes(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    taxname = models.CharField(max_length=100)
    taxcode = models.IntegerField(default=0)
    taxrate = models.IntegerField(default=0)
    def __str__(self) -> str:
        return self.taxname

class RoomsCategory(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    category_name = models.CharField(max_length=150)
    Hsn_sac = models.IntegerField(default=0)
    catprice = models.IntegerField(default=1)
    category_tax = models.ForeignKey(Taxes,on_delete=models.CASCADE)
    def __str__(self) -> str:
        return self.category_name


class RoomImage(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    category = models.ForeignKey(RoomsCategory, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='room_images')

    def __str__(self):
        return f"{self.category.category_name} Image"

class Rooms(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room_name = models.IntegerField(default=0)
    room_type = models.ForeignKey(RoomsCategory,on_delete=models.CASCADE)
    checkin = models.IntegerField(default=0)
    price = models.IntegerField(default=1)
    tax = models.ForeignKey(Taxes,on_delete=models.CASCADE)
    tax_amount = models.BigIntegerField(default=0)
    is_clean = models.BooleanField(default=True)
    max_person = models.PositiveIntegerField(default=1)
    
    # hsn required in gst bill according to services
    



class Gueststay(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    guestname = models.CharField(max_length=150,default=None)
    guestphome = models.BigIntegerField(validators=[MaxValueValidator(9999999999)])
    guestemail = models.EmailField(default=None, blank=True)
    guestcity = models.CharField(max_length=100,default=None, blank=True)
    guestcountry = models.CharField(max_length=50,default=None)
    guestidimg = models.ImageField(upload_to='Guestid', null=True, blank=True)
    checkindate = models.DateTimeField(auto_now=False)
    checkoutdate = models.DateTimeField(auto_now=False)
    noofguest = models.BigIntegerField(default=0, blank=True)
    adults = models.BigIntegerField(default=0, blank=True)
    children = models.BigIntegerField(default=0, blank=True)
    purposeofvisit = models.CharField(max_length=150,default=None, blank=True)
    roomno = models.IntegerField(default=0)
    rate_plan = models.CharField(max_length=50,default=True,blank=True)
    channel = models.CharField(max_length=50,default=True,blank=True)
    subtotal = models.BigIntegerField(default=0)
    discount = models.BigIntegerField(default=0)
    total = models.BigIntegerField(default=0)
    tax = models.CharField(max_length=10)
    checkoutstatus = models.BooleanField(default=False)
    checkoutdone = models.BooleanField(default=False)
    noofrooms = models.IntegerField(default=1)
    guestidtypes = models.CharField(max_length=25,default=None, blank=True)
    guestsdetails = models.CharField(max_length=40,default=None, blank=True)
    gueststates = models.CharField(max_length=50,default=None, blank=True)
    saveguestid = models.IntegerField(blank=True,null=True)
    def __str__(self) -> str:
        return self.guestname


class MoreGuestData(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    mainguest = models.ForeignKey(Gueststay,on_delete=models.CASCADE)
    another_guest_name = models.CharField(max_length=100,default=None,blank=True)
    another_guest_phone = models.BigIntegerField(validators=[MaxValueValidator(9999999999)],default=None,blank=True)
    another_guest_address = models.CharField(max_length=150,default=None,blank=True)


#subscription model
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self) -> str:
        return self.name
    

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now=False)
    end_date = models.DateField(auto_now=False)
    def __str__(self) -> str:
        return self.user.username

class onlinechannls(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    channalname = models.CharField(max_length=100)
    def __str__(self) -> str:
        return self.channalname
    

class loylty_data(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    loylty_rate_prsantage = models.BigIntegerField(default=0)
    Is_active = models.BooleanField(default=False)

class loylty_Guests_Data(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100,default=None)
    guest_contact = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    loylty_point = models.IntegerField(default=0)
    smscount = models.CharField(max_length=10,default=0,null=True,blank=True)
    

# invoice work here
class Invoice(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    customer = models.ForeignKey(Gueststay,on_delete=models.CASCADE)
    customer_gst_number = models.CharField(max_length=15,blank=True)  # GST Identification Number
    invoice_number = models.CharField(max_length=20,blank=True)
    invoice_date = models.DateField(blank=True)
    total_item_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    modeofpayment = models.CharField(max_length=20,blank=True)
    accepted_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    Due_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    room_no = models.CharField(max_length=40,blank=True)
    foliostatus = models.BooleanField(default=False)
    invoice_status = models.BooleanField(default=False)
    CATEGORY_CHOICES = [
        ('GST', 'GST'),
        ('IGST', 'IGST'),
        # Add more categories as needed
    ]
    taxtype = models.CharField(max_length=5, choices=CATEGORY_CHOICES)


class InvoiceItem(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    mdescription = models.CharField(max_length=100)
    hsncode = models.IntegerField(default=0,blank=True)
    quantity_likedays = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    paidstatus = models.BooleanField(default=False)

   
class Items(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    category_tax = models.ForeignKey(Taxes,on_delete=models.CASCADE,null=True,blank=True)
    hsncode = models.CharField(null=True,max_length=10)
    price = models.IntegerField()
    

class LaundryServices(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    CATEGORY_CHOICES = [
        ('laundry', 'laundry'),
        ('drycleaning', 'drycleaning'),
        # Add more categories as needed
    ]
    gender_category = [
        ('mens', 'mens'),
        ('womens', 'womens'),
        # Add more categories as needed
    ]
    name = models.CharField(max_length=255)
    sercategory = models.CharField(max_length=255, choices=CATEGORY_CHOICES)
    gencategory = models.CharField(max_length=255, choices=gender_category)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.name}'

# employeee management model

class Employee(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    date_of_joining = models.DateField()
    employee_contact = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    salarybyday = models.IntegerField(default=0)
    working_hours = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class DailyManagement(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField(null=True,blank=True)
    check_out_time = models.TimeField(null=True,blank=True)
    halfday = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.employee} - {self.date}"

class SalaryManagement(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    salary_date = models.DateField()
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    salary_days = models.DecimalField(max_digits=10, decimal_places=2)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

  


class Events(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    eventname = models.CharField(max_length=100)
    eventprice = models.DecimalField(max_digits=10, decimal_places=2)
    eventax = models.ForeignKey(Taxes,on_delete=models.CASCADE)
    description = models.TextField()
    termscondition = models.TextField()
    Hsn_sac = models.IntegerField(default=0)
    def __str__(self):
        return self.eventname
    
class EventBookGuest(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    event = models.ForeignKey(Events,on_delete=models.CASCADE)
    customername = models.CharField(max_length=50)
    guestemail = models.EmailField(default=None)
    customer_contact = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    customeraddress = models.CharField(max_length=150)
    customergst = models.CharField(max_length=18)
    total =   models.DecimalField(max_digits=10, decimal_places=2)
    discount =   models.DecimalField(max_digits=10, decimal_places=2)
    subtotal =   models.DecimalField(max_digits=10, decimal_places=2)
    taxamount =   models.DecimalField(max_digits=10, decimal_places=2)
    advanceamount =   models.DecimalField(max_digits=10, decimal_places=2)
    reamainingamount =   models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    status = models.BooleanField(default=False)
    invoice_date = models.DateField(auto_now=False,null=True)
    invoice_number = models.CharField(max_length=50,blank=True)
    Grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    CATEGORY_CHOICES = [
        ('GST', 'GST'),
        ('IGST', 'IGST'),
        # Add more categories as needed
    ]
    taxtype = models.CharField(max_length=5, choices=CATEGORY_CHOICES)



class HotelProfile(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    email = models.EmailField(default=None)
    contact = models.CharField(max_length=15)
    address = models.TextField()
    zipcode = models.CharField(max_length=50)
    gstin = models.CharField(max_length=25)
    profile_image = models.ImageField(upload_to='profileimage', null=True, blank=True)
    counrty = models.CharField(max_length=35)
    checkintimes = models.CharField(max_length=35,blank=True)
    checkouttimes = models.CharField(max_length=35,blank=True)
    termscondition = models.TextField(blank=True,null=True)

class HoelImage(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    image = models.ImageField(upload_to='hotel_images')

    def __str__(self):
        return f"{self.vendor.username} Image"

class Messgesinfo(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    defaultlimit = models.IntegerField(default=0)
    changedlimit = models.IntegerField(default=0)
    def __str__(self) -> str:
        return self.vendor.username

class RoomCleaning(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    rooms = models.ForeignKey(Rooms,on_delete=models.CASCADE)
    current_date = models.DateField(null=True)
    status = models.BooleanField(default=False)


class HourlyRoomsdata(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    rooms = models.ForeignKey(Rooms,on_delete=models.CASCADE)
    checkinstatus = models.BooleanField(default=False)
    checkoutstatus = models.BooleanField(default=False)
    checkIntime = models.TimeField(auto_now=False)
    checkottime = models.TimeField(auto_now=False)
    hourlydata = [
        ('3hours', '3hours'),
        ('6hours', '6hours'),
        ('9hours', '9hours'),
        ('12hours', '12hours'),
    ]
    time = models.CharField(max_length=50, choices=hourlydata,blank=True)



class CustomerCredit(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100,blank=True)
    phone =  models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)],blank=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()

    invoice =  models.ForeignKey(Invoice,on_delete=models.CASCADE,blank=True,null=True)
    def __str__(self):
        return f"{self.customer_name} - {self.amount} - {self.due_date}"


class Freedemo(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100,blank=True)
    phone =  models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)],blank=True
    )
    businessname = models.CharField(max_length=300)
    def __str__(self) -> str:
        return self.name
    


class AminitiesInvoice(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    customername = models.CharField(max_length=50)
    customercontact = models.BigIntegerField(validators=[MaxValueValidator(9999999999)])
    customeremail = models.EmailField(max_length=100,blank=True)
    customeraddress = models.CharField(max_length=300)
    customergst = models.CharField(max_length=15,blank=True)
    customercompany = models.CharField(max_length=50,blank=True)
    invoicenumber = models.CharField(max_length=12)
    invoicedate = models.DateField(auto_now=False,null=True)
    CATEGORY_CHOICES = [
        ('GST', 'GST'),
        ('IGST', 'IGST'),
        # Add more categories as needed
    ]
    taxtype = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    total_item_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    modeofpayment = models.CharField(max_length=20,blank=True)
    cash_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    online_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sattle =  models.BooleanField(default=False)


class AminitiesInvoiceItem(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(AminitiesInvoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.PositiveIntegerField(blank=True,null=True)
    hsncode = models.CharField(max_length=8,blank=True,null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amt = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amt = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)







class RatePlan(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room_category = models.ForeignKey(RoomsCategory, related_name='rate_plans', on_delete=models.CASCADE)
    rate_plan_name = models.CharField(max_length=50)
    rate_plan_description = models.CharField(max_length=150)
    rate_plan_code = models.CharField(max_length=50,blank=True,null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)  # Base price for one person
    additional_person_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Price per additional person
    max_persons = models.PositiveIntegerField(default=1)  # Maximum persons allowed
    childmaxallowed = models.PositiveIntegerField(default=1)# Maximum child allowed

   
    def __str__(self):
        return f"{self.rate_plan_name} for {self.room_category.category_name}"


class RatePlanforbooking(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    rate_plan_name = models.CharField(max_length=50)
    rate_plan_code = models.CharField(max_length=50,blank=True,null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.rate_plan_name} for {self.vendor.username}"


class RoomsInventory(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room_category = models.ForeignKey(RoomsCategory, on_delete=models.CASCADE)
    total_availibility = models.IntegerField(blank=True,null=True,default=0)
    date = models.DateField(auto_now=False,blank=True)
    booked_rooms = models.IntegerField(blank=True,null=True,default=0)
    price = models.DecimalField(max_digits=10, decimal_places=1)
    occupancy = models.IntegerField()

    def __str__(self):
        return f"{self.vendor.username} for {self.room_category.category_name,self.date}"




class VendorCM(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    cm_name = [
        ('AIOSELL', 'AIOSELL'),
        ('STAYFLEXI', 'STAYFLEXI'),
        ('EZEE', 'EZEE'),
    ]
    cm_company = models.CharField(max_length=50, choices=cm_name,blank=True)
    hotelcode = models.CharField(max_length=40)
    dynamic_price_active = models.BooleanField(default=False)
    dynamic_price_plan = models.IntegerField(default=None,blank=True,null=True)
    channal_manager_link = models.URLField(max_length=200, blank=True, null=True)
    admin_dynamic_active = models.BooleanField(default=False)





# aiosell booking formate


class SaveAdvanceBookGuestData(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    bookingdate = models.DateField(auto_now=False)
    noofrooms = models.IntegerField(default=0)
    bookingguest = models.CharField(max_length=100)
    bookingguestphone = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    email = models.EmailField(default=None, blank=True)
    address_city = models.CharField(max_length=100,blank=True,null=True)#zipcode also
    state = models.CharField(max_length=100,blank=True,null=True)
    country = models.CharField(max_length=100,blank=True,null=True)
    totalguest = models.CharField(max_length=10,null=True,blank=True)
    # zip_code = models.CharField(max_length=10)
    ACTION_CHOICES = [
        ('book', 'Book'),
        ('cancel', 'Cancel'),
        ("modify","modify"),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES,blank=True,null=True)
    booking_id = models.CharField(max_length=100,null=True, blank=True)
    cm_booking_id = models.CharField(max_length=100,null=True, blank=True)
    checkin = models.DateField()
    segment = models.CharField(max_length=50)
    special_requests = models.TextField(blank=True, null=True)
    pah = models.BooleanField(default=False)
    # Amount information as a JSONField to store the nested amount data
    amount_after_tax = models.FloatField()
    amount_before_tax = models.FloatField()
    tax = models.FloatField()
    currency = models.CharField(max_length=10)
    advance_amount = models.BigIntegerField(default=0)
    reamaining_amount = models.BigIntegerField(default=0)
    total_amount = models.BigIntegerField(default=0)
    discount = models.BigIntegerField(default=0)
    channal = models.ForeignKey(onlinechannls,on_delete=models.CASCADE)
    checkoutdate = models.DateField(auto_now=False)
    staydays = models.IntegerField(default=0)
    checkinstatus = models.BooleanField(default=False)
    ACTION_CHOICES_payment = [
        ('prepaid', 'prepaid'),
        ('postpaid', 'postpaid'),
        ("partially","partially"),
    ]
    Payment_types = models.CharField(max_length=20, choices=ACTION_CHOICES_payment,blank=True,null=True)
    is_selfbook = models.BooleanField(default=False)
    

class RoomBookAdvance(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    bookingdate = models.DateField(auto_now=False)
    roomno = models.ForeignKey(Rooms,on_delete=models.CASCADE)
    saveguestdata = models.ForeignKey(SaveAdvanceBookGuestData,on_delete=models.CASCADE)

    bookingguest = models.CharField(max_length=100)
    bookingguestphone = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    channal = models.ForeignKey(onlinechannls,on_delete=models.CASCADE)
    checkoutdate = models.DateField(auto_now=False)

    checkinstatus = models.BooleanField(default=False)
    partly_checkin = models.BooleanField(default=False)
    bookingstatus = models.BooleanField(default=False)

    totalguest = models.CharField(max_length=10,null=True,blank=True,default="")
    rateplan_code = models.CharField(max_length=50)
    guest_name = models.CharField(max_length=100)
    adults = models.PositiveIntegerField()
    children = models.PositiveIntegerField()
    sell_rate = models.FloatField()
    
    def __str__(self) -> str:
        return self.bookingguest



class Booking(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    check_in_time = models.TimeField()  # New field for check-in time
    check_out_time = models.TimeField() 
    segment = models.CharField(max_length=40,blank=True,null=True)
    totalamount = models.CharField(max_length=40,blank=True,null=True)
    totalroom = models.CharField(max_length=10,blank=True,null=True)
    gueststay = models.ForeignKey(Gueststay,on_delete=models.CASCADE, null=True, blank=True)
    advancebook = models.ForeignKey(SaveAdvanceBookGuestData, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=25, null=True, blank=True)
    def __str__(self):
        return f"{self.guest_name} ({self.check_in_date} - {self.check_out_date})"
    

class InvoicesPayment(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    advancebook = models.ForeignKey(SaveAdvanceBookGuestData, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now=False,null=True)
    payment_mode = models.CharField(max_length=50)  # e.g., 'Credit Card', 'Cash'
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # optional
    descriptions = models.CharField(max_length=50, blank=True, null=True) 





class TravelAgency(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    commission_rate = models.IntegerField()  # Commission percentage


    def __str__(self):
        return self.name
    
class Travelagencyhandling(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    agency = models.ForeignKey(TravelAgency,on_delete=models.CASCADE)
    bookingdata = models.ForeignKey(SaveAdvanceBookGuestData,on_delete=models.CASCADE)
    date = models.DateField()
    commsion = models.IntegerField()





class Supplier(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    customername = models.CharField(max_length=50)
    customercontact = models.BigIntegerField(validators=[MaxValueValidator(9999999999)])
    customeremail = models.EmailField(max_length=100,blank=True)
    customeraddress = models.CharField(max_length=300)
    customergst = models.CharField(max_length=15,blank=True)
    companyname = models.CharField(max_length=50,blank=True)
    invoicenumber = models.CharField(max_length=12)
    invoicedate = models.DateField(auto_now=False,null=True)
    CATEGORY_CHOICES = [
        ('GST', 'GST'),
        ('IGST', 'IGST'),
        # Add more categories as needed
    ]
    taxtype = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    total_item_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    modeofpayment = models.CharField(max_length=20,blank=True)
    cash_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    online_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sattle =  models.BooleanField(default=False)




class SupplierInvoiceItem(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)],blank=True)
    hsncode = models.CharField(max_length=8,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amt = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amt = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)







class Companies(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    companyname = models.CharField(max_length=50)
    contactpersonname = models.CharField(max_length=50)
    contact = models.BigIntegerField(validators=[MaxValueValidator(9999999999)])
    email = models.EmailField(max_length=100,blank=True)
    address = models.CharField(max_length=300)
    customergst = models.CharField(max_length=15,blank=True)
    values = models.CharField(max_length=10,default=0)


class companyinvoice(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    company = models.ForeignKey(Companies,on_delete=models.CASCADE)
    Invoicedata = models.ForeignKey(Invoice,on_delete=models.CASCADE)
    Value = models.CharField(max_length=10)
    date = models.DateField(auto_now=False)
    is_paid = models.BooleanField(default=False)


# Offer model: represents the discount offers, can be quantity or price-based
class OfferBE(models.Model):
    description = models.CharField(max_length=150)
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers')
    min_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=None)  # Required for price-based offer
    discount_percentage = models.IntegerField(default=0)


class beaminities(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='aminities')
    description = models.CharField(max_length=50)
    

class becallemail(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    phome = models.BigIntegerField(validators=[MaxValueValidator(9999999999)])
    guestemail = models.EmailField(default=None, blank=True)
    linkmap = models.URLField(default=None, blank=True)
    

class cancellationpolicy(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    cancellention_policy = models.CharField(max_length=50, null=True, blank=True)

class bestatus(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField()