from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from standard.models import Classification, Standard, StandardProcess


def _make_standard(
    name='AMS 2401', revision='A', **kwargs
):
    return Standard.objects.create(
        name=name,
        description='Test standard',
        revision=revision,
        author='Test Author',
        **kwargs,
    )


def _make_standard_process(
    standard, title='Cad Plate', process_type='electroplate'
):
    return StandardProcess.objects.create(
        standard=standard,
        process_type=process_type,
        title=title,
    )


# ---------------------------------------------------------------------------
# standard_list_view
# ---------------------------------------------------------------------------

class TestStandardListView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester', password='pass'
        )
        cls.std = _make_standard()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auth_redirect(self):
        c = Client()
        resp = c.get(reverse('standard_list'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_returns_200(self):
        resp = self.client.get(reverse('standard_list'))
        self.assertEqual(resp.status_code, 200)

    def test_context_has_standards_by_author(self):
        resp = self.client.get(reverse('standard_list'))
        self.assertIn('standards_by_author', resp.context)

    def test_standard_appears_in_list(self):
        resp = self.client.get(reverse('standard_list'))
        self.assertIn('AMS 2401', resp.content.decode())

    def test_pending_review_flag_false_when_none_pending(self):
        resp = self.client.get(reverse('standard_list'))
        self.assertFalse(resp.context['requires_review'])

    def test_pending_review_flag_true_when_review_needed(self):
        std = _make_standard(
            name='AMS 9999',
            revision='B',
            requires_process_review=True,
        )
        resp = self.client.get(reverse('standard_list'))
        self.assertTrue(resp.context['requires_review'])
        std.delete()

    def test_review_standard_excluded_from_main_list(self):
        """Standards awaiting review must not appear in the main list."""
        std = _make_standard(
            name='AMS 8888',
            revision='A',
            requires_process_review=True,
        )
        resp = self.client.get(reverse('standard_list'))
        all_names = [
            s.name
            for stds in resp.context['standards_by_author'].values()
            for s in stds
        ]
        self.assertNotIn('AMS 8888', all_names)
        std.delete()

    def test_filter_by_process_type(self):
        _make_standard_process(self.std, process_type='anodize')
        resp = self.client.get(
            reverse('standard_list'), {'process': 'anodize'}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['selected_process'], 'anodize')


# ---------------------------------------------------------------------------
# standard_detail_view
# ---------------------------------------------------------------------------

class TestStandardDetailView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester2', password='pass'
        )
        cls.std = _make_standard()
        cls.sp = _make_standard_process(cls.std)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)

    def test_auth_redirect(self):
        c = Client()
        url = reverse('standard_detail', args=[self.std.id])
        resp = c.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_returns_200_for_valid_id(self):
        url = reverse('standard_detail', args=[self.std.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_returns_404_for_invalid_id(self):
        url = reverse('standard_detail', args=[99999])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_standard_in_context(self):
        url = reverse('standard_detail', args=[self.std.id])
        resp = self.client.get(url)
        self.assertEqual(resp.context['standard'], self.std)

    def test_process_data_in_context(self):
        url = reverse('standard_detail', args=[self.std.id])
        resp = self.client.get(url)
        self.assertIn('process_data', resp.context)
        self.assertEqual(len(resp.context['process_data']), 1)

    def test_standard_name_in_content(self):
        url = reverse('standard_detail', args=[self.std.id])
        resp = self.client.get(url)
        self.assertIn('AMS 2401', resp.content.decode())


# ---------------------------------------------------------------------------
# process_review_view
# ---------------------------------------------------------------------------

class TestProcessReviewView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='tester3', password='pass'
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.std = _make_standard(
            name='AMS 0001',
            revision='A',
            requires_process_review=True,
        )

    def tearDown(self):
        self.std.delete()

    def test_auth_redirect(self):
        c = Client()
        resp = c.get(reverse('process_review'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_get_returns_200(self):
        resp = self.client.get(reverse('process_review'))
        self.assertEqual(resp.status_code, 200)

    def test_context_has_standards_to_review(self):
        resp = self.client.get(reverse('process_review'))
        self.assertIn('standards_to_review', resp.context)
        names = [s.name for s in resp.context['standards_to_review']]
        self.assertIn('AMS 0001', names)

    def test_post_clears_review_flag(self):
        self.client.post(
            reverse('process_review'),
            {'standard_id': self.std.pk},
        )
        self.std.refresh_from_db()
        self.assertFalse(self.std.requires_process_review)

    def test_post_redirects_to_process_review(self):
        resp = self.client.post(
            reverse('process_review'),
            {'standard_id': self.std.pk},
        )
        self.assertRedirects(
            resp,
            reverse('process_review'),
            fetch_redirect_response=False,
        )

    def test_post_invalid_id_returns_404(self):
        resp = self.client.post(
            reverse('process_review'),
            {'standard_id': 99999},
        )
        self.assertEqual(resp.status_code, 404)
