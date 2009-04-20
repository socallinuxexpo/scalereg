from django.conf.urls.defaults import *
from scale.reg6 import models

attendee_dict = {
    'queryset': models.Attendee.objects.all(),
    'extra_context': {
    'valid': len(models.Attendee.objects.all().filter(valid=True)),
    'checkin': len(models.Attendee.objects.all().filter(checked_in=True)),
    },
    'allow_empty': True,
}

item_dict = {
    'queryset': models.Item.objects.all(),
    'allow_empty': True,
}

order_dict = {
    'queryset': models.Order.objects.all(),
    'extra_context': {
    'total': sum([x.amount for x in models.Order.objects.all().filter(valid=True)]),
    },
    'allow_empty': True,
}

promocode_dict = {
    'queryset': models.PromoCode.objects.all(),
    'allow_empty': True,
}

ticket_dict = {
    'queryset': models.Ticket.objects.all(),
    'allow_empty': True,
}

urlpatterns = patterns('',
    (r'^$', 'scale.reports.views.index'),
    (r'^attendee/$', 'scale.reports.views.object_list', attendee_dict),
    (r'^item/$', 'scale.reports.views.object_list', item_dict),
    (r'^order/$', 'scale.reports.views.object_list', order_dict),
    (r'^promocode/$', 'scale.reports.views.object_list', promocode_dict),
    (r'^ticket/$', 'scale.reports.views.object_list', ticket_dict),
    (r'^reg6log/$', 'scale.reports.views.reg6log'),
)
