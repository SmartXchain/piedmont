from django.db import models
from django.utils.safestring import mark_safe
from django.db.models import F


class MaskingProcess(models.Model):
    """Represents a masking process for a specific part."""
    
    part_number = models.CharField(max_length=255, unique=True)
    part_number_masking_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.part_number


class MaskingStep(models.Model):
    """Represents individual steps in a masking process."""
    
    masking_process = models.ForeignKey(
        MaskingProcess, 
        on_delete=models.CASCADE, 
        related_name="masking_steps",
    )
    masking_step_number = models.PositiveIntegerField()
    masking_repair_title = models.CharField(max_length=255)
    masking_description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="step_images/", blank=True, null=True)

    class Meta:
        ordering = ["masking_step_number"]

    def save(self, *args, **kwargs):
        """Assigns step number automatically and reorders when needed."""
        if self._state.adding:
            last_step = MaskingStep.objects.filter(masking_process=self.masking_process).order_by("-masking_step_number").first()
            self.masking_step_number = (last_step.masking_step_number + 1) if last_step else 1

        super().save(*args, **kwargs)
        self.reorder_steps()

    def delete(self, *args, **kwargs):
        """Deletes a step and reorders the remaining steps."""
        super().delete(*args, **kwargs)
        self.reorder_steps()

    def reorder_steps(self):
        """Ensures sequential step numbering after deletion or reordering."""
        steps = list(self.masking_process.masking_steps.order_by("masking_step_number"))
        for index, step in enumerate(steps, start=1):
            if step.masking_step_number != index:
                step.masking_step_number = index
        MaskingStep.objects.bulk_update(steps, ["masking_step_number"])

    def image_preview(self):
        """Displays a preview of the uploaded image in Django admin."""
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="200" height="200" />')
        return "No Image"

    image_preview.short_description = "Preview"

    def __str__(self):
        return f"{self.masking_step_number}. {self.masking_repair_title}"
