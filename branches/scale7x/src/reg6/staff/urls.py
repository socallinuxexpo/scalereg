from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scale.reg6.staff.views.index'),
    (r'^checkin/$', 'scale.reg6.staff.views.CheckIn'),
    (r'^finish_checkin/$', 'scale.reg6.staff.views.FinishCheckIn'),
    (r'^cash_payment/$', 'scale.reg6.staff.views.CashPayment'),
)
