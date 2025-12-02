from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.shortcuts import redirect
from tank_controls.models import PeriodicTestSpec
from .models import (
    Standard,
    StandardRevisionNotification,
    StandardProcess,
    InspectionRequirement,
    PeriodicTest,
    Classification,
    StandardPeriodicRequirement,
    PeriodicTestResult,
)

########################################
# Custom inline formsets for process-scoped editing
########################################

# Note: The manual FK setting is necessary here because the standard FK is hidden
# and often overridden by the process-scoped relationship.


class _ProcessScopedInlineFormSet(BaseInlineFormSet):
    """
    Forces FK fields (standard, standard_process) under StandardProcessAdmin.
    """
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        parent_process = self.instance

        # Force linkages
        if hasattr(obj, 'standard_process'):
            obj.standard_process = parent_process
        if hasattr(obj, 'standard'):
            obj.standard = parent_process.standard

        if commit:
            obj.save()
        return obj

    def save_existing(self, form, instance, commit=True):
        obj = super().save_existing(form, instance, commit=False)
        parent_process = self.instance

        # Re-enforce linkage
        if hasattr(obj, 'standard_process'):
            obj.standard_process = parent_process
        if hasattr(obj, 'standard'):
            obj.standard = parent_process.standard

        if commit:
            obj.save()
        return obj


class ProcessInspectionInline(admin.TabularInline):
    model = InspectionRequirement
    extra = 1
    formset = _ProcessScopedInlineFormSet
    fields = (
        'name',
        'description',
        'paragraph_section',
        'sampling_plan',
        'operator',
        'date',
    )
    show_change_link = True
    fk_name = 'standard_process'


class ProcessClassificationInline(admin.TabularInline):
    model = Classification
    extra = 1
    formset = _ProcessScopedInlineFormSet
    fields = (
        'method',
        'method_description',
        'class_name',
        'class_description',
        'type',
        'type_description',
        'strike_asf',
        'plate_asf',
        'plating_time_minutes',
    )
    show_change_link = True
    fk_name = 'standard_process'


########################################
# Existing inlines under Standard
########################################

class StandardProcessInline(admin.TabularInline):
    model = StandardProcess
    extra = 1
    fields = ('title', 'process_type', 'notes')
    show_change_link = True
    # The default FK points to 'standard', so no fk_name is required.


class InspectionRequirementInline(admin.TabularInline):
    model = InspectionRequirement
    extra = 1
    fields = (
        'name',
        'description',
        'paragraph_section',
        'sampling_plan',
        'standard_process',
        'operator',
        'date',
    )
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Safely determine the standard ID based on the object being edited
        standard_id = obj.pk if obj and obj.pk else None

        # Handle the case where the StandardProcess dropdown needs filtering
        if standard_id and 'standard_process' in formset.form.base_fields:
            allowed_qs = StandardProcess.objects.filter(standard__pk=standard_id)
            formset.form.base_fields['standard_process'].queryset = allowed_qs

        elif 'standard_process' in formset.form.base_fields:
            # On 'Add Standard' page (no PK yet), ensure no options are shown
            formset.form.base_fields['standard_process'].queryset = StandardProcess.objects.none()

        return formset


class ClassificationInline(admin.TabularInline):
    model = Classification
    extra = 1
    fields = (
        'standard_process',
        'method',
        'method_description',
        'class_name',
        'class_description',
        'type',
        'type_description',
        'strike_asf',
        'plate_asf',
        'plating_time_minutes',
    )
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        standard_id = obj.pk if obj and obj.pk else None

        if standard_id and 'standard_process' in formset.form.base_fields:
            allowed_qs = StandardProcess.objects.filter(standard__pk=standard_id)
            formset.form.base_fields['standard_process'].queryset = allowed_qs

        elif 'standard_process' in formset.form.base_fields:
            formset.form.base_fields['standard_process'].queryset = StandardProcess.objects.none()

        return formset


class PeriodicTestInline(admin.TabularInline):
    model = PeriodicTest
    extra = 1
    fields = (
        'name',
        'time_period',
        'specification',
        'number_of_specimens',
        'material',
        'dimensions',
    )
    show_change_link = True


class StandardPeriodicRequirementInline(admin.TabularInline):
    model = StandardPeriodicRequirement
    extra = 1
    fields = ("test_spec", "active", "notes")
    autocomplete_fields = ("test_spec",)
    show_change_link = True


########################################
# Parent admins
########################################


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    # FIX: Removed redundant 'process' field from model and admin display
    list_display = (
        'name',
        'revision',
        'author',
        'nadcap',
        'requires_process_review',
        'updated_at',
    )
    search_fields = ('name', 'revision', 'author')
    list_filter = ('nadcap', 'requires_process_review')
    ordering = ('name',)

    inlines = [
        StandardProcessInline,
        InspectionRequirementInline,
        ClassificationInline,
        PeriodicTestInline,
        StandardPeriodicRequirementInline,
    ]

    fieldsets = (
        ('Standard Info', {
            'fields': (
                'name',
                'description',
                'revision',
                'author',
                'upload_file',
            )
        }),
        ('Controls / Metadata', {
            'fields': (
                'nadcap',
                'requires_process_review',
                'previous_version',
            ),
            'description': "Changing revision triggers review logic in save().",
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


@admin.register(StandardProcess)
class StandardProcessAdmin(admin.ModelAdmin):
    list_display = ('standard', 'title', 'process_type')
    list_filter = ('process_type', 'standard__name')
    search_fields = ('title', 'notes', 'standard__name')
    ordering = ('standard__name', 'title')

    fieldsets = (
        ('Parent Standard', {
            'fields': ('standard',),
        }),
        ('Process Definition', {
            'fields': ('title', 'process_type', 'notes'),
            'description': "One operational block in this spec (clean, plate, strip, etc.).",
        }),
    )

    inlines = [
        ProcessInspectionInline,
        ProcessClassificationInline,
    ]


@admin.register(InspectionRequirement)
class InspectionRequirementAdmin(admin.ModelAdmin):
    # Added autocomplete for speed
    list_display = (
        'name',
        'standard',
        'get_standard_process_title',
        'paragraph_section',
        'sampling_plan',
        'operator',
        'date',
    )
    list_filter = ('standard__name', 'standard_process__process_type')
    search_fields = (
        'name',
        'description',
        'paragraph_section',
        'sampling_plan',
        'standard__name',
        'standard_process__title',
    )
    autocomplete_fields = ('standard', 'standard_process')
    ordering = ('standard__name', 'name')

    fieldsets = (
        ('Linkage', {
            'fields': ('standard', 'standard_process'),
            'description': "Leave 'Process' blank if this inspection applies to the entire spec."
        }),
        ('Requirement', {
            'fields': (
                'name',
                'description',
                'paragraph_section',
                'sampling_plan',
            ),
        }),
        ('Execution / Record', {
            'fields': (
                'operator',
                'date',
            ),
        }),
    )

    def get_standard_process_title(self, obj):
        return obj.standard_process.title if obj.standard_process else "— applies to whole spec —"
    get_standard_process_title.short_description = "Process Scope"


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):
    list_display = (
        'standard',
        'get_standard_process_title',
        'class_name',
        'type',
        'plate_asf',
        'strike_asf',
        'plating_time_minutes',
    )
    list_filter = (
        'standard__name',
        'standard_process__process_type',
    )
    search_fields = (
        'standard__name',
        'standard_process__title',
        'class_name',
        'type',
        'method',
    )
    autocomplete_fields = ('standard', 'standard_process')
    ordering = ('standard__name', 'class_name', 'type')

    fieldsets = (
        ('Scope', {
            'fields': ('standard', 'standard_process'),
            'description': "Tie this classification to the full standard OR to a specific process block (e.g. plating only).",
        }),
        ('Method Info', {
            'fields': ('method', 'method_description'),
        }),
        ('Classification Details', {
            'fields': ('class_name', 'class_description', 'type', 'type_description'),
        }),
        ('Plating Parameters (ASF & Time)', {
            'fields': ('strike_asf', 'plate_asf', 'plating_time_minutes'),
            'description': "Used for amperage/time calc during plating. Leave blank if not plating-related.",
        }),
    )

    def get_standard_process_title(self, obj):
        return obj.standard_process.title if obj.standard_process else "— global —"
    get_standard_process_title.short_description = "Process Scope"


@admin.register(PeriodicTest)
class PeriodicTestAdmin(admin.ModelAdmin):
    list_display = (
        'standard',
        'name',
        'time_period',
        'number_of_specimens',
        'material',
        'dimensions',
    )
    list_filter = (
        'time_period',
        'standard__name',
    )
    search_fields = (
        'standard__name',
        'name',
        'specification',
        'material',
    )
    autocomplete_fields = ('standard',)
    ordering = ('standard__name', 'name')

    fieldsets = (
        ('Parent Standard', {
            'fields': ('standard',),
        }),
        ('Test Requirement', {
            'fields': (
                'name',
                'time_period',
                'specification',
                'number_of_specimens',
                'material',
                'dimensions',
            ),
        }),
    )


@admin.register(PeriodicTestResult)
class PeriodicTestResultAdmin(admin.ModelAdmin):
    list_display = (
        'test',
        'performed_on',
        'performed_by',
        'passed',
    )
    list_filter = (
        'passed',
        'performed_on',
        'test__standard__name',
        'test__time_period',
    )
    search_fields = (
        'test__name',
        'test__standard__name',
        'performed_by',
        'notes',
    )
    autocomplete_fields = ('test',)
    ordering = ('-performed_on',)

    fieldsets = (
        ('Test Instance', {
            'fields': ('test',),
        }),
        ('Execution Record', {
            'fields': ('performed_on', 'performed_by', 'passed', 'notes'),
        }),
    )

    readonly_fields = ('performed_on',)


@admin.register(StandardRevisionNotification)
class StandardRevisionNotificationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'message', 'notified_at', 'is_acknowledged')
    search_fields = ('standard__name', 'message')
    list_filter = ('is_acknowledged', 'notified_at')
    ordering = ('-notified_at',)
