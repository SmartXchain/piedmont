from django.db import models
from django.utils.timezone import now


class Fixture(models.Model):
    """Tracks fixtures with maintenance scheduling and Kanban-style status."""

    name = models.CharField(max_length=255, unique=True, help_text="Fixture Name")
    max_amps = models.PositiveIntegerField(help_text="Max Amps the fixture can handle")
    drawing = models.FileField(upload_to='fixture_drawings/', blank=True, null=True, help_text="Upload fixture drawing")

    quantity_available = models.PositiveIntegerField(default=0, help_text="Number of fixtures available")
    fixtures_due_for_repair = models.PositiveIntegerField(default=0, help_text="Number of fixtures currently needing repair")

    inspection_schedule = models.DateField(help_text="Next scheduled inspection date")
    last_inspection_date = models.DateField(null=True, blank=True, help_text="Last completed inspection")
    repair_notes = models.TextField(blank=True, null=True, help_text="Details of repairs needed/completed")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def fixtures_needing_inspection(self):
        """Returns True if the fixture needs inspection today or earlier."""
        return now().date() >= self.inspection_schedule

    @property
    def available_count(self):
        """Calculate the correct number of available fixtures."""
        return max(0, self.quantity_available - self.fixtures_due_for_repair)

    @property
    def status(self):
        """Determines fixture status based on inspections and repairs."""
        if self.available_count > 0 and not self.fixtures_needing_inspection:
            return "Available"
        elif self.available_count > 0 and self.fixtures_needing_inspection:
            return "Inspection Due"
        elif self.fixtures_due_for_repair > 0:
            return "Needs Repair"
        return "Unavailable"

    def __str__(self):
        return f"{self.name} - {self.available_count} Available ({self.status})"
