from django import forms
from .models import Product, ChemicalLot
from django.utils.timezone import now


class ProductForm(forms.ModelForm):
    """Form for managing master product details including stock thresholds and supplier info."""

    class Meta:
        model = Product
        fields = ['name', 'supplier_name', 'supplier_part_number', 'min_quantity', 'max_quantity', 'trigger_level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter supplier name'}),
            'supplier_part_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter supplier part number'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum stock level'}),
            'max_quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter maximum stock level'}),
            'trigger_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Set reorder trigger level'}),
        }

    def clean_min_quantity(self):
        """Ensure minimum quantity is not negative."""
        min_quantity = self.cleaned_data.get('min_quantity')
        if min_quantity < 0:
            raise forms.ValidationError("Minimum quantity cannot be negative.")
        return min_quantity

    def clean_max_quantity(self):
        """Ensure max quantity is greater than min quantity."""
        min_quantity = self.cleaned_data.get('min_quantity')
        max_quantity = self.cleaned_data.get('max_quantity')
        if max_quantity < min_quantity:
            raise forms.ValidationError("Maximum quantity must be greater than or equal to the minimum quantity.")
        return max_quantity


class ChemicalLotForm(forms.ModelForm):
    """Form for managing chemical lot entries linked to a product."""

    expiry_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    class Meta:
        model = ChemicalLot
        fields = ['product', 'purchase_order', 'lot_number', 'expiry_date', 'quantity', 'coc_scan', 'used_up']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'purchase_order': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter PO number'}),
            'lot_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lot number'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}),
            'coc_scan': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'used_up': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_expiry_date(self):
        """Ensure expiry date is in the future or allow N/A."""
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
