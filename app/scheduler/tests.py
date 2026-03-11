import json
import os

from django.test import Client, TestCase
from django.urls import reverse


class TestCSRFProtection(TestCase):
    """
    Verify that scheduler write endpoints enforce CSRF protection.
    Uses Client(enforce_csrf_checks=True) to simulate real browser behavior.
    """

    def setUp(self):
        self.enforced = Client(enforce_csrf_checks=True)
        self.add_delay_url = reverse('scheduler:add_delay')
        self.update_status_url = reverse('scheduler:update_status')

    def _get_csrf_token(self):
        """
        Obtain a valid CSRF token by making a GET request to the scheduler
        page. Django sets the csrftoken cookie when {{ csrf_token }} is
        rendered in the template.
        """
        self.enforced.get(reverse('scheduler:main'))
        cookie = self.enforced.cookies.get('csrftoken')
        self.assertIsNotNone(
            cookie,
            "CSRF cookie was not set by the scheduler page. "
            "Ensure {{ csrf_token }} is present in main.html."
        )
        return cookie.value

    # --- Without CSRF token: must be rejected ---

    def test_add_delay_rejects_post_without_csrf_token(self):
        """POST to add_delay without a CSRF token must return 403."""
        response = self.enforced.post(
            self.add_delay_url,
            data=json.dumps({
                'orderId': 1,
                'stepNumber': 1,
                'minutes': 10,
                'reason': 'test',
            }),
            content_type='application/json',
        )
        self.assertEqual(
            response.status_code, 403,
            "add_delay accepted a POST with no CSRF token — "
            "CSRF protection is not working."
        )

    def test_update_status_rejects_post_without_csrf_token(self):
        """POST to update_status without a CSRF token must return 403."""
        response = self.enforced.post(
            self.update_status_url,
            data=json.dumps({
                'orderId': 1,
                'status': 'in_progress',
            }),
            content_type='application/json',
        )
        self.assertEqual(
            response.status_code, 403,
            "update_status accepted a POST with no CSRF token — "
            "CSRF protection is not working."
        )

    # --- With a valid CSRF token: must not be rejected with 403 ---

    def test_add_delay_accepts_post_with_valid_csrf_token(self):
        """
        POST with a valid CSRF token must not return 403.
        The view may return 404 (order not found) but not a CSRF rejection.
        """
        token = self._get_csrf_token()
        response = self.enforced.post(
            self.add_delay_url,
            data=json.dumps({
                'orderId': 99999,
                'stepNumber': 1,
                'minutes': 10,
                'reason': 'test',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertNotEqual(
            response.status_code, 403,
            "add_delay returned 403 even with a valid CSRF token."
        )

    def test_update_status_accepts_post_with_valid_csrf_token(self):
        """
        POST with a valid CSRF token must not return 403.
        The view may return 404 (order not found) but not a CSRF rejection.
        """
        token = self._get_csrf_token()
        response = self.enforced.post(
            self.update_status_url,
            data=json.dumps({
                'orderId': 99999,
                'status': 'in_progress',
            }),
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertNotEqual(
            response.status_code, 403,
            "update_status returned 403 even with a valid CSRF token."
        )

    # --- GET requests must never be blocked by CSRF ---

    def test_scheduler_data_get_is_not_blocked(self):
        """GET to the data endpoint must not be affected by CSRF."""
        response = self.enforced.get(reverse('scheduler:data'))
        self.assertNotEqual(response.status_code, 403)


class TestNoCSRFExemptInViews(TestCase):
    """
    Code-level regression guard: csrf_exempt must not appear in
    scheduler/views.py. If someone re-adds it, this test fails.
    """

    def test_csrf_exempt_not_in_scheduler_views(self):
        """
        Scan scheduler/views.py source to confirm @csrf_exempt is absent.
        """
        views_path = os.path.join(
            os.path.dirname(__file__), 'views.py'
        )
        with open(views_path) as f:
            source = f.read()
        self.assertNotIn(
            'csrf_exempt',
            source,
            "csrf_exempt found in scheduler/views.py. "
            "Remove it and use X-CSRFToken in the frontend instead."
        )

    def test_csrf_exempt_import_removed(self):
        """
        Confirm the csrf_exempt import is no longer in scheduler/views.py.
        """
        views_path = os.path.join(
            os.path.dirname(__file__), 'views.py'
        )
        with open(views_path) as f:
            source = f.read()
        self.assertNotIn(
            'from django.views.decorators.csrf import csrf_exempt',
            source,
            "csrf_exempt is still imported in scheduler/views.py."
        )
