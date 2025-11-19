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
            'requires_masking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_stress_relief': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_hydrogen_relief': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        part = kwargs.pop('part', None)
        super().__init__(*args, **kwargs)

        if part:
            # 1. Fetch the PartStandard records once for efficiency
            part_standards = PartStandard.objects.filter(part=part).select_related('standard', 'classification')

            # 2. Collect unique Standard IDs and Classification IDs
            standard_ids = part_standards.values_list('standard_id', flat=True).distinct()
            classification_ids = part_standards.values_list('classification_id', flat=True).distinct()

            # 3. Apply the filtered querysets
            self.fields['standard'].queryset = Standard.objects.filter(id__in=standard_ids)
            
            # IMPROVEMENT: Filter classifications including NULLs if the PartStandard model allows it
            # The current classification IDs list contains the PKs of assigned classifications, 
            # but if a PartStandard has a NULL classification, this list won't include it. 
            # However, since Django automatically handles the NULL choice for nullable FKs, 
            # this is okay as long as you intend for the user to ONLY pick from assigned non-null classifications.
            self.fields['classification'].queryset = Classification.objects.filter(id__in=classification_ids)

            # 4. Set initial values if only one PartStandard exists
            if part_standards.count() == 1:
                # Use the prefetched/selected instance from the initial queryset
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
            # Don't raise error here — we want the view to handle redirect
            if Part.objects.filter(part_number=part_number, part_revision=part_revision).exists():
                # Just return cleaned_data without error to avoid form error display
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
        # Pull the standard from the form data if available
        super().__init__(*args, **kwargs)

        self.fields['classification'].queryset = Classification.objects.none()

        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                self.fields['classification'].queryset = Classification.objects.filter(standard_id=standard_id)
            except (ValueError, TypeError):
                pass  # Invalid input; fallback to empty queryset

        elif self.instance.pk and self.instance.standard:
            self.fields['classification'].queryset = Classification.objects.filter(standard=self.instance.standard)

        # Optional: pretty labels
        self.fields['classification'].label_from_instance = lambda obj: (
            f"Method: {obj.method or '—'}, Class: {obj.class_name or '—'}, Type: {obj.type or '—'}"
        )
