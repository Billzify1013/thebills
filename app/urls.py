from django.urls import path
from . import views,newcode
from . import manageQR,cm_file
from . import employeemanage,loyltys,hourlypage,donwloadexcel
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_view
from .newcode import *
from . import dynamicrates
from . import aiosellbook ,travelagancy,stayinvoices,purches,companyies,daterangeprice
from django.urls import re_path
from . import bookingpayment
from . import accountses


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
    path('guesthistorysearchview/',views.guesthistorysearchview,name="guesthistorysearchview"),
    path('guestearch/<int:id>/',stayinvoices.guestearch,name="guestearch"),
    
    path('guestdetails/<int:id>/',views.guestdetails,name="guestdetails"),
    path('openroomclickformpage/<str:id>/',views.openroomclickformpage,name="openroomclickformpage"),
    path('openroomclickformtodayarriwalspage/<str:id>/',views.openroomclickformtodayarriwalspage,name="openroomclickformtodayarriwalspage"),
    path('weekviewcheckin/',views.weekviewcheckin,name="weekviewcheckin"),
    
    path('roomcheckin/<int:id>/',views.roomcheckin,name="roomcheckin"),
    path('checkoutroom/',views.checkoutroom,name="checkoutroom"),
    path('cancelroom/',views.cancelroom,name="cancelroom"),
    path('gotofoliobyhome/<int:id>/',views.gotofoliobyhome,name="gotofoliobyhome"),
    path('gotoaddservice/<int:id>/',views.gotoaddservice,name="gotoaddservice"),

    # cashflow
    path('cashflow/',stayinvoices.cashflow,name="cashflow"),
    path('addcashamount/',stayinvoices.addcashamount,name="addcashamount"),
    path('expenseamount/',stayinvoices.expenseamount,name="expenseamount"),
    path('cashoutamount/',stayinvoices.cashoutamount,name="cashoutamount"),
    path('handovercash/',stayinvoices.handovercash,name="handovercash"),
    path('searchcashdata/',stayinvoices.searchcashdata,name="searchcashdata"),
    path('geditminvc/<int:id>/', stayinvoices.editminvc, name='editminvc'),
    path('geditfbinvc/<int:id>/', stayinvoices.geditfbinvc, name='geditfbinvc'),
    

    
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
    path('invcshow/<int:id>/',stayinvoices.invcshow,name="invcshow"),
    
    path('fbinvoicepage/<int:id>/',views.fbinvoicepage,name="fbinvoicepage"),
    path('addpaymentfolio/',views.addpaymentfolio,name="addpaymentfolio"),
    path('addpaymentfoliocredit/',views.addpaymentfoliocredit,name="addpaymentfoliocredit"),
    path('creditinvoicecheck/<int:id>/',views.creditinvoicecheck,name="creditinvoicecheck"),
    
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
    path('todamainsales/',employeemanage.todamainsales,name="todamainsales"),
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
    path('receipt_book/<int:booking_id>/', views.receipt_view_book, name='receipt_view_book'),

    # extendcheck ins
    path('extendscheck/', loyltys.extendscheck, name='extendscheck'),
    path('extendscheckonebyone/', loyltys.extendscheckonebyone, name='extendscheckonebyone'),
    path('checkoutroombyone/',loyltys.checkoutroombyone,name="checkoutroombyone"),
    path('extednroomform/',loyltys.extednroomform,name="extednroomform"),
    path('changeromcolor/',loyltys.changeromcolor,name="changeromcolor"),

    
    
    # In your urls.py file
    # path('receipt/<int:booking_id>/', views.receipt_view, name='receipt_view'),
    # path('receipt/', views.receipt_view, name='receipt_view'),
    path('receipt/', views.receipt_view, name='receipt_view'),

    path('advncereciptbiew/<int:booking_id>/', views.advncereciptbiew, name='advncereciptbiew'),
    path('advancebookingdeletebe/<int:id>/',views.advancebookingdeletebe,name="advancebookingdeletebe"),
    path('voucherfind/', views.voucherfind, name='voucherfind'),
    

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
    path('deletecreditdata/<int:id>/',loyltys.deletecreditdata,name="deletecreditdata"),
    
    path('searchcredit/',loyltys.searchcredit,name="searchcredit"),
    path('Messages/',loyltys.Messages,name="Messages"),
    path('sendwelcomemsg/',loyltys.sendwelcomemsg,name="sendwelcomemsg"),
    path('sendloyaltymsg/',loyltys.sendloyaltymsg,name="sendloyaltymsg"),
    path('searchguestexportdta/',loyltys.searchguestexportdta,name="searchguestexportdta"),
    path('policereport/',loyltys.policereport,name="policereport"),

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
    path('searchinvoicedata/',hourlypage.searchinvoicedata,name="searchinvoicedata"),
    
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
    path('editinvoice/<int:id>/', stayinvoices.editinvoice, name='editinvoice'),
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

    
    path('notification/', stayinvoices.notification, name='notification'),

    # channel manager changeroompage 
    path('channalmanager/', purches.channalmanager, name='channalmanager'),

    # dynamic rates form and all 
    path('dynamicformpage/', dynamicrates.dynamicformpage, name='dynamicformpage'),
    path('dynamicformdata/', dynamicrates.dynamicformdata, name='dynamicformdata'),

    # change room work
    path('changeroompage/<int:id>/', manageQR.changeroompage, name='changeroompage'),
    path('change-rooms/', manageQR.change_rooms, name='change_rooms_url'),
    path('changeroombooking/<int:id>/', manageQR.changeroombooking, name='changeroombooking'),
    path('changeroomadvance/', manageQR.changeroomadvance, name='changeroomadvance'),
    path('change_rooms_book_url/', manageQR.change_rooms_book_url, name='change_rooms_book_url'),
    path('change_rooms_book_week_url/', manageQR.change_rooms_book_week_url, name='change_rooms_book_week_url'),

    # google reviews
    path('reviews/', loyltys.reviews, name='reviews'), 

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
    path('bulklogshow/',employeemanage.bulklogshow,name="bulklogshow"),
    


    # booking payments 
    path('bookingpayments/',bookingpayment.bookingpayments,name="bookingpayments"),
    path('bookpaymentsearch/',bookingpayment.bookpaymentsearch,name="bookpaymentsearch"),
    path('invoicepayment/',bookingpayment.invoicepayment,name="invoicepayment"),
    path('checkinpaymentsearch/',bookingpayment.checkinpaymentsearch,name="checkinpaymentsearch"),
    
    # invoice explenations
    path('roomsales/',bookingpayment.roomsales,name="roomsales"),
    path('productssales/',bookingpayment.productssales,name="productssales"),
    path('arriwalsrpt/',bookingpayment.arriwalsrpt,name="arriwalsrpt"),
    path('searcharriwlasrpt/',bookingpayment.searcharriwlasrpt,name="searcharriwlasrpt"),
    path('searchitemsales/',bookingpayment.searchitemsales,name="searchitemsales"),
    path('departurerpt/',bookingpayment.departurerpt,name="departurerpt"),
    path('rvrpt/',bookingpayment.rvrpt,name="rvrpt"),
    path('rvrptsearch/',bookingpayment.rvrptsearch,name="rvrptsearch"),
    path('hotelplrpt/',bookingpayment.hotelplrpt,name="hotelplrpt"),
    path('hotelpandlrpt/',bookingpayment.hotelpandlrpt,name="hotelpandlrpt"),
    path('searchdeparture/',bookingpayment.searchdeparture,name="searchdeparture"),
    path('salestablesearch/',bookingpayment.salestablesearch,name="salestablesearch"),
    path('hotelplrptsearch/',bookingpayment.hotelplrptsearch,name="hotelplrptsearch"),
    path('hotelpandlsearch/',bookingpayment.hotelpandlsearch,name="hotelpandlsearch"),
    path('expensesrpt/',bookingpayment.expensesrpt,name="expensesrpt"),
    path('searchexpenses/',bookingpayment.searchexpenses,name="searchexpenses"),


    # accounts working here 
    path('accounts/',accountses.accounts,name="accounts"),
    path('searchtaxesaccount/',accountses.searchtaxesaccount,name="searchtaxesaccount"),
    path('searchtaxslabvidget/',accountses.searchtaxslabvidget,name="searchtaxslabvidget"),
    path('gstr1/',accountses.gstr1,name="gstr1"),
    path('b2bInvoicedetails/',accountses.b2bInvoicedetails,name="b2bInvoicedetails"),
    path('b2cInvoicetaxdetails/',accountses.b2cInvoicetaxdetails,name="b2cInvoicetaxdetails"),
    path('nillratedforms/',accountses.nillratedforms,name="nillratedforms"),
    # path('generate_gstr1_excel/',accountses.generate_gstr1_excel,name="generate_gstr1_excel"), this is gstr-1 actual url with excel buttons
    
    path('generate_gstr1_mix_invoice_excel/',accountses.generate_gstr1_mix_invoice_excel,name="generate_gstr1_mix_invoice_excel"),
    path('hsnsummry/',accountses.hsnsummry,name="hsnsummry"),
    path('documentsummry/',accountses.documentsummry,name="documentsummry"),
    path('generate_b2b_invoice_excel/',accountses.generate_b2b_invoice_excel,name="generate_b2b_invoice_excel"),
    path('generate_form_purchesinvoice_excel/',donwloadexcel.generate_form_purchesinvoice_excel,name="generate_form_purchesinvoice_excel"),
    path('payble/',accountses.payble,name="payble"),

    # online channel management
    path('onlinechannel/',accountses.onlinechannel,name="onlinechannel"),
    path('addchannel/',accountses.addchannel,name="addchannel"),
    path('deletechannel/<int:id>/',accountses.deletechannel,name="deletechannel"),
    path('updatechanel/',accountses.updatechanel,name="updatechanel"),
    path('proformainvoice/<int:id>/',accountses.proformainvoice,name="proformainvoice"),

    path('createpurchasefromproduct/',accountses.createpurchasefromproduct,name="createpurchasefromproduct"),
    
    # new work from here weekview to folio
    path('weekwiewfromfolio/',stayinvoices.weekwiewfromfolio,name="weekwiewfromfolio"),
    path('weekwiewfromfolioviews/',views.weekwiewfromfolioviews,name="weekwiewfromfolioviews"),


    path('addpaymentpagepurchase/<int:id>/',purches.addpaymentpagepurchase,name="addpaymentpagepurchase"),
    path('addpaymenttopurchase/',purches.addpaymenttopurchase,name="addpaymenttopurchase"),   


    # edit invoice work here
    path('editaddpaymentfolio/',stayinvoices.editaddpaymentfolio,name="editaddpaymentfolio"),
    path('editinvoicepayment/',stayinvoices.editinvoicepayment,name="editinvoicepayment"),
    path('invoicepaymentedit/',stayinvoices.invoicepaymentedit,name="invoicepaymentedit"),
    path('editbookingpayment/',stayinvoices.editbookingpayment,name="editbookingpayment"),
    
    path('deletepayment/<int:id>/',stayinvoices.deletepayment,name="deletepayment"),
    
    path('deleteitemstofolioedit/',stayinvoices.deleteitemstofolioedit,name="deleteitemstofolioedit"),
    path('editcustomergstnumberbyedit/',stayinvoices.editcustomergstnumberbyedit,name="editcustomergstnumberbyedit"),
    path('addproductonedit/',stayinvoices.addproductonedit,name="addproductonedit"),
    path('editdueamount/',stayinvoices.editdueamount,name="editdueamount"),
    path('makeseprateinvoice/',stayinvoices.makeseprateinvoice,name="makeseprateinvoice"),
    path('makeotaandfnbinvc/',stayinvoices.makeotaandfnbinvc,name="makeotaandfnbinvc"),

    path("guest_logs/<int:id>/", stayinvoices.guest_logs, name="guest_logs"),
    path("showlogs", stayinvoices.showlogs, name="showlogs"),
    path("showlogsbook", stayinvoices.showlogsbook, name="showlogsbook"),
    path("showbooklog/<int:id>/", stayinvoices.showbooklog, name="showbooklog"),
    path("bookingsearchview", stayinvoices.bookingsearchview, name="bookingsearchview"),
    path("searchbooking/<int:id>/", stayinvoices.searchbooking, name="searchbooking"),
    path("deletecancelbokings", stayinvoices.deletecancelbokings, name="deletecancelbokings"),
    path("editbookingdetails", stayinvoices.editbookingdetails, name="editbookingdetails"),
    path("editamountdetailsbooking", stayinvoices.editamountdetailsbooking, name="editamountdetailsbooking"),
    path("editroomsdata", stayinvoices.editroomsdata, name="editroomsdata"),
    path("edittaxes", stayinvoices.edittaxes, name="edittaxes"),
    path("editrateplanbooking", stayinvoices.editrateplanbooking, name="editrateplanbooking"),
    path("editotarateplan", stayinvoices.editotarateplan, name="editotarateplan"),
    
    # path("logs/gueststay/<int:gueststay_id>/", loggers.get_logs_by_gueststay, name="gueststay_logs"),

    # new date wise price work start here
    # path("priceshow/", daterangeprice.priceshow, name="priceshow"),
    # path('priceshow/', inventory_view, name='priceshow'),
    path('priceshow-new/', daterangeprice.priceshow_new, name='priceshow_new'),
    path('change-date-new/', daterangeprice.change_date_new, name='change_date_new'),
    path('next-day-new/', daterangeprice.next_day_new, name='next_day_new'),
    path('save_prices_new/', daterangeprice.save_prices_new, name='save_prices_new'),
    path('bulklogshow/',employeemanage.bulklogshow,name="bulklogshow"),

    # update inventory
    path('inventory_view/', daterangeprice.inventory_view, name='inventory_view'),
    path('next_day_inventory/', daterangeprice.next_day_inventory, name='next_day_inventory'),
    path('change_date_inventory/', daterangeprice.change_date_inventory, name='change_date_inventory'),
    path('save_inventory_new/', daterangeprice.save_inventory_new, name='save_inventory_new'),

    # new work here 
    path('updatepptdesc/', travelagancy.updatepptdesc, name='updatepptdesc'),
    path('addcatservice/', travelagancy.addcatservice, name='addcatservice'),
    path('deletecatservice/<int:id>/', travelagancy.deletecatservice, name='deletecatservice'),
    path('whatsaapchat/', travelagancy.whatsaapchat, name='whatsaapchat'),
    path('deletewhatsapchat/<int:id>/', travelagancy.deletewhatsapchat, name='deletewhatsapchat'),


    # ota commission
    path('ota_Commission/', travelagancy.ota_Commission, name='ota_Commission'),

    path('formo_view/', travelagancy.formo_view, name='formo_view'),
    path('sync_inventory/', travelagancy.sync_inventory, name='sync_inventory'),
    path('edittotalbookingamount/', travelagancy.edittotalbookingamount, name='edittotalbookingamount'),
    path('editbookingdate/', travelagancy.editbookingdate, name='editbookingdate'),
    path('editcommtdc/', travelagancy.editcommtdc, name='editcommtdc'),
    path('bookingrevoke/<int:id>/', travelagancy.bookingrevoke, name='bookingrevoke'),
    path('bookingrevokenot/<int:id>/', travelagancy.bookingrevokenot, name='bookingrevokenot'),

    # channel manager newworking here
    path('cm/', travelagancy.cm, name='cm'),
    path('bulkupdatecm/',employeemanage.bulkupdatecm,name="bulkupdatecm"),
    path('priceshow_new_cm/', cm_file.priceshow_new_cm, name='priceshow_new_cm'),
    path('next_day_new_cm/', cm_file.next_day_new_cm, name='next_day_new_cm'),
    path('change_date_new_cm/', cm_file.change_date_new_cm, name='change_date_new_cm'),
    path('save_prices_new_cm/', cm_file.save_prices_new_cm, name='save_prices_new_cm'),

    path('inventory_view_cm/', cm_file.inventory_view_cm, name='inventory_view_cm'),
    path('next_day_inventory_cm/', cm_file.next_day_inventory_cm, name='next_day_inventory_cm'),
    path('change_date_inventory_cm/', cm_file.change_date_inventory_cm, name='change_date_inventory_cm'),
    path('save_inventory_new_cm/', cm_file.save_inventory_new_cm, name='save_inventory_new_cm'),
    
    path('ota_Commission_cm/', cm_file.ota_Commission_cm, name='ota_Commission_cm'),
    path('create_roomcount/', cm_file.create_roomcount, name='create_roomcount'),
    path('addroomcount/', cm_file.addroomcount, name='addroomcount'),

    path('sync_inventory_cm/', cm_file.sync_inventory_cm, name='sync_inventory_cm'),

    path('bulkinventoryform_cm/',cm_file.bulkinventoryform_cm,name="bulkinventoryform_cm"),

    path('bulkformprice_cm/',cm_file.bulkformprice_cm,name="bulkformprice_cm"),
    path('channel_manager_aiosell_new_reservation', cm_file.channel_manager_aiosell_new_reservation, name='channel_manager_aiosell_new_reservation'),

    path('searchguestdataadvance_cm/',cm_file.searchguestdataadvance_cm,name="searchguestdataadvance_cm"),

    path('advancebookingdetails_cm/<int:id>/',cm_file.advancebookingdetails_cm,name="advancebookingdetails_cm"),
    path('addpaymenttobooking_cm/<int:booking_id>/',cm_file.addpaymenttobooking_cm,name="addpaymenttobooking_cm"),
    path('addpymenttoboking_cm/',cm_file.addpymenttoboking_cm,name="addpymenttoboking_cm"),
    path('edittotalbookingamount_cm/', cm_file.edittotalbookingamount_cm, name='edittotalbookingamount_cm'),
    path('cmnotification/', cm_file.cmnotification, name='cmnotification'),
    path('dashboardcm/', cm_file.dashboardcm, name='dashboardcm'),
    path('salescm/', cm_file.salescm, name='salescm'),



]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



