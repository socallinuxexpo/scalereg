from django.conf.urls import *
from scalereg.sponsorship import views as sponsorship_view

urlpatterns = [
    # Registration
    url(r'^$', sponsorship_view.index),
    url(r'^add_items/$', sponsorship_view.AddItems),
    url(r'^add_sponsor/$', sponsorship_view.AddSponsor),

    # Payment
    url(r'^payment/$', sponsorship_view.Payment),
    url(r'^sale/$', sponsorship_view.Sale),
    url(r'^failed_payment/$', sponsorship_view.FailedPayment),
    url(r'^finish_payment/$', sponsorship_view.FinishPayment),
]
