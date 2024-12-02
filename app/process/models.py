from django.db import models
from standard.models import Standard, Classification

class Process(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='processes')
    classification = models.ForeignKey(Classification, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField()  # Detailed process description
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('standard', 'classification')  # Ensure unique processes per standard/classification

    def __str__(self):
        classification_name = self.classification or "None"
        return f"{self.standard.name} - {classification_name}"
