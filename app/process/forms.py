# process/forms.py
from django import forms
from .models import Process
from standard.models import Classification


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    class Media:
        js = ('admin/js/jquery.init.js', 'process/js/filter_classifications.js',)
