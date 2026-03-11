from django.db.models import ProtectedError
from django.test import TestCase

from standard.models import Standard, StandardProcess

from .models import Process


def make_standard(name="AMS-2404", revision="A"):
    return Standard.objects.create(
        name=name, revision=revision, description="Test", author="Test"
    )


def make_standard_process(standard, title="Cadmium Plate"):
    return StandardProcess.objects.create(
        standard=standard,
        process_type="electroplate",
        title=title,
    )


class TestStandardProcessDeleteProtection(TestCase):
    """
    Verify that deleting a StandardProcess raises ProtectedError when Process
    records reference it.

    Q-4: on_delete was CASCADE — silently wiping active processes. Changed to
    PROTECT so the database refuses the delete and forces the operator to
    explicitly remove or reassign Process records first.
    """

    def setUp(self):
        self.standard = make_standard()
        self.standard_process = make_standard_process(self.standard)
        self.process = Process.objects.create(
            standard=self.standard,
            standard_process=self.standard_process,
        )

    def test_deleting_standard_process_with_linked_process_raises_protected_error(self):
        """
        Attempting to delete a StandardProcess that has active Process records
        must raise ProtectedError, not silently delete the Process.
        """
        with self.assertRaises(ProtectedError):
            self.standard_process.delete()

    def test_process_still_exists_after_blocked_delete(self):
        """The Process record must survive the blocked delete attempt."""
        try:
            self.standard_process.delete()
        except ProtectedError:
            pass
        self.assertTrue(Process.objects.filter(pk=self.process.pk).exists())

    def test_deleting_standard_process_without_linked_processes_is_allowed(self):
        """A StandardProcess with no Process records can be deleted freely."""
        orphan = make_standard_process(self.standard, title="Unused Process Block")
        # Must not raise.
        orphan.delete()
        self.assertFalse(StandardProcess.objects.filter(pk=orphan.pk).exists())
