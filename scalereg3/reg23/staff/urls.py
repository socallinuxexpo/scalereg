from django.urls import path

from reg23.staff import views

urlpatterns = [
    path('', views.index),
    path('cash_payment/', views.cash_payment),
    path('check_in/', views.check_in),
    path('email/', views.email),
    path('finish_check_in/', views.finish_check_in),
    path('receipt/', views.receipt),
]
