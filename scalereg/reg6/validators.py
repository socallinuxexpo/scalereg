from django.conf import settings
from scalereg.common.validators import ScaleValidationError
import hashlib
from . import models
import string

HASH_LENGTH = 6

def hashfunc(data):
  data = settings.SCALEREG_EXPRESS_CHECKIN_SECRET + data.encode('utf-8')
  return hashlib.sha1(data).hexdigest()


def hashAttendee(attendee):
  return hashfunc(attendee.first_name + attendee.last_name)[:HASH_LENGTH]


def isValidScannedBadge(field_data, all_data):
  if not field_data:
    raise ScaleValidationError('Invalid hash object')
  attendee_hash = field_data[-1]
  try:
    attendee_id = int(field_data[:-1])
    attendee = models.Attendee.objects.get(id=attendee_id)
    if not attendee.valid:
      raise ScaleValidationError('Invalid attendee')

    parity = 0
    for f in hashAttendee(attendee):
      parity += int(f, 16)
    if attendee_hash != str(parity % 10):
      raise ScaleValidationError('Incorrect hash')
  except ValueError:
    raise ScaleValidationError('Not a number')
  except models.Attendee.DoesNotExist:
    raise ScaleValidationError('Attendee does not exist')


def isValidStartStopDates(field_data, all_data):
  if all_data.start_date and all_data.end_date:
    if all_data.start_date > all_data.end_date:
      raise ScaleValidationError('Start date greater than End date')


def isPositive(field_data, all_data):
  if float(field_data) <= 0:
    raise ScaleValidationError('Value should be positive')


def isNotNegative(field_data, all_data):
  if float(field_data) < 0:
    raise ScaleValidationError('Value should not be negative')


def isAllCaps(field_data, all_data):
  for f in field_data:
    if f not in string.ascii_uppercase:
      raise ScaleValidationError('Value must be all upper-case')


def isAllCapsDigits(field_data, all_data):
  valid_letters = string.ascii_uppercase + string.digits
  for f in field_data:
    if f not in valid_letters:
      raise ScaleValidationError('Value must be all upper-case / digits')


def isValidOrderNumber(field_data, all_data):
  if len(field_data) != 10:
    raise ScaleValidationError('Value must be exactly 10 digits')
  isAllCapsDigits(field_data, all_data)


def isValidAttendeeCheckin(field_data, all_data):
  if field_data == 'on':
    if 'valid' not in all_data:
      raise ScaleValidationError('Cannot check in invalid attendee')


def isCommaSeparatedInts(field_data, all_data):
  csv = field_data.split(',')
  if not csv:
    raise ScaleValidationError('No data')
  try:
    for f in csv:
      int(f)
  except ValueError:
    raise ScaleValidationError('Not a number')


def isValidTempOrder(field_data, all_data):
  isValidOrderNumber(all_data.order_num, all_data)
  if all_data.attendees:
    isCommaSeparatedInts(all_data.attendees, all_data)
