"""Verhindert Regressionsfehler im persistenten Dropdown-Dungeonplaner.

Der Test braucht weder Discord-Zugang noch die discord.py-Installation.
"""
import ast
from pathlib import Path
import unittest

BOT = Path(__file__).resolve().parents[1] / "corpsegrinder_wow_bot" / "bot.py"


class PlannerDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BOT.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.classes = {
            node.name: node for node in cls.tree.body
            if isinstance(node, ast.ClassDef)
        }
        cls.functions = {
            node.name: node for node in cls.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_wizard_and_dashboard_types_present(self):
        for name in ("PrivateWizard", "WizardStepOne", "WizardStepTwo",
                     "PlannerDashboardView", "CustomInstanceModal", "WizardSelect"):
            self.assertIn(name, self.classes)

    def test_persistent_public_buttons_have_ids(self):
        self.assertIn('custom_id="corpse_planner_new_v110"', self.source)
        self.assertIn('custom_id="corpse_planner_upcoming_v110"', self.source)
        self.assertIn('custom_id="corpse_planner_mine_v110"', self.source)
        self.assertIn("bot.add_view(PlannerDashboardView())", self.source)
        self.assertIn('super().__init__(timeout=None)', self.source)

    def test_dropdown_option_limits(self):
        self.assertIn("for index in range(21)", self.source)
        self.assertIn("for n in range(24)", self.source)
        self.assertIn("for n in (0, 15, 30, 45)", self.source)
        self.assertIn("for name in COMMON_DUNGEONS[:25]", self.source)

    def test_private_draft_must_not_post_before_submit(self):
        self.assertIn("async def interaction_check(self, interaction)", self.source)
        self.assertIn('interaction.user.id == self.state["owner"]', self.source)
        self.assertIn("async with plan_lock(-interaction.user.id)", self.source)
        self.assertIn('state["published"] = True', self.source)

    def test_dashboard_is_idempotent_and_pin_optional(self):
        self.assertIn("PLANNER_STORAGE_KEY", self.source)
        self.assertIn("ensure_planner_dashboard(guild)", self.source)
        self.assertIn("await existing.pin(", self.source)
        self.assertIn("except discord.Forbidden:", self.source)

    def test_same_publishing_path_for_slash_and_wizard(self):
        self.assertIn("create_plan_record_and_post", self.functions)
        self.assertGreaterEqual(
            self.source.count("await create_plan_record_and_post("), 2)

    def test_current_groups_remain_supported(self):
        for name in ("create_planned_group", "upcoming_plans", "cancel_planned_group",
                     "reschedule_planned_group", "plan_signup"):
            self.assertIn(name, self.functions)


if __name__ == "__main__":
    unittest.main()
