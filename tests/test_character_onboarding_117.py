"""Corpsegrinder 1.0.17: name + class only, persistent onboarding UI.

Offline regression coverage; no Discord token or Home Assistant required.
"""
import ast
from pathlib import Path
import re
import sqlite3
import unittest

BOT=(Path(__file__).resolve().parents[1]/
     "corpsegrinder_wow_bot"/"bot.py").read_text(encoding="utf-8")
FEATURES=(Path(__file__).resolve().parents[1]/
          "corpsegrinder_wow_bot"/"community_features.py").read_text(encoding="utf-8")
TREE=ast.parse(BOT)
NAMES={
    "normalize_character_name","user_characters","owned_character",
    "main_character","select_main_character","ensure_main_character",
    "save_character_without_level","chosen_character","character_member_line"
}
CLASSES=(
    "Krieger","Schamane","Druide","Jäger","Schurke",
    "Magier","Priester","Hexenmeister","Paladin"
)


def functions():
    db=sqlite3.connect(":memory:")
    db.execute(
        "CREATE TABLE characters("
        "guild INTEGER,user INTEGER,name TEXT COLLATE NOCASE,"
        "klass TEXT,level INTEGER,beruf1 TEXT,beruf2 TEXT,"
        "PRIMARY KEY(guild,user,name))")
    db.execute(
        "CREATE TABLE main_characters("
        "guild INTEGER,user INTEGER,name TEXT COLLATE NOCASE,"
        "PRIMARY KEY(guild,user))")
    db.execute(
        "CREATE TABLE group_character_choices("
        "kind TEXT,group_id INTEGER,user INTEGER,name TEXT COLLATE NOCASE,"
        "PRIMARY KEY(kind,group_id,user))")
    body=[node for node in TREE.body
          if isinstance(node,ast.FunctionDef) and node.name in NAMES]
    env={
        "re":re, "db":db,"GUILD_ID":17,"MAX_USER_CHARACTERS":25,
        "CLASSES":CLASSES,
    }
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=body,type_ignores=[])),"bot.py","exec"),env)
    return db,env


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.db,self.f=functions()

    def tearDown(self):
        self.db.close()

    def test_creating_character_needs_only_name_and_class(self):
        name,existed=self.f["save_character_without_level"](
            42,"  Grumok  ","Krieger")
        self.assertEqual((name,existed),("Grumok",False))
        row=self.db.execute(
            "SELECT klass,level,beruf1,beruf2 FROM characters "
            "WHERE user=42 AND name='Grumok'").fetchone()
        self.assertEqual(row,("Krieger",1,"",""))
        self.assertEqual(self.f["main_character"](42)[0],"Grumok")

    def test_updating_existing_profile_preserves_level_and_professions(self):
        self.db.execute(
            "INSERT INTO characters VALUES "
            "(17,42,'Zaraku','Krieger',47,'Ingenieurskunst','Bergbau')")
        name,existed=self.f["save_character_without_level"](
            42,"zaraku","Schamane")
        self.assertTrue(existed)
        row=self.db.execute(
            "SELECT klass,level,beruf1,beruf2 FROM characters "
            "WHERE user=42").fetchone()
        self.assertEqual(
            row,("Schamane",47,"Ingenieurskunst","Bergbau"))
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM characters").fetchone()[0],1)

    def test_rejects_invalid_classes_and_names(self):
        for klass in ("Todesritter","Dämonenjäger",""):
            with self.assertRaises(ValueError):
                self.f["save_character_without_level"](42,"Grumok",klass)
        with self.assertRaises(ValueError):
            self.f["save_character_without_level"](42,"@everyone","Krieger")

    def test_undead_paladin_is_valid_horde_character(self):
        name, existed = self.f["save_character_without_level"](
            42, "Lichtbann", "Paladin")
        self.assertEqual((name, existed), ("Lichtbann", False))
        self.assertEqual(
            self.db.execute(
                "SELECT klass FROM characters WHERE user=42"
            ).fetchone()[0], "Paladin")

    def test_maximum_25_characters(self):
        for i in range(25):
            self.f["save_character_without_level"](
                42,f"Charakter{i}","Krieger")
        with self.assertRaisesRegex(ValueError,"Maximal 25"):
            self.f["save_character_without_level"](
                42,"Charakter26","Druide")
        self.assertEqual(
            self.db.execute("SELECT COUNT(*) FROM characters").fetchone()[0],25)


class VisibleUiTests(unittest.TestCase):
    def test_slash_command_does_not_request_level_or_professions(self):
        index=BOT.index('@bot.tree.command(name="charakter"')
        chunk=BOT[index:BOT.index('@bot.tree.command(name="meine_charaktere"',index)]
        self.assertIn('name: str',chunk)
        self.assertIn('klasse: app_commands.Choice[str]',chunk)
        self.assertNotIn('level:',chunk)
        self.assertNotIn('beruf1:',chunk)
        self.assertNotIn('beruf2:',chunk)
        self.assertIn('save_character_without_level(',chunk)

    def test_no_per_character_level_in_roster_or_profile(self):
        n=BOT.index("def character_member_line(")
        member=BOT[n:BOT.index("async def refresh_user_character_cards(",n)]
        self.assertNotIn("Stufe",member)
        n=BOT.index("def profile_embed(")
        profile=BOT[n:BOT.index("def save_character_without_level(",n)]
        self.assertNotIn("Stufe",profile)
        self.assertIn("discord.utils.escape_markdown(klass)",member)
        self.assertIn("<@{user_id}>",member)

    def test_all_character_selectors_show_only_name_and_class(self):
        n=BOT.index("class GroupCharacterPicker(")
        picker=BOT[n:BOT.index("async def offer_group_character_picker(",n)]
        self.assertNotIn("Stufe",picker)
        self.assertIn("description=klass[:100]",picker)
        self.assertNotIn('description=f"{klass} · Stufe',BOT)

    def test_persistent_onboarding_panel_and_private_registration(self):
        self.assertIn("class CharacterPanelView(discord.ui.View):",BOT)
        self.assertIn("super().__init__(timeout=None)",BOT[
            BOT.index("class CharacterPanelView("):
            BOT.index("def character_panel_embed(")])
        self.assertIn('custom_id="corpse_character_register_v117"',BOT)
        self.assertIn('custom_id="corpse_character_profile_v117"',BOT)
        self.assertIn('custom_id="corpse_character_nick_v117"',BOT)
        self.assertIn("bot.add_view(CharacterPanelView())",BOT)
        self.assertIn('await publish_character_panel(guild)',BOT)
        self.assertIn('await publish_character_panel(i.guild)',BOT)
        self.assertIn("class CharacterNameModal(discord.ui.Modal",BOT)
        self.assertIn("class CharacterClassView(discord.ui.View)",BOT)
        self.assertIn("ephemeral=True",BOT)

    def test_panel_and_welcome_refer_to_name_class_only(self):
        self.assertIn("Ingame-Name und Klasse",BOT)
        self.assertIn("🎭 ERSTE SCHRITTE",FEATURES)
        self.assertIn("ohne Level oder Freigabe",FEATURES)
        self.assertRegex(FEATURES, r'VERSION = "[0-9]+\.[0-9]+\.[0-9]+"')
        self.assertIn("Rollen wählen und **Ingame-Name + Klasse** registrieren",BOT)


if __name__=="__main__":
    unittest.main()
