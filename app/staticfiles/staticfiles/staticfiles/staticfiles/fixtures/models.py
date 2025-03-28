from django.db import models
from django.contrib.auth.models import User
from django.utils.html import mark_safe


class Rack(models.Model):
    class Meta:
        verbose_name = "Rack Info"
        verbose_name_plural = "Racks"

    rack_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique ID or tag number of the rack (e.g. R-101)"
    )
    description = models.TextField(
        blank=True,
        help_text="Short description of the rack, including type or purpose"
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where the rack is normally stored or used"
    )
    coating_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of rack coating (e.g. plastisol, PVC, Teflon)"
    )
    in_service_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the rack was first put into use"
    )

    def __str__(self):
        return self.rack_id


class RackPhoto(models.Model):
    class Meta:
        verbose_name = "Rack Photo"
        verbose_name_plural = "Rack Photos"

    rack = models.ForeignKey(
        Rack,
        on_delete=models.CASCADE,
        related_name='photos',
        help_text="The rack this photo is associated with"
    )
    image = models.ImageField(
        upload_to='rack_photos/',
        help_text="Upload a photo of the rack"
    )

    def thumbnail(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="100" height="auto" />')
        return "-"
    thumbnail.short_description = "Preview"

    def __str__(self):
        return f"Photo for {self.rack.rack_id}"


class PMTask(models.Model):
    class Meta:
        verbose_name = "PM Task Template"
        verbose_name_plural = "PM Task Templates"

    title = models.CharField(
        max_length=100,
        help_text="Short name of the preventive maintenance task"
    )
    description = models.TextField(
        help_text="Detailed description of the PM task"
    )
    frequency_days = models.IntegerField(
        help_text="How often this task should be performed"
    )
    instruction_photo = models.ImageField(
        upload_to='task_photos/',
        blank=True,
        null=True,
        help_text="Optional photo showing how to perform this task"
    )

    def thumbnail(self):
        if self.instruction_photo:
            return mark_safe(f'<img src="{self.instruction_photo.url}" width="100" height="auto" />')
        return "-"
    thumbnail.short_description = "Preview"

    def __str__(self):
        return self.title


class RackPMPlan(models.Model):
    class Meta:
        verbose_name = "PM Schedule"
        verbose_name_plural = "PM Schedules"

    rack = models.ForeignKey(
        Rack,
        on_delete=models.CASCADE,
        related_name='pm_plan',
        help_text="The rack this planned PM applies to"
    )
    task = models.ForeignKey(
        PMTask,
        on_delete=models.CASCADE,
        help_text="The preventive maintenance task to perform"
    )
    due_every_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Override default task frequency (optional)"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes specific to this rack-task pairing"
    )

    def __str__(self):
        return f"{self.rack.rack_id} – {self.task.title}"


class RackPM(models.Model):
    class Meta:
        verbose_name = "Log PM Entry"
        verbose_name_plural = "Log PM Entries"

    rack = models.ForeignKey(
        Rack,
        on_delete=models.CASCADE,
        help_text="The rack that was inspected or maintained"
    )
    pm_task = models.ForeignKey(
        PMTask,
        on_delete=models.CASCADE,
        help_text="The PM task that was performed"
    )
    performed_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        help_text="User who physically performed the PM task"
    )
    date_performed = models.DateField(
        auto_now_add=True,
        help_text="Date the PM task was performed"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes about the PM"
    )
    passed = models.BooleanField(
        default=True,
        help_text="Check if the rack passed the PM"
    )
    photo = models.ImageField(
        upload_to='pm_photos/',
        blank=True,
        null=True,
        help_text="Optional photo taken during or after the PM"
    )

    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rackpm_created_by',
        help_text="User who logged this PM task"
    )
    modified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='rackpm_modified_by',
        help_text="User who last modified this PM task"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created"
    )
    modified_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last modified"
    )

    def __str__(self):
        return f"{self.rack} - {self.pm_task} on {self.date_performed}"
