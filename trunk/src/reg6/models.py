from django.db import models

# Create your models here.

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
)

PAYMENT_CHOICES = (
  ('verisign', 'Verisign'),
  ('google', 'Google Checkout'),
  ('cash', 'Cash'),
  ('invitee', 'Invitee'),
  ('exhibitor', 'Exhibitor'),
  ('speaker', 'Speaker'),
  ('press', 'Press'),
)

TICKET_CHOICES = (
  ('expo', 'Expo Only'),
  ('full', 'Full'),
  ('press', 'Press'),
  ('speaker', 'Speaker'),
  ('exhibitor', 'Exhibitor'),
)

class Order(models.Model):
  # basic info
  date = models.DateTimeField(auto_now_add=True)
  order_num = models.CharField(maxlength=10, primary_key=True,
    help_text='Unique 10 digit alphanumeric code')
  valid = models.BooleanField()

  # name and address
  name = models.CharField(maxlength=120)
  address = models.CharField(maxlength=120)
  city = models.CharField(maxlength=60)
  state = models.CharField(maxlength=60)
  zip = models.PositiveIntegerField(maxlength=10)
  country = models.CharField(maxlength=60)

  # contact info
  email = models.EmailField()
  phone = models.CharField(maxlength=20, blank=True)

  # payment info
  amount = models.FloatField(max_digits=4, decimal_places=2)
  payment_type = models.CharField(maxlength=10, choices=PAYMENT_CHOICES)
  auth_code = models.CharField(maxlength=30, blank=True,
    help_text='Only used by Verisign')
  resp_msg = models.CharField(maxlength=60, blank=True,
    help_text='Only used by Verisign')
  result = models.CharField(maxlength=60, blank=True,
    help_text='Only used by Verisign')

  class Admin:
    fields = (
      ('Billing Info', {'fields': ('name', 'address', 'city', 'state', 'zip', 'country')}),
      ('Contact Info', {'fields': ('email', 'phone')}),
      ('Order Info', {'fields': ('order_num', 'valid')}),
      ('Payment Info', {'fields': ('amount', 'payment_type', 'auth_code', 'resp_msg', 'result')}),
    )
    list_display = ('order_num', 'date', 'name', 'address', 'city', 'state', 'zip', 'country', 'email', 'phone', 'amount', 'payment_type', 'valid')
    list_filter = ('date', 'payment_type', 'valid')

  class Meta:
    permissions = (('view_order', 'Can view order'),)

  def __str__(self):
    return "%s" % self.order_num


class Ticket(models.Model):
  name = models.CharField(maxlength=60, primary_key=True)
  type = models.CharField(maxlength=10, choices=TICKET_CHOICES)
  price = models.FloatField(max_digits=5, decimal_places=2)
  public = models.BooleanField(help_text='Publicly available on the order page')
  start_date = models.DateField(null=True, blank=True,
    help_text='Available on this day')
  end_date = models.DateField(null=True, blank=True,
    help_text='Not Usable on this day')

  class Admin:
    list_display = ('name', 'type', 'price', 'start_date', 'end_date')
    list_filter = ('public', 'start_date', 'end_date')

  class Meta:
    permissions = (('view_ticket', 'Can view ticket'),)

  def __str__(self):
    return "%s" % self.name


class PromoCode(models.Model):
  name = models.CharField(maxlength=5)
  description = models.CharField(maxlength=60)

  price_modifier = models.FloatField(max_digits=3, decimal_places=2,
    help_text='This is the price multiplier, i.e. for 0.4, $10 becomes $4.')
  applies_to = models.ManyToManyField(Ticket)
  active = models.BooleanField()
  start_date = models.DateField(null=True, blank=True,
    help_text='Available on this day')
  end_date = models.DateField(null=True, blank=True,
    help_text='Not Usable on this day')

  class Admin:
    list_display = ('name', 'description', 'price_modifier', 'active', 'start_date', 'end_date')
    list_filter = ('active', 'start_date', 'end_date')

  class Meta:
    permissions = (('view_promocode', 'Can view promo code'),)

  def __str__(self):
    return self.description


class Attendee(models.Model):
  # badge info
  badge_id = models.PositiveIntegerField(maxlength=5, primary_key=True,
    help_text='5 digit badge id, must be unique')
  badge_type = models.ForeignKey(Ticket)
  valid = models.BooleanField()
  checked_in = models.BooleanField()
  ordered_items = models.CharField(maxlength=60, blank=True,
    help_text='comma separated list of items')
  obtained_items = models.CharField(maxlength=60, blank=True,
    help_text='comma separated list of items')

  # attendee name
  salutation = models.CharField(maxlength=10, choices=SALUTATION_CHOICES)
  first_name = models.CharField(maxlength=60)
  last_name = models.CharField(maxlength=60)
  title = models.CharField(maxlength=60, blank=True)
  org = models.CharField(maxlength=60, blank=True)

  # contact info
  email = models.EmailField(unique=True, help_text='Must be unique')
  phone = models.CharField(maxlength=20, blank=True)

  # etc
  survey_answers = models.CharField(maxlength=60,
    help_text='comma separated list of key=value')
  order = models.ForeignKey(Order)

  class Admin:
    fields = (
      ('Attendee Info', {'fields': ('salutation', 'first_name', 'last_name', 'title', 'org')}),
      ('Contact Info', {'fields': ('email', 'phone')}),
      ('Badge Info', {'fields': ('badge_id', 'badge_type', 'valid', 'checked_in')}),
      ('Items', {'fields': ('ordered_items', 'obtained_items')}),
      ('Misc', {'fields': ('survey_answers', 'order')}),
    )
    list_display = ('badge_id', 'first_name', 'last_name', 'email', 'badge_type', 'valid', 'checked_in', 'ordered_items', 'obtained_items', 'order')
    list_filter = ('order', 'badge_type', 'valid', 'checked_in')

  class Meta:
    permissions = (('view_attendee', 'Can view attendee'),)

  def __str__(self):
    return "%s %s (%s)" % (self.first_name, self.last_name, self.badge_id)


class Item(models.Model):
  name = models.CharField(maxlength=4, help_text='up to 4 letters')
  description = models.CharField(maxlength=60)

  price = models.FloatField(max_digits=5, decimal_places=2)

  active = models.BooleanField()
  pickup = models.BooleanField(help_text='Can we track if this item gets picked up?')
  applies_to = models.ManyToManyField(Ticket)

  class Admin:
    list_display = ('name', 'description', 'price', 'active', 'pickup')
    list_filter = ('active', 'pickup')

  class Meta:
    permissions = (('view_item', 'Can view item'),)

  def __str__(self):
    return self.description
