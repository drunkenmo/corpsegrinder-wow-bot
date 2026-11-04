"""1.0.27: Compact Addon-Schmiede without banner and installation notice."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def constant(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(name)


class FakeEmbed:
    def __init__(self, *, title, description, colour):
        self.title, self.description, self.colour = title, description, colour
        self.fields = []
        self.footer = ""
        self.image_url = None

    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))

    def set_footer(self, *, text):
        self.footer = text

    def set_image(self, *, url):
        self.image_url = url


def load():
    nodes = [node for node in TREE.body
             if isinstance(node, ast.FunctionDef)
             and node.name in ("addon_catalogue_embeds",
                               "addon_simplified_embeds", "addon_project_url")]
    scope = {
        "discord": SimpleNamespace(
            Embed=FakeEmbed, Colour=SimpleNamespace(from_rgb=lambda *_: 1)),
        "ADDON_SOURCES": constant("ADDON_SOURCES"),
        "ADDON_HUB_ART_URL": "https://example.com/assets/welcome.png",
        "ADDON_MARKER": "corpsegrinder:forever-addon-panel",
        "ADDON_PROJECT_BASE": "https://www.curseforge.com/wow/addons/",
        "re": __import__("re"),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=nodes, type_ignores=[])), "bot.py", "exec"), scope)
    return scope


class SimpleAddonForgeTests(unittest.TestCase):
    def test_two_compact_embeds_show_all_eight_addons(self):
        scope = load()
        cards = scope["addon_simplified_embeds"]()
        self.assertEqual(len(cards), 2)
        self.assertIn("ADDON-SCHMIEDE", cards[0].title)
        self.assertEqual(cards[0].footer, "Corpsegrinder · Addon-Schmiede")
        all_items = [field for card in cards for field in card.fields]
        self.assertEqual(len(all_items), 10)  # 8 addons + 2 row spacers
        for slug, name, _area, _summary in constant("ADDON_SOURCES"):
            matches = [value for title, value, _ in all_items if name in title]
            self.assertEqual(len(matches), 1, name)
            self.assertIn(
                "https://www.curseforge.com/wow/addons/" + slug,
                matches[0])
        self.assertNotIn("VOR DER INSTALLATION", str(all_items))
        self.assertNotIn("WoW-Forever-Datei (1.60.1)", str(all_items))
        self.assertNotIn("Die Werkzeuge für deine Abenteuer", str(all_items))

    def test_inline_pairs_with_full_width_row_breaks(self):
        cards = load()["addon_catalogue_embeds"]()
        for card in cards:
            addon_fields = [field for field in card.fields
                            if field[0].startswith("✦ ")]
            separators = [field for field in card.fields
                          if field[0] == "\\u200b" or field[0] == "\u200b"]
            self.assertEqual(len(addon_fields), 4)
            self.assertTrue(all(inline for _, _, inline in addon_fields))
            self.assertEqual(len(separators), 1)
            self.assertFalse(separators[0][2])
        self.assertTrue(cards[-1].fields[-1][2])

    def test_old_pin_is_reused_and_nested_menu_is_removed(self):
        self.assertIn('key="addons_intro_post_v114"', SOURCE)
        self.assertIn('ADDON_MARKER = "corpsegrinder:forever-addon-panel"', SOURCE)
        self.assertIn('"Corpsegrinder · Addon-Schmiede"', SOURCE)
        self.assertIn("await existing.edit(embeds=addon_simplified_embeds(), view=None)", SOURCE)
        self.assertIn("embeds=addon_simplified_embeds()", SOURCE)
        self.assertNotIn("bot.add_view(AddonForgeView())", SOURCE)
        self.assertNotIn("view=AddonForgeView()", SOURCE)
        self.assertIn("background(forever_addons_worker())", SOURCE)
        self.assertIn("ADDON_CHECK_INTERVAL = 6 * 3600", SOURCE)

    def test_pinned_cards_not_too_long_on_phone(self):
        cards = load()["addon_simplified_embeds"]()
        for card in cards:
            self.assertLess(len(card.description), 900)
            self.assertLessEqual(len(card.fields), 7)
            for name, value, _ in card.fields:
                self.assertLessEqual(len(value), 1024)


if __name__ == "__main__":
    unittest.main()
