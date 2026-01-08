# drawings/tests.py
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Drawing, DrawingZone


User = get_user_model()


class DrawingAnnotatorTests(TestCase):
    def setUp(self):
        self.engineer = User.objects.create_user(
            username="engineer",
            password="pass1234",
            is_staff=True,
        )
        self.operator = User.objects.create_user(
            username="operator",
            password="pass1234",
            is_staff=False,
        )

        self.drawing = Drawing.objects.create(
            drawing_number="DWG-1001",
            title="Test Drawing",
            revision="A",
            # pdf_file not required to test endpoints; annotate page renders without it too.
            is_active=True,
            uploaded_by=self.engineer,
        )

    def test_annotate_view_requires_staff(self):
        url = reverse("drawings:annotate", kwargs={"drawing_id": self.drawing.id})

        # Not logged in -> redirect to login
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 301))

        # Logged in as operator -> forbidden by user_passes_test (redirect)
        self.client.login(username="operator", password="pass1234")
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (302, 301))

        # Logged in as engineer -> OK
        self.client.login(username="engineer", password="pass1234")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_create_list_delete_rect_zone(self):
        self.client.login(username="engineer", password="pass1234")

        save_url = reverse("drawings:save_zone", kwargs={"drawing_id": self.drawing.id})
        list_url = reverse("drawings:zones_json", kwargs={"drawing_id": self.drawing.id})

        payload = {
            "page_number": 1,
            "label": "Zone A - Outside surfaces",
            "geom_type": "rect",
            "geometry": {"x": 0.10, "y": 0.20, "w": 0.30, "h": 0.25},
            "area_value": "12.5000",
            "area_unit": "in2",
            "is_exclusion_zone": False,
            "default_selected": True,
            "notes": "Includes both sides; excludes threads.",
        }

        # Create
        resp = self.client.post(
            save_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        zone_id = data["zone"]["id"]
        self.assertTrue(DrawingZone.objects.filter(id=zone_id).exists())

        # List for page 1
        resp = self.client.get(list_url, {"page": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["zones"]), 1)
        self.assertEqual(data["zones"][0]["id"], zone_id)
        self.assertEqual(data["zones"][0]["geom_type"], "rect")

        # Delete
        del_url = reverse("drawings:delete_zone", kwargs={"drawing_id": self.drawing.id, "zone_id": zone_id})
        resp = self.client.post(del_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertFalse(DrawingZone.objects.filter(id=zone_id).exists())

    def test_operator_cannot_create_zone(self):
        self.client.login(username="operator", password="pass1234")
        save_url = reverse("drawings:save_zone", kwargs={"drawing_id": self.drawing.id})

        payload = {
            "page_number": 1,
            "label": "Should Fail",
            "geom_type": "rect",
            "geometry": {"x": 0.10, "y": 0.10, "w": 0.10, "h": 0.10},
            "area_value": "1.0",
            "area_unit": "in2",
            "is_exclusion_zone": False,
            "default_selected": True,
            "notes": "",
        }

        resp = self.client.post(
            save_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        # user_passes_test usually redirects to login by default
        self.assertIn(resp.status_code, (302, 301))
        self.assertEqual(DrawingZone.objects.count(), 0)
