from django.conf.urls import *
from scalereg.reg6 import models
from scalereg.reports import views as reports_views

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

urlpatterns = [
    url(r'^$', reports_views.index),
    url(r'^answer/$', reports_views.object_list, answer_dict),
    url(r'^attendee/$', reports_views.object_list, attendee_dict),
    url(r'^coupon/$', reports_views.object_list, coupon_dict),
    url(r'^item/$', reports_views.object_list, item_dict),
    url(r'^order/$', reports_views.object_list, order_dict),
    url(r'^promocode/$', reports_views.object_list, promocode_dict),
    url(r'^question/$', reports_views.object_list, question_dict),
    url(r'^ticket/$', reports_views.object_list, ticket_dict),
    url(r'^reg6log/$', reports_views.reg6log),
    url(r'^dashboard/$', reports_views.dashboard),
    url(r'^badorder/$', reports_views.badorder),
    url(r'^getleads/$', reports_views.getleads),
    url(r'^getpgp/$', reports_views.getpgp),
    url(r'^putpgp/$', reports_views.putpgp),
    url(r'^checkpgp/$', reports_views.checkpgp),
    url(r'^announce_subscribers/$', reports_views.AnnounceSubscribers),
    url(r'^coupon_usage/$', reports_views.CouponUsage),
]
