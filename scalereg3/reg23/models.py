from django.db import models

TICKET_CHOICES = (
    ('exhibitor', 'Exhibitor'),
    ('expo', 'Expo Only'),
    ('full', 'Full'),
    ('kid', 'Kids Pass'),
    ('press', 'Press'),
    ('speaker', 'Speaker'),
    ('staff', 'Staff'),
)


class Ticket(models.Model):
    name = models.CharField(
        max_length=5,
        primary_key=True,
        help_text='Up to 5 letters, upper-case letters + numbers')
    description = models.CharField(max_length=60)
    ticket_type = models.CharField(max_length=10, choices=TICKET_CHOICES)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    public = models.BooleanField(
        help_text='Publicly available on the order page')
    cash = models.BooleanField(help_text='Available for cash purchase')
    upgradable = models.BooleanField(help_text='Eligible for upgrades')
    start_date = models.DateField(null=True,
                                  blank=True,
                                  help_text='Available on this day')
    end_date = models.DateField(null=True,
                                blank=True,
                                help_text='Not Usable on this day')
