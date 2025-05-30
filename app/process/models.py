# process/models.py
from django.db import models
from methods.models import Method
from standard.models import Standard, Classification


class Process(models.Model):
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='processes')
    classification = models.ForeignKey(Classification, on_delete=models.SET_NULL, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Process"
        verbose_name_plural = "Processes"

    def __str__(self):
        if self.standard_id:
            standard_name = self.standard.name
        else:
            standard_name = "No Standard"

        classification_name = self.classification or "Unclassified"
        return f"{standard_name} - {classification_name}"


class ProcessStep(models.Model):
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='steps')
    method = models.ForeignKey(Method, on_delete=models.CASCADE, related_name='process_steps')
    step_number = models.PositiveIntegerField(editable=True)

    class Meta:
        ordering = ['step_number']
        verbose_name = "Process Step"
        verbose_name_plural = "Process Steps"

    def save(self, *args, **kwargs):
        if not self.step_number:
            last_step = ProcessStep.objects.filter(process=self.process).order_by('-step_number').first()
            self.step_number = (last_step.step_number + 1) if last_step else 1
        super().save(*args, **kwargs)

    def __str__(self):
        process_info = f"{getattr(self.process.standard, 'name', 'No Standard')}" if self.process_id else "Unsaved Process"
        method_info = self.method.title if self.method_id else "No Method"
        return f"Step {self.step_number} for {process_info} - {method_info}"
