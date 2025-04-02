from django.contrib import admin
from .models import Method, ParameterToBeRecorded, TITLE_CHOICES
from django import forms


class MethodAdminForm(forms.ModelForm):
    predefined_title = forms.ChoiceField(
        choices=[('', '--- Select Predefined ---')] + TITLE_CHOICES,
        required=False,
        label='Predefined Title',
    )

    class Meta:
        model = Method
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        custom_title = cleaned_data.get('title')
        predefined_title = cleaned_data.get('predefined_title')
        if not custom_title and predefined_title:
            cleaned_data['title'] = predefined_title
        return cleaned_data


class MethodAdmin(admin.ModelAdmin):
    form = MethodAdminForm
    list_display = ('title', 'method_type', 'tank_name', 'chemical')
    search_fields = ['title', 'description']


admin.site.register(Method, MethodAdmin)
