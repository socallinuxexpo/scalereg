from django.forms import ModelForm
from django.forms import RadioSelect

from . import models


class AttendeeForm(ModelForm):

    class Meta:
        model = models.Attendee
        fields = (
            'salutation',
            'first_name',
            'last_name',
            'title',
            'org',
            'email',
            'zip_code',
            'phone',
            'can_email',
        )
        widgets = {'can_email': RadioSelect}


class AttendeeLookupForm(ModelForm):

    class Meta:
        model = models.Attendee
        fields = (
            'email',
            'zip_code',
        )
