import unittest

from app.gui.admin import AdminDashboard


class TestAdminOrganisationMethods(unittest.TestCase):
    def test_academic_organisation_actions_are_exposed(self):
        required_methods = [
            "setup_organisation",
            "setup_academic_years_ui",
            "setup_cycles_ui",
            "setup_levels_ui",
            "setup_classes_ui",
            "activate_year",
            "archive_year",
            "clone_year_structure",
        ]

        for method_name in required_methods:
            self.assertTrue(hasattr(AdminDashboard, method_name))
