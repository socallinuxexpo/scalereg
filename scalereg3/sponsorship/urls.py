from django.urls import path

from . import views

urlpatterns = [
    # Registration
    path('', views.index),
    path('add_items/', views.add_items),
    path('add_sponsor/', views.add_sponsor),

    # Payment
    path('payment/', views.payment),
    path('sale/', views.sale),
    path('failed_payment/', views.failed_payment),
]
