from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date
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
    
class Rooms_count(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomsCategory,on_delete=models.CASCADE)
    total_room_numbers = models.IntegerField(default=0)


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
    ar = models.CharField(max_length=50,default=True,blank=True)
    dp = models.CharField(max_length=50,default=True,blank=True)
    male = models.CharField(max_length=50,default=True,blank=True)
    female = models.CharField(max_length=50,default=True,blank=True)
    transg = models.CharField(max_length=50,default=True,blank=True)
    extend = models.BooleanField(default=False)
    extend_decription = models.CharField(max_length=500,default=True,blank=True)
    created_checkoutdate = models.DateTimeField(editable=False)
    fandbinvoiceid = models.CharField(max_length=50,default=True,blank=True)
    def __str__(self) -> str:
        return self.guestname
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Means this is a new record (first time save)
            self.created_checkoutdate = self.checkoutdate  
        super().save(*args, **kwargs)


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
    company_gstin = models.CharField(max_length=15,blank=True,null=True)
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
    smscount = models.IntegerField(default=0)
    

# invoice work here
class Invoice(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    customer = models.ForeignKey(Gueststay,on_delete=models.CASCADE)
    customer_gst_number = models.CharField(max_length=15,blank=True)  # GST Identification Number
    customer_company = models.CharField(max_length=15,blank=True,null=True)
    invoice_number = models.CharField(max_length=20,blank=True)
    invoice_date = models.DateField(blank=True)
    total_item_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True) 
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
    is_fandb = models.BooleanField(default=False)
    is_ota = models.BooleanField(default=False)


class InvoiceItem(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,related_name='items')
    description = models.CharField(max_length=100)
    mdescription = models.CharField(max_length=100)
    hsncode = models.IntegerField(default=0,blank=True)
    quantity_likedays = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    cgst_rate_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],blank=True, null=True)
    sgst_rate_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],blank=True, null=True)
    totalwithouttax = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    is_room = models.BooleanField(default=False)
    is_checkout = models.BooleanField(default=False)
    date = models.DateField(auto_now=True)
    is_extend = models.BooleanField(default=False)
    checkout_date = models.DateField(auto_now=False,blank=True, null=True)
    is_room_extra = models.BooleanField(default=False)
    is_mealp = models.BooleanField(default=False)
    mealpprice = models.FloatField(default=0.0,null=True,blank=True)
    mealplanname = models.CharField(max_length=25,null=True,blank=True)

   
class taxSlab(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='taxslab', null=True, blank=True)
    tax_rate_name = models.CharField(max_length=15, blank=True, null=True)
    cgst = models.FloatField()
    sgst = models.FloatField()  # e.g., 'Credit Card', 'Cash'
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

class Items(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    category_tax = models.ForeignKey(Taxes,on_delete=models.CASCADE,null=True,blank=True)
    hsncode = models.CharField(null=True,max_length=10)
    price = models.IntegerField()
    available_qty = models.BigIntegerField(default=0)
    total_qty = models.BigIntegerField(default=0)

class itempurchasehistorlocal(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    items =  models.ForeignKey(Items,on_delete=models.CASCADE)
    date = models.DateField(auto_now=True)
    add_qty = models.IntegerField()
    total_amount = models.FloatField()
    


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
    totalhours = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    overtime = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    

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
    gst_number = models.CharField(max_length=20,blank=True,null=True)

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
    date =models.DateField(auto_now=True)







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
    inventory_active = models.BooleanField(default=True)





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
    checkin = models.DateField() #ye mene asa boooking date li hai or booking date checkin date hai 
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
    is_noshow =  models.BooleanField(default=False)
    is_hold = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bookingguest} for {self.vendor.username} id {self.id}"
    

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
    checkOutstatus = models.BooleanField(default=False)
    partly_checkin = models.BooleanField(default=False)
    bookingstatus = models.BooleanField(default=False)

    totalguest = models.CharField(max_length=10,null=True,blank=True,default="")
    rateplan_code = models.CharField(max_length=50,null=True,blank=True)
    rateplan_code_main = models.CharField(max_length=50,null=True,blank=True)
    guest_name = models.CharField(max_length=100,null=True,blank=True)
    adults = models.PositiveIntegerField(null=True,blank=True)
    children = models.PositiveIntegerField(null=True,blank=True)
    sell_rate = models.FloatField(null=True,blank=True)
    
    def __str__(self) -> str:
        return self.bookingguest

class tds_comm_model(models.Model):
    roombook = models.ForeignKey(SaveAdvanceBookGuestData,on_delete=models.CASCADE,blank=True,null=True)
    commission = models.FloatField(default=0.0,null=True,blank=True)
    tds = models.FloatField(default=0.0,null=True,blank=True)
    tcs = models.FloatField(default=0.0,null=True,blank=True)
    
class bookpricesdates(models.Model):
    roombook = models.ForeignKey(RoomBookAdvance,on_delete=models.CASCADE,blank=True,null=True)
    date = models.CharField(max_length=250,blank=True,null=True)
    price = models.FloatField(default=0.0,blank=True,null=True)



class extraBookingAmount(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    bookdata = models.ForeignKey(RoomBookAdvance, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField()
    taxable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    csgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2)


class Cm_RoomBookAdvance(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room_category = models.ForeignKey(RoomsCategory,on_delete=models.CASCADE)
    saveguestdata = models.ForeignKey(SaveAdvanceBookGuestData,on_delete=models.CASCADE)

    bookingguest = models.CharField(max_length=100)
    bookingguestphone = models.BigIntegerField(
        validators=[MaxValueValidator(9999999999)]
    )
    totalguest = models.CharField(max_length=10,null=True,blank=True,default="")
    rateplan_code = models.CharField(max_length=50,null=True,blank=True)
    rateplan_code_main = models.CharField(max_length=50,null=True,blank=True,default='')
    guest_name = models.CharField(max_length=100,null=True,blank=True)
    adults = models.PositiveIntegerField(null=True,blank=True)
    children = models.PositiveIntegerField(null=True,blank=True)
    sell_rate = models.FloatField(null=True,blank=True)
    
    def __str__(self) -> str:
        return self.bookingguest
    
class Cm_bookpricesdates(models.Model):
    roombook = models.ForeignKey(Cm_RoomBookAdvance,on_delete=models.CASCADE,blank=True,null=True)
    date = models.CharField(max_length=250,blank=True,null=True)
    price = models.FloatField(default=0.0,blank=True,null=True)

class Booking(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    guest_name = models.CharField(max_length=100)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    check_in_time = models.TimeField()  # New field for check-in time
    check_out_time = models.TimeField() 
    segment = models.CharField(max_length=40,blank=True,null=True)
    totalamount = models.FloatField(blank=True, null=True, default=0.0)
    totalroom = models.CharField(max_length=10,blank=True,null=True)
    gueststay = models.ForeignKey(Gueststay,on_delete=models.CASCADE, null=True, blank=True)
    advancebook = models.ForeignKey(SaveAdvanceBookGuestData, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=25, null=True, blank=True)
    fnbinvoice = models.ForeignKey(Invoice,on_delete=models.CASCADE, null=True, blank=True)
    hourly = models.ForeignKey(HourlyRoomsdata,on_delete=models.SET_NULL, null=True, blank=True)

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
    descriptions = models.CharField(max_length=350, blank=True, null=True) 
    maindate = models.DateField(default=date.today, blank=True, null=True)





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
    state = models.CharField(max_length=50,blank=True)
    unpaid =  models.BooleanField(default=False)
    reviced_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True,null=True)




class SupplierInvoiceItem(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.PositiveIntegerField(default=0)
    hsncode = models.CharField(max_length=8,blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    subtotal_amt = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amt = models.DecimalField(max_digits=10, decimal_places=2,blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)
    is_intvntory = models.BooleanField(default=False)
    salerate = models.PositiveIntegerField()
    date=models.DateField(auto_now=True)
    sellinghsn = models.CharField(max_length=8,blank=True)



class taxSlabpurchase(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Supplier, on_delete=models.CASCADE,  null=True, blank=True)
    tax_hsnsac_name = models.CharField(max_length=15, blank=True, null=True)
    cgst = models.FloatField()
    sgst = models.FloatField()  # e.g., 'Credit Card', 'Cash'
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    taxableamount = models.DecimalField(max_digits=10, decimal_places=2,blank=True)

class PurchasePayment(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    invoice = models.ForeignKey(Supplier, on_delete=models.CASCADE, null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now=False,null=True)
    payment_mode = models.CharField(max_length=50)  # e.g., 'Credit Card', 'Cash'
    transaction_id = models.CharField(max_length=100, blank=True, null=True)  # optional
    descriptions = models.CharField(max_length=50, blank=True, null=True) 
    maindate = models.DateField(default=date.today, blank=True, null=True)



class Companies(models.Model):
    vendor = models.ForeignKey(User,on_delete=models.CASCADE)
    companyname = models.CharField(max_length=50)
    contactpersonname = models.CharField(max_length=50,blank=True,null=True)
    contact = models.BigIntegerField(validators=[MaxValueValidator(9999999999)],blank=True,null=True)
    email = models.EmailField(max_length=100,blank=True)
    address = models.CharField(max_length=300,blank=True,null=True)
    customergst = models.CharField(max_length=15,blank=True)
    values = models.FloatField(default=0,blank=True,null=True)
    


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
    cancellention_policy = models.TextField( null=True, blank=True)

class bestatus(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField()

class Roomcleancheck(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    current_date = models.DateField(null=True)
    
class invPermit(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    pos_billing_active = models.BooleanField()
    
class invoiceDesign(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    invcdesign = models.IntegerField(default=1)
    guestinvcdesign = models.IntegerField(default=1)
    
class Subuser(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subusers')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subuser_profile')
    permissions = models.JSONField(default=dict)  # JSONField to store permissions
    is_cleaner = models.BooleanField(default=False)
   

    def __str__(self):
        return f"{self.user.username} (Subuser of {self.vendor.username})"
    
class savedateblock(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Rooms, on_delete=models.CASCADE)
    date = models.DateField(auto_now=False)





class addCash(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    subuser = models.ForeignKey(Subuser, on_delete=models.CASCADE, null=True, blank=True)
    add_amount = models.BigIntegerField(default=0)
    date_time = models.DateTimeField(auto_now=False)

class expenseCash(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    subuser = models.ForeignKey(Subuser, on_delete=models.CASCADE, null=True, blank=True)
    less_amount = models.BigIntegerField(default=0)
    date_time = models.DateTimeField(auto_now=False)
    comments = models.CharField(max_length=50,null=True, blank=True)

class avlCash(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    avl_amount = models.BigIntegerField(default=0)

class CashOut(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    subuser = models.ForeignKey(Subuser, on_delete=models.CASCADE, null=True, blank=True)
    cash_out_amount = models.BigIntegerField(default=0)
    date_time = models.DateTimeField(auto_now=False)
    comments = models.CharField(max_length=50,null=True, blank=True)


class hand_overCash(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    userto = models.CharField(max_length=20,null=True, blank=True)
    userfrom = models.CharField(max_length=20,null=True, blank=True)
    amount = models.BigIntegerField(default=0)
    date_time = models.DateTimeField(auto_now=False)


class googlereview(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE)
    googleurl = models.URLField(max_length=200, blank=True, null=True)


from django.utils.timezone import now

class CustomGuestLog(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    customer = models.ForeignKey(Gueststay,on_delete=models.CASCADE, null=True, blank=True)
    by = models.CharField(max_length=100)  
    action = models.CharField(max_length=30)  # Action type (Create, Update, Delete)
    description = models.CharField(max_length=250,blank=True, null=True)  # Extra details
    timestamp = models.DateTimeField(default=now)  # Action ka time
    advancebook = models.ForeignKey(SaveAdvanceBookGuestData,on_delete=models.CASCADE, null=True, blank=True)


class bulklogs(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    by = models.CharField(max_length=100)  
    action = models.CharField(max_length=30)  # Action type (Create, Update, Delete)
    description = models.TextField(blank=True, null=True)  # Extra details
    timestamp = models.DateTimeField(default=now)  

class property_description(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True, null=True) 

class room_services(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(RoomsCategory,  on_delete=models.CASCADE)
    service = models.CharField(max_length=150,blank=True, null=True)

class whatsaap_link(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    link = models.URLField(blank=True, null=True) 


class Vendor_Service(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_software = models.BooleanField(default=False)
    only_cm = models.BooleanField(default=False)

class Guest_BackId(models.Model):
    vendor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(Gueststay, on_delete=models.CASCADE, null=True, blank=True)
    guestidbackimg = models.ImageField(upload_to='Guestid_Back', null=True, blank=True)
    def __str__(self):
        return f"{self.vendor.username} (Guest {self.guest.guestname})"
    