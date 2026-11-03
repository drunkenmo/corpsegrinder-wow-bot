"""Offline regression tests for Corpsegrinder 1.0.16 ingame names.

These tests use the real unchanged character schema with new sidecar tables.
No token, discord.py, Internet, or Home Assistant is required.
"""
import ast
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTIONS = {
    "normalize_character_name", "user_characters", "owned_character",
    "main_character", "select_main_character", "ensure_main_character",
    "remember_group_character", "forget_group_character", "chosen_character",
    "character_member_line", "ingame_server_nickname"
}


def load_profiles():
    db = sqlite3.connect(":memory:")
    db.execute(
        "CREATE TABLE characters("
        "guild INTEGER,user INTEGER,name TEXT COLLATE NOCASE,klass TEXT,"
        "level INTEGER,beruf1 TEXT,beruf2 TEXT,"
        "PRIMARY KEY(guild,user,name))")
    db.execute(
        "CREATE TABLE main_characters("
        "guild INTEGER,user INTEGER,name TEXT COLLATE NOCASE,"
        "PRIMARY KEY(guild,user))")
    db.execute(
        "CREATE TABLE group_character_choices("
        "kind TEXT,group_id INTEGER,user INTEGER,name TEXT COLLATE NOCASE,"
        "PRIMARY KEY(kind,group_id,user))")
    db.execute(
        "CREATE TABLE planned_signups("
        "group_id INTEGER,user INTEGER,role TEXT,PRIMARY KEY(group_id,user))")
    db.execute(
        "CREATE TABLE level_signups("
        "group_id INTEGER,user INTEGER,PRIMARY KEY(group_id,user))")
    nodes = [item for item in TREE.body
             if isinstance(item, ast.FunctionDef) and item.name in FUNCTIONS]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    escape = lambda text: str(text).replace("*", "\\*").replace("_", "\\_")
    context = {
        "db": db, "re": re, "GUILD_ID": 17,
        "MAX_USER_CHARACTERS": 25,
        "discord": SimpleNamespace(utils=SimpleNamespace(
            escape_markdown=escape))
    }
    exec(compile(module, "bot.py", "exec"), context)
    return context, db


def add_character(db, user, name, klass="Krieger", level=35):
    db.execute(
        "INSERT INTO characters VALUES (?,?,?,?,?,?,?)",
        (17, user, name, klass, level, "", ""))


class CharacterProfileTests(unittest.TestCase):
    def setUp(self):
        self.f, self.db = load_profiles()

    def tearDown(self):
        self.db.close()

    def test_existing_characters_become_profiles_without_migration_loss(self):
        add_character(self.db, 42, "Grumok")
        add_character(self.db, 42, "Zaraku", "Schamane", 38)
        self.assertEqual(self.f["main_character"](42)[0], "Grumok")
        self.f["ensure_main_character"](42)
        self.assertEqual(self.db.execute(
            "SELECT name FROM main_characters WHERE user=42").fetchone(),
            ("Grumok",))
        self.assertEqual(len(self.f["user_characters"](42)), 2)

    def test_main_can_change_without_affecting_event_character(self):
        add_character(self.db, 42, "Grumok")
        add_character(self.db, 42, "Zaraku", "Schamane", 38)
        self.f["ensure_main_character"](42)
        self.f["remember_group_character"]("dungeon", 8, 42, "Grumok")
        self.f["remember_group_character"]("level", 9, 42, "Zaraku")
        self.f["select_main_character"](42, "zaraku")
        self.assertEqual(self.f["main_character"](42)[0], "Zaraku")
        self.assertEqual(
            self.f["chosen_character"]("dungeon", 8, 42)[0], "Grumok")
        self.assertEqual(
            self.f["chosen_character"]("level", 9, 42)[0], "Zaraku")
        self.assertIn("Grumok", self.f["character_member_line"](
            "dungeon", 8, 42))
        self.assertIn("<@42>", self.f["character_member_line"](
            "dungeon", 8, 42))
        self.assertNotIn("Stufe", self.f["character_member_line"](
            "dungeon", 8, 42))

    def test_cannot_select_someone_elses_characters(self):
        add_character(self.db, 42, "Grumok")
        add_character(self.db, 43, "Zaraku")
        with self.assertRaises(ValueError):
            self.f["remember_group_character"]("level", 2, 42, "Zaraku")
        with self.assertRaises(ValueError):
            self.f["select_main_character"](42, "Zaraku")

    def test_missing_deleted_or_legacy_characters_have_safe_fallbacks(self):
        self.assertIsNone(self.f["chosen_character"]("dungeon", 1, 42))
        self.assertIn("Noch kein Charakter", self.f[
            "character_member_line"]("dungeon", 1, 42))
        add_character(self.db, 42, "Grumok")
        self.assertEqual(
            self.f["chosen_character"]("dungeon", 1, 42)[0],
            "Grumok")  # old signup receives its first registered profile
        self.f["remember_group_character"]("dungeon", 1, 42, "Grumok")
        self.db.execute("DELETE FROM characters WHERE user=42")
        self.assertIn("Charakter aus Profil entfernt", self.f[
            "character_member_line"]("dungeon", 1, 42))

    def test_unsubscribe_only_removes_chosen_character_for_that_event(self):
        add_character(self.db, 42, "Grumok")
        self.f["remember_group_character"]("dungeon", 1, 42, "Grumok")
        self.f["remember_group_character"]("level", 1, 42, "Grumok")
        self.f["forget_group_character"]("dungeon", 1, 42)
        rows = self.db.execute(
            "SELECT kind FROM group_character_choices ORDER BY kind").fetchall()
        self.assertEqual(rows, [("level",)])

    def test_one_signup_per_discord_member_even_with_twinks(self):
        add_character(self.db, 42, "Grumok")
        add_character(self.db, 42, "Zaraku")
        self.db.execute("INSERT INTO planned_signups VALUES (1,42,'Tank')")
        self.db.execute("INSERT OR REPLACE INTO planned_signups "
                        "VALUES (1,42,'DD')")
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM planned_signups WHERE group_id=1").fetchone()[0],
            1)
        self.f["remember_group_character"]("dungeon", 1, 42, "Grumok")
        self.f["remember_group_character"]("dungeon", 1, 42, "Zaraku")
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM group_character_choices "
            "WHERE kind='dungeon' AND group_id=1 AND user=42").fetchone()[0],1)

    def test_sanitize_in_game_name(self):
        normalize = self.f["normalize_character_name"]
        self.assertEqual(normalize("  Grumok  "), "Grumok")
        self.assertEqual(normalize("Torahan Stiernacken"),
                         "Torahan Stiernacken")
        with self.assertRaises(ValueError):
            normalize("<@123456>")
        with self.assertRaises(ValueError):
            normalize("**@everyone**")
        with self.assertRaises(ValueError):
            normalize("")

    def test_server_nickname_opt_in_format_is_valid(self):
        add_character(self.db, 42, "Grumok")
        fake_member = SimpleNamespace(name="Discord-Spieler-123")
        result = self.f["ingame_server_nickname"](
            self.f["main_character"](42), fake_member)
        self.assertEqual(result, "Grumok")
        self.assertLessEqual(len(result), 32)


class IntegrationTests(unittest.TestCase):
    def test_profile_is_offline_upgradable(self):
        for fragment in (
            "CREATE TABLE IF NOT EXISTS main_characters",
            "CREATE TABLE IF NOT EXISTS group_character_choices",
            "CREATE TABLE IF NOT EXISTS character_nickname_preferences",
            "await sync_optional_character_nickname(i.user)",
            "await restore_character_nickname(i.user)",
        ):
            self.assertIn(fragment, SOURCE)

    def test_both_group_types_select_a_character(self):
        for fragment in (
            "class GroupCharacterPicker(discord.ui.View):",
            "async def offer_group_character_picker(",
            "await plan_signup(interaction,self.group_id,self.role,character_name=name)",
            "await join_level_group(",
            "character_member_line(\"dungeon\",group_id,user)",
            "character_member_line(\"level\",group_id,user)",
            'custom_id=f"corpse_plan_{group_id}_character"',
            '"character" if item.label == "Charakter ändern"',
        ):
            self.assertIn(fragment, SOURCE)

    def test_group_creation_uses_user_character_and_has_picker(self):
        self.assertIn("creator_main = (owned_character(user_id,character_name)", SOURCE)
        self.assertIn('state,"character","🎭 Mit welchem Charakter spielst du?"', SOURCE)
        self.assertIn('state,"character",', SOURCE)
        self.assertIn('character_name=state.get("character")', SOURCE)

    def test_no_login_verification_and_no_multiboxing(self):
        self.assertNotIn("warcraft_oauth", SOURCE)
        self.assertIn("PRIMARY KEY(group_id,user)", SOURCE)
        self.assertIn("SELECT name FROM group_character_choices", SOURCE)


if __name__ == "__main__":
    unittest.main()
