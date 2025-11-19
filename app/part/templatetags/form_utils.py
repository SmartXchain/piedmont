from django import template
# Note: You need to import the BoundField class to check the type
from django.forms.fields import BoundField 

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    # Check if the object is a BoundField (the kind you get from {{ form.field_name }})
    if isinstance(field, BoundField):
        # We modify the widget's attributes directly
        existing_classes = field.field.widget.attrs.get('class', '')
        new_classes = existing_classes + ' ' + css_class
        field.field.widget.attrs['class'] = new_classes.strip()
        
        # We return the field itself so it can be rendered later (e.g., using {{ field }})
        return field
    
    # If it's not a BoundField (or a different type), just return the object unchanged
    return field

@register.filter(name='split')
def split(value, arg=','):
    """Splits a string by the given argument (defaulting to a comma)."""
    return value.split(arg)

@register.filter(name='get_field')
def get_field(form, field_name):
    """
    Dynamically retrieves a Bound Field from the form.
    Note: Must be used with {{ form|get_field:field_name }}
    """
    # The form instance (first argument) already holds Bound Fields indexed by name.
    return form[field_name]
