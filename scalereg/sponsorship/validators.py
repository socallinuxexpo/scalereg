from scalereg.common.validators import ScaleValidationError
from . import models
import string

def CheckValidStartStopDates(field_data, all_data):
  if all_data.start_date and all_data.end_date:
    if all_data.start_date > all_data.end_date:
      raise ScaleValidationError('Start date greater than End date')


def CheckPositive(field_data, all_data):
  if float(field_data) <= 0:
    raise ScaleValidationError('Value should be positive')


def CheckNotNegative(field_data, all_data):
  if float(field_data) < 0:
    raise ScaleValidationError('Value should not be negative')


def CheckAllCaps(field_data, all_data):
  for f in field_data:
    if f not in string.ascii_uppercase:
      raise ScaleValidationError('Value must be all upper-case')


def CheckAllCapsDigits(field_data, all_data):
  valid_letters = string.ascii_uppercase + string.digits
  for f in field_data:
    if f not in valid_letters:
      raise ScaleValidationError('Value must be all upper-case / digits')


def CheckValidOrderNumber(field_data, all_data):
  if len(field_data) != 10:
    raise ScaleValidationError('Value must be exactly 10 digits')
  CheckAllCapsDigits(field_data, all_data)


def CheckCommaSeparatedInts(field_data, all_data):
  csv = field_data.split(',')
  if not csv:
    raise ScaleValidationError('No data')
  try:
    for f in csv:
      int(f)
  except ValueError:
    raise ScaleValidationError('Not a number')
