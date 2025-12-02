from django.contrib import admin
from .models import DailyInspectionLogEntry, ScrubberLog
from django.contrib.auth.models import User

# --- 1. Custom Admin for DailyInspectionLogEntry ---


class DailyInspectionLogAdmin(admin.ModelAdmin):
    # What fields to display in the list view (the main table)
    list_display = (
        'log_date',
        'operator',
        'system_undamaged',
        'leaks_present',
        'containment_is_clean',
        'has_notes_icon'
    )

    # Fields to use for searching (useful for finding specific logs)
    search_fields = ('operator', 'notes')

    # Fields to use as filters on the right sidebar (useful for quick sorting)
    list_filter = ('log_date', 'leaks_present', 'system_undamaged')

    # The order of fields in the edit form
    fieldsets = (
        # Section 1: Record Details
        ('Log Information', {
            'fields': ('log_date', 'operator'),
        }),
        # Section 2: Integrity Checks
        ('System Integrity Checks (Check True for PASS)', {
            'description': 'Check TRUE for a PASSING condition.',
            'fields': (
                'containment_is_clean',
                'system_undamaged',
                'pipes_are_secure',
                'tank_lid_closed',
            ),
        }),
        # Section 3: Critical Negative Check (Leaked)
        ('Critical Check (Check TRUE if FAIL)', {
            'fields': ('leaks_present',),
        }),
        # Section 4: Notes and Documentation
        ('Comments', {
            'fields': ('notes',),
        }),
    )

    # Custom method to display an icon if notes are present
    def has_notes_icon(self, obj):
        return bool(obj.notes)

    has_notes_icon.short_description = "Notes"
    has_notes_icon.boolean = True

# --- 2. Custom Admin for ScrubberLog ---


class ScrubberLogAdmin(admin.ModelAdmin):
    # What fields to display in the list view (the main table)
    list_display = (
        'log_date',
        'operator',
        'limits_exceeded',
        'stage_one_reading',
        'stage_two_reading',
        'stage_three_reading'
    )

    # Fields to use as filters on the right sidebar
    list_filter = ('limits_exceeded', 'log_date')

    # The order of fields in the edit form
    fieldsets = (
        (None, {
            'fields': ('operator', 'limits_exceeded', 'notes', 'log_date')
        }),
        ('Pressure Readings (in)', {
            'fields': ('stage_one_reading', 'stage_two_reading', 'stage_three_reading'),
            'description': 'Enter readings. Leave blank if the scrubber is offline.'
        }),
    )

# --- 3. Register the Models ---

# Link the model to its custom Admin class


admin.site.register(DailyInspectionLogEntry, DailyInspectionLogAdmin)
admin.site.register(ScrubberLog, ScrubberLogAdmin)
