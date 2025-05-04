# process/forms.py
from django import forms
from .models import Process, ProcessStep
from standard.models import Classification, Standard
from methods.models import Method


# process/forms.py
class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        standard_id = (
            self.data.get('standard') or
            getattr(self.instance, 'standard_id', None) or
            (self.initial.get('standard').id if isinstance(self.initial.get('standard'), Standard) else self.initial.get('standard'))
        )

        if 'classification' in self.fields:
            if standard_id:
                self.fields['classification'].queryset = Classification.objects.filter(standard_id=standard_id)
            else:
                self.fields['classification'].queryset = Classification.objects.none()

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'process/js/filter_classifications.js',
        )


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
