from django import forms
from django.forms import inlineformset_factory
from .models import Specification, Step

class SpecificationForm(forms.ModelForm):
    class Meta:
        model = Specification
        fields = ['name', 'description']

StepFormSet = inlineformset_factory(Specification, Step, fields=('name', 'description', 'is_optional'), extra=3)
