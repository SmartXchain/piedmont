from django.contrib import admin
from tank_controls.models import PeriodicTestSpec
from .models import (
    Standard,
    StandardRevisionNotification,
    InspectionRequirement,
    PeriodicTest,
    Classification,
    StandardPeriodicRequirement,
)


class InspectionRequirementInline(admin.TabularInline):
    model = InspectionRequirement
    extra = 1
    fields = ('name', 'description', 'paragraph_section', 'sampling_plan', 'operator', 'date')
    show_change_link = True


class PeriodicTestInline(admin.TabularInline):
    model = PeriodicTest
    extra = 1
    fields = ('name', 'time_period', 'specification', 'number_of_specimens', 'material', 'dimensions')
    show_change_link = True


class ClassificationInline(admin.TabularInline):
    model = Classification
    extra = 1
    fields = ('method',
              'method_description',
              'class_name',
              'class_description',
              'type',
              'type_description',
              'strike_asf',
              'plate_asf',
              'plating_time_minutes')
    show_change_link = True


class StandardPeriodicRequirementInline(admin.TabularInline):
    """
    Link this Standard to one or more PeriodicTestSpec
    defined in the tank_controls app.
    """
    model = StandardPeriodicRequirement
    extra = 1
    fields = ("test_spec", "active", "notes")
    autocomplete_fields = ("test_spec",)
    show_change_link = True

@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author', 'process', 'nadcap', 'requires_process_review')
    search_fields = ('name', 'revision', 'author', 'process')
    ordering = ('-name',)
    inlines = [InspectionRequirementInline, StandardPeriodicRequirementInline, ClassificationInline]


@admin.register(StandardRevisionNotification)
class StandardRevisionNotificationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'message', 'notified_at', 'is_acknowledged')
    search_fields = ('standard__name', 'message')
    list_filter = ('is_acknowledged', 'notified_at')


@admin.register(Classification)
class ClassificationAdmin(admin.ModelAdmin):

    list_display = ('standard', 'class_name', 'type', 'plate_asf', 'strike_asf', 'plating_time_minutes')
    fieldsets = (
        (
            'Standard & Method Info',
            {
                'fields': ('standard', 'method', 'method_description')
            }
        ),
        (
            'Classification Details',
            {
                'fields': ('class_name', 'class_description', 'type', 'type_description')
            }
        ),
        (
            'Plating Parameters (ASF & Time)',
            {
                'fields': ('strike_asf', 'plate_asf', 'plating_time_minutes'),
                'description': "These values are used to calculate amps and plating time for cadmium plating jobs."
            }
        ),
    )


@admin.register(StandardPeriodicRequirement)
class StandardPeriodicRequirementAdmin(admin.ModelAdmin):
    list_display = ("standard", "test_spec", "active")
    list_filter = ("active", "standard__process")
    search_fields = ("standard__name", "test_spec__name", "test_spec__control_set__name")
    autocomplete_fields = ("standard", "test_spec")
    ordering = ("standard__name", "test_spec__name")
