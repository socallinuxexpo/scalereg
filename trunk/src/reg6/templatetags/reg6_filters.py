# Create your views here.

from django import template

register = template.Library()

@register.filter
def money(value):
    value = float(value)
    return '$%0.2f' % value
