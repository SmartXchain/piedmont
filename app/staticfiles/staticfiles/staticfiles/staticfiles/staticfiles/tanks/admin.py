from django.contrib import admin
from .models import Tank, ProductionLine


@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Tank)
class TankAdmin(admin.ModelAdmin):
    list_display = ('name', 'production_line', 'chemical_composition', 'surface_area', 'max_amps', 'is_vented')
    list_filter = ('production_line', 'is_vented')
    search_fields = ('name', 'chemical_composition')
    readonly_fields = ('surface_area',)  # Prevent editing surface area
