from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.

class Service(models.Model):
  # basic info
  # FIXME don't use this as the primary key
  name = models.CharField(maxlength=60, primary_key=True)
  url = models.CharField(maxlength=120, help_text='absolute url, no trailing /')
  active = models.BooleanField()
  users = models.ManyToManyField(User, blank=True)
  groups = models.ManyToManyField(Group, blank=True)

  class Admin:
    list_display = ('name', 'active', 'url')
    #list_filter = ('date', 'payment_type', 'valid')

  def __str__(self):
    return "%s" % self.name
