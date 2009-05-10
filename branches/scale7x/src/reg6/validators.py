from django.core import validators
import models
import string

def isValidStartStopDates(field_data, all_data):
  if all_data['start_date'] and all_data['end_date']:
    if all_data['start_date'] > all_data['end_date']:
      raise validators.ValidationError('Start date greater than End date')


def isPositive(field_data, all_data):
  if float(field_data) <= 0:
    raise validators.ValidationError('Value should be positive')


def isNotNegative(field_data, all_data):
  if float(field_data) < 0:
    raise validators.ValidationError('Value should not be negative')


def isValidObtainedItems(field_data, all_data):
  obtained_items = {}
  for f in field_data.replace(' ', '').split(','):
    if not f:
      raise validators.ValidationError('Value cannot be parsed')
    if f in obtained_items:
      raise validators.ValidationError('Item listed twice')
    obtained_items[f] = None

  obj = models.Attendee.objects.get(id=all_data['id'])
  for item in obj.ordered_items.all():
    if item.name in obtained_items:
      del obtained_items[item.name]

  num_invalid_items = len(obtained_items)
  if num_invalid_items:
    invalid_items = ', '.join(obtained_items.keys())
    if num_invalid_items > 1:
      plural = 's'
    else:
      plural = ''
    raise validators.ValidationError('Item%s not found: %s' %
      (plural, invalid_items))


def isAllCaps(field_data, all_data):
  for f in field_data:
    if f not in string.ascii_uppercase:
      raise validators.ValidationError('Value must be all upper-case')


def isAllCapsDigits(field_data, all_data):
  valid_letters = string.ascii_uppercase + string.digits
  for f in field_data:
    if f not in valid_letters:
      raise validators.ValidationError('Value must be all upper-case / digits')


def isValidOrderNumber(field_data, all_data):
  if len(field_data) != 10:
    raise validators.ValidationError('Value must be exactly 10 digits')
  isAllCapsDigits(field_data, all_data)


def isValidAttendeeCheckin(field_data, all_data):
  if field_data == 'on':
    if 'valid' not in all_data:
      raise validators.ValidationError('Cannot check in invalid attendee')


def isCommaSeparatedInts(field_data, all_data):
  csv = field_data.split(',')
  if not csv:
    raise validators.ValidationError('No data')
  try:
    for f in csv:
      int(f)
  except ValueError:
    raise validators.ValidationError('Not a number')


def isQuestionsUnique(field_data, all_data):
  questions = []
  for id in field_data:
    answer = models.Answer.objects.get(id=id)
    if answer.question in questions:
      raise validators.ValidationError('Question cannot have multiple answers')
    questions.append(answer.question)
