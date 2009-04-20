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
  date = models.DateTimeField()
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
  amount = models.PositiveIntegerField()
  payment_type = models.CharField(maxlength=10)
  auth_code = models.CharField(maxlength=30)
  resp_msg = models.CharField(maxlength=60)
  result = models.CharField(maxlength=60)


class Ticket(models.Model):
  code = models.CharField(maxlength=1, primary_key=True)
  description = models.CharField(maxlength=60)
  price = models.PositiveIntegerField()


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


class Item(models.Model):
  name = models.CharField(maxlength=4)
  description = models.CharField(maxlength=60)
  price = models.PositiveIntegerField()
  active = models.BooleanField()
  pickup = models.BooleanField()


class PromoCode(models.Model):
  name = models.CharField(maxlength=5)
