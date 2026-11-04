"""Corpsegrinder 1.0.29: real server emoji mapping and banner persistence."""
import ast
from pathlib import Path
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(BOT)


def literal(name):
    for item in TREE.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(item.value)
    raise AssertionError(name)


class EmojiTests(unittest.TestCase):
    def test_all_11_names_match_uploaded_server_emojis(self):
        names = literal("CORPSEGRINDER_EMOJI_NAMES")
        expected = {
            "Horde": "horde", "PvE": "pve",
            "Krieger": "krieger", "Jäger": "jaeger",
            "Schamane": "schami", "Druide": "druide",
            "Schurke": "schurke", "Magier": "magier",
            "Priester": "priester", "Hexenmeister": "hexer",
            "Paladin": "pala",
        }
        self.assertEqual(names, expected)

    def test_custom_emoji_lookup_uses_real_guild_objects(self):
        fn = next(item for item in TREE.body
                  if isinstance(item, ast.FunctionDef)
                  and item.name == "corp_emoji")
        emoji = SimpleNamespace(name="jaeger", id=123,
                                is_usable=lambda: True)
        guild = SimpleNamespace(emojis=[emoji])
        ns = {"CORPSEGRINDER_EMOJI_NAMES": literal("CORPSEGRINDER_EMOJI_NAMES"),
              "EMOJI": literal("EMOJI"),
              "discord": SimpleNamespace(utils=SimpleNamespace(
                  get=lambda things, *, name: next(
                      (thing for thing in things if thing.name == name), None))),
              "bot": SimpleNamespace(get_guild=lambda _id: guild),
              "GUILD_ID": 123}
        exec(compile(ast.fix_missing_locations(ast.Module(
            body=[fn], type_ignores=[])), "bot.py", "exec"), ns)
        self.assertIs(ns["corp_emoji"]("Jäger"), emoji)
        self.assertEqual(ns["corp_emoji"]("Jäger", SimpleNamespace(emojis=[])), "🏹")
        self.assertEqual(ns["corp_emoji"]("PvP", guild), "🏹")

    def test_classes_role_panel_and_character_menu_are_reused(self):
        self.assertIn("emoji=corp_emoji(name)", BOT)
        self.assertIn("emoji=corp_emoji(label)", BOT)
        self.assertIn("emoji=corp_emoji(klasse)", BOT)
        self.assertIn('corp_emoji(\'Horde\')', BOT)
        self.assertIn('corpse_classes_v104', BOT)  # keeps stable interactions
        self.assertIn('corpse_character_register_v117', BOT)

    def test_banner_command_edits_original_message_without_extra_posts(self):
        start = BOT.index('name="willkommensbanner_setzen"')
        end = BOT.index("async def publish_info(", start)
        command = BOT[start:end]
        self.assertIn("discord.Attachment", command)
        self.assertIn('target, "welcome_post", "corpsegrinder:welcome"', command)
        self.assertIn('filename = "corpsegrinder_banner" + extension', command)
        self.assertIn("await existing.edit(", command)
        self.assertIn("uploaded = await existing.edit(", command)
        self.assertIn("await uploaded.edit(", command)
        self.assertNotIn("target.send(", command)

    def test_banner_survives_existing_welcome_refresh(self):
        block = BOT[BOT.index("async def publish_info("):
                    BOT.index('@bot.tree.command(', BOT.index("async def publish_info("))]
        self.assertIn('a.filename.startswith("corpsegrinder_banner.")', block)
        self.assertIn('embed.set_image(url="attachment://" + banner.filename)', block)
        self.assertIn('await existing.edit(embed=embed, view=view)', block)
        self.assertIn('save_setting(storage_key, existing.id)', block)
        self.assertNotIn("corpsegrinder_banner.png", FEATURES)
        self.assertNotIn("assets/welcome.png", FEATURES)
        self.assertNotIn("Alte Säcke. Kaltes Bier.", FEATURES)
        self.assertGreaterEqual(
            tuple(int(p) for p in next(line.split('"')[1]
                for line in FEATURES.splitlines()
                if line.startswith("VERSION = ")).split(".")),
            (1, 0, 31))


if __name__ == "__main__":
    unittest.main()
