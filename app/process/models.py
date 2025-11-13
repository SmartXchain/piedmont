# process/models.py
from django.db import models
from methods.models import Method
from standard.models import Standard, Classification

from django.db.models import UniqueConstraint, CheckConstraint, Q
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Process(models.Model):
    standard = models.ForeignKey(
        Standard, on_delete=models.CASCADE, related_name='processes',
        db_index=True
    )
    classification = models.ForeignKey(
        Classification, on_delete=models.SET_NULL, blank=True, null=True,
        db_index=True
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Process"
        verbose_name_plural = "Processes"
        constraints = [
            UniqueConstraint(
                fields=['standard', 'classification'],
                name='uniq_process_per_standard_classification'
            ),
        ]
        indexes = [
            models.Index(fields=['standard', 'classification']),
        ]

    def __str__(self):
        standard_name =getattr(self.standard, 'name', 'No Standard')
        classification_name = self.classification or "Unclassified"
        return f"{standard_name} - {classification_name}"

    @property
    def steps_count(self) -> int:
        return getattr(self, '_steps_count', None) or self.steps.count()

    def renumber_steps(self, commit=True):
        """
        Ensure stemp_number is 1..N with no gaps, ordered by current step_number then pk.
        """
        ordered = list(self.steps.order_by("step_number", "pk").value_list("pk", flat=True))
        for i, pk in enumerate(ordered, start=1):
            ProcessStep.objects.filter(pk=pk).update(step_number=i)
        if commit:
            Process.objects.filter(pk=self.pk).update(updated_at=models.functions.Now())


class ProcessStep(models.Model):
    process = models.ForeignKey(
        Process, on_delete=models.CASCADE, related_name='steps',
        db_index=True
    )
    method = models.ForeignKey(
        Method, on_delete=models.CASCADE, related_name='process_steps',
        db_index=True
    )
    step_number = models.PositiveIntegerField(editable=True)

    class Meta:
        ordering = ['step_number']
        verbose_name = "Process Step"
        verbose_name_plural = "Process Steps"
        constraints = [
            UniqueConstraint(
                fields=["process", "step_number"],
                name="uniq_step_number_per_process"
            ),
            CheckConstraint(
                check=Q(step_number__gte=1),
                name="step_number_gte_1"
            ),
        ]
        indexes = [
            models.Index(fields=["process", "step_number"]),
        ]

    def save(self, *args, **kwargs):
        if not self.step_number:
            last = ProcessStep.objects.filter(process=self.process).order_by('-step_number').first()
            self.step_number = (last.step_number + 1) if last else 1
        super().save(*args, **kwargs)

    def __str__(self):
        process_info = getattr(self.process.standard, 'name', 'No Standard') if self.process_id else "Unsaved Process"
        method_info = self.method.title if self.method_id else "No Method"
        return f"Step {self.step_number} for {process_info} - {method_info}"


@receiver(post_delete, sender=ProcessStep)
def _renumber_after_delete(sender, instance: ProcessStep, **kwargs):
    """
    Keep numbering contiguous when a step is removed.
    """
    if instance.process_id:
        instance.process.renumber_steps(commit=True)
