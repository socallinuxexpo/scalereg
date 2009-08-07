from django.db import models

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
)


class Speaker(models.Model):
  # speaker name
  salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES,
                                blank=True)
  first_name = models.CharField(max_length=60)
  last_name = models.CharField(max_length=60)
  title = models.CharField(max_length=60, blank=True)
  org = models.CharField(max_length=60, blank=True)

  # contact info
  email = models.EmailField(unique=True)
  zip = models.CharField(max_length=20)
  phone = models.CharField(max_length=20, blank=True)

  # other info
  url = models.URLField(blank=True)
  bio = models.TextField(blank=True)
  signup_date = models.DateField(auto_now_add=True)

  # validation info
  valid = models.BooleanField(default=True)
  validation_code = models.CharField(max_length=10, unique=True)

  class Meta:
    permissions = (('view_speaker', 'Can view speakers'),)

  def __unicode__(self):
    return u'%s: %s %s' % (self.email, self.first_name, self.last_name)
