from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import PMTask, Rack, RackPM, RackPMPlan


def make_task(title="Inspect Coating", frequency_days=30):
    return PMTask.objects.create(
        title=title,
        description="Inspect coating condition",
        frequency_days=frequency_days,
    )


def make_rack(rack_id, in_service_date=None):
    return Rack.objects.create(
        rack_id=rack_id,
        description="Test rack",
        in_service_date=in_service_date,
    )


class TestRackListNoNPlusOne(TestCase):
    """
    Verify rack_list executes a fixed number of queries regardless of how many
    racks and PM plans exist.

    B-2 bug: the view called RackPM.objects.filter(rack=rack, pm_task=plan.task)
    inside a nested loop — one query per (rack × plan) combination.
    After the fix, all RackPM rows are prefetched in a single query.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.task = make_task()

        # Create 2 racks with 1 plan and 1 PM history each as baseline
        for i in range(1, 3):
            rack = make_rack(f'R-{i:03d}', in_service_date=date.today() - timedelta(days=90))
            RackPMPlan.objects.create(rack=rack, task=self.task)
            RackPM.objects.create(
                rack=rack,
                pm_task=self.task,
                performed_by=self.user,
                passed=True,
            )

        self.client.force_login(self.user)

    def test_rack_list_query_count_does_not_grow_with_more_racks(self):
        """
        Adding more racks must not increase the query count (proves no N+1).
        """
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get(reverse('rack_list'))
        self.assertEqual(response.status_code, 200)
        small_count = len(ctx_small)

        # Add 3 more racks with plans and history
        task2 = make_task(title="Check Contacts", frequency_days=14)
        for i in range(3, 6):
            rack = make_rack(f'R-{i:03d}', in_service_date=date.today() - timedelta(days=45))
            RackPMPlan.objects.create(rack=rack, task=self.task)
            RackPMPlan.objects.create(rack=rack, task=task2)
            RackPM.objects.create(rack=rack, pm_task=self.task, performed_by=self.user)
            RackPM.objects.create(rack=rack, pm_task=task2, performed_by=self.user)

        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get(reverse('rack_list'))
        self.assertEqual(response.status_code, 200)
        large_count = len(ctx_large)

        self.assertEqual(
            small_count, large_count,
            f"N+1 detected in rack_list: {small_count} queries with 2 racks, "
            f"{large_count} queries with 5 racks (3 with 2 plans each). "
            f"Queries should be constant — check for missing prefetch_related."
        )

    def test_rack_list_returns_overdue_and_upcoming(self):
        """Smoke test: view renders correctly with PM history present."""
        response = self.client.get(reverse('rack_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('racks', response.context)
        self.assertIn('overdue', response.context)
        self.assertIn('upcoming', response.context)
        self.assertIn('stats', response.context)

    def test_rack_list_stats_total_racks_matches(self):
        """stats.total_racks must equal the actual rack count."""
        response = self.client.get(reverse('rack_list'))
        self.assertEqual(response.context['stats']['total_racks'], Rack.objects.count())


class TestPMCalendarNoNPlusOne(TestCase):
    """
    Verify pm_calendar also executes a fixed number of queries.
    Same N+1 pattern as rack_list.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.task = make_task()

        for i in range(1, 3):
            rack = make_rack(f'C-{i:03d}', in_service_date=date.today() - timedelta(days=60))
            RackPMPlan.objects.create(rack=rack, task=self.task)

        self.client.force_login(self.user)

    def test_pm_calendar_query_count_does_not_grow_with_more_racks(self):
        """
        Adding more racks must not increase the query count in pm_calendar.
        """
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get(reverse('pm_calendar'))
        self.assertEqual(response.status_code, 200)
        small_count = len(ctx_small)

        for i in range(3, 6):
            rack = make_rack(f'C-{i:03d}')
            RackPMPlan.objects.create(rack=rack, task=self.task)

        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get(reverse('pm_calendar'))
        self.assertEqual(response.status_code, 200)
        large_count = len(ctx_large)

        self.assertEqual(
            small_count, large_count,
            f"N+1 detected in pm_calendar: {small_count} queries with 2 racks, "
            f"{large_count} queries with 5 racks."
        )

    def test_pm_calendar_returns_events(self):
        """Smoke test: calendar view renders and passes events to template."""
        response = self.client.get(reverse('pm_calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('events', response.context)


# ---------------------------------------------------------------------------
# T-4: PM due-date logic
# ---------------------------------------------------------------------------

def make_pm(rack, task, user, days_ago):
    """Create a RackPM and backdate date_performed by days_ago from today."""
    pm = RackPM.objects.create(rack=rack, pm_task=task, performed_by=user)
    performed = date.today() - timedelta(days=days_ago)
    RackPM.objects.filter(pk=pm.pk).update(date_performed=performed)
    pm.refresh_from_db()
    return pm


def overdue_rack_ids(response):
    return {rack.rack_id for rack, _, _ in response.context['overdue']}


def upcoming_rack_ids(response):
    return {rack.rack_id for rack, _, _ in response.context['upcoming']}


class TestPMDueDateCalculation(TestCase):
    """
    Verify rack_list correctly computes next_due and places each rack in
    overdue, upcoming (within 10 days), or neither.

    Formula:
        next_due = last_pm.date_performed + frequency   (if PM history exists)
        next_due = rack.in_service_date or today        (fallback)
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.task = make_task(title="Inspect Coating", frequency_days=30)
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(reverse('rack_list'))

    # --- overdue ---

    def test_pm_past_due_appears_in_overdue(self):
        """PM done 40 days ago with 30-day frequency → next_due 10 days ago → overdue."""
        rack = make_rack('R-OVERDUE')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=40)

        response = self._get()
        self.assertIn('R-OVERDUE', overdue_rack_ids(response))
        self.assertNotIn('R-OVERDUE', upcoming_rack_ids(response))

    def test_pm_past_due_is_not_in_upcoming(self):
        """An overdue rack must not also appear in upcoming."""
        rack = make_rack('R-OVERDUE2')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=50)

        response = self._get()
        self.assertNotIn('R-OVERDUE2', upcoming_rack_ids(response))

    # --- upcoming ---

    def test_pm_due_today_appears_in_upcoming(self):
        """PM done exactly 30 days ago → next_due = today → upcoming."""
        rack = make_rack('R-TODAY')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=30)

        response = self._get()
        self.assertIn('R-TODAY', upcoming_rack_ids(response))
        self.assertNotIn('R-TODAY', overdue_rack_ids(response))

    def test_pm_due_in_5_days_appears_in_upcoming(self):
        """PM done 25 days ago → next_due in 5 days → within 10-day window → upcoming."""
        rack = make_rack('R-SOON')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=25)

        response = self._get()
        self.assertIn('R-SOON', upcoming_rack_ids(response))

    def test_pm_due_in_exactly_10_days_appears_in_upcoming(self):
        """Boundary: next_due = today + 10 is still within the upcoming window."""
        rack = make_rack('R-BOUNDARY')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=20)  # 30 - 20 = 10 days from now

        response = self._get()
        self.assertIn('R-BOUNDARY', upcoming_rack_ids(response))

    # --- neither ---

    def test_pm_not_yet_due_not_in_overdue_or_upcoming(self):
        """PM done 5 days ago → next_due in 25 days → outside window → neither."""
        rack = make_rack('R-FINE')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=5)

        response = self._get()
        self.assertNotIn('R-FINE', overdue_rack_ids(response))
        self.assertNotIn('R-FINE', upcoming_rack_ids(response))

    def test_pm_due_in_11_days_is_not_upcoming(self):
        """Boundary: next_due = today + 11 is just outside the window."""
        rack = make_rack('R-OUTSIDE')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=19)  # 30 - 19 = 11 days from now

        response = self._get()
        self.assertNotIn('R-OUTSIDE', upcoming_rack_ids(response))
        self.assertNotIn('R-OUTSIDE', overdue_rack_ids(response))

    # --- fallback: no PM history ---

    def test_no_pm_uses_in_service_date_overdue(self):
        """No PM history, in_service_date 40 days ago → overdue."""
        rack = make_rack('R-INSERVICE', in_service_date=date.today() - timedelta(days=40))
        RackPMPlan.objects.create(rack=rack, task=self.task)

        response = self._get()
        self.assertIn('R-INSERVICE', overdue_rack_ids(response))

    def test_no_pm_uses_in_service_date_upcoming(self):
        """No PM history, in_service_date today → next_due = today → upcoming."""
        rack = make_rack('R-INSERVICE2', in_service_date=date.today())
        RackPMPlan.objects.create(rack=rack, task=self.task)

        response = self._get()
        self.assertIn('R-INSERVICE2', upcoming_rack_ids(response))

    def test_no_pm_no_in_service_date_falls_back_to_today(self):
        """No PM, no in_service_date → next_due = today → appears in upcoming."""
        rack = make_rack('R-NODATE')
        RackPMPlan.objects.create(rack=rack, task=self.task)

        response = self._get()
        self.assertIn('R-NODATE', upcoming_rack_ids(response))

    # --- frequency override ---

    def test_plan_due_every_days_overrides_task_frequency(self):
        """RackPMPlan.due_every_days takes precedence over PMTask.frequency_days."""
        rack = make_rack('R-OVERRIDE')
        # Task has 30-day frequency but plan overrides to 7 days
        RackPMPlan.objects.create(rack=rack, task=self.task, due_every_days=7)
        make_pm(rack, self.task, self.user, days_ago=10)  # 10 > 7 → overdue with override

        response = self._get()
        self.assertIn('R-OVERRIDE', overdue_rack_ids(response))

    def test_plan_without_override_uses_task_frequency(self):
        """When due_every_days is None, falls back to task.frequency_days."""
        rack = make_rack('R-NOOVERRIDE')
        RackPMPlan.objects.create(rack=rack, task=self.task, due_every_days=None)
        make_pm(rack, self.task, self.user, days_ago=10)  # 10 < 30 → not overdue

        response = self._get()
        self.assertNotIn('R-NOOVERRIDE', overdue_rack_ids(response))

    # --- most recent PM is used ---

    def test_most_recent_pm_is_used_not_oldest(self):
        """When a rack has multiple PMs, the most recent date_performed is used."""
        rack = make_rack('R-MULTI')
        RackPMPlan.objects.create(rack=rack, task=self.task)
        make_pm(rack, self.task, self.user, days_ago=60)   # old — would be overdue
        make_pm(rack, self.task, self.user, days_ago=5)    # recent — not yet due

        response = self._get()
        # The recent PM means it's not overdue
        self.assertNotIn('R-MULTI', overdue_rack_ids(response))
        self.assertNotIn('R-MULTI', upcoming_rack_ids(response))

    # --- multiple tasks on one rack ---

    def test_each_task_has_independent_due_date(self):
        """Two plans on the same rack produce independent due-date entries."""
        task_overdue = make_task(title="Task Overdue", frequency_days=30)
        task_fine = make_task(title="Task Fine", frequency_days=30)
        rack = make_rack('R-TWOTASKS')
        RackPMPlan.objects.create(rack=rack, task=task_overdue)
        RackPMPlan.objects.create(rack=rack, task=task_fine)
        make_pm(rack, task_overdue, self.user, days_ago=40)  # overdue
        make_pm(rack, task_fine, self.user, days_ago=5)      # fine

        response = self._get()
        overdue_entries = [(r.rack_id, t) for r, t, _ in response.context['overdue']]
        self.assertIn(('R-TWOTASKS', 'Task Overdue'), overdue_entries)
        # task_fine must NOT appear in overdue
        self.assertNotIn(('R-TWOTASKS', 'Task Fine'),
                         [(r.rack_id, t) for r, t, _ in response.context['overdue']])

    # --- stats ---

    def test_stats_counts_match_list_lengths(self):
        """stats.total_overdue and total_upcoming must match the actual list lengths."""
        rack1 = make_rack('R-STAT1')
        rack2 = make_rack('R-STAT2')
        RackPMPlan.objects.create(rack=rack1, task=self.task)
        RackPMPlan.objects.create(rack=rack2, task=self.task)
        make_pm(rack1, self.task, self.user, days_ago=45)  # overdue
        make_pm(rack2, self.task, self.user, days_ago=28)  # upcoming (due in 2 days)

        response = self._get()
        stats = response.context['stats']
        self.assertEqual(stats['total_overdue'], len(response.context['overdue']))
        self.assertEqual(stats['total_upcoming'], len(response.context['upcoming']))
        self.assertEqual(stats['total_racks'], Rack.objects.count())
