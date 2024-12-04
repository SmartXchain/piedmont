from django.db import models
from methods.models import Method
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
        classification_name = self.classification
        return f"{self.standard.name} - {classification_name}"


class ProcessStep(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='steps')  # Link to Process
    method = models.ForeignKey(Method, on_delete=models.CASCADE, related_name='process_steps')  # Link to Method
    step_number = models.PositiveIntegerField(editable=False)  # Step order in the process

    class Meta:
        ordering = ['step_number']  # Default order by step number

    def __str__(self):
        return f"Step {self.step_number} for {self.process} - {self.method.title}"
