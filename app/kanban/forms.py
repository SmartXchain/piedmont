from django import forms
from .models import Chemical
from django.utils.timezone import now

class ChemicalForm(forms.ModelForm):
    """Form for managing chemical inventory."""
    
    class Meta:
        model = Chemical
        fields = ['name', 'quantity', 'lot_number', 'expiry_date', 'coc_scan', 'reorder_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter chemical name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter stock quantity'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lot number'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'coc_scan': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Set reorder threshold'}),
        }

    def clean_expiry_date(self):
        """Ensure expiry date is in the future."""
        expiry_date = self.cleaned_data.get('expiry_date')
        if expiry_date and expiry_date < now().date():
            raise forms.ValidationError("Expiry date must be in the future.")
        return expiry_date

    def clean_quantity(self):
        """Ensure quantity is a positive number."""
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity
