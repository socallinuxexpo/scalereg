from django.urls import path

from reg23.staff import views

urlpatterns = [
    path('', views.index),
    path('cash_payment/', views.cash_payment),
    path('receipt/', views.receipt),
]
