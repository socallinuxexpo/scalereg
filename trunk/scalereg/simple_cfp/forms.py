from django.forms import ModelForm
from scalereg.simple_cfp.models import Speaker


class SpeakerForm(ModelForm):
  class Meta:
    model = Speaker
    fields = (
      'salutation',
      'first_name',
      'last_name',
      'title',
      'org',
      'zip',
      'email',
      'phone',
      'url',
      'bio',
    )
