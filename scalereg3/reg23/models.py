import datetime

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


class TicketManager(models.Manager):

    def get_queryset(self):
        tickets = super().get_queryset()
        today = datetime.date.today()
        exclude = [item for item in tickets if not item.is_public(today)]
        for item in exclude:
            tickets = tickets.exclude(name=item.name)
        return tickets


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

    objects = models.Manager()
    public_objects = TicketManager()

    def is_public(self, date):
        if not self.public:
            return False
        if self.start_date and self.start_date > date:
            return False
        if self.end_date and self.end_date <= date:
            return False
        return True
