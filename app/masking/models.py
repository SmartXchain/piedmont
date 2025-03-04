from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.utils.timezone import now


class MaskingProcess(models.Model):
    """Represents a masking process for a specific part with version control."""

    part_number = models.CharField(max_length=255)
    masking_description = models.TextField(blank=True, null=True)
    version = models.PositiveIntegerField(default=1)  # Tracks process version
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # Indicates the latest version
    previous_version = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name="next_versions")

    class Meta:
        unique_together = ('part_number', 'version')  # Ensures unique versions per part_number

    def save(self, *args, **kwargs):
        """Handles versioning when a Masking Process is updated."""
        if self.pk:  # If the object already exists, create a new version instead of updating
            self.is_active = False  # Mark current version as inactive
            super().save(*args, **kwargs)

            # Create a new version
            new_version = MaskingProcess.objects.create(
                part_number=self.part_number,
                masking_description=self.masking_description,
                version=self.version + 1,
                previous_version=self,
                is_active=True
            )
            return new_version
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.part_number} (v{self.version})"


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
