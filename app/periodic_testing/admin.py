from django.contrib import admin
from django.utils import timezone
from .models import FailureLog, DailyTask, DailyTaskTemplate


@admin.register(FailureLog)
class FailureLogAdmin(admin.ModelAdmin):
    list_display = (
        'test_report_number', 'test_date', 'test_result',
        'original_po', 'failure_reason', 'investigated_by',
        'test_type', 'retest_report_number', 'retest_date',
        'retest_result', 'retest_po',
        'evidence_of_trend', 'reviewed_by'
    )
    readonly_fields = ()
    search_fields = ('test_report_number', 'investigated_by', 'reviewed_by')
    list_filter = ('test_result', 'retest_result', 'test_date', 'retest_date')


ENGINEER_GROUPS = {"Engineers", "Quality"}


def user_in_groups(user, groups):
    return user.is_superuser or user.groups.filter(name__in=groups).exists()


@admin.register(DailyTaskTemplate)
class DailyTaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "created_by", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "description")
    fields = ("name", "description", "active", "created_by")
    readonly_fields = ("created_by",)

    def has_add_permission(self, request):
        return user_in_groups(request.user, ENGINEER_GROUPS)

    def has_change_permission(self, request, obj=None):
        return user_in_groups(request.user, ENGINEER_GROUPS)

    def has_delete_permission(self, request, obj=None):
        return user_in_groups(request.user, ENGINEER_GROUPS)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ("template", "scheduled_for", "completed", "result", "completed_by", "completed_at")
    list_filter = ("scheduled_for", "completed", "result", "template__active")
    search_fields = ("template__name", "note")
    fields = (
        "template", "scheduled_for",
        "completed", "result", "note",
        "completed_by", "completed_at",
    )
    readonly_fields = ("template", "scheduled_for", "completed_by", "completed_at")

    def has_add_permission(self, request):
        # Instances are auto-created; no manual adds
        return False

    def has_delete_permission(self, request, obj=None):
        # Optional: prevent deletes; or allow only engineers/quality
        return user_in_groups(request.user, ENGINEER_GROUPS)

    def save_model(self, request, obj, form, change):
        # When toggled to completed, stamp signer/time
        if "completed" in form.changed_data and obj.completed:
            obj.completed_at = timezone.now()
            obj.completed_by = request.user
            # Ensure result is provided; you can enforce via form validation if desired
        # If toggled back to not completed, clear stamps/result
        if "completed" in form.changed_data and not obj.completed:
            obj.completed_at = None
            obj.completed_by = None
            obj.result = None
        super().save_model(request, obj, form, change)
