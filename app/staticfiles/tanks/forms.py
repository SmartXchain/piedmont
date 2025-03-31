from django import forms
from .models import Tank, ProductionLine


class TankForm(forms.ModelForm):
    """Form for managing tank details."""

    class Meta:
        model = Tank
        fields = [
            'name', 'production_line', 'chemical_composition',
            'length', 'width', 'height', 'liquid_level',
            'max_amps', 'is_vented', 'scrubber_system'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tank name'}),
            'production_line': forms.Select(attrs={'class': 'form-select'}),
            'chemical_composition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter chemical composition'}),
            'length': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter length in inches'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter width in inches'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter height in inches'}),
            'liquid_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter liquid level from top'}),
            'max_amps': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter max amps'}),
            'is_vented': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scrubber_system': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter scrubber system details'}),
        }

    def __init__(self, *args, **kwargs):
        """Ensure that production line choices are populated dynamically."""
        super().__init__(*args, **kwargs)
        self.fields['production_line'].choices = ProductionLine._meta.get_field('name').choices
