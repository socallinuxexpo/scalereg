from scalereg.common.validators import ScaleValidationError
from scalereg.reg6 import models
import sha

def hash(data):
  return sha.new('SECRET' + data).hexdigest()

def isValid7XHash(field_data, all_data):
  if not field_data:
    raise ScaleValidationError('Invalid hash object')
  if len(field_data) != 10:
    raise ScaleValidationError('Value must be exactly 10 digits')
  for i in field_data[:6]:
    if i not in '0123456789abcdef':
      raise ScaleValidationError('Invalid hash')
  try:
    id = int(field_data[6:])
    attendee = models.Attendee.objects.get(id=id)
    if not attendee.valid or not attendee.checked_in:
      raise ScaleValidationError('Invalid attendee')
    if field_data[:6] != hash(attendee.first_name + attendee.last_name)[:6]:
      raise ScaleValidationError('Incorrect hash')
  except ValueError:
    raise ScaleValidationError('Not a number')
  except models.Attendee.DoesNotExist:
    raise ScaleValidationError('Attendee does not exist')
