import datetime

from django.db import models


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

    def package_cost(self, items):
        package_price = self.price
        items_price = 0
        for item in items:
            items_price += item.price
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
