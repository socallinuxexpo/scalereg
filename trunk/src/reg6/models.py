from django.db import models

# Create your models here.

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
)

PAYMENT_CHOICES = (
  ('VS', 'Verisign'),
  ('GC', 'Google Checkout'),
  ('CS', 'Cash'),
  ('IV', 'Invitee'),
  ('EX', 'Exhibitor'),
  ('SP', 'Speaker'),
  ('PR', 'Press'),
)

TICKET_CHOICES = (
  ('e', 'Expo Only'),
  ('r', 'Full'),
  ('p', 'Press'),
  ('s', 'Speaker'),
  ('x', 'Exhibitor'),
)
class Order(models.Model):
  # basic info
  date = models.DateTimeField(auto_now_add=True)
  order_num = models.CharField(maxlength=10, primary_key=True)
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
  payment_type = models.CharField(maxlength=2, choices=PAYMENT_CHOICES)
  auth_code = models.CharField(maxlength=30, blank=True)
  resp_msg = models.CharField(maxlength=60, blank=True)
  result = models.CharField(maxlength=60, blank=True)

  class Admin:
    fields = (
      ('Attendee Info', {'fields': ('name', 'address', 'city', 'state', 'zip', 'country')}),
      ('Contact Info', {'fields': ('email', 'phone')}),
      ('Order Info', {'fields': ('order_num', 'valid')}),
      ('Payment Info', {'fields': ('amount', 'payment_type', 'auth_code', 'resp_msg', 'result')}),
    )
    list_display = ('name', 'address', 'city', 'state', 'zip', 'country')

  def __str__(self):
    return "%s (%s)" % (self.name, self.order_num)


class Ticket(models.Model):
  code = models.CharField(maxlength=1, primary_key=True, choices=TICKET_CHOICES)
  price = models.FloatField(max_digits=5, decimal_places=2)

  class Admin:
    pass

  def __str__(self):
    return self.code


class Attendee(models.Model):
  # badge info
  badge_id = models.PositiveIntegerField(maxlength=5, primary_key=True)
  badge_type = models.ForeignKey(Ticket)
  valid = models.BooleanField()
  checked_in = models.BooleanField()
  ordered_items = models.CharField(maxlength=60, blank=True)
  obtained_items = models.CharField(maxlength=60, blank=True)

  # attendee name
  salutation = models.CharField(maxlength=10, choices=SALUTATION_CHOICES)
  first_name = models.CharField(maxlength=60)
  last_name = models.CharField(maxlength=60)
  title = models.CharField(maxlength=60, blank=True)
  org = models.CharField(maxlength=60, blank=True)

  # contact info
  email = models.EmailField(unique=True)
  phone = models.CharField(maxlength=20, blank=True)

  # etc
  survey_answers = models.CharField(maxlength=60)
  order = models.ForeignKey(Order)

  class Admin:
    fields = (
      ('Attendee Info', {'fields': ('salutation', 'first_name', 'last_name', 'title', 'org')}),
      ('Contact Info', {'fields': ('email', 'phone')}),
      ('Badge Info', {'fields': ('badge_id', 'badge_type', 'valid', 'checked_in')}),
      ('Items', {'fields': ('ordered_items', 'obtained_items')}),
      ('Misc', {'fields': ('survey_answers', 'order')}),
    )

  def __str__(self):
    return "%s %s (%s)" % (self.first_name, self.last_name, self.badge_id)


class Item(models.Model):
  name = models.CharField(maxlength=4)
  description = models.CharField(maxlength=60)

  price = models.FloatField(max_digits=5, decimal_places=2)

  active = models.BooleanField()
  pickup = models.BooleanField()

  class Admin:
    pass

  def __str__(self):
    return self.description


class PromoCode(models.Model):
  name = models.CharField(maxlength=5)
  description = models.CharField(maxlength=60)

  price_modifier = models.FloatField(max_digits=3, decimal_places=2)

  active = models.BooleanField()
  start_date = models.DateField()
  expiration_date = models.DateField()

  class Admin:
    pass

  def __str__(self):
    return self.description
