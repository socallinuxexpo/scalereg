from django.db import models

# Create your models here.

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
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
  payment_type = models.CharField(maxlength=10)
  auth_code = models.CharField(maxlength=30)
  resp_msg = models.CharField(maxlength=60)
  result = models.CharField(maxlength=60)

  def __str__(self):
    return "%s (%s)" % (self.name, self.order_num)


class Ticket(models.Model):
  code = models.CharField(maxlength=1, primary_key=True)
  description = models.CharField(maxlength=60)
  price = models.FloatField(max_digits=5, decimal_places=2)

  def __str__(self):
    return self.description


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

  def __str__(self):
    return "%s %s (%s)" % (self.first_name, self.last_name, self.badge_id)


class Item(models.Model):
  name = models.CharField(maxlength=4)
  description = models.CharField(maxlength=60)

  price = models.FloatField(max_digits=5, decimal_places=2)

  active = models.BooleanField()
  pickup = models.BooleanField()

  def __str__(self):
    return self.description


class PromoCode(models.Model):
  name = models.CharField(maxlength=5)
  description = models.CharField(maxlength=60)

  price_modifier = models.FloatField(max_digits=3, decimal_places=2)

  active = models.BooleanField()
  start_date = models.DateField()
  expiration_date = models.DateField()

  def __str__(self):
    return self.description
