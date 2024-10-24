from django.urls import path
from . import views,newcode
from . import manageQR
from . import employeemanage,loyltys,hourlypage,donwloadexcel
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from app2.views import app2index,terms,privcy,refund
from .newcode import *

urlpatterns = [
    path('', app2index, name='empty-url-view'),
    path('terms/', terms, name='terms'),
    path('privcy/', privcy, name='privcy'),
    path('refund/', refund, name='refund'),
    # path("",views.index),
    path('homepage/',views.homepage,name="homepage"),
    path('index/',views.index,name="index"),
    path('signuppage/',views.signuppage,name="signuppage"),
    path('loginpage/',views.loginpage,name="loginpage"),
    path('advanceroombookpage/',views.advanceroombookpage,name="advanceroombookpage"),
    path('subscriptionplanpage/',views.subscriptionplanpage,name="subscriptionplanpage"),
    path('createsubscription/<str:id>/',views.createsubscription,name="createsubscription"),
    path('dologin/',views.login_view,name="dologin"),
    path('logout/', views.logout_view, name='logout'),
    path('signup/',views.signup,name="signup"),
    path('addtax/',views.addtax,name="addtax"),
    path('foliobillingpage/',views.foliobillingpage,name="foliobillingpage"),
    path('addcategory/',views.addcategory,name="addcategory"),
    path('updatecategory/',views.updatecategory,name="updatecategory"),
    path('addroom/',views.addroom,name="addroom"),
    path('updaterooms/',views.updaterooms,name="updaterooms"),
    path('guesthistory/',views.guesthistory,name="guesthistory"),
    path('guestdetails/<int:id>/',views.guestdetails,name="guestdetails"),
    path('openroomclickformpage/<str:id>/',views.openroomclickformpage,name="openroomclickformpage"),
    path('openroomclickformtodayarriwalspage/<str:id>/',views.openroomclickformtodayarriwalspage,name="openroomclickformtodayarriwalspage"),
    path('roomcheckin/<int:id>/',views.roomcheckin,name="roomcheckin"),
    path('checkoutroom/',views.checkoutroom,name="checkoutroom"),
    path('cancelroom/',views.cancelroom,name="cancelroom"),
    path('gotofoliobyhome/<int:id>/',views.gotofoliobyhome,name="gotofoliobyhome"),
    path('editcustomergstnumber/',views.editcustomergstnumber,name="editcustomergstnumber"),
    path('addguestdata/',views.addguestdata,name="addguestdata"),
    path('addguestdatafromadvanceroombook/',views.addguestdatafromadvanceroombook,name="addguestdatafromadvanceroombook"),
    path('guestregform/<int:id>/',views.guestregform,name="guestregform"),

    path('bookingdate/',views.bookingdate,name="bookingdate"),
    path('addadvancebooking/',views.addadvancebooking,name="addadvancebooking"),
    path('advanceroomhistory/',views.advanceroomhistory,name="advanceroomhistory"),
    path('advancebookingdetails/<int:id>/',views.advancebookingdetails,name="advancebookingdetails"),
    path('advancebookingdelete/<int:id>/',views.advancebookingdelete,name="advancebookingdelete"),
    path('todaybookingpage/',views.todaybookingpage,name="todaybookingpage"),
    path('rooms/',views.rooms,name="rooms"),
    path('deleteroom/<int:id>/',views.deleteroom,name="deleteroom"),
    path('openposforroom/',views.openposforroom,name="openposforroom"),
    path('chekinonebyoneguestdata/',views.chekinonebyoneguestdata,name="chekinonebyoneguestdata"),
    path('opencheckinforadvanebooking/<int:pk>/',views.opencheckinforadvanebooking,name="opencheckinforadvanebooking"),
    path('invoicepage/<int:id>/',views.invoicepage,name="invoicepage"),
    path('addpaymentfolio/',views.addpaymentfolio,name="addpaymentfolio"),
    path('addpaymentfoliocredit/',views.addpaymentfoliocredit,name="addpaymentfoliocredit"),
    path('generate_qr/<path:url>/', views.generate_qr, name='generate_qr'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('addprofile/', views.addprofile, name='addprofile'),
    path('updateprofile/', views.updateprofile, name='updateprofile'),
    path('billingplanpage/',employeemanage.billingplanpage,name="billingplanpage"),
    path('roomclean/',employeemanage.roomclean,name="roomclean"),
    path('cleanroom/',employeemanage.cleanroom,name="cleanroom"),
    path('mobileview/<str:user>/',employeemanage.mobileview,name="mobileview"),
    path('addcoupnoffers/',employeemanage.addcoupnoffers,name="addcoupnoffers"),
    path('addserviceshow/',employeemanage.addserviceshow,name="addserviceshow"),
    path('gallryimgwebsite/',employeemanage.gallryimgwebsite,name="gallryimgwebsite"),
    path('reviewscount/',employeemanage.reviewscount,name="reviewscount"),
    path('pos/',employeemanage.pos,name="pos"),
    path('additems/',employeemanage.additems,name="additems"),
    path('updateitems/',employeemanage.updateitems,name="updateitems"),
    path('additemstofolio/',employeemanage.additemstofolio,name="additemstofolio"),
    path('addlaundryitems/',employeemanage.addlaundryitems,name="addlaundryitems"),
    path('Product/',employeemanage.Product,name="Product"),
    path('deleteproduct/<int:id>/',employeemanage.deleteproduct,name="deleteproduct"),
    # delete product in the folio url
    path('deleteitemstofolio/',views.deleteitemstofolio,name="deleteitemstofolio"),
    # for users check data
    path('userdatacheckbychandanbillsteam/',employeemanage.userdatacheckbychandanbillsteam,name="userdatacheckbychandanbillsteam"),
    path('searchuserdata/',employeemanage.searchuserdata,name="searchuserdata"),
    path('finddatevisesales/',employeemanage.finddatevisesales,name="finddatevisesales"),
    # aminityinvoice codes
    path('aminityinvoice/',loyltys.aminityinvoice,name="aminityinvoice"),
    path('addaminitiesinvoice/',loyltys.addaminitiesinvoice,name="addaminitiesinvoice"),
    path('addmoreaminitiesproductininvoice/',loyltys.addmoreaminitiesproductininvoice,name="addmoreaminitiesproductininvoice"),
    path('aminitiesitemdelete/<int:id>/',loyltys.aminitiesitemdelete,name="aminitiesitemdelete"),
    path('saveaminitiesinvoice/',loyltys.saveaminitiesinvoice,name="saveaminitiesinvoice"),
    path('aminityhistory/',loyltys.aminityhistory,name="aminityhistory"),
    path('deleteaminitesinvc/<int:id>/',loyltys.deleteaminitesinvc,name="deleteaminitesinvc"),
    path('aminitiesinvoice/<int:id>/',loyltys.aminitiesinvoice,name="aminitiesinvoice"),
    path('searchaminitiesdata/',loyltys.searchaminitiesdata,name="searchaminitiesdata"),
    path('aminitysales/',loyltys.aminitysales,name="aminitysales"),
    path('searchaminitiesinvoicedata/',loyltys.searchaminitiesinvoicedata,name="searchaminitiesinvoicedata"),
    path('generate_aminitiesinvoice_excel/',donwloadexcel.generate_aminitiesinvoice_excel,name="generate_aminitiesinvoice_excel"),

    # ajax data
    path('getloyltydataajax',loyltys.getloyltydataajax,name="getloyltydataajax"),
    path('deleteloyltyajaxdata',loyltys.deleteloyltyajaxdata,name="deleteloyltyajaxdata"),
    path('getguestdatabyajaxinform',loyltys.getguestdatabyajaxinform,name="getguestdatabyajaxinform"),
    path('getrateplandata',loyltys.getrateplandata,name="getrateplandata"),


    # loylty.py data
    path('setting/',loyltys.setting,name="setting"),
    path('activeloylty/',loyltys.activeloylty,name="activeloylty"),
    path('updateloylty/',loyltys.updateloylty,name="updateloylty"),
    path('deletetaxitem/<int:id>/',loyltys.deletetaxitem,name="deletetaxitem"),
    path('deletecategory/<int:id>/',loyltys.deletecategory,name="deletecategory"),
    path('websetting/',loyltys.websetting,name="websetting"),
    path('deleteamenities/<int:id>/',loyltys.deleteamenities,name="deleteamenities"),
    path('deleteimages/<int:id>/',loyltys.deleteimages,name="deleteimages"),
    path('creditmanage/',loyltys.creditmanage,name="creditmanage"),
    path('addpaymentininvoice/<int:id>/',loyltys.addpaymentininvoice,name="addpaymentininvoice"),
    path('addcreditcustomer/',loyltys.addcreditcustomer,name="addcreditcustomer"),
    path('saveinvoicetocredit/<int:id>/',loyltys.saveinvoicetocredit,name="saveinvoicetocredit"),
    path('searchcredit/',loyltys.searchcredit,name="searchcredit"),
    path('Messages/',loyltys.Messages,name="Messages"),
    path('sendwelcomemsg/',loyltys.sendwelcomemsg,name="sendwelcomemsg"),
    path('sendloyaltymsg/',loyltys.sendloyaltymsg,name="sendloyaltymsg"),
    path('searchguestexportdta/',loyltys.searchguestexportdta,name="searchguestexportdta"),
    # exceldata page
    path('exceldatapage/',donwloadexcel.exceldatapage,name="exceldatapage"),
    path('generate_invoice_excel/',donwloadexcel.generate_invoice_excel,name="generate_invoice_excel"),
    path('generate_eventinvoice_excel/',donwloadexcel.generate_eventinvoice_excel,name="generate_eventinvoice_excel"),

    # hourly data
    path('hourlyhomepage/',hourlypage.hourlyhomepage,name="hourlyhomepage"),
    path('addroomtohourlyrooms/',hourlypage.addroomtohourlyrooms,name="addroomtohourlyrooms"),
    path('hourlyroomclickform/<int:id>/',hourlypage.hourlyroomclickform,name="hourlyroomclickform"),
    path('hourlycheckinroom/',hourlypage.hourlycheckinroom,name="hourlycheckinroom"),
    path('removeroomfromhourly/',hourlypage.removeroomfromhourly,name="removeroomfromhourly"),
    path('searchguestdata/',hourlypage.searchguestdata,name="searchguestdata"),
    path('searchguestdataadvance/',hourlypage.searchguestdataadvance,name="searchguestdataadvance"),
    path('searchdateevents/',hourlypage.searchdateevents,name="searchdateevents"),
    path('loylty/',hourlypage.loylty,name="loylty"),
    path('offers/',hourlypage.offers,name="offers"),
    path('eventsalse/',hourlypage.eventsalse,name="eventsalse"),
    path('billzifymall/',hourlypage.billzifymall,name="billzifymall"),

    # qr website work
    path('Website/',manageQR.Website,name="Website"),
    path('Showqr/<int:id>/',manageQR.Showqr,name="Showqr"),
    path('IGfKg/<str:id>/',manageQR.IGfKg,name="IGfKg"),
    path('yourwebpage/<int:rid>/',manageQR.yourwebpage,name="yourwebpage"),
    path('addwebsitedata/',manageQR.addwebsitedata,name="addwebsitedata"),
    path('updatewebsitedata/',manageQR.updatewebsitedata,name="updatewebsitedata"),
    path('laundrysrvs/<str:id>/',manageQR.laundrysrvs,name="laundrysrvs"),
    path('addlaundrypage/',manageQR.addlaundrypage,name="addlaundrypage"),
    path('addlaundryitem/',manageQR.addlaundryitem,name="addlaundryitem"),
    path('deletelaundryitem/<int:id>/',manageQR.deletelaundryitem,name="deletelaundryitem"),
    path('addfoodurlbyqr/',manageQR.addfoodurlbyqr,name="addfoodurlbyqr"),
    path('deleteroomoffersweb/<int:id>/',manageQR.deleteroomoffersweb,name="deleteroomoffersweb"),


    #employeee management in employeemanagement 
    path('employee/',employeemanage.employee,name="employee"),
    path('addemployee/',employeemanage.addemployee,name="addemployee"),
    path('deleteemployee/<int:id>/',employeemanage.deleteemployee,name="deleteemployee"),
    path('updateemployee/<int:id>/',employeemanage.updateemployee,name="updateemployee"),
    path('dailyattendance/',employeemanage.dailyattendance,name="dailyattendance"),
    path('employeecheckin/<int:dsd>/',employeemanage.employeecheckin,name="employeecheckin"),
    path('employeecheckout/<int:dsd>/',employeemanage.employeecheckout,name="employeecheckout"),
    path('employeehalfday/<int:dsd>/',employeemanage.employeehalfday,name="employeehalfday"),
    path('attendancepage/',employeemanage.attendancepage,name="attendancepage"),
    path('employeereport/<int:eid>/',employeemanage.employeereport,name="employeereport"),
    path('addsalary/',employeemanage.addsalary,name="addsalary"),
    path('payslippage/',employeemanage.payslippage,name="payslippage"),
    path('showpayslip/<int:eid>/',employeemanage.showpayslip,name="showpayslip"),
    path('eventpackage/',employeemanage.eventpackage,name="eventpackage"),
    path('createevent/',employeemanage.createevent,name="createevent"),
    path('searchdateevent/',employeemanage.searchdateevent,name="searchdateevent"),
    path('createeventbooking/',employeemanage.createeventbooking,name="createeventbooking"),
    path('upcomingevent/',employeemanage.upcomingevent,name="upcomingevent"),
    path('deleteupcomingevent/<int:id>/',employeemanage.deleteupcomingevent,name="deleteupcomingevent"),
    path('showeventinvoice/<int:id>/',employeemanage.showeventinvoice,name="showeventinvoice"),
    path('createeventinvoice/<int:id>/',employeemanage.createeventinvoice,name="createeventinvoice"),

    # forgot password
    path('password_reset/', views.password_reset_request, name='password_reset'),
    
    #new updated code  
    path('gridview/', newcode.gridview, name='gridview'),
    path('gridviewviasearch/', newcode.gridviewviasearch, name='gridviewviasearch'),
    path('inventory_push/', newcode.inventory_push, name='inventory_push'),
    path('api/update-inventory/', inventory_push, name='update_inventory'),
    path('webhook/booking/', booking_webhook, name='booking_webhook'),
    path('fetch_and_save_bookings/', fetch_and_save_bookings, name='fetch_and_save_bookings'),


    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



