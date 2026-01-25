from django.urls import include
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

    # Upgrade
    path('start_upgrade/', views.start_upgrade),
    path('free_upgrade/', views.free_upgrade),
    path('non_free_upgrade/', views.non_free_upgrade),

    # Misc
    path('redeem_payment_code/', views.redeem_payment_code),
    path('reg_lookup/', views.reg_lookup),

    # Admin
    path('mass_add_attendees/', views.mass_add_attendees),
    path('mass_add_payment_codes/', views.mass_add_payment_codes),
    path('mass_add_promos/', views.mass_add_promos),
    path('staff/', include('reg23.staff.urls')),
]
