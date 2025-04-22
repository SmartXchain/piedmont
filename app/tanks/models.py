from django.db import models


class ProductionLine(models.Model):
    """Represents a production line that tanks belong to."""
    name = models.CharField(
        max_length=5,
        unique=True,
        choices=[
            ('l1', 'Line 1'),
            ('l2', 'Line 2'),
            ('l3', 'Line 3'),
            ('l4', 'Line 4'),
            ('l5', 'Line 5'),
            ('l6', 'Line 6'),
            ('l7', 'Line 7'),
            ('kl', 'Kernersville'),
            ('hw', 'Honeywell'),
        ],
        help_text="Select the production line",
    )

    def __str__(self):
        return self.get_name_display()  # Display the full name


class Tank(models.Model):
    """Represents a tank used in production."""

    production_line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE, related_name="tanks")
    name = models.CharField(max_length=255, unique=True, help_text="Enter the tank name")
    chemical_composition = models.TextField(help_text="Describe the chemical composition")
    length = models.FloatField(null=True, blank=True, help_text="Length of the tank (inches)")
    width = models.FloatField(null=True, blank=True, help_text="Width of the tank (inches)")
    height = models.FloatField(null=True, blank=True, help_text="Height of the tank (inches)")
    liquid_level = models.FloatField(null=True, blank=True, help_text="Liquid level (inches from the top)")
    is_vented = models.BooleanField(default=False, help_text="Is the tank vented?")
    scrubber = models.CharField(max_length=255, blank=True, null=True, help_text="Scrubber system (if applicable)")
    max_amps = models.PositiveIntegerField(blank=True, null=True, help_text="Max amps (if applicable)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def surface_area(self):
        """Calculate the surface area of the tank based on width and length."""
        if self.length is None or self.width is None:
            return None  # Return None if values are missing
        return round(self.length * self.width, 2)  # Square inches

    def __str__(self):
        return f"{self.name} - {self.production_line}"
