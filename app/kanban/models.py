from django.db import models
from django.utils.timezone import now
from datetime import timedelta


class Product(models.Model):
    """Master list of products with general details like stock thresholds and supplier information."""
    
    name = models.CharField(max_length=255, unique=True, help_text="Product name")
    supplier_name = models.CharField(max_length=255, blank=True, null=True, help_text="Supplier Name")
    supplier_part_number = models.CharField(max_length=100, blank=True, null=True, help_text="Supplier Part Number")

    min_quantity = models.PositiveIntegerField(default=5, help_text="Minimum stock level before reordering")
    max_quantity = models.PositiveIntegerField(default=50, help_text="Maximum stock level allowed")
    trigger_level = models.PositiveIntegerField(default=10, help_text="Trigger level for automatic reordering")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_quantity(self):
        """Calculates the total quantity across all lots."""
        return sum(lot.quantity for lot in self.chemical_lots.all())

    @property
    def needs_reorder(self):
        """Determines if the total stock is below the reorder trigger level."""
        return self.total_quantity <= self.trigger_level

    def __str__(self):
        return f"{self.name} - {self.total_quantity} in stock (Min: {self.min_quantity}, Max: {self.max_quantity})"


class ChemicalLot(models.Model):
    """Tracks individual chemical lots linked to a master product, storing lot-specific details."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="chemical_lots")
    purchase_order = models.CharField(max_length=100, blank=True, null=True, help_text="Purchase Order Number")
    lot_number = models.CharField(max_length=100, blank=True, null=True, help_text="Lot tracking number")
    expiry_date = models.DateField(blank=True, null=True, help_text="Expiry date (leave blank if not applicable)")
    quantity = models.PositiveIntegerField(default=0, help_text="Quantity in this lot")
    coc_scan = models.FileField(upload_to='coc_scans/', blank=True, null=True, help_text="Upload Certificate of Conformance")
    used_up = models.BooleanField(default=False, help_text="Mark if this lot has been completely used up")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def status(self):
        """Determine the stock status of the lot."""
        today = now().date()
        expiring_soon_threshold = today + timedelta(days=7)

        if self.used_up:
            return "Used Up"
        elif self.expiry_date and self.expiry_date < today:
            return "Expired"
        elif self.expiry_date and self.expiry_date <= expiring_soon_threshold:
            return "Expiring Soon"
        return "Available"

    def is_expired(self):
        """Check if the lot has expired."""
        return self.status == "Expired"

    def __str__(self):
        return f"{self.product.name} - Lot {self.lot_number} - {self.quantity} units ({self.status})"
