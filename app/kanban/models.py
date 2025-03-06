from django.db import models
from django.utils.timezone import now
from datetime import timedelta


class Chemical(models.Model):
    """Represents a chemical in the inventory system with Kanban tracking."""

    name = models.CharField(max_length=255, unique=True, help_text="Enter the chemical name")
    quantity = models.PositiveIntegerField(default=0, help_text="Current stock quantity")
    lot_number = models.CharField(max_length=100, blank=True, null=True, help_text="Lot tracking number")
    expiry_date = models.DateField(help_text="Date when the chemical expires")
    coc_scan = models.FileField(upload_to='coc_scans/', blank=True, null=True, help_text="Upload Certificate of Conformance")
    reorder_level = models.PositiveIntegerField(default=10, help_text="Threshold for reordering")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status(self):
        """Determine the stock status of the chemical."""
        today = now().date()
        expiring_soon_threshold = today + timedelta(days=7)

        if self.expiry_date < today:
            return "Expired"
        elif self.expiry_date <= expiring_soon_threshold:
            return "Expiring Soon"
        elif self.quantity <= self.reorder_level:
            return "Low Stock"
        return "Available"

    def is_expired(self):
        return self.status == "Expired"

    def needs_reorder(self):
        return self.quantity <= self.reorder_level

    def __str__(self):
        return f"{self.name} - {self.quantity} units ({self.status})"
