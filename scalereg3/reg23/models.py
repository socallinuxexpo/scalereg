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

    def get_items(self):
        items = Item.objects.filter(applies_to_all=True).filter(active=True)
        return items.union(self.item_set.filter(active=True)).order_by('name')

    def apply_promo(self, promo):
        if promo and promo.is_applicable_to(self):
            self.price *= promo.price_modifier


class PromoCodeManager(models.Manager):

    def get_queryset(self):
        promo_codes = super().get_queryset()
        exclude = [item for item in promo_codes if not item.is_active()]
        for item in exclude:
            promo_codes = promo_codes.exclude(name=item.name)
        return promo_codes

    def names(self):
        name_list = []
        for f in self.get_queryset():
            name_list.append(f.name)
        return name_list


class PromoCode(models.Model):
    name = models.CharField(
        max_length=5,
        primary_key=True,
        help_text='Up to 5 letters, upper-case letters + numbers')
    description = models.CharField(max_length=60)

    price_modifier = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        help_text='This is the price multiplier, i.e. for 0.4, $10 becomes $4.'
    )
    active = models.BooleanField(default=False)
    start_date = models.DateField(null=True,
                                  blank=True,
                                  help_text='Available on this day')
    end_date = models.DateField(null=True,
                                blank=True,
                                help_text='Not Usable on this day')
    applies_to = models.ManyToManyField(Ticket, blank=True)
    applies_to_all = models.BooleanField(default=False,
                                         help_text='Applies to all tickets')

    objects = models.Manager()
    active_objects = PromoCodeManager()

    def is_active(self):
        if not self.active:
            return False
        today = datetime.date.today()
        if self.start_date and self.start_date > today:
            return False
        if self.end_date and self.end_date <= today:
            return False
        return True

    def is_applicable_to(self, ticket):
        if self.applies_to_all:
            return True
        return ticket in self.applies_to.all()


class Item(models.Model):
    name = models.CharField(
        max_length=4,
        primary_key=True,
        help_text='Unique, up to 4 upper-case letters / numbers')
    description = models.CharField(max_length=60)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField()
    promo = models.BooleanField(help_text='Price affected by promo code?')
    ticket_offset = models.BooleanField(help_text='Item offsets ticket price?')
    applies_to = models.ManyToManyField(Ticket, blank=True)
    applies_to_all = models.BooleanField(help_text='Applies to all tickets')

    def apply_promo(self, promo):
        if promo and self.promo:
            self.price *= promo.price_modifier
