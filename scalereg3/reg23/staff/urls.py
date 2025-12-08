from django.urls import path

from reg23.staff import views

urlpatterns = [
    path('receipt/', views.receipt),
]
