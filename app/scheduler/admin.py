from django.contrib import admin
from .models import ManufacturingOrder, Operation, Resource
from .services import build_initial_schedule_for_order

# ---------------------------------------------------------
# INLINE: Operations shown inside Manufacturing Order admin
# ---------------------------------------------------------
class OperationInline(admin.TabularInline):
    model = Operation
    extra = 0
    readonly_fields = (
        'sequence',
        'planned_start',
        'planned_end',
        'status',
        'method',
        'resource',
        'actual_start',
        'actual_end',
    )
    fields = (
        'sequence',
        'process_step',
        'method',
        'resource',
        'planned_start',
        'planned_end',
        'status',
        'actual_start',
        'actual_end',
    )
    can_delete = False
    show_change_link = True


# ---------------------------------------------------------
# MANUFACTURING ORDER ADMIN
# ---------------------------------------------------------
@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order',
        'part_number',
        'quantity',
        'status',
        'part_status',
        'start_date',
        'due_date',
        'estimated_finish_date',
        'assigned_to',
        'is_late_display',
    )
    list_filter = (
        'status',
        'part_status',
        'assigned_to',
        'start_date',
        'due_date',
        'created_at',
    )
    search_fields = (
        'work_order',
        'part_number',
        'part_description',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    inlines = [OperationInline]

    fieldsets = (
        ("Routing", {
            "fields": ('process',),
        }),
        ("Work Order Info", {
            "fields": (
                'work_order',
                'part_number',
                'part_description',
                'quantity',
            ),
        }),
        ("Dates", {
            "fields": (
                'start_date',
                'due_date',
                'estimated_finish_date',
            ),
        }),
        ("Assignment & Status", {
            "fields": (
                'assigned_to',
                'status',
                'part_status',
            ),
        }),
        ("Audit", {
            "fields": (
                'created_at',
                'updated_at',
            ),
        }),
    )

    def is_late_display(self, obj):
        return obj.is_late
    is_late_display.short_description = "Late?"
    is_late_display.boolean = True

    def save_model(self, request, obj, form, change):
        """
        When a ManufacturingOrder is first created (or process changed),
        auto-generate the Operations from the selected process.
        """
        super().save_model(request, obj, form, change)

        # only generate if there are no operations yet and a process is set
        if obj.process and not obj.operations.exists():
            build_initial_schedule_for_order(obj)

# ---------------------------------------------------------
# OPERATION ADMIN
# ---------------------------------------------------------
@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = (
        'manufacturing_order',
        'sequence',
        'process_step',
        'method',
        'resource',
        'planned_start',
        'planned_end',
        'status',
    )
    list_filter = (
        'status',
        'resource',
        'planned_start',
        'planned_end',
    )
    search_fields = (
        'manufacturing_order__work_order',
        'process_step__instructions',
        'method__title',
        'resource__name',
    )
    readonly_fields = (
        'sequence',
        'planned_start',
        'planned_end',
        'actual_start',
        'actual_end',
    )


# ---------------------------------------------------------
# RESOURCE ADMIN
# ---------------------------------------------------------
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'resource_type',
        'department',
        'is_active',
    )
    list_filter = (
        'resource_type',
        'department',
        'is_active',
    )
    search_fields = ('name',)

