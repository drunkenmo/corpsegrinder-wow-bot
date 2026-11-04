"""WoW Forever fantasy Addon-Schmiede 1.0.24 regression checks."""
import ast
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT/"corpsegrinder_wow_bot"/"bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT/"corpsegrinder_wow_bot"/"community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def constant(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(name)


class FakeEmbed:
    def __init__(self, *, title, description, colour, url=None):
        self.title, self.description, self.url = title, description, url
        self.fields, self.footer, self.image_url = [], "", None

    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))

    def set_footer(self, *, text):
        self.footer = text

    def set_image(self, *, url):
        self.image_url = url


def isolated():
    names = {"addon_category", "addon_catalogue_rows", "addon_latest_version",
             "addon_intro_embed", "addon_detail_embed", "addon_category_embed",
             "addon_recent_embed", "addon_project_url"}
    nodes = [node for node in TREE.body if
             isinstance(node, ast.FunctionDef) and node.name in names]
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE forever_addon_files (slug TEXT PRIMARY KEY, "
               "latest_version TEXT, last_seen_utc INTEGER)")
    env = {
        "db": db, "re": __import__("re"),
        "discord": SimpleNamespace(
            Embed=FakeEmbed,
            utils=SimpleNamespace(escape_markdown=lambda s:s.replace("*", r"\*")),
            Colour=SimpleNamespace(
                from_rgb=lambda *_: 42, gold=lambda: 42)),
        "ADDON_SOURCES": constant("ADDON_SOURCES"),
        "ADDON_CATEGORIES": constant("ADDON_CATEGORIES"),
        "ADDON_MARKER": "corpsegrinder:forever-addon-panel",
        "ADDON_HUB_ART_URL":
            "https://raw.githubusercontent.com/drunkenmo/corpsegrinder-wow-bot/main/assets/welcome.png",
        "ADDON_PROJECT_BASE": "https://www.curseforge.com/wow/addons/",
    }
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=nodes, type_ignores=[])), "bot.py", "exec"), env)
    return db, env


class AddonSchmiedeTests(unittest.TestCase):
    def setUp(self):
        self.db, self.fn = isolated()

    def tearDown(self):
        self.db.close()

    def test_categories_cover_all_eight_curated_addons_once(self):
        categories = constant("ADDON_CATEGORIES")
        self.assertEqual(len(categories), 6)
        slugs = [slug for _, _, _, members in categories for slug in members]
        self.assertEqual(set(slugs),
                         {row[0] for row in constant("ADDON_SOURCES")})
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_hub_is_compact_and_preserves_old_pin_marker(self):
        intro = self.fn["addon_intro_embed"]()
        self.assertIn("ADDON-SCHMIEDE", intro.title)
        self.assertIn("corpsegrinder:forever-addon-panel", intro.footer)
        self.assertIn("Forever", intro.description)
        self.assertEqual(len(intro.fields), 3)
        self.assertTrue(intro.image_url.endswith("/welcome.png"))
        self.assertLessEqual(len(intro.description), 4096)
        self.assertIn("view=AddonForgeView()", SOURCE)
        self.assertIn('key="addons_intro_post_v114"', SOURCE)

    def test_category_and_detail_addons_show_unverified_versions_honestly(self):
        category = self.fn["addon_category_embed"]("quests")
        self.assertIn("Quests & Leveln", category.title)
        self.assertEqual(len(category.fields), 2)
        detail = self.fn["addon_detail_embed"]("questie")
        self.assertIn("Questie", detail.title)
        self.assertIn("Noch nicht bestätigt", detail.description)
        self.assertIn("curseforge.com", detail.fields[0][1])
        self.db.execute(
            "INSERT INTO forever_addon_files VALUES (?, ?, ?)",
            ("questie", "v1.60.25-forever", 10))
        updated = self.fn["addon_detail_embed"]("questie")
        self.assertIn("v1.60.25-forever", updated.description)

    def test_recent_updates_not_claimed_newly_published(self):
        empty = self.fn["addon_recent_embed"]()
        self.assertIn("Noch keine Einträge", empty.fields[0][0])
        self.db.execute(
            "INSERT INTO forever_addon_files VALUES (?, ?, ?)",
            ("leatrix-plus", "Forever v2", 23))
        results = self.fn["addon_recent_embed"]()
        self.assertIn("Leatrix Plus", results.fields[0][0])
        self.assertIn("nicht zwingend", results.description)
        self.assertIn("curseforge.com", results.fields[0][1])

    def test_buttons_persist_and_news_scanner_kept(self):
        for text in ("class AddonForgeView(discord.ui.View):",
                     "class AddonPicker(discord.ui.View):",
                     "bot.add_view(AddonForgeView())",
                     "custom_id=ADDON_HUB_VIEW_ID",
                     'label="Empfehlungen"',
                     'label="Neu auf CurseForge"',
                     "background(forever_addons_worker())",
                     "ADDON_CHECK_INTERVAL = 6 * 3600",
                     "async def check_forever_addons():"):
            self.assertIn(text, SOURCE)


if __name__ == "__main__":
    unittest.main()
