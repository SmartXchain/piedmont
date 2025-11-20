from django import template

register = template.Library()


@register.filter
def split(value, arg=','):
    """
    Splits a string by the given argument (defaulting to a comma).
    Used to iterate over lists of field names in templates.
    """
    return value.split(arg)
