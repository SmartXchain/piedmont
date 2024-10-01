from django.db import models
from parts.models import Part
from specifications.models import Step
from quality.models import QualityControl

class TechnicalSheet(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    specifications = models.ManyToManyField(Step, related_name='technical_sheets')
    instructions = models.TextField()
    tools_required = models.CharField(max_length=200)
    safety_precautions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    quality_controls = models.ManyToManyField(QualityControl, related_name='technical_sheets', blank=True)

    def save(self, *args, **kwargs):
        # Automatically add lot inspection if not already added
        lot_inspection, _ = QualityControl.objects.get_or_create(
            name="Lot Inspection",
            defaults={"description": "Perform lot inspection as per the standard quality control procedures."}
        )
        super().save(*args, **kwargs)
        self.quality_controls.add(lot_inspection)

    def __str__(self):
        return f"Tech Sheet for {self.part.name}"
    
class ReworkSheet(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    steps = models.ManyToManyField(Step)
    instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate the instruction set including optional steps selected
        selected_steps = "\n".join([step.description for step in self.steps.all()])
        self.instructions = f"Rework Steps for {self.part.name}:\n{selected_steps}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rework Sheet for {self.part.name}"

class Operator(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20)
    assigned_parts = models.ManyToManyField(Part, related_name='operators')

    def __str__(self):
        return self.name
    
class Supervisor(models.Model):
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20)

    def __str__(self):
        return self.name