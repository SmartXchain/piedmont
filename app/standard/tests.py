from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Standard


def make_standard(name="AMS-2404", revision="A", requires_process_review=False):
    return Standard.objects.create(
        name=name,
        revision=revision,
        description="Test standard",
        author="Test",
        requires_process_review=requires_process_review,
    )


class TestStandardRevisionSetsReviewFlag(TestCase):
    """
    Verify Standard.save() sets requires_process_review=True whenever the
    revision field changes on an existing record.

    T-2: this is the key model behaviour — downstream processes depend on the
    flag to know when re-review is needed after a spec update.
    """

    def test_new_standard_does_not_set_review_flag(self):
        """Creating a Standard for the first time must not set the flag."""
        std = make_standard()
        self.assertFalse(std.requires_process_review)

    def test_changing_revision_sets_review_flag(self):
        """Saving an existing Standard with a new revision must set the flag."""
        std = make_standard(revision="A")
        std.revision = "B"
        std.save()
        std.refresh_from_db()
        self.assertTrue(std.requires_process_review)

    def test_saving_same_revision_does_not_change_flag(self):
        """Re-saving with the same revision must not flip the flag."""
        std = make_standard(revision="A")
        self.assertFalse(std.requires_process_review)
        std.description = "Updated description"
        std.save()
        std.refresh_from_db()
        self.assertFalse(std.requires_process_review)

    def test_changing_other_fields_does_not_set_review_flag(self):
        """Only a revision change triggers the flag — not author, description, etc."""
        std = make_standard(revision="A")
        std.author = "New Author"
        std.description = "New description"
        std.save()
        std.refresh_from_db()
        self.assertFalse(std.requires_process_review)

    def test_flag_stays_true_after_second_revision_change(self):
        """If the flag is already True, another revision bump keeps it True."""
        std = make_standard(revision="A")
        std.revision = "B"
        std.save()
        std.revision = "C"
        std.save()
        std.refresh_from_db()
        self.assertTrue(std.requires_process_review)

    def test_flag_can_be_cleared_and_revision_bump_re_sets_it(self):
        """
        After a reviewer manually clears the flag, the next revision change
        must set it again.
        """
        std = make_standard(revision="A")
        std.revision = "B"
        std.save()
        # Reviewer clears the flag
        std.requires_process_review = False
        std.save()
        std.refresh_from_db()
        self.assertFalse(std.requires_process_review)
        # Next revision change re-sets it
        std.revision = "C"
        std.save()
        std.refresh_from_db()
        self.assertTrue(std.requires_process_review)

    def test_revision_change_persists_to_database(self):
        """The flag must be committed to the DB, not just set on the instance."""
        std = make_standard(revision="A")
        std.revision = "B"
        std.save()
        from_db = Standard.objects.get(pk=std.pk)
        self.assertTrue(from_db.requires_process_review)


class TestStandardUniqueConstraint(TestCase):
    """Verify the unique_standard_name_revision constraint."""

    def test_duplicate_name_revision_is_blocked(self):
        make_standard(name="AMS-2404", revision="A")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_standard(name="AMS-2404", revision="A")

    def test_same_name_different_revision_is_allowed(self):
        make_standard(name="AMS-2404", revision="A")
        std2 = make_standard(name="AMS-2404", revision="B")
        self.assertIsNotNone(std2.pk)

    def test_same_revision_different_name_is_allowed(self):
        make_standard(name="AMS-2404", revision="A")
        std2 = make_standard(name="AMS-2405", revision="A")
        self.assertIsNotNone(std2.pk)


class TestStandardStr(TestCase):
    """Verify Standard.__str__() output."""

    def test_str_without_review_flag(self):
        std = make_standard(name="AMS-2404", revision="A")
        self.assertEqual(str(std), "AMS-2404 (Rev A) ")

    def test_str_with_review_flag(self):
        std = make_standard(name="AMS-2404", revision="A", requires_process_review=True)
        self.assertIn("[REVIEW REQUIRED]", str(std))

    def test_str_contains_no_emoji(self):
        """Encoding safety: __str__ must not contain emoji characters."""
        std = make_standard(requires_process_review=True)
        for char in str(std):
            self.assertLess(ord(char), 0x2000,
                            f"Non-ASCII/emoji character found in __str__: {repr(char)}")
