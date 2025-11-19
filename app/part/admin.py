from django.contrib import admin
from .models import Part, PartStandard, WorkOrder, PDFSettings
from .forms import PartStandardForm  # 👈 import your new form


class PartStandardInline(admin.TabularInline):
    model = PartStandard
    fields = ('standard', 'classification')
    extra = 0 # Prevent creation of empty placeholder rows by default
    verbose_name_plural = "Assigned Standards & Classifications"


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_description', 'part_revision')
    search_fields = ('part_number', 'part_description')
    # IMPROVEMENT: Add inline to manage PartStandards directly
    inlines = [PartStandardInline]


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_number', 
        'part', 
        'standard', 
        'classification', 
        'job_identity', # CRITICAL: Add the job type here
        'rework',       # CRITICAL: Add rework status
        'surface_repaired'
    )
    list_filter = (
        'standard', 
        'classification', 
        'job_identity', # IMPROVEMENT: Filter by operation type
        'rework'        # IMPROVEMENT: Filter by rework status
    )
    search_fields = (
        'work_order_number', 
        'part__part_number', 
        'standard__name', 
        'classification__name',
        'customer' # IMPROVEMENT: Allow searching by customer
    )
    # Fields to display when viewing/editing a WO instance
    fieldsets = (
        ("Work Order Details", {
            "fields": (
                'part', 'work_order_number', 'job_identity', 'rework', 
                'surface_repaired', 'date'
            ),
        }),
        ("Processing Requirements", {
            "fields": ('standard', 'classification', 'surface_area'),
        }),
        ("Customer/Tracking Info", {
            "fields": ('customer', 'purchase_order_with_revision', 'part_quantity', 'serial_or_lot_numbers'),
        }),
    )


@admin.register(PDFSettings)
class PDFSettingsAdmin(admin.ModelAdmin):
    list_display = ('doc_id', 'revision', 'date', 'repair_station')
    fields = ('doc_id', 'revision', 'date', 'repair_station', 'footer_text')
    
    # IMPROVEMENT: Prevent creation and only allow editing of existing records
    def has_add_permission(self, request):
        # Allow adding if the table is empty, otherwise disallow
        if self.model.objects.exists():
            return False
        return True
    
    # Optional: If you need to make the single existing object easy to find:
    def changelist_view(self, request, extra_context=None):
        if self.model.objects.count() == 1:
            obj = self.model.objects.first()
            return redirect('admin:part_pdfsettings_change', obj.pk)
        return super().changelist_view(request, extra_context)
