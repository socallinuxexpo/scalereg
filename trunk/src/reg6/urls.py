from django.conf.urls.defaults import *
from scale.reg6 import models

urlpatterns = patterns('',
    (r'^$', 'scale.reg6.views.index'),
    (r'^add_items/$', 'scale.reg6.views.AddItems'),
    (r'^add_attendee/$', 'scale.reg6.views.AddAttendee'),
    (r'^registered_attendee/$', 'scale.reg6.views.RegisteredAttendee'),
    (r'^start_payment/$', 'scale.reg6.views.StartPayment'),
    (r'^payment/$', 'scale.reg6.views.Payment'),
    (r'^sale/$', 'scale.reg6.views.Sale'),
    (r'^failed_payment/$', 'scale.reg6.views.FailedPayment'),
)
