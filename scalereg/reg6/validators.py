from scalereg.common.validators import ScaleValidationError
import models
import string

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
