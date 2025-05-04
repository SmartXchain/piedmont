# process/forms.py
from django import forms
from .models import Process, ProcessStep
from standard.models import Classification, Standard
from methods.models import Method


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        standard = None

        # First: check submitted data (on POST)
        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                standard = Standard.objects.get(id=standard_id)
            except (ValueError, Standard.DoesNotExist):
                pass

        # Second: check instance (edit mode)
        elif self.instance and self.instance.standard:
            standard = self.instance.standard

        # Third: check initial form data
        elif 'standard' in self.initial:
            initial = self.initial.get('standard')
            standard = initial if isinstance(initial, Standard) else Standard.objects.filter(id=initial).first()

        # Set queryset
        if 'classification' in self.fields:
            if standard:
                self.fields['classification'].queryset = Classification.objects.filter(standard=standard)
            else:
                self.fields['classification'].queryset = Classification.objects.none()
                

class MethodModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.title} — {obj.description[:60]}{'...' if len(obj.description) > 60 else ''}"


class ProcessStepInlineForm(forms.ModelForm):
    method = MethodModelChoiceField(queryset=Method.objects.all(), required=True)

    class Meta:
        model = ProcessStep
        fields = ['step_number', 'method']
        widgets = {
            'step_number': forms.NumberInput(attrs={'style': 'width: 80px;'}),
        }
