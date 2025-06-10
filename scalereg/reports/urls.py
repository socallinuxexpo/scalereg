from django.urls import re_path
from scalereg.reg6 import models
from scalereg.reports import views as reports_views

def get_attendee_extra_context():
    return {
        'valid': models.Attendee.objects.filter(valid=True).count(),
        'checkin': models.Attendee.objects.filter(checked_in=True).count(),
    }

def get_order_extra_context():
    return {
        'total': sum([x.amount for x in models.Order.objects.filter(valid=True)])
    }

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
    'opts': models.Attendee._meta,
    'dynamic_counts': get_attendee_extra_context,
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
    'dynamic_total': get_order_extra_context,
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
    re_path(r'^$', reports_views.index),
    re_path(r'^answer/$', reports_views.object_list, answer_dict),
    re_path(r'^attendee/$', reports_views.object_list, attendee_dict),
    re_path(r'^coupon/$', reports_views.object_list, coupon_dict),
    re_path(r'^item/$', reports_views.object_list, item_dict),
    re_path(r'^order/$', reports_views.object_list, order_dict),
    re_path(r'^promocode/$', reports_views.object_list, promocode_dict),
    re_path(r'^question/$', reports_views.object_list, question_dict),
    re_path(r'^ticket/$', reports_views.object_list, ticket_dict),
    re_path(r'^reg6log/$', reports_views.reg6log),
    re_path(r'^dashboard/$', reports_views.dashboard),
    re_path(r'^badorder/$', reports_views.badorder),
    re_path(r'^getleads/$', reports_views.getleads),
    re_path(r'^getpgp/$', reports_views.getpgp),
    re_path(r'^putpgp/$', reports_views.putpgp),
    re_path(r'^checkpgp/$', reports_views.checkpgp),
    re_path(r'^announce_subscribers/$', reports_views.AnnounceSubscribers),
    re_path(r'^coupon_usage/$', reports_views.CouponUsage),
]
