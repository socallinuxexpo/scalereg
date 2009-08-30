from django.db import models

SALUTATION_CHOICES = (
  ('Mr', 'Mr.'),
  ('Ms', 'Ms.'),
  ('Mrs', 'Mrs.'),
  ('Dr', 'Dr.'),
)

# Some of the following three choices originally came from utos-conman's
# speakers/models.py @ r378.

STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Denied', 'Denied'),
    ('Cancelled', 'Speaker Cancelled'),
    ('Alternate', 'Alternate'),
    ('Approved', 'Approved'),
)

AUDIENCE_CHOICES = (
    ('Everyone', 'Everyone'),
    ('Beginner', 'Beginner'),
    ('Intermediate', 'Intermediate'),
    ('Advanced', 'Advanced'),
)

CATEGORY_CHOICES = (
    ('General', 'General'),
    ('Business', 'Business'),
    ('Technology', 'Technology'),
    ('Community', 'Community'),
    ('Educational', 'Educational'),
)

class Speaker(models.Model):
  # administrative contact info
  contact_name = models.CharField(max_length=60)
  contact_email = models.EmailField(unique=True)

  # speaker name
  salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES,
                                blank=True)
  first_name = models.CharField(max_length=60)
  last_name = models.CharField(max_length=60)
  title = models.CharField(max_length=60, blank=True)
  org = models.CharField(max_length=60, blank=True)

  # speaker contact info
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


class Audience(models.Model):
  name = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, unique=True)

  def __unicode__(self):
    return u'%s' % self.name


class Category(models.Model):
  name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)

  class Meta:
    verbose_name_plural = 'categories'

  def __unicode__(self):
    return u'%s' % self.name


class Presentation(models.Model):
  speaker = models.ForeignKey(Speaker)
  # not strictly needed, convenience items to put on the form
  contact_email = models.EmailField()
  speaker_code = models.CharField(max_length=10)

  # categories
  categories = models.ManyToManyField(Category)
  audiences = models.ManyToManyField(Audience)

  # presentation data
  title = models.CharField(max_length=150, unique=True)
  description = models.CharField(max_length=255)
  short_abstract = models.TextField(max_length=1000)
  long_abstract = models.TextField(max_length=10000, blank=True)
  msg = models.TextField(max_length=1000, blank=True)
  file = models.FileField(upload_to='scale/simple_cfp/%Y%m%d-%H%M%S/',
                          blank=True)

  # validation info
  valid = models.BooleanField(default=True)
  submission_code = models.CharField(max_length=10)

  # private data
  submit_date = models.DateField(auto_now_add=True)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                            default='Pending')
  score = models.IntegerField(default=0)
  notes = models.TextField(max_length=1000, blank=True)

  class Meta:
    permissions = (('view_presentations', 'Can view presentations'),)

  def __unicode__(self):
    return u'(%s) - %s' % (self.speaker, self.title)
