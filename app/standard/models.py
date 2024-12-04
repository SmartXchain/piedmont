from django.db import models


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
    name = models.CharField(max_length=255)
    description = models.TextField()
    revision = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    upload_file = models.FileField(upload_to='standard/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


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
    specification = models.TextField()  # Section or specification the test complies with
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
