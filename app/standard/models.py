from django.db import models


class Standard(models.Model):
    """Tracks standards with versioning and notifications when revised."""
    PROCESS_CHOICES = [
        ('anodize', 'Anodizing'),
        ('brush plate', 'Brush Plating'),
        ('clean', 'Cleaning'),
        ('conversion coating', 'Conversion Coating'),
        ('electroplate', 'Electroplating'),
        ('nital etch', 'Nital Etch'),
        ('paint', 'Paint'),
        ('passivation', 'Passivation'),
        ('pre-pen etch', 'Pre-Pen Etch'),
        ('strip', 'Stripping of Coating'),
        ('thermal', 'Thermal Treatment'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    revision = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    process = models.CharField(max_length=50, choices=PROCESS_CHOICES)
    nadcap = models.BooleanField(default=False)
    upload_file = models.FileField(upload_to='standard/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    previous_version = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='next_versions'
    )
    requires_process_review = models.BooleanField(default=False, help_text="Flagged when a new revision is issued.")

    class Meta:
        unique_together = ('name', 'revision')
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.pk:
            previous = Standard.objects.get(pk=self.pk)
            if previous.revision != self.revision:
                self.requires_process_review = True
                old_version = Standard.objects.create(
                    name=previous.name,
                    description=previous.description,
                    revision=previous.revision,
                    author=previous.author,
                    upload_file=previous.upload_file,
                    previous_version=previous,
                    requires_process_review=False
                )
                self.previous_version = old_version
        super().save(*args, **kwargs)

    def __str__(self):
        review_flag = "🔴 Requires Process Review" if self.requires_process_review else ""
        return f"{self.name} (Rev {self.revision}) {review_flag}"


class StandardRevisionNotification(models.Model):
    """Tracks and alerts when a standard is updated."""
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField(help_text="Details of the standard update.")
    notified_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.standard.name} (Rev {self.standard.revision})"


class InspectionRequirement(models.Model):
    """Inspection requirement tied to a specific standard."""
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='inspections')
    name = models.CharField(max_length=255)
    description = models.TextField()
    paragraph_section = models.CharField(max_length=255, blank=True, null=True)
    sampling_plan = models.CharField(max_length=255, blank=True, null=True)
    operator = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name


class PeriodicTest(models.Model):
    """Periodic test requirements for standards."""
    TIME_PERIOD_CHOICES = [
        ('35d', 'Every 35 Days'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='periodic_tests')
    name = models.CharField(max_length=255)
    time_period = models.CharField(max_length=50, choices=TIME_PERIOD_CHOICES)
    specification = models.TextField()
    number_of_specimens = models.PositiveIntegerField()
    material = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.get_time_period_display()})"


class Classification(models.Model):
    """Classifications: method, class, type — optional per standard."""
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='classifications', null=True, blank=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    method_description = models.TextField(blank=True, null=True)
    class_name = models.CharField(max_length=255, blank=True, null=True)
    class_description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    type_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Method: {self.method or 'N/A'}, Class: {self.class_name or 'N/A'}, Type: {self.type or 'N/A'}"


# Utility functions (optional, move to a separate utils.py if desired)
def create_standard(name, description, revision, author, upload_file=None):
    return Standard.objects.create(
        name=name, description=description, revision=revision, author=author, upload_file=upload_file
    )


def list_standards():
    return Standard.objects.all()


def get_standard_by_id(standard_id):
    return Standard.objects.get(id=standard_id)
