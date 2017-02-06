from django.conf.urls import *

urlpatterns = patterns('',
    # Registration
    (r'^$', 'scalereg.sponsorship.views.index'),
    (r'^add_items/$', 'scalereg.sponsorship.views.AddItems'),
    (r'^add_sponsor/$', 'scalereg.sponsorship.views.AddSponsor'),

    # Payment
    (r'^payment/$', 'scalereg.sponsorship.views.Payment'),
    (r'^sale/$', 'scalereg.sponsorship.views.Sale'),
    (r'^failed_payment/$', 'scalereg.sponsorship.views.FailedPayment'),
    (r'^finish_payment/$', 'scalereg.sponsorship.views.FinishPayment'),
)
