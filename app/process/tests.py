import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from methods.models import Method
from standard.models import Classification, Standard, StandardProcess

from .models import Process, ProcessStep


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def make_classification(standard, class_name="Type I"):
    return Classification.objects.create(
        standard=standard,
        class_name=class_name,
    )


def make_method(title="Rinse", method_type="manual_method"):
    return Method.objects.create(title=title, method_type=method_type)


def make_process(standard, standard_process, classification=None):
    return Process.objects.create(
        standard=standard,
        standard_process=standard_process,
        classification=classification,
    )


# ---------------------------------------------------------------------------
# Model __str__ tests
# ---------------------------------------------------------------------------

class TestProcessStr(TestCase):
    def setUp(self):
        self.standard = make_standard()
        self.sp = make_standard_process(self.standard)

    def test_str_with_classification(self):
        classification = make_classification(self.standard, "Type I")
        process = make_process(self.standard, self.sp, classification)
        self.assertEqual(str(process), "AMS-2404 - Type I")

    def test_str_without_classification(self):
        process = make_process(self.standard, self.sp)
        self.assertEqual(str(process), "AMS-2404 - Unclassified")


class TestProcessStepStr(TestCase):
    def setUp(self):
        self.standard = make_standard()
        self.sp = make_standard_process(self.standard)
        self.process = make_process(self.standard, self.sp)
        self.method = make_method(title="Cadmium Plate Tank")

    def test_str_includes_step_number_standard_and_method(self):
        step = ProcessStep.objects.create(
            process=self.process,
            method=self.method,
            step_number=1,
        )
        result = str(step)
        self.assertIn("Step 1", result)
        self.assertIn("AMS-2404", result)
        self.assertIn("Cadmium Plate Tank", result)


# ---------------------------------------------------------------------------
# FK protection (existing, kept for regression)
# ---------------------------------------------------------------------------

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

    def test_deleting_standard_process_with_linked_process_raises_protected_error(
        self,
    ):
        with self.assertRaises(ProtectedError):
            self.standard_process.delete()

    def test_process_still_exists_after_blocked_delete(self):
        try:
            self.standard_process.delete()
        except ProtectedError:
            pass
        self.assertTrue(Process.objects.filter(pk=self.process.pk).exists())

    def test_deleting_standard_process_without_linked_processes_is_allowed(self):
        orphan = make_standard_process(self.standard, title="Unused Process Block")
        orphan.delete()
        self.assertFalse(StandardProcess.objects.filter(pk=orphan.pk).exists())


# ---------------------------------------------------------------------------
# View tests — shared auth setup
# ---------------------------------------------------------------------------

class _AuthBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="tester", password="pass"
        )
        cls.standard = make_standard()
        cls.sp = make_standard_process(cls.standard)
        cls.process = make_process(cls.standard, cls.sp)

    def _login(self):
        self.client.force_login(self.user)


# ---------------------------------------------------------------------------
# ProcessLandingView
# ---------------------------------------------------------------------------

class TestProcessLandingView(_AuthBase):
    def test_auth_redirect(self):
        resp = self.client.get(reverse("process_landing"))
        self.assertRedirects(
            resp, f"/login/?next={reverse('process_landing')}",
            fetch_redirect_response=False,
        )

    def test_returns_200_authenticated(self):
        self._login()
        resp = self.client.get(reverse("process_landing"))
        self.assertEqual(resp.status_code, 200)

    def test_lists_processes(self):
        self._login()
        resp = self.client.get(reverse("process_landing"))
        self.assertIn(self.process, resp.context["processes"])

    def test_search_by_standard_name(self):
        self._login()
        resp = self.client.get(reverse("process_landing"), {"q": "AMS-2404"})
        self.assertIn(self.process, resp.context["processes"])

    def test_search_no_match_returns_empty(self):
        self._login()
        resp = self.client.get(
            reverse("process_landing"), {"q": "ZZZNOMATCH"}
        )
        self.assertEqual(list(resp.context["processes"]), [])

    def test_search_by_description(self):
        self._login()
        Process.objects.filter(pk=self.process.pk).update(
            description="Special anodize run"
        )
        resp = self.client.get(
            reverse("process_landing"), {"q": "anodize"}
        )
        pks = [p.pk for p in resp.context["processes"]]
        self.assertIn(self.process.pk, pks)


# ---------------------------------------------------------------------------
# ProcessFlowchartView
# ---------------------------------------------------------------------------

class TestProcessFlowchartView(_AuthBase):
    def test_auth_redirect(self):
        url = reverse("process_flowchart", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertRedirects(
            resp, f"/login/?next={url}", fetch_redirect_response=False
        )

    @patch("process.views.build_process_flowchart_svg", return_value="<svg/>")
    def test_returns_200_authenticated(self, _mock_svg):
        self._login()
        url = reverse("process_flowchart", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    @patch("process.views.build_process_flowchart_svg", return_value="<svg/>")
    def test_context_contains_process_and_svg(self, _mock_svg):
        self._login()
        url = reverse("process_flowchart", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.context["process"], self.process)
        self.assertEqual(resp.context["svg"], "<svg/>")

    def test_returns_404_for_unknown_pk(self):
        self._login()
        url = reverse("process_flowchart", args=[99999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# ProcessFlowchartDownloadView
# ---------------------------------------------------------------------------

class TestProcessFlowchartDownloadView(_AuthBase):
    def test_auth_redirect(self):
        url = reverse("process_flowchart_download", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertRedirects(
            resp, f"/login/?next={url}", fetch_redirect_response=False
        )

    @patch("process.views.build_process_flowchart_svg", return_value="<svg/>")
    def test_returns_svg_content_type(self, _mock_svg):
        self._login()
        url = reverse("process_flowchart_download", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "image/svg+xml")

    @patch("process.views.build_process_flowchart_svg", return_value="<svg/>")
    def test_content_disposition_is_attachment(self, _mock_svg):
        self._login()
        url = reverse("process_flowchart_download", args=[self.process.pk])
        resp = self.client.get(url)
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertIn(".svg", resp["Content-Disposition"])

    def test_returns_404_for_unknown_pk(self):
        self._login()
        url = reverse("process_flowchart_download", args=[99999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


# ---------------------------------------------------------------------------
# AJAX: get_classifications
# ---------------------------------------------------------------------------

class TestGetClassificationsView(_AuthBase):
    def setUp(self):
        self._login()
        self.classification = make_classification(self.standard, "Type I")

    def test_no_standard_id_returns_empty_list(self):
        resp = self.client.get(reverse("get_classifications"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])

    def test_returns_classifications_for_standard(self):
        resp = self.client.get(
            reverse("get_classifications"),
            {"standard_id": self.standard.pk},
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        ids = [item["id"] for item in data]
        self.assertIn(self.classification.pk, ids)

    def test_unknown_standard_returns_empty_list(self):
        resp = self.client.get(
            reverse("get_classifications"), {"standard_id": 99999}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.content), [])


# ---------------------------------------------------------------------------
# AJAX: get_method_info
# ---------------------------------------------------------------------------

class TestGetMethodInfoView(_AuthBase):
    def setUp(self):
        self._login()
        self.method = make_method(title="Cadmium Plate Tank")

    def test_no_method_id_returns_400(self):
        resp = self.client.get(reverse("get_method_info"))
        self.assertEqual(resp.status_code, 400)

    def test_unknown_method_id_returns_404(self):
        resp = self.client.get(
            reverse("get_method_info"), {"method_id": 99999}
        )
        self.assertEqual(resp.status_code, 404)

    def test_valid_method_id_returns_title(self):
        resp = self.client.get(
            reverse("get_method_info"), {"method_id": self.method.pk}
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertEqual(data["title"], "Cadmium Plate Tank")

    def test_valid_method_id_returns_method_type(self):
        resp = self.client.get(
            reverse("get_method_info"), {"method_id": self.method.pk}
        )
        data = json.loads(resp.content)
        self.assertEqual(data["method_type"], "manual_method")
