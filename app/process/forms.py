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

        # On POST, use submitted value
        if self.data.get('standard'):
            try:
                standard_id = int(self.data.get('standard'))
                standard = Standard.objects.get(pk=standard_id)
            except (ValueError, Standard.DoesNotExist):
                pass
        # On GET, use initial or instance
        elif self.initial.get('standard'):
            standard = self.initial.get('standard')
        elif hasattr(self.instance, 'standard'):
            standard = self.instance.standard

        if 'classification' in self.fields:
            if standard:
                self.fields['classification'].queryset = Classification.objects.filter(standard=standard)
            else:
                self.fields['classification'].queryset = Classification.objects.none()

    def get_readonly_fields(self, request, obj=None):
        if obj:  # on edit
            return ['classification']
        return []

    class Media:
        js = ('admin/js/jquery.init.js', 'process/js/filter_classifications.js',)


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
