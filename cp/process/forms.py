from django import forms
from .models import TechnicalSheet
from parts.models import Part
from specifications.models import Specification, Step

class TechnicalSheetForm(forms.ModelForm):
    class Meta:
        model = TechnicalSheet
        fields = ['part', 'specifications', 'instructions', 'tools_required', 'safety_precautions']

class SelectReworkStepsForm(forms.Form):
    part = forms.ModelChoiceField(queryset=Part.objects.all(), label="Select Part")
    specification = forms.ModelChoiceField(queryset=Specification.objects.all(), label="Select Specification")
    steps = forms.ModelMultipleChoiceField(
        queryset=Step.objects.filter(is_optional=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Optional Steps for Rework"
    )