# admin/forms.py
from django import forms
from part.models import PartStandard, WorkOrder
from standard.models import Standard, Classification


class PartStandardForm(forms.ModelForm):
    class Meta:
        model = PartStandard
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Custom label for classifications showing method/class/type and standard name
        self.fields['classification'].label_from_instance = lambda obj: (
            f"Method: {obj.method or '—'}, Class: {obj.class_name or '—'}, Type: {obj.type or '—'}" + (f" ({obj.standard.name})" if obj.standard else "")
        )


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number', 'rework', 'job_identity', 'standard',
            'classification', 'surface_repaired', 'customer',
            'purchase_order_with_revision', 'part_quantity',
            'serial_or_lot_numbers', 'surface_area', 'current_density'
        ]
        widgets = {
            'serial_or_lot_numbers': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        part = kwargs.pop('part', None)
        super().__init__(*args, **kwargs)

        if part:
            # ✅ Use actual model instances
            self.fields['standard'].queryset = Standard.objects.filter(
                id__in=PartStandard.objects.filter(part=part).values_list('standard', flat=True)
            )

            self.fields['classification'].queryset = Classification.objects.filter(
                id__in=PartStandard.objects.filter(part=part).values_list('classification', flat=True)
            )
