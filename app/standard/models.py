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

class InspectionRequirement(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='inspections')
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name