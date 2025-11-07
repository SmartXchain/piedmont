from django.contrib import admin
from django.conf import settings

from .models import ProcessRun, EmbrittlementRelief, ControlInspection


class ControlInspectionInline(admin.TabularInline):
    model = ControlInspection
    extra = 1
    fields = (
        'inspection_name',
        'inspection_spec',
        'sample_size',
        'inspection_result',
        'inspected_at',
        'inspector',
        'comments',
    )
    raw_id_fields = ('inspector',)
    show_change_link = False  # keep inline simple and safe


class EmbrittlementReliefInline(admin.StackedInline):
    model = EmbrittlementRelief
    extra = 0
    can_delete = False
    fieldsets = (
        (None, {
            'fields': (
                'required',
                'start_time',
                'end_time',
                'furnace_number',
                'linked_operation',
                'remarks',
            )
        }),
    )


@admin.register(ProcessRun)
class ProcessRunAdmin(admin.ModelAdmin):
    list_display = (
        'part_number_text',
        'process_name',
        'work_order_number',
        'repaired_surface',
        'date_of_process',
        'is_rework',
    )
    list_filter = (
        'process_name',
        'date_of_process',
        'technician',
        'is_rework',
    )
    search_fields = (
        'work_order_number',
        'lot_number',
        'notes',
    )
    date_hierarchy = 'date_of_process'
    inlines = [EmbrittlementReliefInline, ControlInspectionInline]


    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Identifiers', {
            'fields': (
                'part_number_text',
                'process_name',
                'work_order_number',
                'repaired_surface',
            )
        }),
        ('Standards / Classifications', {
            'fields': (
                'standard_text',
                'classification_text',
                'spec_revision',
            )
        }),
        ('Process Data', {
            'fields': (
                'date_of_process',
                'plating_end_time',
                'quantity_processed',
                'lot_number',
            )
        }),
        ('Rework', {
            'fields': (
                'is_rework',
                'rework_source',
                'rework_reason',
            )
        }),
        ('People & Notes', {
            'fields': (
                'technician',
                'notes',
            )
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'created_by',
                'updated_at',
                'updated_by',
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ControlInspection)
class ControlInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'inspection_name',
        'process_run',
        'inspection_result',
        'sample_size',
        'inspected_at',
        'inspector',
    )
    list_filter = ('inspection_result', 'inspection_name', 'inspector')
    search_fields = (
        'inspection_name',
        'inspection_spec',
        'process_run__work_order_number',
        'process_run__part_number_text',
    )
    raw_id_fields = ('process_run', 'inspector')


@admin.register(EmbrittlementRelief)
class EmbrittlementReliefAdmin(admin.ModelAdmin):
    list_display = (
        'process_run',
        'required',
        'start_time',
        'end_time',
        'furnace_number',
        'linked_operation',
    )
    list_filter = ('required', 'linked_operation')
    search_fields = (
        'process_run__work_order_number',
        'furnace_number',
    )
    raw_id_fields = ('process_run',)

