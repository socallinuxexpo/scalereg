from django.forms import ModelForm
from scalereg.reg6.models import Attendee
from scalereg.reg6.models import Order
from scalereg.reg6.models import PromoCode

class AddCouponForm(ModelForm):
  class Meta:
    model = Order
    fields = (
      'name',
      'address',
      'city',
      'state',
      'zip',
      'email',
      'country',
      'phone',
    )


class AttendeeForm(ModelForm):
  class Meta:
    model = Attendee
    fields = (
      'salutation',
      'first_name',
      'last_name',
      'title',
      'org',
      'email',
      'zip',
      'phone',
      'can_email',
      'answers',
    )


class MassAddAttendeeForm(ModelForm):
  class Meta:
    model = Attendee
    fields = (
      'first_name',
      'last_name',
      'title',
      'org',
      'zip',
      'email',
      'order',
      'badge_type',
    )


class MassAddPromoForm(ModelForm):
  class Meta:
    model = PromoCode
    fields = (
      'name',
      'price_modifier',
      'description',
    )
