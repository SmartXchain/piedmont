from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from methods.models import Method
from process.models import Process, ProcessStep
from standard.models import Classification, Standard, StandardProcess

from .models import Part, PartStandard, WorkOrder


def make_standard(name="AMS-2404", revision="A"):
    return Standard.objects.create(
        name=name,
        revision=revision,
        description="Test standard",
        author="Test",
    )


def make_part(number="12345", revision="A"):
    return Part.objects.create(
        part_number=number,
        part_description="Test part",
        part_revision=revision,
    )


def make_classification(standard, class_name="Class 1"):
    return Classification.objects.create(
        standard=standard,
        class_name=class_name,
    )


class TestPartStandardUniqueConstraints(TestCase):
    """
    Verify the two PartStandard unique constraints behave correctly.

    Constraint 1 (unique_part_standard_with_classification):
        Fields: part + standard + classification
        Condition: classification IS NOT NULL
        Intent: prevent duplicate (part, standard, classification) triples.

    Constraint 2 (unique_part_standard_unclassified):
        Fields: part + standard
        Condition: classification IS NULL
        Intent: prevent duplicate (part, standard) rows with no classification.

    B-1 bug: Constraint 1 has condition=Q(classification__isnull=True) instead
    of isnull=False, so it NEVER fires when a classification is present.
    This test file exposes the bug (tests fail before the fix, pass after).
    """

    def setUp(self):
        self.standard = make_standard()
        self.part = make_part()
        self.classification = make_classification(self.standard)

    # -----------------------------------------------------------------------
    # Constraint 1 — with classification (currently BROKEN by B-1 bug)
    # -----------------------------------------------------------------------

    def test_duplicate_with_same_classification_is_blocked(self):
        """
        Creating two PartStandard rows for the same part+standard+classification
        (classification IS NOT NULL) must raise IntegrityError.

        This test FAILS before fixing B-1 because the constraint condition is wrong.
        """
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PartStandard.objects.create(
                    part=self.part,
                    standard=self.standard,
                    classification=self.classification,
                )

    def test_different_classifications_same_standard_are_allowed(self):
        """
        Two PartStandard rows for the same part+standard but different
        classifications must be allowed (they represent distinct spec options).
        """
        classification2 = make_classification(self.standard, class_name="Class 2")
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
        )
        # This must NOT raise.
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=classification2,
        )
        self.assertEqual(
            PartStandard.objects.filter(part=self.part, standard=self.standard).count(),
            2,
        )

    # -----------------------------------------------------------------------
    # Constraint 2 — without classification (currently works correctly)
    # -----------------------------------------------------------------------

    def test_duplicate_without_classification_is_blocked(self):
        """
        Two PartStandard rows for the same part+standard with no classification
        must raise IntegrityError.
        """
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=None,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PartStandard.objects.create(
                    part=self.part,
                    standard=self.standard,
                    classification=None,
                )

    def test_unclassified_and_classified_same_standard_are_allowed(self):
        """
        One unclassified row and one classified row for the same part+standard
        must both be allowed (they cover different use cases).
        """
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=None,
        )
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
        )
        self.assertEqual(
            PartStandard.objects.filter(part=self.part, standard=self.standard).count(),
            2,
        )

    # -----------------------------------------------------------------------
    # Isolation — different parts / standards are never affected
    # -----------------------------------------------------------------------

    def test_same_standard_classification_different_parts_are_allowed(self):
        """Constraint is per-part — different parts may share the same standard/class."""
        part2 = make_part(number="99999", revision="B")
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
        )
        PartStandard.objects.create(
            part=part2,
            standard=self.standard,
            classification=self.classification,
        )
        self.assertEqual(PartStandard.objects.count(), 2)

    def test_same_part_classification_different_standards_are_allowed(self):
        """Constraint is per-standard — different standards may share the same part/class."""
        standard2 = make_standard(name="AMS-2405", revision="A")
        classification2 = make_classification(standard2, class_name="Class 1")
        PartStandard.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
        )
        PartStandard.objects.create(
            part=self.part,
            standard=standard2,
            classification=classification2,
        )
        self.assertEqual(PartStandard.objects.count(), 2)


# ---------------------------------------------------------------------------
# T-1 helpers
# ---------------------------------------------------------------------------

def make_standard_process(standard, title="Cadmium Plate"):
    return StandardProcess.objects.create(
        standard=standard,
        process_type="electroplate",
        title=title,
    )


def make_method(title, method_type="processing_tank", is_rectified=False):
    return Method.objects.create(
        title=title,
        method_type=method_type,
        is_rectified=is_rectified,
    )


def make_process(standard, standard_process, classification=None):
    return Process.objects.create(
        standard=standard,
        standard_process=standard_process,
        classification=classification,
    )


def make_work_order(part, standard, classification=None,
                    surface_area=None, wo_number="WO-001"):
    """Build an unsaved WorkOrder (avoids triggering clean/save validation)."""
    wo = WorkOrder(
        part=part,
        standard=standard,
        classification=classification,
        work_order_number=wo_number,
        job_identity="cadmium_plate",
        surface_area=surface_area,
    )
    return wo


# ---------------------------------------------------------------------------
# T-1: WorkOrder.get_process_steps()
# ---------------------------------------------------------------------------

class TestWorkOrderGetProcessSteps(TestCase):
    """
    Verify WorkOrder.get_process_steps() returns the correct ProcessStep
    queryset for a given standard + classification combination.
    """

    def setUp(self):
        self.standard = make_standard(name="AMS-2404", revision="A")
        self.std_process = make_standard_process(self.standard, "Cadmium Plate")
        self.classification = make_classification(self.standard, class_name="Class 1")
        self.part = make_part()
        self.method = make_method("Electroclean", is_rectified=False)
        self.process = make_process(self.standard, self.std_process, self.classification)
        self.step = ProcessStep.objects.create(
            process=self.process, method=self.method, step_number=1
        )

    def test_returns_steps_for_matching_standard_and_classification(self):
        wo = make_work_order(self.part, self.standard, self.classification)
        steps = list(wo.get_process_steps())
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0], self.step)

    def test_returns_all_steps_ordered_by_step_number(self):
        method2 = make_method("Cadmium Plate Tank", is_rectified=True)
        step2 = ProcessStep.objects.create(
            process=self.process, method=method2, step_number=2
        )
        wo = make_work_order(self.part, self.standard, self.classification)
        steps = list(wo.get_process_steps())
        self.assertEqual(steps, [self.step, step2])

    def test_returns_empty_list_when_no_matching_process(self):
        other_standard = make_standard(name="AMS-2405", revision="A")
        wo = make_work_order(self.part, other_standard, None)
        self.assertEqual(wo.get_process_steps(), [])

    def test_returns_empty_list_when_classification_does_not_match(self):
        other_class = make_classification(self.standard, class_name="Class 2")
        wo = make_work_order(self.part, self.standard, other_class)
        self.assertEqual(wo.get_process_steps(), [])

    def test_unclassified_work_order_matches_unclassified_process(self):
        """A Process with classification=None should be found by a WO with no classification."""
        std2 = make_standard(name="AMS-2406", revision="A")
        sp2 = make_standard_process(std2, "Alkaline Clean")
        process_no_class = make_process(std2, sp2, classification=None)
        method2 = make_method("Alkaline Etch")
        step2 = ProcessStep.objects.create(
            process=process_no_class, method=method2, step_number=1
        )
        wo = make_work_order(self.part, std2, classification=None)
        steps = list(wo.get_process_steps())
        self.assertEqual(steps, [step2])

    def test_steps_have_method_prefetched(self):
        """select_related('method') must be applied — no extra query for step.method."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        wo = make_work_order(self.part, self.standard, self.classification)
        steps = list(wo.get_process_steps())

        with CaptureQueriesContext(connection) as ctx:
            _ = steps[0].method.title  # access method — must use prefetch cache
        self.assertEqual(len(ctx), 0, "step.method hit the DB; select_related is missing")


# ---------------------------------------------------------------------------
# T-1: WorkOrder.clean()
# ---------------------------------------------------------------------------

class TestWorkOrderClean(TestCase):
    """
    Verify WorkOrder.clean() enforces surface_area when a rectified processing
    tank step exists, and is a no-op otherwise.
    """

    def setUp(self):
        self.standard = make_standard(name="AMS-2404", revision="A")
        self.std_process = make_standard_process(self.standard, "Cadmium Plate")
        self.classification = make_classification(self.standard, class_name="Class 1")
        self.part = make_part()

        self.rectified_method = make_method("Cad Plate Tank", is_rectified=True)
        self.plain_method = make_method("Rinse", method_type="manual", is_rectified=False)

        self.process = make_process(self.standard, self.std_process, self.classification)
        ProcessStep.objects.create(
            process=self.process, method=self.rectified_method, step_number=1
        )

    def test_raises_when_rectified_step_and_no_surface_area(self):
        wo = make_work_order(self.part, self.standard, self.classification, surface_area=None)
        with self.assertRaises(ValidationError) as cm:
            wo.clean()
        self.assertIn("Surface Area", str(cm.exception))

    def test_passes_when_rectified_step_and_surface_area_provided(self):
        wo = make_work_order(self.part, self.standard, self.classification, surface_area=144.0)
        wo.clean()  # must not raise

    def test_passes_when_no_rectified_steps_even_without_surface_area(self):
        std2 = make_standard(name="AMS-2405", revision="A")
        sp2 = make_standard_process(std2, "Alkaline Clean")
        process2 = make_process(std2, sp2, classification=None)
        ProcessStep.objects.create(
            process=process2, method=self.plain_method, step_number=1
        )
        wo = make_work_order(self.part, std2, classification=None, surface_area=None)
        wo.clean()  # must not raise

    def test_skips_validation_when_part_not_set(self):
        wo = WorkOrder(standard=self.standard, job_identity="cadmium_plate")
        wo.clean()  # must not raise — incomplete WO

    def test_skips_validation_when_standard_not_set(self):
        wo = WorkOrder(part=self.part, job_identity="cadmium_plate")
        wo.clean()  # must not raise — incomplete WO

    def test_save_propagates_clean_error(self):
        """WorkOrder.save() calls clean() — saving without surface_area must fail."""
        with self.assertRaises(ValidationError):
            WorkOrder.objects.create(
                part=self.part,
                standard=self.standard,
                classification=self.classification,
                work_order_number="WO-SAVE-01",
                job_identity="cadmium_plate",
                surface_area=None,
            )

    def test_save_succeeds_when_surface_area_provided(self):
        wo = WorkOrder.objects.create(
            part=self.part,
            standard=self.standard,
            classification=self.classification,
            work_order_number="WO-SAVE-02",
            job_identity="cadmium_plate",
            surface_area=288.0,
        )
        self.assertIsNotNone(wo.pk)


# ---------------------------------------------------------------------------
# T-1: WorkOrder._calc_amps()
# ---------------------------------------------------------------------------

class TestWorkOrderCalcAmps(TestCase):
    """
    Verify _calc_amps() correctly converts surface area to amps using the
    Classification's ASF values (Amps per Square Foot).

    Formula: amps = (surface_area_in_sq_in / 144) * asf
    """

    def setUp(self):
        self.standard = make_standard()
        self.classification = Classification.objects.create(
            standard=self.standard,
            class_name="Class 1",
            plate_asf=Decimal("15.00"),
            strike_asf=Decimal("25.00"),
        )

    def _make_wo(self, surface_area, classification=None):
        """Return an unsaved WorkOrder with the given surface_area."""
        wo = WorkOrder(job_identity="cadmium_plate")
        wo.surface_area = surface_area
        wo.classification = classification if classification is not None else self.classification
        return wo

    def test_returns_none_when_surface_area_is_none(self):
        wo = self._make_wo(surface_area=None)
        result = wo._calc_amps()
        self.assertIsNone(result)
        self.assertIsNone(wo._plate_amps)
        self.assertIsNone(wo._strike_amps)

    def test_returns_none_when_no_classification(self):
        wo = self._make_wo(surface_area=144.0)
        wo.classification = None
        result = wo._calc_amps()
        self.assertIsNone(result)

    def test_plate_amps_at_144_sq_in(self):
        """144 sq in = 1 sq ft; plate_asf=15 → plate_amps=15."""
        wo = self._make_wo(surface_area=144.0)
        wo._calc_amps()
        self.assertAlmostEqual(wo._plate_amps, 15.0, places=4)

    def test_strike_amps_at_144_sq_in(self):
        """144 sq in = 1 sq ft; strike_asf=25 → strike_amps=25."""
        wo = self._make_wo(surface_area=144.0)
        wo._calc_amps()
        self.assertAlmostEqual(wo._strike_amps, 25.0, places=4)

    def test_amps_scale_linearly_with_surface_area(self):
        """288 sq in = 2 sq ft → double the amps."""
        wo = self._make_wo(surface_area=288.0)
        wo._calc_amps()
        self.assertAlmostEqual(wo._plate_amps, 30.0, places=4)
        self.assertAlmostEqual(wo._strike_amps, 50.0, places=4)

    def test_returns_plate_amps_value(self):
        wo = self._make_wo(surface_area=144.0)
        result = wo._calc_amps()
        self.assertAlmostEqual(result, 15.0, places=4)

    def test_amps_are_none_when_asf_not_set_on_classification(self):
        """Classification with no ASF values → both amps are None."""
        bare_class = Classification.objects.create(
            standard=self.standard,
            class_name="Class 2",
            plate_asf=None,
            strike_asf=None,
        )
        wo = self._make_wo(surface_area=144.0, classification=bare_class)
        wo._calc_amps()
        self.assertIsNone(wo._plate_amps)
        self.assertIsNone(wo._strike_amps)
