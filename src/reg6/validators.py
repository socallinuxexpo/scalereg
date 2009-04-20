from django.core import validators

def isValidStartStopDates(field_data, all_data):
  if all_data['start_date'] and all_data['end_date']:
    if all_data['start_date'] > all_data['end_date']:
      raise validators.ValidationError('Start date greater than End date')

def isPositive(field_data, all_data):
  if float(field_data) < 0:
    raise validators.ValidationError('Value should be positive')

def isNotNegative(field_data, all_data):
  if float(field_data) <= 0:
    raise validators.ValidationError('Value should be positive')
