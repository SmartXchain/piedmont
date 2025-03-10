from django.contrib import admin
from .models import Product, ChemicalLot


class ChemicalLotInline(admin.TabularInline):
    """Allows inline editing of chemical lots within the Product admin page."""
    model = ChemicalLot
    extra = 1
    fields = ('purchase_order', 'lot_number', 'expiry_date', 'quantity', 'coc_scan', 'used_up', 'status_display')
    readonly_fields = ('status_display',)

    @admin.display(description='Status')
    def status_display(self, obj):
        return obj.status


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin panel configuration for managing products."""
    list_display = ('name', 'supplier_name', 'supplier_part_number', 'total_quantity', 'min_quantity', 'max_quantity', 'trigger_level', 'needs_reorder_display')
    search_fields = ('name', 'supplier_name', 'supplier_part_number')
    list_filter = ('supplier_name',)
    inlines = [ChemicalLotInline]

    @admin.display(description="Needs Reorder")
    def needs_reorder_display(self, obj):
        return "Yes" if obj.needs_reorder else "No"


@admin.register(ChemicalLot)
class ChemicalLotAdmin(admin.ModelAdmin):
    """Admin panel configuration for managing individual chemical lots."""
    list_display = ('product', 'purchase_order', 'lot_number', 'expiry_date', 'quantity', 'status_display', 'used_up')
    list_filter = ('product', 'expiry_date', 'used_up')
    search_fields = ('product__name', 'lot_number', 'purchase_order')

    @admin.display(description="Status")
    def status_display(self, obj):
        return obj.status
