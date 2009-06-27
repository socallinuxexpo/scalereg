from django.db import models
from django.contrib.auth.models import User, Group

# Create your models here.

class Service(models.Model):
  # basic info
  # FIXME don't use this as the primary key
  name = models.CharField(max_length=60, primary_key=True)
  url = models.CharField(max_length=120, help_text='absolute url, no trailing /')
  active = models.BooleanField()
  users = models.ManyToManyField(User, blank=True)
  groups = models.ManyToManyField(Group, blank=True)

  def __unicode__(self):
    return u'%s' % self.name
