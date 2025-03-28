from django.contrib import admin
from .models import Method, ParameterToBeRecorded


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = ('title', 'method_type', 'description', 'tank_name', 'is_rectified')
    list_filter = ('method_type', 'is_rectified')
    search_fields = ('title', 'description', 'tank_name', 'chemical')

    fieldsets = (
        ('General Information', {
            'fields': ('method_type', 'title', 'description')
        }),
        ('Processing Tank Details', {
            'fields': ('tank_name', 'temp_min', 'temp_max', 'immersion_time_min', 'immersion_time_max', 'chemical', 'is_rectified'),
            'classes': ('collapse',),  # Collapsible section
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for existing objects."""
        if obj:
            return ['method_type']
        return []


@admin.register(ParameterToBeRecorded)
class ParameterToBeRecordedAdmin(admin.ModelAdmin):
    list_display = ('title', 'method')
    list_filter = ('title',)
    search_fields = ('title', 'description')
    autocomplete_fields = ['method']

    def save_model(self, request, obj, form, change):
        """Auto-fill the description based on title if not manually set."""
        descriptions = {
            'Pre-Cleaning': "None as long as method is non-etching. Process sheet must specify the maximum time.",
            'Masking': "Only record masking family (tape, lacquer, etc.).",
            'Abrasive Blasting': "Media, Pressure, Offset distance",
            'Cleaning': "None unless etching. Process sheet must specify max time.",
            'Rinsing': "None",
            'De-Oxidize/Pickle': "Immersion Time",
            'Electrolytic Clean': "Voltage, Amperage, Surface area if current density controlled.",
            'Acid Desmut': "None for dilute acid solutions used for neutralizing. Process sheet specifies max time.",
            'Etching': "Immersion Time. Voltage/Amperage if required. Surface area if amperage-controlled.",
            'Chemical Milling': "Immersion Time",
            'Conversion Coating': "Immersion Time",
            'Electroless Plating': "Immersion Time",
            'Anodize': "Ramp-up data, Voltage/Amperage, Time, Ramp-down data.",
            'Sealing/Dying': "Immersion Time",
            'Barrel Plating': "Voltage/Amperage, Surface area, Time",
            'Brush Plating': "Surface Area, Solution Type, Voltage, Ampere Hours",
            'Electroplating': "Strike voltage/amperage, Plating time, Surface area.",
            'Painting/Dry Film Coating': "Batch # of each paint component, Mixing times, Application start/finish, Cure start/end.",
            'Thermal Treatment': "Time, Temperature",
            'Vacuum Cadmium & Aluminum IVD': "Glow Discharge, Partial Pressure, Voltage, Amperage, Time"
        }

        if not obj.description:
            obj.description = descriptions.get(obj.title, "")
        super().save_model(request, obj, form, change)
