from django.conf import settings
from scalereg.common.validators import ScaleValidationError
from scalereg.reg6 import models
import hashlib
import string

HASH_LENGTH = 6

def hashfunc(data):
  data = settings.SCALEREG_SPEAKERSURVEY_SECRET + data.encode('utf-8')
  return hashlib.sha1(data).hexdigest().upper()

def hashAttendee(attendee):
  return hashfunc(attendee.first_name + attendee.last_name)[:HASH_LENGTH]

def isValid7XHash(field_data, all_data):
  if not field_data:
    raise ScaleValidationError('Invalid hash object')
  if len(field_data) != 10:
    raise ScaleValidationError('Value must be exactly 10 digits')
  attendee_hash = field_data[:HASH_LENGTH].upper()
  for i in attendee_hash:
    if i not in string.hexdigits:
      raise ScaleValidationError('Invalid hash')
  try:
    attendee_id = int(field_data[HASH_LENGTH:])
    attendee = models.Attendee.objects.get(id=attendee_id)
    if not attendee.valid or not attendee.checked_in:
      raise ScaleValidationError('Invalid attendee')
    if attendee_hash != hashAttendee(attendee):
      raise ScaleValidationError('Incorrect hash')
  except ValueError:
    raise ScaleValidationError('Not a number')
  except models.Attendee.DoesNotExist:
    raise ScaleValidationError('Attendee does not exist')
