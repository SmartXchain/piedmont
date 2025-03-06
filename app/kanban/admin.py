from django.contrib import admin
from .models import Chemical


class ChemicalAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'lot_number', 'expiry_date', 'status_display')
    list_filter = ('expiry_date',)  # Remove 'status' from filters

    @admin.display(ordering='expiry_date', description='Status')
    def status_display(self, obj):
        """Allows 'status' to be used in Django Admin."""
        return obj.status


admin.site.register(Chemical, ChemicalAdmin)
