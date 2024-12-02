from django.db import models

class Method(models.Model):
    METHOD_TYPE_CHOICES = [
        ('processing_tank', 'Processing Tank'),
        ('manual_method', 'Manual Method'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    method_type = models.CharField(max_length=50, choices=METHOD_TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.get_method_type_display()})"
