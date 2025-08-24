from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('sales_dashboard/', views.sales_dashboard,
         {'report_name': 'Sales Dashboard'}),
]
