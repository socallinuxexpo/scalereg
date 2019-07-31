from django.conf.urls import *
from scalereg.reg6.staff import views as staff_views

urlpatterns = [
    url(r'^$', staff_views.index),
    url(r'^checkin/$', staff_views.CheckIn),
    url(r'^finish_checkin/$', staff_views.FinishCheckIn),
    url(r'^cash_payment/$', staff_views.CashPayment),
    url(r'^cash_payment_registered/$', staff_views.CashPaymentRegistered),
    url(r'^email/$', staff_views.Email),
    url(r'^reprint/$', staff_views.Reprint),
    url(r'^update_attendee/$', staff_views.UpdateAttendee),
]
