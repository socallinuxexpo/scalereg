# Create your views here.

from django import template

register = template.Library()

@register.filter
def money(value):
  try:
    f_value = float(value)
    return '$%0.2f' % f_value
  except ValueError:
    return value
