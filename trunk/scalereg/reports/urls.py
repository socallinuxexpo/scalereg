from django.conf.urls.defaults import *
from scale.reg6 import models

answer_dict = {
    'queryset': models.Answer.objects.all(),
    'extra_context': {
    'opts': models.Answer._meta,
    },
    'allow_empty': True,
}

attendee_dict = {
    'queryset': models.Attendee.objects.all(),
    'extra_context': {
    'valid': models.Attendee.objects.all().filter(valid=True).count(),
    'checkin': models.Attendee.objects.all().filter(checked_in=True).count(),
    'opts': models.Attendee._meta,
    },
    'allow_empty': True,
}

coupon_dict = {
    'queryset': models.Coupon.objects.all(),
    'extra_context': {
    'opts': models.Coupon._meta,
    },
    'allow_empty': True,
}

item_dict = {
    'queryset': models.Item.objects.all(),
    'extra_context': {
    'opts': models.Item._meta,
    },
    'allow_empty': True,
}

order_dict = {
    'queryset': models.Order.objects.all(),
    'extra_context': {
    'opts': models.Order._meta,
    'total': sum([x.amount for x in models.Order.objects.all().filter(valid=True)]),
    },
    'allow_empty': True,
}

promocode_dict = {
    'queryset': models.PromoCode.objects.all(),
    'extra_context': {
    'opts': models.PromoCode._meta,
    },
    'allow_empty': True,
}

question_dict = {
    'queryset': models.Question.objects.all(),
    'extra_context': {
    'opts': models.Question._meta,
    },
    'allow_empty': True,
}

ticket_dict = {
    'queryset': models.Ticket.objects.all(),
    'extra_context': {
    'opts': models.Ticket._meta,
    },
    'allow_empty': True,
}

urlpatterns = patterns('',
    (r'^$', 'scale.reports.views.index'),
    (r'^answer/$', 'scale.reports.views.object_list', answer_dict),
    (r'^attendee/$', 'scale.reports.views.object_list', attendee_dict),
    (r'^coupon/$', 'scale.reports.views.object_list', coupon_dict),
    (r'^item/$', 'scale.reports.views.object_list', item_dict),
    (r'^order/$', 'scale.reports.views.object_list', order_dict),
    (r'^promocode/$', 'scale.reports.views.object_list', promocode_dict),
    (r'^question/$', 'scale.reports.views.object_list', question_dict),
    (r'^ticket/$', 'scale.reports.views.object_list', ticket_dict),
    (r'^reg6log/$', 'scale.reports.views.reg6log'),
    (r'^dashboard/$', 'scale.reports.views.dashboard'),
    (r'^badorder/$', 'scale.reports.views.badorder'),
    (r'^getleads/$', 'scale.reports.views.getleads'),
)
