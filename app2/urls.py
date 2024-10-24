from django.urls import path
from .views import app2index,terms,privcy,refund,addfreedemo

urlpatterns = [
    path('', app2index, name='app2index'),
    path('terms',terms, name='terms'),
    path('privcy',privcy, name='privcy'),
    path('refund',refund, name='refund'),
    path('addfreedemo',addfreedemo,name="addfreedemo"),
]