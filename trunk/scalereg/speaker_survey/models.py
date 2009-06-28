from django.core.exceptions import FieldError
from django.db import DatabaseError
from django.db import models
from django.forms import ModelForm
from scalereg.speaker_survey import validators

VALUE_CHOICES = (
  ('0sd', 'Strongly Disagree'),
  ('1di', 'Disagree'),
  ('2ne', 'Neutral'),
  ('3ag', 'Agree'),
  ('4sa', 'Strongly Agree'),
)

class Speaker(models.Model):
  name = models.CharField(max_length=100)
  title = models.CharField(max_length=200)
  url = models.URLField(max_length=200, blank=True)

  def __unicode__(self):
    return u'%s: %s' % (self.name, self.title)


class Survey7X(models.Model):
  hash = models.CharField(max_length=10)
  speaker = models.ForeignKey(Speaker)
  q00 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Speaker was easy to understand')
  q01 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Speaker had good presentation skills')
  q02 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Speaker was properly prepared')
  q03 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Speaker was sufficiently knowledgeable')
  q04 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Speaker provided enough time for Q&A')
  q05 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='I would attend another session by speaker')
  q06 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='I would recommend speaker')
  q07 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='This presentation met my expectations')
  q08 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='The technical level met my expectations')
  q09 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Would Recommend Presentation')
  q10 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Presentation Was Applicable to Real World')
  q11 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Presentation Slides were Useful')
  q12 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='AV aids were easy to hear & see')
  q13 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Would like similar topics in future')
  q14 = models.CharField(max_length=3, choices=VALUE_CHOICES, default='2ne',
                         help_text='Presentation was commercial in nature')
  comments = models.TextField(blank=True)

  class Meta:
    permissions = (('view_survey', 'Can view survey'),)
    unique_together = (('hash', 'speaker'),)

  def __unicode__(self):
    return u'%s - %s' % (self.hash, self.speaker)

  def help_text(self):
    r = []
    for i in xrange(0, 15):
      r.append(self._meta.get_field('q%02d' % i).help_text)
    return r

  def save(self, *args, **kwargs):
    validators.isValid7XHash(self.hash, self)
    return super(Survey7X, self).save(*args, **kwargs)


class Survey7XForm(ModelForm):
  class Meta:
    model = Survey7X
    fields = (
      'q00',
      'q01',
      'q02',
      'q03',
      'q04',
      'q05',
      'q06',
      'q07',
      'q08',
      'q09',
      'q10',
      'q11',
      'q12',
      'q13',
      'q14',
      'comments',
    )
