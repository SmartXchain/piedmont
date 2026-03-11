from django.test import TestCase

from .models import Method, ParameterTemplate, ParameterToBeRecorded


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def make_template(category="Electroplating", description="Record plating current (amps)",
                  is_nadcap_required=False):
    return ParameterTemplate.objects.create(
        category=category,
        description=description,
        is_nadcap_required=is_nadcap_required,
    )


def make_method(title="Cadmium Plate Tank", category=None,
                method_type="processing_tank"):
    return Method.objects.create(
        title=title,
        method_type=method_type,
        category=category,
    )


# ---------------------------------------------------------------------------
# T-3: Case A — new Method with category auto-creates ParameterToBeRecorded
# ---------------------------------------------------------------------------

class TestNewMethodAutoCreatesParameter(TestCase):
    """
    Case A: when a Method is created with a category set, save() must call
    create_required_parameters_from_template() and produce exactly one
    ParameterToBeRecorded if a matching ParameterTemplate exists.
    """

    def setUp(self):
        self.template = make_template(
            category="Electroplating",
            description="Record plating current (amps)",
            is_nadcap_required=True,
        )

    def test_creates_parameter_on_new_method_with_category(self):
        method = make_method(category="Electroplating")
        self.assertEqual(method.recorded_parameters.count(), 1)

    def test_created_parameter_copies_description_from_template(self):
        method = make_method(category="Electroplating")
        param = method.recorded_parameters.get()
        self.assertEqual(param.description, self.template.description)

    def test_created_parameter_copies_nadcap_flag_from_template(self):
        method = make_method(category="Electroplating")
        param = method.recorded_parameters.get()
        self.assertTrue(param.is_nadcap_required)

    def test_no_parameter_created_when_no_category(self):
        method = make_method(category=None)
        self.assertEqual(method.recorded_parameters.count(), 0)

    def test_no_parameter_created_when_no_matching_template(self):
        """Category set but no ParameterTemplate for it → no param created."""
        method = make_method(category="Cleaning")  # no template for Cleaning
        self.assertEqual(method.recorded_parameters.count(), 0)

    def test_no_parameter_created_when_template_has_empty_description(self):
        ParameterTemplate.objects.create(category="Anodize", description="")
        method = make_method(title="Anodize Tank", category="Anodize")
        self.assertEqual(method.recorded_parameters.count(), 0)

    def test_only_one_parameter_created_not_duplicates(self):
        """Exactly one ParameterToBeRecorded per template match."""
        method = make_method(category="Electroplating")
        self.assertEqual(method.recorded_parameters.count(), 1)

    def test_parameter_is_linked_to_correct_method(self):
        method = make_method(category="Electroplating")
        param = method.recorded_parameters.get()
        self.assertEqual(param.method, method)


# ---------------------------------------------------------------------------
# T-3: Case B — assigning category to an existing Method triggers creation
# ---------------------------------------------------------------------------

class TestCategoryAssignedToExistingMethod(TestCase):
    """
    Case B: an existing Method that previously had no category must have
    parameters auto-created when a category is assigned for the first time.
    """

    def setUp(self):
        self.template = make_template(
            category="Electroplating",
            description="Record plating current (amps)",
        )
        # Method starts with no category — no params created yet
        self.method = make_method(category=None)

    def test_no_params_before_category_assigned(self):
        self.assertEqual(self.method.recorded_parameters.count(), 0)

    def test_params_created_when_category_assigned(self):
        self.method.category = "Electroplating"
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 1)

    def test_params_not_created_when_category_assigned_but_no_template(self):
        self.method.category = "Cleaning"  # no template for Cleaning
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 0)

    def test_resaving_same_category_does_not_duplicate_params(self):
        """
        If a method already has parameters, re-saving with the same category
        must not create duplicates (idempotent guard).
        """
        self.method.category = "Electroplating"
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 1)
        # Save again with same category
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 1)


# ---------------------------------------------------------------------------
# T-3: Case C — changing category overwrites existing parameters
# ---------------------------------------------------------------------------

class TestCategoryChangeOverwritesParameters(TestCase):
    """
    Case C: when a Method's category changes, save() must call
    create_required_parameters_from_template(force=True), which deletes
    the old parameters and creates new ones from the new template.
    """

    def setUp(self):
        self.old_template = make_template(
            category="Electroplating",
            description="Record plating current (amps)",
            is_nadcap_required=True,
        )
        self.new_template = make_template(
            category="Cleaning",
            description="Record bath temperature (°F)",
            is_nadcap_required=False,
        )
        self.method = make_method(category="Electroplating")

    def test_initial_parameter_from_old_template(self):
        param = self.method.recorded_parameters.get()
        self.assertEqual(param.description, self.old_template.description)

    def test_changing_category_replaces_parameters(self):
        self.method.category = "Cleaning"
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 1)
        param = self.method.recorded_parameters.get()
        self.assertEqual(param.description, self.new_template.description)

    def test_old_parameter_is_deleted_after_category_change(self):
        old_param_id = self.method.recorded_parameters.get().pk
        self.method.category = "Cleaning"
        self.method.save()
        self.assertFalse(
            ParameterToBeRecorded.objects.filter(pk=old_param_id).exists()
        )

    def test_changing_category_to_one_with_no_template_deletes_old_params(self):
        """Switching to a category with no template → old params deleted, none created."""
        self.method.category = "Masking"  # no template for Masking
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 0)

    def test_updating_non_category_fields_does_not_change_params(self):
        """Changing title/description without touching category must not touch params."""
        original_param = self.method.recorded_parameters.get()
        self.method.title = "Updated Plate Tank"
        self.method.save()
        self.assertEqual(self.method.recorded_parameters.count(), 1)
        self.assertEqual(self.method.recorded_parameters.get().pk, original_param.pk)


# ---------------------------------------------------------------------------
# T-3: create_required_parameters_from_template() — direct unit tests
# ---------------------------------------------------------------------------

class TestCreateRequiredParametersFromTemplate(TestCase):
    """
    Unit tests for Method.create_required_parameters_from_template().
    Tests force=True and force=False behaviour directly.
    """

    def setUp(self):
        self.template = make_template(
            category="Electroplating",
            description="Record plating current (amps)",
        )
        self.method = make_method(category="Electroplating")

    def test_force_false_is_idempotent_when_params_exist(self):
        """Calling without force when params exist must be a no-op."""
        self.assertEqual(self.method.recorded_parameters.count(), 1)
        self.method.create_required_parameters_from_template(force=False)
        self.assertEqual(self.method.recorded_parameters.count(), 1)

    def test_force_true_deletes_and_recreates_params(self):
        """force=True must delete existing params and recreate from template."""
        existing_pk = self.method.recorded_parameters.get().pk
        self.method.create_required_parameters_from_template(force=True)
        self.assertEqual(self.method.recorded_parameters.count(), 1)
        new_pk = self.method.recorded_parameters.get().pk
        self.assertNotEqual(existing_pk, new_pk)

    def test_no_op_when_method_has_no_category(self):
        method = make_method(title="No Category Method", category=None)
        method.create_required_parameters_from_template()
        self.assertEqual(method.recorded_parameters.count(), 0)
