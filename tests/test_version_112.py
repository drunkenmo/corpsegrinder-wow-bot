"""Offline-Regressionsprüfungen für die Corpsegrinder-Version 1.0.12.

Ohne Discord-Token, Home Assistant oder Netzwerkkontakt ausführbar.
"""
import ast
import sqlite3
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def parse_functions(names, environment):
    functions = [node for node in TREE.body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
    ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
    exec(compile(ast.Module(body=functions, type_ignores=[]), "bot.py", "exec"), environment)
    return environment


class Version112Tests(unittest.TestCase):
    def test_persistent_meta_tables_and_opt_out(self):
        for piece in (
            "CREATE TABLE IF NOT EXISTS event_meta",
            "CREATE TABLE IF NOT EXISTS notification_preferences",
            "CREATE TABLE IF NOT EXISTS event_reminder_deliveries",
            "INSERT OR IGNORE INTO event_reminder_deliveries",
            'custom_id="corpse_alert_toggle_v112"',
            "@bot.tree.command(name=\"erinnerungen\"",
        ):
            self.assertIn(piece, SOURCE)

    def test_one_hour_then_five_minutes(self):
        self.assertIn("EVENT_RETIRE_SECONDS = 3600", SOURCE)
        self.assertIn("EVENT_DELETE_DELAY = 300", SOURCE)
        self.assertIn("EVENT_REMIND_SECONDS = 900", SOURCE)
        self.assertIn("now >= start + EVENT_RETIRE_SECONDS", SOURCE)
        self.assertIn("done_at+EVENT_DELETE_DELAY", SOURCE)

    def test_automation_is_restart_safe_and_unique(self):
        for piece in (
            "background(event_scheduler_loop())",
            "initialize_scheduler_meta()",
            "_event_processing_locks.setdefault",
            "if cursor.rowcount:",
            "await voice",  # not needed literal, can remove below
        ):
            if piece == "await voice":
                continue
            self.assertIn(piece, SOURCE)
        self.assertIn("VOICE_UNUSED_TTL = 3600", SOURCE)

    def test_only_full_groups_receive_voice_rooms(self):
        self.assertIn("if event_is_full(kind,group_id):", SOURCE)
        self.assertIn("await create_scheduled_voice(kind,group)", SOURCE)
        self.assertIn("if scheduled and not scheduled[2]:", SOURCE)
        self.assertIn("if target.members:", SOURCE)

    def test_owner_only_completion(self):
        self.assertIn("finish_scheduled_group", SOURCE)
        self.assertIn("interaction.user.id != event_owner(group) and not admin(interaction)", SOURCE)
        self.assertIn("corpse_level_finish_placeholder", SOURCE)
        self.assertIn('custom_id=f"corpse_plan_{group_id}_finish"', SOURCE)

    def test_dynamic_three_groups_and_banners(self):
        for piece in (
            "ORDER BY start_utc LIMIT 3",
            "DUNGEON_ART_URL",
            "LEVEL_ART_URL",
            "WELCOME_ART_URL",
            "refresh_event_dashboard(kind)",
        ):
            self.assertIn(piece, SOURCE)
        for name in ("welcome.svg", "dungeons.svg", "levelgruppen.svg"):
            self.assertTrue((ROOT / "assets" / name).exists(), name)

    def test_discard_only_old_guild_category(self):
        self.assertIn('endswith("WOW FOREVER | GILDE")', SOURCE)
        self.assertIn('{"gildenchat","gilden-raids","offiziers-chat"}', SOURCE)
        self.assertIn("if not present.issubset(allowed_names):", SOURCE)

    def test_full_groups_are_tank_healer_three_dd(self):
        sql=sqlite3.connect(":memory:")
        sql.execute("CREATE TABLE planned_signups(group_id INTEGER,user INTEGER,role TEXT)")
        sql.execute("CREATE TABLE level_signups(group_id INTEGER,user INTEGER)")
        sql.executemany("INSERT INTO planned_signups VALUES(?,?,?)",
                        [(1,1,"Tank"), (1,2,"Heiler"),(1,3,"DD"),(1,4,"DD"),(1,5,"DD")])
        sql.executemany("INSERT INTO level_signups VALUES(?,?)",
                        [(2,1),(2,2),(2,3),(2,4),(2,5)])
        env={"db":sql, "PLAN_ROLES": ("Tank","Heiler","DD"),
             "PLAN_LIMITS":{"Tank":1,"Heiler":1,"DD":3}}
        parse_functions({"plan_members","plan_counts","level_players","event_is_full"},env)
        # Hier die Query-Kernlogik per Test-Datenbanken absichern.
        self.assertEqual(env["plan_counts"](1),{"Tank":1,"Heiler":1,"DD":3})
        self.assertEqual(len(env["level_players"](2)),5)
        sql.close()


if __name__ == "__main__":
    unittest.main()
