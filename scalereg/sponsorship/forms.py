from django.forms import BooleanField
from django.forms import ModelForm
from scalereg.sponsorship.models import Sponsor

class SponsorForm(ModelForm):
  class Meta:
    model = Sponsor
    fields = (
      'salutation',
      'first_name',
      'last_name',
      'title',
      'org',
      'email',
      'zip_code',
      'phone',
    )

  agreed = BooleanField()
