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


class MassAddAttendeesForm(ModelForm):

    class Meta:
        model = models.Attendee
        fields = (
            'first_name',
            'last_name',
            'title',
            'org',
            'zip_code',
            'email',
            'order',
            'badge_type',
        )


class MassAddPromoForm(ModelForm):

    class Meta:
        model = models.PromoCode
        fields = (
            'name',
            'price_modifier',
            'description',
        )
