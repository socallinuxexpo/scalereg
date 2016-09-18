from django.db import models
from scalereg.sponsorship import validators
import datetime

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
)

class Order(models.Model):
  # basic info
  order_num = models.CharField(max_length=10, primary_key=True,
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
  auth_code = models.CharField(max_length=30, blank=True)
  pnref = models.CharField(max_length=15, blank=True)
  resp_msg = models.CharField(max_length=60, blank=True)
  result = models.CharField(max_length=60, blank=True)

  # sponsor data
  sponsor = models.OneToOneField('Sponsor')
  already_paid_sponsor = models.BooleanField(default=False)

  def __unicode__(self):
    return u'%s' % self.order_num

  def save(self, *args, **kwargs):
    validators.CheckNotNegative(self.amount, self)
    validators.CheckValidOrderNumber(self.order_num, self)
    return super(Order, self).save(*args, **kwargs)


class PackageManager(models.Manager):
  def get_queryset(self):
    exclude = []
    item_set = super(PackageManager, self).get_queryset()
    for item in item_set:
      if not item.is_public():
        exclude.append(item)
    for item in exclude:
      item_set = item_set.exclude(name=item.name)
    return item_set

  def names(self):
    name_list = []
    for f in self.get_queryset():
      name_list.append(f.name)
    return name_list


class Package(models.Model):
  name = models.CharField(max_length=5, primary_key=True,
      help_text='Up to 5 letters, upper-case letters + numbers')
  description = models.CharField(max_length=60)
  long_description = models.CharField(max_length=120)
  price = models.DecimalField(max_digits=7, decimal_places=2)
  public = models.BooleanField(default=False,
      help_text='Publicly available on the order page')
  start_date = models.DateField(null=True, blank=True,
      help_text='Available on this day')
  end_date = models.DateField(null=True, blank=True,
      help_text='Not Usable on this day')

  objects = models.Manager()
  public_objects = PackageManager()

  @staticmethod
  def package_cost(package, items, promo):
    # TODO remove this without double-apply promo.
    package = Package.objects.get(name=package.name)
    price_modifier = promo.price_modifier if promo else 1
    package_price = package.price
    if promo and (promo.applies_to_all or
                  package in promo.applies_to.all()):
      package_price *= price_modifier

    items_price = 0
    for item in items:
      # TODO remove this without double-apply promo.
      item = Item.objects.get(name=item.name)
      additional_cost = item.price
      if item.promo:
        additional_cost *= price_modifier
      items_price += additional_cost
      if item.package_offset:
        package_price = 0
    return package_price + items_price

  def is_public(self):
    if not self.public:
      return False
    today = datetime.date.today()
    if self.start_date and self.start_date > today:
      return False
    if self.end_date and self.end_date <= today:
      return False
    return True

  def __unicode__(self):
    return u'%s' % self.name

  def save(self, *args, **kwargs):
    validators.CheckAllCapsDigits(self.name, self)
    validators.CheckNotNegative(self.price, self)
    validators.CheckValidStartStopDates(self.start_date, self)
    return super(Package, self).save(*args, **kwargs)


class PromoCodeManager(models.Manager):
  def get_queryset(self):
    exclude = []
    set = super(PromoCodeManager, self).get_queryset()
    for item in set:
      if not item.is_active():
        exclude.append(item)
    for item in exclude:
      set = set.exclude(name=item.name)
    return set

  def names(self):
    name_list = []
    for f in self.get_queryset():
      name_list.append(f.name)
    return name_list


class PromoCode(models.Model):
  name = models.CharField(max_length=5, primary_key=True,
      help_text='Up to 5 letters, upper-case letters + numbers')
  description = models.CharField(max_length=60)

  price_modifier = models.DecimalField(max_digits=3, decimal_places=2,
      help_text='This is the price multiplier, i.e. for 0.4, $10 becomes $4.')
  active = models.BooleanField(default=False)
  start_date = models.DateField(null=True, blank=True,
      help_text='Available on this day')
  end_date = models.DateField(null=True, blank=True,
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

  def __unicode__(self):
    return self.name

  def save(self, *args, **kwargs):
    validators.CheckAllCapsDigits(self.name, self)
    validators.CheckPositive(self.price_modifier, self)
    validators.CheckValidStartStopDates(self.start_date, self)
    return super(PromoCode, self).save(*args, **kwargs)


class Item(models.Model):
  name = models.CharField(max_length=4,
      help_text='Unique, up to 4 upper-case letters / numbers')
  description = models.CharField(max_length=60)
  long_description = models.CharField(max_length=120)

  price = models.DecimalField(max_digits=7, decimal_places=2)

  active = models.BooleanField(default=False)
  promo = models.BooleanField(default=False,
      help_text='Price affected by promo code?')
  package_offset = models.BooleanField(default=False,
      help_text='Item offsets package price?')
  applies_to = models.ManyToManyField(Package, blank=True)
  applies_to_all = models.BooleanField(default=False,
      help_text='Applies to all packages')

  def __unicode__(self):
    return u'%s (%s)' % (self.description, self.name)

  def save(self, *args, **kwargs):
    validators.CheckAllCapsDigits(self.name, self)
    validators.CheckNotNegative(self.price, self)
    return super(Item, self).save(*args, **kwargs)


class TempOrder(models.Model):
  order_num = models.CharField(max_length=10, primary_key=True,
      help_text='Unique 10 upper-case letters + numbers code')
  sponsor = models.OneToOneField('Sponsor')
  date = models.DateTimeField(auto_now_add=True)

  def __unicode__(self):
    return '%s' % self.order_num

  def save(self, *args, **kwargs):
    validators.CheckValidOrderNumber(self.order_num, self)
    return super(TempOrder, self).save(*args, **kwargs)


class Sponsor(models.Model):
  # meta
  package = models.ForeignKey(Package)
  valid = models.BooleanField(default=False)

  # name
  salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES,
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
  promo = models.ForeignKey(PromoCode, blank=True, null=True)
  agreed = models.BooleanField(default=False)
  ordered_items = models.ManyToManyField(Item, blank=True)

  def package_cost(self):
    return Package.package_cost(self.package, self.ordered_items.all(),
                                self.promo)

  def full_name(self):
    return '%s - %s %s' % (self.org, self.first_name, self.last_name)

  def __unicode__(self):
    return u'%s (%s) ' % (self.id, self.email)
