from django.forms import ModelForm

from . import models


class SponsorForm(ModelForm):

    class Meta:
        model = models.Sponsor
        fields = (
            'salutation',
            'first_name',
            'last_name',
            'title',
            'org',
            'email',
            'zip_code',
            'phone',
            'agreed',
        )
