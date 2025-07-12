from django import template

register = template.Library()


@register.filter
def money(value):
    try:
        f_value = float(value)
        return f'${f_value:.2f}'
    except ValueError:
        return value
