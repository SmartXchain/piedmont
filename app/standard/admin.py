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
    fields = ('method', 'method_description', 'class_name', 'class_description', 'type', 'type_description')
    show_change_link = True


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ('name', 'revision', 'author', 'process', 'requires_process_review')
    search_fields = ('name', 'revision', 'author', 'process')
    list_filter = ('requires_process_review', 'created_at', 'updated_at')
    ordering = ('-updated_at',)
    inlines = [InspectionRequirementInline, PeriodicTestInline, ClassificationInline]


@admin.register(StandardRevisionNotification)
class StandardRevisionNotificationAdmin(admin.ModelAdmin):
    list_display = ('standard', 'message', 'notified_at', 'is_acknowledged')
    search_fields = ('standard__name', 'message')
    list_filter = ('is_acknowledged', 'notified_at')
