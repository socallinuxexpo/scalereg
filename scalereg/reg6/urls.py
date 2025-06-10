from django.urls import re_path, include
from scalereg.reg6 import views as reg6_views

urlpatterns = [
    # Registration
    re_path(r'^$', reg6_views.index),
    re_path(r'^add_items/$', reg6_views.AddItems),
    re_path(r'^add_attendee/$', reg6_views.AddAttendee),
    re_path(r'^registered_attendee/$', reg6_views.RegisteredAttendee),

    # Payment
    re_path(r'^start_payment/$', reg6_views.StartPayment),
    re_path(r'^payment/$', reg6_views.Payment),
    re_path(r'^sale/$', reg6_views.Sale),
    re_path(r'^failed_payment/$', reg6_views.FailedPayment),
    re_path(r'^finish_payment/$', reg6_views.FinishPayment),

    # Upgrade
    re_path(r'^start_upgrade/$', reg6_views.StartUpgrade),
    re_path(r'^nonfree_upgrade/$', reg6_views.NonFreeUpgrade),
    re_path(r'^free_upgrade/$', reg6_views.FreeUpgrade),

    # Misc
    re_path(r'^reg_lookup/$', reg6_views.RegLookup),
    re_path(r'^kiosk/$', reg6_views.kiosk_index),
    re_path(r'^checkin/$', reg6_views.CheckIn),
    re_path(r'^finish_checkin/$', reg6_views.FinishCheckIn),
    re_path(r'^redeem_coupon/$', reg6_views.RedeemCoupon),
    re_path(r'^scanned_badge/$', reg6_views.ScannedBadge),

    # Admin
    re_path(r'^add_coupon/$', reg6_views.AddCoupon),
    re_path(r'^checked_in/$', reg6_views.CheckedIn),
    re_path(r'^mass_add_attendee/$', reg6_views.MassAddAttendee),
    re_path(r'^mass_add_coupon/$', reg6_views.MassAddCoupon),
    re_path(r'^mass_add_promo/$', reg6_views.MassAddPromo),
    re_path(r'^clear_badorder/$', reg6_views.ClearBadOrder),
    re_path(r'^staff/', include('scalereg.reg6.staff.urls')),
]
