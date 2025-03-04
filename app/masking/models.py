from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html


class MaskingProcess(models.Model):
    """Represents a masking process for a specific part."""
    
    part_number = models.CharField(max_length=255, unique=True)
    masking_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.part_number


class MaskingStep(models.Model):
    """Represents individual steps in a masking process."""
    
    masking_process = models.ForeignKey(
        MaskingProcess, on_delete=models.CASCADE, related_name="masking_steps"
    )
    step_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="step_images/", blank=True, null=True)

    class Meta:
        ordering = ["step_number"]

    def save(self, *args, **kwargs):
        """Assigns step number automatically and reorders when needed."""
        if self._state.adding:
            last_step = MaskingStep.objects.filter(masking_process=self.masking_process).order_by("-step_number").first()
            self.step_number = (last_step.step_number + 1) if last_step else 1

        super().save(*args, **kwargs)
        self.reorder_steps()

    def delete(self, *args, **kwargs):
        """Restrict deletion outside Django Admin."""
        if not hasattr(self, "_force_delete"):  # Allow only forced admin deletions
            raise PermissionDenied("You are not allowed to delete this step outside the Django admin.")
        super().delete(*args, **kwargs)
        self.reorder_steps()

    def reorder_steps(self):
        """Ensures sequential step numbering after deletion or reordering."""
        steps = list(self.masking_process.masking_steps.order_by("step_number"))
        for index, step in enumerate(steps, start=1):
            if step.step_number != index:
                step.step_number = index
        MaskingStep.objects.bulk_update(steps, ["step_number"])

    def image_preview(self):
        """Displays a preview of the uploaded image in Django admin."""
        if self.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;"/>', self.image.url)
        return "No Image"

    image_preview.short_description = "Preview"

    def __str__(self):
        return f"{self.step_number}. {self.title}"
