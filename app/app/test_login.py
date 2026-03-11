from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class TestLoginPageAccessibility(TestCase):
    """Verify the login page is reachable without authentication."""

    def test_login_page_returns_200(self):
        """Login page must be accessible to unauthenticated users."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_contains_ac_notice(self):
        """Login page must display the AC 120-78B compliance notice."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'AC 120-78B')

    def test_login_page_contains_credential_warning(self):
        """Login page must state that credential sharing is prohibited."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'prohibited')

    def test_login_page_has_csrf_token(self):
        """Login form must include a CSRF token."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'csrfmiddlewaretoken')


class TestLoginRequired(TestCase):
    """
    Verify that protected views redirect unauthenticated users to the
    login page, and that authenticated users can access them.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='testoperator',
            password='testpass123'
        )

    def _assert_redirects_to_login(self, url):
        """Helper: unauthenticated GET must redirect to login."""
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 302,
            f"{url} did not redirect unauthenticated request (got "
            f"{response.status_code})"
        )
        self.assertIn(
            '/login/',
            response['Location'],
            f"{url} redirected to '{response['Location']}' "
            f"instead of login page"
        )

    # --- Unauthenticated access must redirect ---

    def test_standard_list_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('standard_list'))

    def test_scheduler_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('scheduler:main'))

    def test_logbook_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('logbook:index'))

    def test_masking_list_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('masking_list'))

    def test_kanban_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('kanban_dashboard'))

    def test_ndt_redirects_unauthenticated(self):
        self._assert_redirects_to_login(reverse('ndt:index'))

    # --- The login page itself must NOT redirect ---

    def test_login_page_not_redirected(self):
        """Login page must be reachable without a login loop."""
        response = self.client.get(reverse('login'))
        self.assertNotEqual(
            response.status_code, 302,
            "Login page is redirecting — possible infinite redirect loop."
        )

    # --- Authenticated users must reach protected views ---

    def test_authenticated_user_reaches_standard_list(self):
        """Logged-in user must not be redirected away from protected views."""
        self.client.login(username='testoperator', password='testpass123')
        response = self.client.get(reverse('standard_list'))
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_reaches_scheduler(self):
        self.client.login(username='testoperator', password='testpass123')
        response = self.client.get(reverse('scheduler:main'))
        self.assertEqual(response.status_code, 200)

    # --- Login redirects to next URL after authentication ---

    def test_login_preserves_next_parameter(self):
        """After login, user is sent to the page they originally requested."""
        target = reverse('standard_list')
        response = self.client.post(
            f"{reverse('login')}?next={target}",
            {'username': 'testoperator', 'password': 'testpass123'},
        )
        self.assertRedirects(response, target)


class TestLogout(TestCase):
    """Verify logout behaviour."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testoperator',
            password='testpass123'
        )

    def test_logout_redirects_to_login(self):
        """After logout, user is sent to the login page."""
        self.client.login(username='testoperator', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_logout_requires_post(self):
        """GET to logout must not log the user out (Django 5.x security)."""
        self.client.login(username='testoperator', password='testpass123')
        self.client.get(reverse('logout'))
        # User should still be authenticated after a GET
        response = self.client.get(reverse('standard_list'))
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# T-6: All views must redirect unauthenticated users to /login/
# ---------------------------------------------------------------------------

class TestAllViewsRequireAuth(TestCase):
    """
    Verify that every named URL in the project returns HTTP 302 → /login/
    for unauthenticated requests.

    LoginRequiredMiddleware (Django 5.1+) runs before any view logic, so
    even detail views with non-existent PKs and POST-only endpoints redirect
    before reaching the view.  This makes fake PKs (99999) safe to use here.

    Test is organised into two sub-test loops:
      - no_arg_views: URL names that take no path arguments.
      - detail_views: URL names that require path arguments (fake IDs used).
    """

    # --- No-argument views ---
    NO_ARG_URLS = [
        # landing_page
        'home',
        'export_capabilities_csv',
        # standard
        'standard_list',
        'process_review',
        # part
        'operator_start',
        'part_list',
        'part_create',
        'global_template_list',
        # masking
        'masking_list',
        'masking_process_add',
        # kanban
        'kanban_dashboard',
        'product_list',
        'export_inventory_report',
        # pm
        'pm_landing_page',
        # fixtures
        'rack_list',
        'pm_calendar',
        # tanks
        'export_tanks_to_excel',
        # process
        'get_classifications',
        'get_method_info',
        'process_landing',
        # customer_links
        'customer_links_list',
        # sds
        'chemical_list',
        # periodic_testing
        'periodic_testing_landing',
        'failure_log_view',
        'daily_view',
        'weekly_view',
        'semi_annual_view',
        'annual_view',
        'monthly_tests',
        # logbook (namespaced)
        'logbook:index',
        'logbook:create',
        'logbook:list',
        'logbook:env_create',
        'logbook:manager_dashboard',
        'logbook:download_logs',
        # scheduler (namespaced)
        'scheduler:main',
        'scheduler:data',
        'scheduler:add_delay',
        'scheduler:update_status',
        # drawings (namespaced)
        'drawings:operator_list',
        # ndt (namespaced)
        'ndt:index',
        'ndt:product_list',
        'ndt:product_add',
        'ndt:lot_list',
        'ndt:lot_add',
        'ndt:mix_list',
        'ndt:mix_add',
        'ndt:curve_list',
        'ndt:curve_add',
        'ndt:log_list',
        'ndt:log_add',
    ]

    # --- Views that require URL arguments ---
    # Each entry is (url_name, kwargs_dict).
    # Fake IDs are safe: middleware redirects before the view runs.
    _PK = {'pk': 99999}
    DETAIL_URLS = [
        # landing_page
        ('capability_pricing_detail', _PK),
        # standard
        ('standard_detail', {'standard_id': 99999}),
        # part
        ('part_detail', {'part_id': 99999}),
        ('part_assign_standard', {'part_id': 99999}),
        ('work_order_create', {'part_id': 99999}),
        ('work_order_detail', {'work_order_id': 99999}),
        ('work_order_pdf', {'work_order_id': 99999}),
        ('template_selection', {'process_id': 99999}),
        ('template_process_print', {'process_id': 99999}),
        ('standard_classifications_json', {'standard_id': 99999}),
        # masking
        ('masking_process_detail', {'process_id': 99999}),
        ('masking_process_edit', {'process_id': 99999}),
        ('masking_step_list', {'process_id': 99999}),
        ('masking_step_add', {'process_id': 99999}),
        ('masking_step_edit', {'process_id': 99999, 'step_id': 99999}),
        ('masking_process_pdf', {'process_id': 99999}),
        # kanban
        ('product_detail', {'product_id': 99999}),
        # fixtures
        ('rack_detail', _PK),
        # process
        ('process_flowchart', _PK),
        ('process_flowchart_download', _PK),
        # periodic_testing
        ('daily_task_summary', {'template_id': 99999}),
        # tank_controls
        ('tank_detail', _PK),
        # drawings (namespaced)
        ('drawings:annotate', {'drawing_id': 99999}),
        ('drawings:page_image', {'drawing_id': 99999}),
        ('drawings:zones_json', {'drawing_id': 99999}),
        ('drawings:save_zone', {'drawing_id': 99999}),
        ('drawings:delete_zone', {'drawing_id': 99999, 'zone_id': 99999}),
        ('drawings:operator_card', {'drawing_id': 99999}),
        ('drawings:operator_zones_json', {'drawing_id': 99999}),
        # ndt (namespaced)
        ('ndt:product_edit', _PK),
        ('ndt:lot_edit', _PK),
        ('ndt:product_lot_list', {'product_id': 99999}),
        ('ndt:mix_edit', _PK),
        ('ndt:curve_detail', _PK),
        ('ndt:curve_edit', _PK),
        ('ndt:curvepoint_add', {'curve_id': 99999}),
        ('ndt:curvepoint_edit', _PK),
        ('ndt:curvepoint_delete', _PK),
        ('ndt:log_detail', _PK),
        ('ndt:log_edit', _PK),
    ]

    def _assert_redirects_to_login(self, url):
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 302,
            f"Expected 302 for unauthenticated GET {url}, "
            f"got {response.status_code}"
        )
        self.assertIn(
            '/login/',
            response['Location'],
            f"{url} redirected to '{response['Location']}' "
            f"instead of /login/"
        )

    def test_no_arg_views_redirect_unauthenticated(self):
        """Every no-argument view must redirect to /login/ without auth."""
        for name in self.NO_ARG_URLS:
            with self.subTest(url_name=name):
                self._assert_redirects_to_login(reverse(name))

    def test_detail_views_redirect_unauthenticated(self):
        """Every detail/action view must redirect to /login/ without auth."""
        for name, kwargs in self.DETAIL_URLS:
            with self.subTest(url_name=name):
                self._assert_redirects_to_login(reverse(name, kwargs=kwargs))
