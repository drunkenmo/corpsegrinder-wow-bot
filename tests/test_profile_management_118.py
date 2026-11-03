"""Regression tests for editing/deleting profiles and voluntary voice nicknames."""
import ast
from pathlib import Path
import re
import sqlite3
from types import SimpleNamespace
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/
        "corpsegrinder_wow_bot"/"bot.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)
FUNCTIONS={
    "normalize_character_name", "user_characters", "owned_character",
    "main_character", "select_main_character", "ensure_main_character",
    "chosen_character", "edit_character_profile", "delete_character_profile",
    "ingame_server_nickname", "character_member_line"
}
CLASSES=("Krieger","Schamane","Druide","Jäger","Schurke","Magier",
         "Priester","Hexenmeister")


def profile_env():
    db=sqlite3.connect(":memory:")
    db.execute(
        "CREATE TABLE characters(guild INTEGER,user INTEGER,"
        "name TEXT COLLATE NOCASE,klass TEXT,level INTEGER,"
        "beruf1 TEXT,beruf2 TEXT,PRIMARY KEY(guild,user,name))")
    db.execute(
        "CREATE TABLE main_characters(guild INTEGER,user INTEGER,"
        "name TEXT COLLATE NOCASE,PRIMARY KEY(guild,user))")
    db.execute(
        "CREATE TABLE group_character_choices(kind TEXT,group_id INTEGER,"
        "user INTEGER,name TEXT COLLATE NOCASE,PRIMARY KEY(kind,group_id,user))")
    db.execute(
        "CREATE TABLE planned_signups(group_id INTEGER,user INTEGER,role TEXT,"
        "PRIMARY KEY(group_id,user))")
    db.execute(
        "CREATE TABLE level_signups(group_id INTEGER,user INTEGER,"
        "PRIMARY KEY(group_id,user))")
    body=[node for node in TREE.body
          if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS]
    escape=lambda value: str(value).replace("*","\\*").replace("_","\\_")
    env={"db":db,"re":re,"GUILD_ID":17,
         "CLASSES":CLASSES,"MAX_USER_CHARACTERS":25,
         "discord":SimpleNamespace(utils=SimpleNamespace(
             escape_markdown=escape))}
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=body,type_ignores=[])),"bot.py","exec"),env)
    return db,env


class CharacterModificationTests(unittest.TestCase):
    def setUp(self):
        self.db,self.f=profile_env()
        self.db.execute(
            "INSERT INTO characters VALUES"
            "(17,42,'Grumok','Krieger',35,'Bergbau','Schmiedekunst')")
        self.db.execute(
            "INSERT INTO characters VALUES"
            "(17,42,'Zaraku','Schamane',38,'','')")
        self.db.execute(
            "INSERT INTO characters VALUES"
            "(17,43,'Grumok','Krieger',60,'','')")
        self.f["select_main_character"](42,"Grumok")
        self.db.execute(
            "INSERT INTO group_character_choices VALUES"
            "('dungeon',7,42,'Grumok')")
        self.db.execute(
            "INSERT INTO group_character_choices VALUES"
            "('level',8,42,'Grumok')")
        self.db.execute(
            "INSERT INTO planned_signups VALUES(7,42,'Tank')")
        self.db.execute(
            "INSERT INTO level_signups VALUES(8,42)")

    def tearDown(self):
        self.db.close()

    def test_rename_main_preserves_group_choices_old_data_and_other_users(self):
        new_name,klass=self.f["edit_character_profile"](
            42,"Grumok","GRUMOK-NEU","druide")
        self.assertEqual((new_name,klass),("GRUMOK-NEU","Druide"))
        self.assertEqual(self.f["main_character"](42)[0],"GRUMOK-NEU")
        self.assertEqual(self.f["chosen_character"](
            "dungeon",7,42)[0],"GRUMOK-NEU")
        self.assertEqual(self.f["chosen_character"](
            "level",8,42)[0],"GRUMOK-NEU")
        self.assertEqual(self.db.execute(
            "SELECT klass,level,beruf1,beruf2 FROM characters "
            "WHERE user=42 AND name='GRUMOK-NEU'").fetchone(),
            ("Druide",35,"Bergbau","Schmiedekunst"))
        self.assertEqual(self.db.execute(
            "SELECT name FROM characters WHERE user=43").fetchone(),
            ("Grumok",))
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM planned_signups WHERE group_id=7").fetchone()[0],1)

    def test_edit_duplicate_name_rejected_without_partial_changes(self):
        with self.assertRaisesRegex(ValueError,"bereits"):
            self.f["edit_character_profile"](42,"Grumok","Zaraku","Jäger")
        self.assertEqual(self.f["main_character"](42)[0],"Grumok")
        self.assertEqual(self.f["chosen_character"](
            "dungeon",7,42)[0],"Grumok")

    def test_invalid_class_and_ownership_rejected(self):
        with self.assertRaisesRegex(ValueError,"Klasse"):
            self.f["edit_character_profile"](42,"Grumok","Grumok","Paladin")
        with self.assertRaisesRegex(ValueError,"nicht gefunden"):
            self.f["edit_character_profile"](44,"Grumok","Grumok","Krieger")

    def test_deleting_main_keeps_signups_and_selects_twinks(self):
        deleted=self.f["delete_character_profile"](42,"Grumok")
        self.assertEqual(deleted,"Grumok")
        self.assertEqual(self.f["main_character"](42)[0],"Zaraku")
        self.assertEqual(self.f["chosen_character"](
            "dungeon",7,42)[0],"Zaraku")
        self.assertEqual(self.f["chosen_character"](
            "level",8,42)[0],"Zaraku")
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM planned_signups WHERE group_id=7").fetchone()[0],1)
        self.assertEqual(self.db.execute(
            "SELECT COUNT(*) FROM level_signups WHERE group_id=8").fetchone()[0],1)
        self.assertEqual(self.f["owned_character"](43,"Grumok")[0],"Grumok")

    def test_delete_last_character_leaves_no_main(self):
        self.f["delete_character_profile"](42,"Grumok")
        self.f["delete_character_profile"](42,"Zaraku")
        self.assertIsNone(self.f["main_character"](42))
        self.assertIsNone(self.db.execute(
            "SELECT name FROM main_characters WHERE user=42").fetchone())

    def test_voice_server_nickname_shows_only_ingame_character(self):
        member=SimpleNamespace(name="drunkenmo")
        self.assertEqual(self.f["ingame_server_nickname"](
            self.f["main_character"](42),member),"Grumok")


class DiscordUxTests(unittest.TestCase):
    def test_private_edit_select_and_modal_prepopulated(self):
        self.assertIn("class CharacterEditModal(discord.ui.Modal",SOURCE)
        self.assertIn("default=row[0]",SOURCE)
        self.assertIn("default=row[1]",SOURCE)
        self.assertIn("class CharacterEditSelectView(discord.ui.View)",SOURCE)
        self.assertIn("label=\"Bearbeiten\"",SOURCE)
        self.assertIn("edit_character_profile(",SOURCE)

    def test_delete_requires_explicit_confirmation(self):
        self.assertIn("class CharacterDeleteConfirmView(discord.ui.View)",SOURCE)
        self.assertIn("label=\"Ja, endgültig löschen\"",SOURCE)
        self.assertIn("label=\"Abbrechen\"",SOURCE)
        self.assertIn("class CharacterDeleteSelectView(discord.ui.View)",SOURCE)
        self.assertIn("label=\"Löschen\"",SOURCE)

    def test_voice_optin_has_discoverable_buttons_and_reversal(self):
        self.assertIn("label=\"Im Sprachchat anzeigen\"",SOURCE)
        self.assertIn("label=\"Sprachchat-Name an/aus\"",SOURCE)
        self.assertIn("await restore_character_nickname(member)",SOURCE)
        self.assertIn("member.nick != preference[1]",SOURCE)
        self.assertIn("Serverinhaber",SOURCE)

    def test_no_extra_verification_or_level_added(self):
        self.assertNotIn("warcraft_oauth",SOURCE)
        profile=SOURCE[
            SOURCE.index("class CharacterEditModal("):
            SOURCE.index("class CharacterEditSelectView(")]
        self.assertNotIn("Stufe",profile)
        self.assertIn("self.character_class",profile)


if __name__=="__main__":
    unittest.main()
