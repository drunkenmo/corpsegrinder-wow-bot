"""Offline tests for Corpsegrinder 1.0.11 – Voice creator, dungeon move, leveling."""
import ast
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
import unittest

BOT = Path(__file__).resolve().parents[1] / "corpsegrinder_wow_bot" / "bot.py"


def inspect_code():
    source = BOT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return source, tree


def isolate_functions(function_names, context):
    source, tree = inspect_code()
    nodes = [
        item for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name in function_names]
    ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(BOT), "exec"), context)
    return context


class VoiceAndLevelTests(unittest.TestCase):
    def test_voice_user_is_moved_and_permissions_checked(self):
        s, _ = inspect_code()
        self.assertIn("async def on_voice_state_update(", s)
        self.assertIn("perms.move_members", s)
        self.assertIn("new_channel.permissions_for(bot_member)", s)
        self.assertIn("await member.move_to(", s)
        self.assertIn("background(delete_temp_if_empty(", s)
        self.assertIn("discord.ClientException", s)

    def test_dungeon_planer_is_in_dungeons(self):
        s, _ = inspect_code()
        self.assertIn('target = channel(guild, "dungeon-planer")', s)
        self.assertIn('async def ensure_planner_dashboard(guild):\n    target = channel(guild, "dungeon-planer")', s)
        self.assertIn('old_channel = channel(guild, "pve-gruppensuche")', s)

    def test_level_group_tables_exist(self):
        s, _ = inspect_code()
        self.assertIn('CREATE TABLE IF NOT EXISTS level_groups', s)
        self.assertIn('CREATE TABLE IF NOT EXISTS level_signups', s)
        self.assertIn('PRIMARY KEY(group_id,user)', s)

    def test_level_zone_choices_and_time_select_limits(self):
        source, tree = inspect_code()
        zone = next(
            node for node in tree.body if isinstance(node, ast.Assign) and
            any(isinstance(x, ast.Name) and x.id == "LEVEL_AREAS" for x in node.targets))
        areas = ast.literal_eval(zone.value)
        self.assertGreaterEqual(len(areas), 20)
        self.assertLessEqual(len(areas), 25)
        self.assertIn("Brachland", areas)
        self.assertIn("Schlingendorntal", areas)
        self.assertIn("for ix in range(21)", source)
        self.assertIn("for h in range(24)", source)
        self.assertIn("for m in (0, 15, 30, 45)", source)

    def test_level_group_reservation_limit_and_db(self):
        memory = sqlite3.connect(":memory:")
        memory.execute("CREATE TABLE level_signups(group_id INTEGER,user INTEGER)")
        memory.executemany(
            "INSERT INTO level_signups VALUES (?,?)",
            [(1, 10), (1, 11), (1, 12), (1, 13), (1, 14)])
        env = {"db": memory, "datetime": datetime, "timezone": timezone}
        isolate_functions(["level_players", "level_open"], env)
        self.assertEqual(len(env["level_players"](1)), 5)
        now = int(datetime.now(timezone.utc).timestamp())
        record = (1, 123, 10, "Brachland", 10, 20, now + 3600, "", "", 1, 2, "open")
        self.assertTrue(env["level_open"](record))
        self.assertFalse(env["level_open"](record[:-1] + ("cancelled",)))
        memory.close()

    def test_ui_and_restart_hooks(self):
        s, _ = inspect_code()
        for snippet in (
            "class LevelDashboardView(discord.ui.View)",
            "class LevelGroupView(discord.ui.View)",
            "class LevelWizardOne(LevelPrivateWizard)",
            "class LevelWizardTwo(LevelPrivateWizard)",
            "bot.add_view(LevelDashboardView())",
            "bot.add_view(level_group_view(group_id), message_id=message_id)",
            "background(ensure_level_dashboard_on_start())",
            'custom_id="corpse_level_dashboard_new_v111"',
            'custom_id="corpse_level_dashboard_upcoming_v111"',
            'custom_id="corpse_level_dashboard_mine_v111"',
        ):
            self.assertIn(snippet, s)


if __name__ == "__main__":
    unittest.main()
