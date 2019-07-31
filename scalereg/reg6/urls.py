from django.conf.urls import *
from scalereg.reg6 import views as reg6_views

urlpatterns = [
    # Registration
    url(r'^$', reg6_views.index),
    url(r'^add_items/$', reg6_views.AddItems),
    url(r'^add_attendee/$', reg6_views.AddAttendee),
    url(r'^registered_attendee/$', reg6_views.RegisteredAttendee),

    # Payment
    url(r'^start_payment/$', reg6_views.StartPayment),
    url(r'^payment/$', reg6_views.Payment),
    url(r'^sale/$', reg6_views.Sale),
    url(r'^failed_payment/$', reg6_views.FailedPayment),
    url(r'^finish_payment/$', reg6_views.FinishPayment),

    # Upgrade
    url(r'^start_upgrade/$', reg6_views.StartUpgrade),
    url(r'^nonfree_upgrade/$', reg6_views.NonFreeUpgrade),
    url(r'^free_upgrade/$', reg6_views.FreeUpgrade),

    # Misc
    url(r'^reg_lookup/$', reg6_views.RegLookup),
    url(r'^kiosk/$', reg6_views.kiosk_index),
    url(r'^checkin/$', reg6_views.CheckIn),
    url(r'^finish_checkin/$', reg6_views.FinishCheckIn),
    url(r'^redeem_coupon/$', reg6_views.RedeemCoupon),
    url(r'^scanned_badge/$', reg6_views.ScannedBadge),

    # Admin
    url(r'^add_coupon/$', reg6_views.AddCoupon),
    url(r'^checked_in/$', reg6_views.CheckedIn),
    url(r'^mass_add_attendee/$', reg6_views.MassAddAttendee),
    url(r'^mass_add_coupon/$', reg6_views.MassAddCoupon),
    url(r'^mass_add_promo/$', reg6_views.MassAddPromo),
    url(r'^clear_badorder/$', reg6_views.ClearBadOrder),
    url(r'^staff/', include('scalereg.reg6.staff.urls')),
]
