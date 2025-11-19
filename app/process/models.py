# process/models.py
from django.db import models
from methods.models import Method
from standard.models import Standard, Classification
from django.db.models import UniqueConstraint, CheckConstraint, Q
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Process(models.Model):
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='processes',
        db_index=True
    )
    classification = models.ForeignKey(
        Classification,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        db_index=True
    )
    description = models.TextField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Process"
        verbose_name_plural = "Processes"
        constraints = [
            models.UniqueConstraint(
                fields=['standard', 'classification'],
                name='uniq_process_with_classification'
            ),
            models.UniqueConstraint(
                fields=['standard'],
                condition=Q(classification__isnull=True),
                name='uniq_unclassified_process_per_standard'
            )
        ]
        indexes = [
            models.Index(fields=['standard', 'classification']),
        ]

    def __str__(self):
        standard_name = self.standard.name if self.standard else 'No Standard'
        classification_name = self.classification.class_name if self.classification else "Unclassified"
        return f"{standard_name} - {classification_name}"


class ProcessStep(models.Model):
    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name='steps',
        db_index=True
    )
    method = models.ForeignKey(
        Method,
        on_delete=models.CASCADE,
        related_name='process_steps',
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
        super().save(*args, **kwargs)

    def __str__(self):
        process_info = self.process.standard.name if self.process_id and self.process.standard else "Unsaved Process"
        method_info = self.method.title if self.method_id else "No Method"
        return f"Step {self.step_number} for {process_info} - {method_info}"

