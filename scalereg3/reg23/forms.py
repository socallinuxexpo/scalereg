from django.forms import ModelForm
from django.forms import RadioSelect

from . import models


class AttendeeCashForm(ModelForm):

    class Meta:
        model = models.Attendee
        fields = (
            'first_name',
            'last_name',
            'title',
            'org',
            'email',
            'zip_code',
        )


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


class MassAddOrderForm(ModelForm):

    class Meta:
        model = models.Order
        fields = (
            'order_num',
            'name',
            'address',
            'city',
            'state',
            'zip_code',
            'email',
            'phone',
            'payment_type',
        )


class MassAddPromoForm(ModelForm):

    class Meta:
        model = models.PromoCode
        fields = (
            'name',
            'price_modifier',
            'description',
        )
