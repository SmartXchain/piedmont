from django.contrib import admin
from .models import (
    Standard,
    StandardRevisionNotification,
    InspectionRequirement,
    PeriodicTest,
    Classification,
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


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author', 'process', 'nadcap', 'requires_process_review')
    search_fields = ('name', 'revision', 'author', 'process')
    ordering = ('-name',)
    inlines = [InspectionRequirementInline, PeriodicTestInline, ClassificationInline]


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
