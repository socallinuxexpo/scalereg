import datetime

from django.db import models

SALUTATION_CHOICES = (
    ('Mr', 'Mr.'),
    ('Ms', 'Ms.'),
    ('Mrs', 'Mrs.'),
    ('Dr', 'Dr.'),
)


class Order(models.Model):
    # basic info
    order_num = models.CharField(
        max_length=10,
        primary_key=True,
        help_text='Unique 10 upper-case letters + numbers code')
    valid = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    # name and address
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=120)
    city = models.CharField(max_length=60)
    state = models.CharField(max_length=60)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=60, blank=True)

    # contact info
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # payment info
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payflow_auth_code = models.CharField(max_length=30, blank=True)
    payflow_pnref = models.CharField(max_length=15, blank=True)
    payflow_resp_msg = models.CharField(max_length=60, blank=True)
    payflow_result = models.CharField(max_length=60, blank=True)

    # sponsor data
    sponsor = models.OneToOneField('Sponsor', on_delete=models.PROTECT)
    already_paid_sponsor = models.BooleanField(default=False)


class PackageManager(models.Manager):

    def get_queryset(self):
        packages = super().get_queryset()
        today = datetime.date.today()
        exclude = [item for item in packages if not item.is_public(today)]
        for item in exclude:
            packages = packages.exclude(name=item.name)
        return packages


class Package(models.Model):
    name = models.CharField(
        max_length=5,
        primary_key=True,
        help_text='Up to 5 letters, upper-case letters + numbers')
    description = models.CharField(max_length=60)
    long_description = models.CharField(max_length=600)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    public = models.BooleanField(
        default=False, help_text='Publicly available on the order page')
    start_date = models.DateField(null=True,
                                  blank=True,
                                  help_text='Available on this day')
    end_date = models.DateField(null=True,
                                blank=True,
                                help_text='Not Usable on this day')

    objects = models.Manager()
    public_objects = PackageManager()

    def package_cost(self, items, promo):
        package_price = self.get_promo_price(promo)
        items_price = 0
        for item in items:
            items_price += item.get_promo_price(promo)
            if item.package_offset:
                package_price = 0
        return package_price + items_price

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

    def get_promo_price(self, promo):
        if promo and promo.is_applicable_to(self):
            return round(self.price * promo.price_modifier, 2)
        return self.price

    def apply_promo(self, promo):
        self.price = self.get_promo_price(promo)


class PromoCodeManager(models.Manager):

    def get_queryset(self):
        promo_codes = super().get_queryset()
        exclude = [item for item in promo_codes if not item.is_active()]
        for item in exclude:
            promo_codes = promo_codes.exclude(name=item.name)
        return promo_codes

    def names(self):
        return [f.name for f in self.get_queryset()]


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
    applies_to = models.ManyToManyField(Package, blank=True)
    applies_to_all = models.BooleanField(default=False,
                                         help_text='Applies to all packages')

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

    def is_applicable_to(self, package):
        if self.applies_to_all:
            return True
        return package in self.applies_to.all()


class Item(models.Model):
    name = models.CharField(
        max_length=4,
        primary_key=True,
        help_text='Unique, up to 4 upper-case letters / numbers')
    description = models.CharField(max_length=60)
    long_description = models.CharField(max_length=600)

    price = models.DecimalField(max_digits=7, decimal_places=2)

    active = models.BooleanField(default=False)
    promo = models.BooleanField(default=False,
                                help_text='Price affected by promo code?')
    package_offset = models.BooleanField(
        default=False, help_text='Item offsets package price?')
    applies_to = models.ManyToManyField(Package, blank=True)
    applies_to_all = models.BooleanField(default=False,
                                         help_text='Applies to all packages')

    def get_promo_price(self, promo):
        if promo and self.promo:
            return round(self.price * promo.price_modifier, 2)
        return self.price

    def apply_promo(self, promo):
        self.price = self.get_promo_price(promo)


class Sponsor(models.Model):
    # meta
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    valid = models.BooleanField(default=False)

    # name
    salutation = models.CharField(max_length=10,
                                  choices=SALUTATION_CHOICES,
                                  blank=True)
    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    title = models.CharField(max_length=60, blank=True)
    org = models.CharField(max_length=60)

    # contact info
    email = models.EmailField()
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20, blank=True)

    # etc
    promo = models.ForeignKey(PromoCode,
                              on_delete=models.PROTECT,
                              blank=True,
                              null=True)
    agreed = models.BooleanField(default=False)
    ordered_items = models.ManyToManyField(Item, blank=True)

    def package_cost(self):
        return self.package.package_cost(self.ordered_items.all(), self.promo)


class PendingOrder(models.Model):
    order_num = models.CharField(
        max_length=10,
        primary_key=True,
        help_text='Unique 10 upper-case letters + numbers code')
    sponsor = models.ForeignKey(Sponsor, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
