from django.urls import re_path
from scalereg.reg6.staff import views as staff_views

urlpatterns = [
    re_path(r'^$', staff_views.index),
    re_path(r'^checkin/$', staff_views.CheckIn),
    re_path(r'^finish_checkin/$', staff_views.FinishCheckIn),
    re_path(r'^cash_payment/$', staff_views.CashPayment),
    re_path(r'^cash_payment_registered/$', staff_views.CashPaymentRegistered),
    re_path(r'^email/$', staff_views.Email),
    re_path(r'^reprint/$', staff_views.Reprint),
    re_path(r'^update_attendee/$', staff_views.UpdateAttendee),
]
