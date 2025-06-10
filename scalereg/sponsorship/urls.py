from django.urls import re_path
from scalereg.sponsorship import views as sponsorship_view

urlpatterns = [
    # Registration
    re_path(r'^$', sponsorship_view.index),
    re_path(r'^add_items/$', sponsorship_view.AddItems),
    re_path(r'^add_sponsor/$', sponsorship_view.AddSponsor),

    # Payment
    re_path(r'^payment/$', sponsorship_view.Payment),
    re_path(r'^sale/$', sponsorship_view.Sale),
    re_path(r'^failed_payment/$', sponsorship_view.FailedPayment),
    re_path(r'^finish_payment/$', sponsorship_view.FinishPayment),
]
