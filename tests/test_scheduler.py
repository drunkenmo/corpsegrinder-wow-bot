"""Isolierte Tests für Datum/UTC und die Dungeon-Platzberechnung."""
import ast
import calendar
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import sqlite3
import unittest
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SOURCE = Path(__file__).resolve().parents[1] / "corpsegrinder_wow_bot" / "bot.py"
FUNCTIONS = {"last_sunday", "berlin_now", "parse_plan_time", "plan_members", "plan_counts"}


def load_test_functions():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    built = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    env = {
        "calendar": calendar, "datetime": datetime, "timedelta": timedelta,
        "timezone": timezone, "re": re, "ZoneInfo": ZoneInfo,
        "ZoneInfoNotFoundError": ZoneInfoNotFoundError,
        "GUILD_ID": 1234, "PLAN_ROLES": ("Tank", "Heiler", "DD")
    }
    exec(compile(built, str(SOURCE), "exec"), env)
    return env


class ScheduleTests(unittest.TestCase):
    def setUp(self):
        self.f = load_test_functions()

    def test_relative_day_and_utc(self):
        ts, display = self.f["parse_plan_time"]("übermorgen", "20:00")
        self.assertIn("20:00", display)
        self.assertGreater(ts, datetime.now(timezone.utc).timestamp() + 24 * 3600)

    def test_german_absolute_dates(self):
        chosen = (datetime.now(timezone.utc) + timedelta(days=15)).date()
        ts, display = self.f["parse_plan_time"](chosen.strftime("%d.%m.%Y"), "19:30")
        self.assertEqual(datetime.fromtimestamp(ts, ZoneInfo("Europe/Berlin")).hour, 19)
        self.assertIn("19:30", display)

    def test_summer_and_winter_utc(self):
        # Vermeidet Sommer-/Winterzeit-Umrechnungsfehler.
        year = datetime.now(timezone.utc).year + 1
        for month, day, expected_hour in ((1, 15, 19), (7, 15, 18)):
            future_day = datetime(year, month, day).date()
            if (future_day - datetime.now(timezone.utc).date()).days > 120:
                continue
            ts, _ = self.f["parse_plan_time"](future_day.strftime("%d.%m.%Y"), "20:00")
            self.assertEqual(datetime.fromtimestamp(ts, timezone.utc).hour, expected_hour)

    def test_reject_invalid_hour(self):
        with self.assertRaises(ValueError):
            self.f["parse_plan_time"]("übermorgen", "25:99")

    def test_reject_past(self):
        with self.assertRaises(ValueError):
            self.f["parse_plan_time"]("01.01.2020", "20:00")

    def test_dst_unavailable_hour(self):
        year = datetime.now(timezone.utc).year
        day = self.f["last_sunday"](year, 3)
        with self.assertRaises(ValueError):
            self.f["parse_plan_time"](f"{day:02d}.03.{year}", "02:30")

    def test_one_tank_one_healer_three_dd(self):
        env = self.f
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE planned_signups(group_id INTEGER,user INTEGER,role TEXT)")
        db.executemany("INSERT INTO planned_signups VALUES (?,?,?)",
                       [(1, 10, "Tank"), (1, 11, "Heiler"),
                        (1, 12, "DD"), (1, 13, "DD"), (1, 14, "DD")])
        env["db"] = db
        self.assertEqual(env["plan_counts"](1), {"Tank": 1, "Heiler": 1, "DD": 3})
        db.close()


if __name__ == "__main__":
    unittest.main()
