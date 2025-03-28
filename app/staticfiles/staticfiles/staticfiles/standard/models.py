from django.db import models
from django.core.exceptions import ValidationError


def create_standard(name, description, revision, author, upload_file=None):
    """Creates and saves a new Standard."""
    return Standard.objects.create(
        name=name, description=description, revision=revision, author=author, upload_file=upload_file
    )


def list_standards():
    """Fetches all Standards."""
    return Standard.objects.all()


def get_standard_by_id(standard_id):
    """Fetches a specific Standard by its ID."""
    return Standard.objects.get(id=standard_id)


class Standard(models.Model):
    """Tracks standards with versioning and notifications when revised."""

    name = models.CharField(max_length=255)
    description = models.TextField()
    revision = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    upload_file = models.FileField(upload_to='standard/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    previous_version = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='next_versions'
    )

    requires_process_review = models.BooleanField(default=False, help_text="Flagged when a new revision is issued.")

    class Meta:
        unique_together = ('name', 'revision')  # Ensures unique revisions per standard

    def save(self, *args, **kwargs):
        """Handles revisioning and process notifications."""
        if self.pk:  # If updating an existing standard
            # Check if revision number has changed
            previous_instance = Standard.objects.get(pk=self.pk)
            if previous_instance.revision != self.revision:
                # Create a new version instead of modifying the existing one
                self.requires_process_review = True  # Notify Process App

                # Save current version as old version and create a new entry
                old_version = Standard.objects.create(
                    name=previous_instance.name,
                    description=previous_instance.description,
                    revision=previous_instance.revision,
                    author=previous_instance.author,
                    upload_file=previous_instance.upload_file,
                    previous_version=previous_instance,
                    requires_process_review=False  # Older versions do not require review
                )
                self.previous_version = old_version  # Link new version to the old one

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Rev {self.revision}) {'🔴 Requires Process Review' if self.requires_process_review else ''}"


class StandardRevisionNotification(models.Model):
    """Tracks and alerts when a standard is updated."""

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(help_text="Details of the standard update.")
    notified_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.standard.name} (Rev {self.standard.revision})"


class InspectionRequirement(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='inspections')
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name


class PeriodicTest(models.Model):
    TIME_PERIOD_CHOICES = [
        ('35d', 'Every 35 Days'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='periodic_tests')
    name = models.CharField(max_length=255)
    time_period = models.CharField(max_length=50, choices=TIME_PERIOD_CHOICES)
    specification = models.TextField(help_text="Section and Description the test complies with")  # Section or specification the test complies with
    number_of_specimens = models.PositiveIntegerField()
    material = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)  # Dimensions of the specimen

    def __str__(self):
        return f"{self.name} ({self.get_time_period_display()})"


class Classification(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='classifications', null=True, blank=True)
    method = models.CharField(max_length=255, blank=True, null=True, help_text="Optional method classification")
    method_description = models.TextField(blank=True, null=True, help_text="Description of the method classification")
    class_name = models.CharField(max_length=255, blank=True, null=True, help_text="Optional class classification")
    class_description = models.TextField(blank=True, null=True, help_text="Description of the class classification")
    type = models.CharField(max_length=255, blank=True, null=True, help_text="Optional type classification")
    type_description = models.TextField(blank=True, null=True, help_text="Description of the type classification")

    def __str__(self):
        return f"Method: {self.method or 'N/A'}, Class: {self.class_name or 'N/A'}, Type: {self.type or 'N/A'}"
