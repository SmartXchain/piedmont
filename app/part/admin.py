from django.contrib import admin
from django.shortcuts import redirect # <-- ADDED: Necessary for changelist_view redirect
from .models import Part, PartStandard, WorkOrder, PDFSettings
from .forms import PartStandardForm 


class PartStandardInline(admin.TabularInline):
    model = PartStandard
    # Note: Using PartStandardForm here might be better if you need custom form logic/queries on the inline
    # form = PartStandardForm 
    fields = ('standard', 'classification')
    extra = 0
    verbose_name_plural = "Assigned Standards & Classifications"


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_description', 'part_revision')
    search_fields = ('part_number', 'part_description')
    inlines = [PartStandardInline]


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_number',
        'part',
        'standard',
        'classification',
        'job_identity',
        'rework',
        # ⭐ ADDED TOGGLES TO LIST DISPLAY ⭐
        'requires_masking',
        'requires_stress_relief',
        'requires_hydrogen_relief',
    )
    list_filter = (
        'standard',
        'classification',
        'job_identity',
        'rework',
        # ⭐ ADDED TOGGLES TO LIST FILTER ⭐
        'requires_masking',
        'requires_stress_relief',
        'requires_hydrogen_relief',
    )
    search_fields = (
        'work_order_number',
        'part__part_number',
        'standard__name',
        'classification__name',
        'customer'
    )
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
        # ⭐ ADDED NEW FIELDSET FOR TOGGLES ⭐
        ("Optional Process Inclusions (PDF Control)", {
            "fields": (
                'requires_masking',
                'requires_stress_relief',
                'requires_hydrogen_relief',
            ),
            "classes": ("collapse",),
            "description": "These flags control which steps are excluded from the printed traveler. Uncheck if the step is NOT required for this job.",
        }),
        ("Customer/Tracking Info", {
            "fields": ('customer', 'purchase_order_with_revision', 'part_quantity', 'serial_or_lot_numbers'),
        }),
    )


@admin.register(PDFSettings)
class PDFSettingsAdmin(admin.ModelAdmin):
    list_display = ('doc_id', 'revision', 'date', 'repair_station')
    fields = ('doc_id', 'revision', 'date', 'repair_station', 'footer_text')
    
    def has_add_permission(self, request):
        # Prevent addition if a record already exists
        if self.model.objects.exists() and self.model.objects.count() >= 1:
            return False
        return True
    
    def changelist_view(self, request, extra_context=None):
        # Redirect directly to the change page if only one record exists
        if self.model.objects.count() == 1:
            obj = self.model.objects.first()
            # Ensure the URL name is correct (appname_modelname_change)
            return redirect('admin:part_pdfsettings_change', obj.pk) 
        return super().changelist_view(request, extra_context)

# NOTE: Since PartStandard is managed via PartAdmin inline, 
# you do not need to register a standalone admin class for it.
