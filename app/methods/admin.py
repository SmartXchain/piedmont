from django.contrib import admin
from django.forms.models import BaseInlineFormSet

from .models import Method, ParameterToBeRecorded, ParameterTemplate


# ----- Inline for per-method recordables -----

class ParameterInlineFormSet(BaseInlineFormSet):
    """
    Tie ParameterToBeRecorded rows to the parent Method automatically.
    """
    def save_new(self, form, commit=True):
        # We don't need to manually set the title anymore, only the FK
        obj = super().save_new(form, commit=False)
        parent_method = self.instance
        obj.method = parent_method
        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        # We don't need to manually set the title anymore, only the FK
        obj = super().save_existing(form, instance, commit=False)
        parent_method = self.instance
        obj.method = parent_method
        if commit:
            obj.save()
        return obj


class ParameterInline(admin.TabularInline):
    model = ParameterToBeRecorded
    formset = ParameterInlineFormSet
    extra = 1
    # CHANGED: Removed 'title' field here
    fields = ("description", "unit", "is_nadcap_required") 


# ----- Method admin (No essential changes needed) -----

@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    # ... (Keep all existing list_display, list_filter, search_fields, ordering) ...

    inlines = [ParameterInline]

    # ... (Keep all existing fieldsets) ...

    # ... (Keep Media class) ...
    
    def has_parameters(self, obj):
        return obj.recorded_parameters.exists()
    has_parameters.boolean = True
    has_parameters.short_description = "Has Record Blanks?"


# ----- Parameter template admin (No changes needed) -----

@admin.register(ParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    # ... (Keep all existing setup) ...
    pass
