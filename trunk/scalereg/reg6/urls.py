from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Registration
    (r'^$', 'scalereg.reg6.views.index'),
    (r'^add_items/$', 'scalereg.reg6.views.AddItems'),
    (r'^add_attendee/$', 'scalereg.reg6.views.AddAttendee'),
    (r'^registered_attendee/$', 'scalereg.reg6.views.RegisteredAttendee'),

    # Payment
    (r'^start_payment/$', 'scalereg.reg6.views.StartPayment'),
    (r'^payment/$', 'scalereg.reg6.views.Payment'),
    (r'^sale/$', 'scalereg.reg6.views.Sale'),
    (r'^failed_payment/$', 'scalereg.reg6.views.FailedPayment'),
    (r'^finish_payment/$', 'scalereg.reg6.views.FinishPayment'),

    # Misc
    (r'^reg_lookup/$', 'scalereg.reg6.views.RegLookup'),
    (r'^kiosk/$', 'scalereg.reg6.views.kiosk_index'),
    (r'^checkin/$', 'scalereg.reg6.views.CheckIn'),
    (r'^finish_checkin/$', 'scalereg.reg6.views.FinishCheckIn'),
    (r'^redeem_coupon/$', 'scalereg.reg6.views.RedeemCoupon'),

    # Admin
    (r'^add_coupon/$', 'scalereg.reg6.views.AddCoupon'),
    (r'^checked_in/$', 'scalereg.reg6.views.CheckedIn'),
    (r'^mass_add_attendee/$', 'scalereg.reg6.views.MassAddAttendee'),
    (r'^mass_add_promo/$', 'scalereg.reg6.views.MassAddPromo'),
    (r'^clear_badorder/$', 'scalereg.reg6.views.ClearBadOrder'),
    (r'^staff/', include('scalereg.reg6.staff.urls')),
)
