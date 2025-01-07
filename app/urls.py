from django.urls import path
from . import views,newcode
from . import manageQR
from . import employeemanage,loyltys,hourlypage,donwloadexcel
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from .newcode import *
from . import dynamicrates
from . import aiosellbook ,travelagancy,stayinvoices,purches,companyies

urlpatterns = [
    path('',views.loginpage,name="loginpage"),
    path('homepage/',views.homepage,name="homepage"),
    path('index/',views.index,name="index"),
    path('changeindexyear/', views.changeindexyear, name='changeindexyear'),
    # path('signuppage/',views.signuppage,name="signuppage"),
    path('loginpage/',views.loginpage,name="loginpage"),
    path('advanceroombookpage/',views.advanceroombookpage,name="advanceroombookpage"),
    path('subscriptionplanpage/',views.subscriptionplanpage,name="subscriptionplanpage"),
    path('createsubscription/<str:id>/',views.createsubscription,name="createsubscription"),
    path('dologin/',views.login_view,name="dologin"),
    path('logout/', views.logout_view, name='logout'),
    path('signup/',views.signup,name="signup"),
    path('addtax/',views.addtax,name="addtax"),
    path('foliobillingpage/',views.foliobillingpage,name="foliobillingpage"),
    path('searchguestdatabyfolio/',hourlypage.searchguestdatabyfolio,name="searchguestdatabyfolio"),
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
    path('addpaymenttobooking/<int:booking_id>/',views.addpaymenttobooking,name="addpaymenttobooking"),

    path('addpymenttoboking/',views.addpymenttoboking,name="addpymenttoboking"),
    path('websettings/',views.websettings,name="websettings"),
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
    path('guestaddfromfolio/',views.guestaddfromfolio,name="guestaddfromfolio"),
    path('opencheckinforadvanebooking/<int:pk>/',views.opencheckinforadvanebooking,name="opencheckinforadvanebooking"),
    path('invoicepage/<int:id>/',views.invoicepage,name="invoicepage"),
    path('addpaymentfolio/',views.addpaymentfolio,name="addpaymentfolio"),
    path('addpaymentfoliocredit/',views.addpaymentfoliocredit,name="addpaymentfoliocredit"),
    path('generate_qr/<path:url>/', views.generate_qr, name='generate_qr'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('addprofile/', views.addprofile, name='addprofile'),
    path('updateprofile/', views.updateprofile, name='updateprofile'),
    path('billingplanpage/',employeemanage.billingplanpage,name="billingplanpage"),
    path('roomclean/<int:user>/',employeemanage.roomclean,name="roomclean"),
    path('cleanroom/',employeemanage.cleanroom,name="cleanroom"),
    path('mobileview/<str:user>/',employeemanage.mobileview,name="mobileview"),
    path('pos/',employeemanage.pos,name="pos"),
    path('additems/',employeemanage.additems,name="additems"),
    path('updateitems/',employeemanage.updateitems,name="updateitems"),
    path('setivcpermission/',employeemanage.setivcpermission,name="setivcpermission"),
    path('invtransection/<int:id>/',employeemanage.invtransection,name="invtransection"),
    path('cleanpermission/<int:id>/',employeemanage.cleanpermission,name="cleanpermission"),
    path('deletesubuser/<int:id>/',employeemanage.deletesubuser,name="deletesubuser"),

    path('fininvtransectiondata/',employeemanage.fininvtransectiondata,name="fininvtransectiondata"),
    path('additemstofolio/',employeemanage.additemstofolio,name="additemstofolio"),
    path('addlaundryitems/',employeemanage.addlaundryitems,name="addlaundryitems"),
    path('Product/',employeemanage.Product,name="Product"),
    path('deleteproduct/<int:id>/',employeemanage.deleteproduct,name="deleteproduct"),
    # delete product in the folio url
    path('deleteitemstofolio/',views.deleteitemstofolio,name="deleteitemstofolio"),
    # for users check data
    path('userdatacheckbychandanbillsteam/',employeemanage.userdatacheckbychandanbillsteam,name="userdatacheckbychandanbillsteam"),
    path('handleuser/',employeemanage.handleuser,name="handleuser"),
    
    path('searchuserdata/',employeemanage.searchuserdata,name="searchuserdata"),
    path('finddatevisesales/',employeemanage.finddatevisesales,name="finddatevisesales"),
    path('todaysales/',employeemanage.todaysales,name="todaysales"),
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
    path('generate_purchesinvoice_excel/',donwloadexcel.generate_purchesinvoice_excel,name="generate_purchesinvoice_excel"),
    path('search_user/', loyltys.search_user, name='search_user'),
    path('check_product/', loyltys.check_product, name='check_product'),



    # ajax data
    path('getloyltydataajax',loyltys.getloyltydataajax,name="getloyltydataajax"),
    path('deleteloyltyajaxdata',loyltys.deleteloyltyajaxdata,name="deleteloyltyajaxdata"),
    path('getguestdatabyajaxinform',loyltys.getguestdatabyajaxinform,name="getguestdatabyajaxinform"),
    path('getrateplandata',loyltys.getrateplandata,name="getrateplandata"),
    path('receipt/<int:booking_id>/', views.receipt_view, name='receipt_view'),
    path('advncereciptbiew/<int:booking_id>/', views.advncereciptbiew, name='advncereciptbiew'),
    path('advancebookingdeletebe/<int:id>/',views.advancebookingdeletebe,name="advancebookingdeletebe"),

    # loylty.py data
    path('setting/',loyltys.setting,name="setting"),
    path('activeloylty/',loyltys.activeloylty,name="activeloylty"),
    path('updateloylty/',loyltys.updateloylty,name="updateloylty"),
    path('deletetaxitem/<int:id>/',loyltys.deletetaxitem,name="deletetaxitem"),
    path('deletecategory/<int:id>/',loyltys.deletecategory,name="deletecategory"),
    path('creditmanage/',loyltys.creditmanage,name="creditmanage"),
    path('addpaymentininvoice/<int:id>/',loyltys.addpaymentininvoice,name="addpaymentininvoice"),
    path('addcreditcustomer/',loyltys.addcreditcustomer,name="addcreditcustomer"),
    path('saveinvoicetocredit/<int:id>/',loyltys.saveinvoicetocredit,name="saveinvoicetocredit"),
    path('searchcredit/',loyltys.searchcredit,name="searchcredit"),
    path('Messages/',loyltys.Messages,name="Messages"),
    path('sendwelcomemsg/',loyltys.sendwelcomemsg,name="sendwelcomemsg"),
    path('sendloyaltymsg/',loyltys.sendloyaltymsg,name="sendloyaltymsg"),
    path('searchguestexportdta/',loyltys.searchguestexportdta,name="searchguestexportdta"),
    path('sendbulksmsloylty/<int:id>/',loyltys.sendbulksmsloylty,name="sendbulksmsloylty"),
    path('deleteloylty/<int:id>/',loyltys.deleteloylty,name="deleteloylty"),
    # exceldata page
    path('exceldatapage/',donwloadexcel.exceldatapage,name="exceldatapage"),
    path('generate_invoice_excel/',donwloadexcel.generate_invoice_excel,name="generate_invoice_excel"),
    path('generate_eventinvoice_excel/',donwloadexcel.generate_eventinvoice_excel,name="generate_eventinvoice_excel"),

    # hourly data
    path('hourlyhomepage/',hourlypage.hourlyhomepage,name="hourlyhomepage"),
    path('addroomtohourlyrooms/',hourlypage.addroomtohourlyrooms,name="addroomtohourlyrooms"),
    path('removeroomfromhourly/',hourlypage.removeroomfromhourly,name="removeroomfromhourly"),
    path('searchguestdata/',hourlypage.searchguestdata,name="searchguestdata"),
    path('searchguestdataadvance/',hourlypage.searchguestdataadvance,name="searchguestdataadvance"),
    path('searchdateevents/',hourlypage.searchdateevents,name="searchdateevents"),
    path('loylty/',hourlypage.loylty,name="loylty"),
    path('eventsalse/',hourlypage.eventsalse,name="eventsalse"),

    # qr website work
    path('laundrysrvs/<str:id>/',manageQR.laundrysrvs,name="laundrysrvs"),
    path('addlaundrypage/',manageQR.addlaundrypage,name="addlaundrypage"),
    path('addlaundryitem/',manageQR.addlaundryitem,name="addlaundryitem"),
    path('deletelaundryitem/<int:id>/',manageQR.deletelaundryitem,name="deletelaundryitem"),
    


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
    path('rate_push/', dynamicrates.rate_push, name='rate_push'),

    # demo create link
    path("create_demo/", views.create_demo, name="create_demo"),

    # cleaning
    path('cleanroombtn/<int:id>/', loyltys.cleanroombtn, name='cleanroombtn'),
    path('cleanroombtnweek/<int:id>/', loyltys.cleanroombtnweek, name='cleanroombtnweek'),
    path('weekviews/', views.weekviews, name='weekviews'),
    
    # aiosell booking management
    path('aiosell/new_reservation/', aiosellbook.aiosell_new_reservation, name='aiosell_new_reservation'),
    path('update_reservation', aiosellbook.aiosell_new_reservation, name='aiosell_new_reservation'),
    
    
    # travel agancy handling
    path('travelagancy/', travelagancy.travelagancy, name='travelagancy'),
    path('createtravelagancy/', travelagancy.createtravelagancy, name='createtravelagancy'),
    path('deletetravelagency/<int:id>/', travelagancy.deletetravelagency, name='deletetravelagency'),
    path('updatetravelagancy/', travelagancy.updatetravelagancy, name='updatetravelagancy'),
    path('opentravelagencydata/<int:id>/', travelagancy.opentravelagencydata, name='opentravelagencydata'),

    # stayinvoice data
    
    path('stayinvoice/', stayinvoices.stayinvoice, name='stayinvoice'),
    path('searchmonthinvoice/', stayinvoices.searchmonthinvoice, name='searchmonthinvoice'),

    # path('room/<int:id>/', views.openroomclickformpage, name='openroomclickformpage'),
    
    path('cleanroombtnajax/', views.cleanroombtnajax, name='cleanroombtnajax'),

    # website booking data 
    path('bookrooms/<str:user_name>/from/<int:mids>/', travelagancy.bookrooms, name='bookrooms'),
    path('bookingdatetravel/', travelagancy.bookingdatetravel, name='bookingdatetravel'),
    path('addadvancebookingfromtrvel/', travelagancy.addadvancebookingfromtrvel, name='addadvancebookingfromtrvel'),
    path('searchmonthbookingagent/', travelagancy.searchmonthbookingagent, name='searchmonthbookingagent'),

    # purches invoice management
    
    path('purchesinvoice/', purches.purchesinvoice, name='purchesinvoice'),
    path('purchesinvoiceform/', purches.purchesinvoiceform, name='purchesinvoiceform'),
    path('addmorepurchesproductininvoice/', purches.addmorepurchesproductininvoice, name='addmorepurchesproductininvoice'),
    path('purchesitemdelete/<int:id>/', purches.purchesitemdelete, name='purchesitemdelete'),
    path('deletepurchesinvc/<int:id>/', purches.deletepurchesinvc, name='deletepurchesinvc'),
    path('savepurchesinvoice/', purches.savepurchesinvoice, name='savepurchesinvoice'),
    path('purcheshistory/', purches.purcheshistory, name='purcheshistory'),
    path('searchpurchesdata/', purches.searchpurchesdata, name='searchpurchesdata'),
    path('deletepurchesinvc/<int:id>/', purches.deletepurchesinvc, name='deletepurchesinvc'),
    path('purchesinvoices/<int:id>/', purches.purchesinvoices, name='purchesinvoices'),
    path('purchessales/', purches.purchessales, name='purchessales'),
    path('searpurchesinvoicedata/', purches.searpurchesinvoicedata, name='searpurchesinvoicedata'),
    path('get_supplier_details/', purches.get_supplier_details, name='get_supplier_details'),
    path('fetch-supplier-items/', purches.fetch_supplier_items, name='fetch_supplier_items'),

    # channel manager changeroompage 
    path('channalmanager/', purches.channalmanager, name='channalmanager'),

    # dynamic rates form and all 
    path('dynamicformpage/', dynamicrates.dynamicformpage, name='dynamicformpage'),
    path('dynamicformdata/', dynamicrates.dynamicformdata, name='dynamicformdata'),

    # change room work
    path('changeroompage/<int:id>/', manageQR.changeroompage, name='changeroompage'),
    path('change-rooms/', manageQR.change_rooms, name='change_rooms_url'),
    path('changeroombooking/<int:id>/', manageQR.changeroombooking, name='changeroombooking'),
    path('change_rooms_book_url/', manageQR.change_rooms_book_url, name='change_rooms_book_url'),

    # rate lan page 
    path('rateplanpage/', dynamicrates.rateplanpage, name='rateplanpage'),
    path('addbookingrateplan/', dynamicrates.addbookingrateplan, name='addbookingrateplan'),
    path('deleteplanbookingcode/<int:id>/', dynamicrates.deleteplanbookingcode, name='deleteplanbookingcode'),
    path('addrateplan/', dynamicrates.addrateplan, name='addrateplan'),
    path('deleteplanratecode/<int:id>/', dynamicrates.deleteplanratecode, name='deleteplanratecode'),
    path('guestplans/', dynamicrates.guestplans, name='guestplans'),


    path('update_room_book_advance/', views.update_room_book_advance, name='update_room_book_advance'),

    # company management  
    path('comaypage/', companyies.comaypage, name='comaypage'),
    path('add_company/', companyies.add_company, name='add_company'),
    path('deletecompany/<int:id>/', companyies.deletecompany, name='deletecompany'),
    path('get-companies/', companyies.get_companies, name='get_companies'),
    path('submit-form/', companyies.submit_form, name='submit_form'),
    path('gotocmpbills/<int:id>/', companyies.gotocmpbills, name='gotocmpbills'),

    path('process-cart/', views.cart_processing, name='your_cart_processing_view'),
    path('searchwebsitedata/',employeemanage.searchwebsitedata,name='searchwebsitedata'),


    # websettings deleteaminity
    path('addaminities/', hourlypage.addaminities, name='addaminities'),
    path('deleteaminity/<int:id>/', hourlypage.deleteaminity, name='deleteaminity'),
    path('addoffers/', hourlypage.addoffers, name='addoffers'),
    path('addcp/', hourlypage.addcp, name='addcp'),
    path('addcatimg/', hourlypage.addcatimg, name='addcatimg'),
    path('deleteimg/<int:id>/', hourlypage.deleteimg, name='deleteimg'),
    path('addhotelimg/', hourlypage.addhotelimg, name='addhotelimg'),
    path('deletehotelimg/<int:id>/', hourlypage.deletehotelimg, name='deletehotelimg'),
    path('addcontactbe/', hourlypage.addcontactbe, name='addcontactbe'),
    path('updatebookeg/', hourlypage.updatebookeg, name='updatebookeg'),
    path('rollspermission/', hourlypage.rollspermission, name='rollspermission'),
    path('create_subuser/', hourlypage.create_subuser, name='create_subuser'),
    path('get-permissions/<int:subuser_id>/', hourlypage.get_permissions, name='get_permissions'),
    path('createsubuserpermission/', hourlypage.createsubuserpermission, name='createsubuserpermission'),

    
    path('saveloyltydata/',loyltys.saveloyltydata,name="saveloyltydata"),

    path('createsubplan/',employeemanage.createsubplan,name="createsubplan"),
    path('addmsgtouser/',employeemanage.addmsgtouser,name="addmsgtouser"),
    path('bulkupdate/',employeemanage.bulkupdate,name="bulkupdate"),
    path('bulkinventoryform/',employeemanage.bulkinventoryform,name="bulkinventoryform"),
    path('bulkformprice/',employeemanage.bulkformprice,name="bulkformprice"),

    
    
    



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



