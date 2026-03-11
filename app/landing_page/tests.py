from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from standard.models import Classification, Standard, StandardProcess

from .models import Capability, CapabilityCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_standard(name='AMS 2401', revision='A'):
    return Standard.objects.create(
        name=name,
        description='Test standard',
        revision=revision,
        author='Test Author',
    )


def _make_standard_process(standard, title='Cadmium Plate'):
    return StandardProcess.objects.create(
        standard=standard,
        process_type='electroplate',
        title=title,
    )


def _make_capability(name='Cad Plate', standard_name='AMS 2401'):
    cat = CapabilityCategory.objects.create(name='Electroplating')
    return Capability.objects.create(
        name=name,
        standard=standard_name,
        category=cat,
        cost_usd='100.00',
    )


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

class TestHomePageView(TestCase):
    """landing_page view — Process table and auth."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester', password='pass'
        )
        cls.std = _make_standard()
        cls.sp = _make_standard_process(cls.std)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    # -- auth ----------------------------------------------------------------

    def test_auth_redirect(self):
        """Unauthenticated request redirects to /login/."""
        c = Client()
        resp = c.get(reverse('home'))
        self.assertRedirects(
            resp, '/login/?next=/', fetch_redirect_response=False
        )

    # -- status --------------------------------------------------------------

    def test_returns_200_with_processes(self):
        from process.models import Process
        Process.objects.create(
            standard=self.std,
            standard_process=self.sp,
        )
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    def test_returns_200_no_processes(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)

    # -- grouped context -----------------------------------------------------

    def test_grouped_context_present(self):
        resp = self.client.get(reverse('home'))
        self.assertIn('grouped', resp.context)

    def test_grouped_empty_when_no_processes(self):
        resp = self.client.get(reverse('home'))
        grouped = dict(resp.context['grouped'])
        self.assertEqual(len(grouped), 0)

    def test_grouped_contains_process_when_exists(self):
        from process.models import Process
        Process.objects.create(
            standard=self.std,
            standard_process=self.sp,
        )
        resp = self.client.get(reverse('home'))
        grouped = dict(resp.context['grouped'])
        self.assertIn(self.std, grouped)
        self.assertEqual(len(grouped[self.std]), 1)

    # -- classification label ------------------------------------------------

    def test_classification_label_all_fields(self):
        """All three classification fields produce a combined label."""
        from process.models import Process
        clf = Classification.objects.create(
            standard=self.std,
            method='I',
            class_name='1',
            type='II',
        )
        std2 = _make_standard(name='AMS 2402', revision='A')
        sp2 = _make_standard_process(std2, title='Cad Plate')
        Process.objects.create(
            standard=std2,
            standard_process=sp2,
            classification=clf,
        )
        resp = self.client.get(reverse('home'))
        grouped = dict(resp.context['grouped'])
        row = grouped[std2][0]
        self.assertEqual(
            row['classification_label'], 'Method I, Class 1, Type II'
        )

    def test_classification_label_partial_fields(self):
        """Only method set -> label is just 'Method X'."""
        from process.models import Process
        clf = Classification.objects.create(
            standard=self.std,
            method='II',
        )
        std3 = _make_standard(name='AMS 2403', revision='A')
        sp3 = _make_standard_process(std3, title='Anodize')
        Process.objects.create(
            standard=std3,
            standard_process=sp3,
            classification=clf,
        )
        resp = self.client.get(reverse('home'))
        grouped = dict(resp.context['grouped'])
        row = grouped[std3][0]
        self.assertEqual(row['classification_label'], 'Method II')

    def test_classification_label_none_when_no_classification(self):
        """Process without classification -> classification_label is None."""
        from process.models import Process
        std4 = _make_standard(name='AMS 2404', revision='A')
        sp4 = _make_standard_process(std4, title='Clean')
        Process.objects.create(
            standard=std4,
            standard_process=sp4,
        )
        resp = self.client.get(reverse('home'))
        grouped = dict(resp.context['grouped'])
        row = grouped[std4][0]
        self.assertIsNone(row['classification_label'])


# ---------------------------------------------------------------------------
# Capability pricing detail
# ---------------------------------------------------------------------------

class TestCapabilityPricingDetailView(TestCase):
    """capability_pricing_detail -- 200/404 and auth."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester2', password='pass'
        )
        cls.cap = _make_capability()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auth_redirect(self):
        c = Client()
        url = reverse('capability_pricing_detail', args=[self.cap.pk])
        resp = c.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_returns_200_for_valid_pk(self):
        url = reverse('capability_pricing_detail', args=[self.cap.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_returns_404_for_invalid_pk(self):
        url = reverse('capability_pricing_detail', args=[99999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_capability_in_context(self):
        url = reverse('capability_pricing_detail', args=[self.cap.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.context['capability'], self.cap)


# ---------------------------------------------------------------------------
# Export capabilities CSV
# ---------------------------------------------------------------------------

class TestExportCapabilitiesCSV(TestCase):
    """export_capabilities_csv -- content-type, header row, auth."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester3', password='pass'
        )
        _make_capability()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auth_redirect(self):
        c = Client()
        url = reverse('export_capabilities_csv')
        resp = c.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_content_type_is_csv(self):
        resp = self.client.get(reverse('export_capabilities_csv'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv')

    def test_content_disposition_header(self):
        resp = self.client.get(reverse('export_capabilities_csv'))
        self.assertIn('attachment', resp['Content-Disposition'])
        self.assertIn(
            'capabilities_pricing.csv', resp['Content-Disposition']
        )

    def test_csv_first_row_is_header(self):
        resp = self.client.get(reverse('export_capabilities_csv'))
        content = resp.content.decode('utf-8')
        first_line = content.splitlines()[0]
        self.assertIn('Name', first_line)
        self.assertIn('Standard', first_line)
        self.assertIn('Category', first_line)

    def test_csv_contains_capability_data(self):
        resp = self.client.get(reverse('export_capabilities_csv'))
        content = resp.content.decode('utf-8')
        self.assertIn('Cad Plate', content)
        self.assertIn('AMS 2401', content)
