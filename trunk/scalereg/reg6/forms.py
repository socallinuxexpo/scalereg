from django.forms import ModelForm
from scalereg.reg6.models import Attendee

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
