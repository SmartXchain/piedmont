from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import ChemicalLot, Product


def make_product(name="Chromic Acid", trigger_level=10):
    return Product.objects.create(
        name=name,
        trigger_level=trigger_level,
        min_quantity=5,
        max_quantity=50,
    )


def make_lot(product, quantity=20, days_until_expiry=30):
    expiry = date.today() + timedelta(days=days_until_expiry)
    return ChemicalLot.objects.create(
        product=product,
        lot_number=f"LOT-{product.id}-{quantity}",
        quantity=quantity,
        expiry_date=expiry,
    )


class TestKanbanDashboardNoNPlusOne(TestCase):
    """
    Verify kanban_dashboard executes a fixed number of queries regardless of
    how many products and lots exist.

    B-3 bug: Product.objects.all() with no prefetch caused one query per product
    for every call to chemical_lots.all() (total_quantity, is_expiring_soon,
    is_expired). After the fix, all lots are prefetched in a single query.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')

        # Baseline: 2 products with 2 lots each
        for i in range(1, 3):
            p = make_product(name=f"Chemical {i}")
            make_lot(p, quantity=20, days_until_expiry=60)
            make_lot(p, quantity=5, days_until_expiry=4)   # expiring soon

        self.client.force_login(self.user)

    def test_dashboard_query_count_does_not_grow_with_more_products(self):
        """
        Adding more products and lots must not increase the query count.
        """
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get(reverse('kanban_dashboard'))
        self.assertEqual(response.status_code, 200)
        small_count = len(ctx_small)

        # Add 3 more products with 3 lots each
        for i in range(3, 6):
            p = make_product(name=f"Chemical {i}")
            make_lot(p, quantity=25, days_until_expiry=90)
            make_lot(p, quantity=3, days_until_expiry=3)   # expiring soon
            make_lot(p, quantity=0, days_until_expiry=-5)  # expired (past date)

        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get(reverse('kanban_dashboard'))
        self.assertEqual(response.status_code, 200)
        large_count = len(ctx_large)

        self.assertEqual(
            small_count, large_count,
            f"N+1 detected in kanban_dashboard: {small_count} queries with 2 products, "
            f"{large_count} queries with 5 products. "
            f"Queries should be constant — check for missing prefetch_related."
        )

    def test_dashboard_categorizes_products_correctly(self):
        """Products are placed into the correct status buckets."""
        response = self.client.get(reverse('kanban_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('available_products', response.context)
        self.assertIn('expiring_soon_products', response.context)
        self.assertIn('expired_products', response.context)
        self.assertIn('needs_reorder_products', response.context)

    def test_expiring_soon_product_appears_in_correct_bucket(self):
        """A product with a lot expiring within 7 days must appear in expiring_soon."""
        p = make_product(name="Soon-To-Expire Chemical", trigger_level=5)
        make_lot(p, quantity=50, days_until_expiry=3)  # within 7-day window

        response = self.client.get(reverse('kanban_dashboard'))
        expiring_names = [prod.name for prod in response.context['expiring_soon_products']]
        self.assertIn("Soon-To-Expire Chemical", expiring_names)

    def test_expired_product_appears_in_correct_bucket(self):
        """A product with an expired lot must appear in expired_products."""
        p = make_product(name="Expired Chemical", trigger_level=5)
        make_lot(p, quantity=10, days_until_expiry=-10)  # already expired

        response = self.client.get(reverse('kanban_dashboard'))
        expired_names = [prod.name for prod in response.context['expired_products']]
        self.assertIn("Expired Chemical", expired_names)


class TestProductListNoNPlusOne(TestCase):
    """
    Verify product_list executes a fixed number of queries.
    Product.__str__ calls chemical_lots.all(), creating an N+1 if not prefetched.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')

        for i in range(1, 3):
            p = make_product(name=f"Product {i}")
            make_lot(p, quantity=15)

        self.client.force_login(self.user)

    def test_product_list_query_count_does_not_grow_with_more_products(self):
        """
        Adding more products must not increase the query count.
        """
        with CaptureQueriesContext(connection) as ctx_small:
            response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        small_count = len(ctx_small)

        for i in range(3, 7):
            p = make_product(name=f"Product {i}")
            make_lot(p, quantity=10)
            make_lot(p, quantity=5)

        with CaptureQueriesContext(connection) as ctx_large:
            response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        large_count = len(ctx_large)

        self.assertEqual(
            small_count, large_count,
            f"N+1 detected in product_list: {small_count} queries with 2 products, "
            f"{large_count} queries with 6 products."
        )


class TestIsExpiringSoonMethod(TestCase):
    """Unit tests for ChemicalLot.is_expiring_soon()."""

    def setUp(self):
        self.product = make_product()

    def test_lot_expiring_in_3_days_is_expiring_soon(self):
        lot = make_lot(self.product, days_until_expiry=3)
        self.assertTrue(lot.is_expiring_soon())

    def test_lot_expiring_in_30_days_is_not_expiring_soon(self):
        lot = make_lot(self.product, days_until_expiry=30)
        self.assertFalse(lot.is_expiring_soon())

    def test_expired_lot_is_not_expiring_soon(self):
        """An already-expired lot is 'Expired', not 'Expiring Soon'."""
        lot = make_lot(self.product, days_until_expiry=-5)
        self.assertFalse(lot.is_expiring_soon())
        self.assertTrue(lot.is_expired())

    def test_lot_with_no_expiry_date_is_not_expiring_soon(self):
        lot = ChemicalLot.objects.create(
            product=self.product,
            lot_number="NO-EXPIRY",
            quantity=10,
            expiry_date=None,
        )
        self.assertFalse(lot.is_expiring_soon())


# ---------------------------------------------------------------------------
# T-5: Stock level and expiry logic
# ---------------------------------------------------------------------------

class TestChemicalLotStatus(TestCase):
    """
    Unit tests for ChemicalLot.status, is_expired(), and is_expiring_soon().

    Status rules:
      used_up=True                         → "Used Up"
      expiry_date < today                  → "Expired"
      today < expiry_date <= today + 7d    → "Expiring Soon"
      otherwise                            → "Available"
    """

    def setUp(self):
        self.product = make_product()

    def test_status_available_when_expiry_far_away(self):
        lot = make_lot(self.product, days_until_expiry=30)
        self.assertEqual(lot.status, "Available")

    def test_status_expiring_soon_at_boundary_day_7(self):
        """Exactly 7 days out is still 'Expiring Soon'."""
        lot = make_lot(self.product, days_until_expiry=7)
        self.assertEqual(lot.status, "Expiring Soon")

    def test_status_available_at_day_8(self):
        """8 days out is outside the window — Available."""
        lot = make_lot(self.product, days_until_expiry=8)
        self.assertEqual(lot.status, "Available")

    def test_status_expiring_soon_at_day_1(self):
        lot = make_lot(self.product, days_until_expiry=1)
        self.assertEqual(lot.status, "Expiring Soon")

    def test_status_expired_when_past_date(self):
        lot = make_lot(self.product, days_until_expiry=-1)
        self.assertEqual(lot.status, "Expired")

    def test_status_used_up_takes_precedence_over_expiry(self):
        """used_up=True overrides expiry status."""
        lot = ChemicalLot.objects.create(
            product=self.product,
            lot_number="USED-UP",
            quantity=0,
            expiry_date=date.today() - timedelta(days=10),
            used_up=True,
        )
        self.assertEqual(lot.status, "Used Up")
        self.assertFalse(lot.is_expired())
        self.assertFalse(lot.is_expiring_soon())

    def test_status_available_when_no_expiry_date(self):
        lot = ChemicalLot.objects.create(
            product=self.product,
            lot_number="NO-EXP-2",
            quantity=10,
            expiry_date=None,
        )
        self.assertEqual(lot.status, "Available")


class TestProductTotalQuantity(TestCase):
    """Unit tests for Product.total_quantity."""

    def setUp(self):
        self.product = make_product(trigger_level=10)

    def test_total_quantity_with_no_lots_is_zero(self):
        self.assertEqual(self.product.total_quantity, 0)

    def test_total_quantity_sums_all_lot_quantities(self):
        make_lot(self.product, quantity=15, days_until_expiry=60)
        make_lot(self.product, quantity=5, days_until_expiry=30)
        self.assertEqual(self.product.total_quantity, 20)

    def test_total_quantity_includes_used_up_lots(self):
        """used_up flag is a UI indicator; quantity still counts toward total."""
        ChemicalLot.objects.create(
            product=self.product,
            lot_number="USED",
            quantity=8,
            used_up=True,
        )
        make_lot(self.product, quantity=5, days_until_expiry=30)
        self.assertEqual(self.product.total_quantity, 13)

    def test_total_quantity_includes_expired_lots(self):
        """Expired lots are still counted in total_quantity."""
        make_lot(self.product, quantity=10, days_until_expiry=-5)
        make_lot(self.product, quantity=5, days_until_expiry=60)
        self.assertEqual(self.product.total_quantity, 15)


class TestProductNeedsReorder(TestCase):
    """
    Unit tests for Product.needs_reorder.

    Rule: needs_reorder = total_quantity <= trigger_level
    """

    def setUp(self):
        self.product = make_product(trigger_level=10)

    def test_needs_reorder_when_stock_below_trigger(self):
        make_lot(self.product, quantity=5, days_until_expiry=60)
        self.assertTrue(self.product.needs_reorder)

    def test_needs_reorder_when_stock_equals_trigger(self):
        """Exactly at the trigger level still triggers reorder."""
        make_lot(self.product, quantity=10, days_until_expiry=60)
        self.assertTrue(self.product.needs_reorder)

    def test_no_reorder_when_stock_above_trigger(self):
        make_lot(self.product, quantity=11, days_until_expiry=60)
        self.assertFalse(self.product.needs_reorder)

    def test_needs_reorder_when_no_lots(self):
        """Zero stock is always below any positive trigger level."""
        self.assertTrue(self.product.needs_reorder)


class TestDashboardStockBuckets(TestCase):
    """
    Verify kanban_dashboard places products into correct buckets based on
    stock level vs. trigger_level.

    available_products:      total_quantity > trigger_level
    needs_reorder_products:  total_quantity <= trigger_level
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.client.force_login(self.user)

    def _get(self):
        return self.client.get(reverse('kanban_dashboard'))

    def test_product_above_trigger_is_available(self):
        p = make_product(name="Plentiful Chemical", trigger_level=10)
        make_lot(p, quantity=20, days_until_expiry=60)

        response = self._get()
        available_names = [
            prod.name for prod in response.context['available_products']
        ]
        self.assertIn("Plentiful Chemical", available_names)
        needs_reorder_names = [
            prod.name for prod in response.context['needs_reorder_products']
        ]
        self.assertNotIn("Plentiful Chemical", needs_reorder_names)

    def test_product_at_trigger_is_in_needs_reorder_not_available(self):
        """Stock exactly at trigger level → needs_reorder, not available."""
        p = make_product(name="Borderline Chemical", trigger_level=10)
        make_lot(p, quantity=10, days_until_expiry=60)

        response = self._get()
        needs_reorder_names = [
            prod.name for prod in response.context['needs_reorder_products']
        ]
        self.assertIn("Borderline Chemical", needs_reorder_names)
        available_names = [
            prod.name for prod in response.context['available_products']
        ]
        self.assertNotIn("Borderline Chemical", available_names)

    def test_product_with_no_stock_is_in_needs_reorder(self):
        make_product(name="Empty Chemical", trigger_level=10)

        response = self._get()
        needs_reorder_names = [
            prod.name for prod in response.context['needs_reorder_products']
        ]
        self.assertIn("Empty Chemical", needs_reorder_names)

    def test_product_with_one_unit_above_trigger_is_available(self):
        """One unit above trigger → available, not needs_reorder."""
        p = make_product(name="Just Enough Chemical", trigger_level=10)
        make_lot(p, quantity=11, days_until_expiry=60)

        response = self._get()
        available_names = [
            prod.name for prod in response.context['available_products']
        ]
        self.assertIn("Just Enough Chemical", available_names)
