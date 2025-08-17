from django.urls import path

from . import views

urlpatterns = [
    # Registration
    path('', views.index),
    path('add_items/', views.add_items),
    path('add_attendee/', views.add_attendee),
    path('registered_attendee/', views.registered_attendee),

    # Payment
    path('start_payment/', views.start_payment),
    path('payment/', views.payment),
    path('sale/', views.sale),
    path('failed_payment/', views.failed_payment),
    path('finish_payment/', views.finish_payment),

    # Misc
    path('reg_lookup/', views.reg_lookup),
]
