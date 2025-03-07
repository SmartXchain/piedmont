from django import forms
from .models import Fixture


class FixtureForm(forms.ModelForm):
    """Form for managing fixture inventory."""

    class Meta:
        model = Fixture
        fields = ['name', 'max_amps', 'drawing', 'quantity_available', 'fixtures_due_for_repair', 'inspection_schedule', 'repair_notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter fixture name'}),
            'max_amps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max Amps'}),
            'drawing': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'quantity_available': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'fixtures_due_for_repair': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fixtures needing repair'}),
            'inspection_schedule': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'repair_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter repair notes'}),
        }
