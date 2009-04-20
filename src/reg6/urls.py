from django.conf.urls.defaults import *
from scale.reg6 import models

urlpatterns = patterns('',
    (r'^$', 'scale.reg6.views.index'),
    (r'^add_items/$', 'scale.reg6.views.AddItems'),
    (r'^add_attendee/$', 'scale.reg6.views.AddAttendee'),
    (r'^registered_attendee/$', 'scale.reg6.views.RegisteredAttendee'),
)
