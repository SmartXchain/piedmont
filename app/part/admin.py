from django.contrib import admin
from .models import Part, PartStandard, WorkOrder, PDFSettings
from .forms import PartStandardForm  # 👈 import your new form


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'part_description', 'part_revision')
    search_fields = ('part_number', 'part_description')


@admin.register(PartStandard)
class PartStandardAdmin(admin.ModelAdmin):
    form = PartStandardForm  # 👈 apply the form
    list_display = ('part', 'standard', 'classification')
    list_filter = ('standard', 'classification')
    search_fields = ('part__part_number', 'standard__name', 'classification__name')



@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'part', 'standard', 'classification', 'surface_repaired')
    list_filter = ('standard', 'classification')
    search_fields = ('work_order_number', 'part__part_number', 'standard__name', 'classification__name')


@admin.register(PDFSettings)
class PDFSettingsAdmin(admin.ModelAdmin):
    list_display = ('doc_id', 'revision', 'date', 'repair_station')
    fields = ('doc_id', 'revision', 'date', 'repair_station', 'footer_text')
