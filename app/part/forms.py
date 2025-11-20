# admin/forms.py
from django import forms
from part.models import PartStandard, WorkOrder, Part
from standard.models import Standard, Classification


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number', 'rework', 'job_identity', 'standard',
            'classification', 'surface_repaired', 'customer',
            'purchase_order_with_revision', 'part_quantity',
            'serial_or_lot_numbers', 'surface_area',
            'requires_masking', 'requires_stress_relief',
            'requires_hydrogen_relief',
        ]
        widgets = {
            'serial_or_lot_numbers': forms.Textarea(attrs={'rows': 2}),
            # These widgets are correctly defined for Bootstrap switch styling
            'requires_masking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_stress_relief': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_hydrogen_relief': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        part = kwargs.pop('part', None)
        super().__init__(*args, **kwargs)

        if part:
            # 1. Fetch PartStandard records efficiently
            part_standards = PartStandard.objects.filter(part=part).select_related('standard', 'classification')

            # 2. Collect unique Standard IDs and Classification IDs
            standard_ids = part_standards.values_list('standard_id', flat=True).distinct()
            
            # Filter out NULL classification IDs before filtering the Classification model
            classification_ids = part_standards.values_list('classification_id', flat=True).filter(classification_id__isnull=False).distinct()

            # 3. Apply the filtered querysets
            self.fields['standard'].queryset = Standard.objects.filter(id__in=standard_ids)
            self.fields['classification'].queryset = Classification.objects.filter(id__in=classification_ids)

            # 4. Set initial values if only one PartStandard exists
            if part_standards.count() == 1:
                single_part_standard = part_standards.first()
                self.fields['standard'].initial = single_part_standard.standard
                self.fields['classification'].initial = single_part_standard.classification


class PartForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_number', 'part_description', 'part_revision']
        widgets = {
            'part_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Part Number'}),
            'part_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Description'}),
            'part_revision': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Revision'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        part_number = cleaned_data.get('part_number')
        part_revision = cleaned_data.get('part_revision')

        if part_number and part_revision:
            if Part.objects.filter(part_number=part_number, part_revision=part_revision).exists():
                self._duplicate_exists = True  # Flag for the view
        return cleaned_data


class PartStandardForm(forms.ModelForm):
    class Meta:
        model = PartStandard
        fields = ['standard', 'classification']
        widgets = {
            'standard': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['classification'].queryset = Classification.objects.none()

        standard_id = None
        
        # Determine standard ID from POST data or existing instance
        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.standard:
            standard_id = self.instance.standard_id

        if standard_id is not None:
            self.fields['classification'].queryset = Classification.objects.filter(standard_id=standard_id)

        # Corrected: Use safer getattr and removed the incorrect 'method' reference
        self.fields['classification'].label_from_instance = lambda obj: (
             f"Class: {getattr(obj, 'class_name', '—')}, Type: {getattr(obj, 'type', '—')}"
        )
