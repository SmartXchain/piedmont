from django.contrib import admin
from .models import Method, ParameterToBeRecorded, ParameterTemplate


# --- Method Admin ---


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "category",
        "description",
    )
    ordering = ("title",)

# --- Parameter Template Admin ---


@admin.register(ParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    """
    Admin to manage the master blueprints for recorded parameters.
    """
    list_display = (
        "category",
        "description",
        "is_nadcap_required"
    )
    ordering = ("category",)
