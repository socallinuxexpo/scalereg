from django.core import validators
from scalereg.reg6 import models
import sha

def hash(data):
  return sha.new('SECRET' + data).hexdigest()

def isValid7XHash(field_data, all_data):
  if not field_data:
    raise validators.ValidationError('Invalid hash object')
  if len(field_data) != 10:
    raise validators.ValidationError('Value must be exactly 10 digits')
  for i in field_data[:6]:
    if i not in '0123456789abcdef':
      raise validators.ValidationError('Invalid hash')
  try:
    id = int(field_data[6:])
    attendee = models.Attendee.objects.get(id=id)
    if not attendee.valid or not attendee.checked_in:
      raise validators.ValidationError('Invalid attendee')
    if field_data[:6] != hash(attendee.first_name + attendee.last_name)[:6]:
      raise validators.ValidationError('Incorrect hash')
  except ValueError:
    raise validators.ValidationError('Not a number')
  except models.Attendee.DoesNotExist:
    raise validators.ValidationError('Attendee does not exist')
