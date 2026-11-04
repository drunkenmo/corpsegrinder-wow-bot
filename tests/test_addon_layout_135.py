"""Test the real discord.py 2.6.4 Components V2 catalogue renderer offline."""
import ast
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse

import discord

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text("utf-8")
TREE = ast.parse(SOURCE)


def constant(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(x, ast.Name) and x.id == name
                   for x in node.targets):
                return ast.literal_eval(node.value)
    raise AssertionError("missing " + name)


def load():
    needed = {"addon_catalogue_layout", "addon_project_url",
              "trusted_addon_icon_url"}
    nodes = [n for n in TREE.body if isinstance(n, ast.FunctionDef)
             and n.name in needed]
    scope = {
        "discord": discord, "html": html, "HTMLParser": HTMLParser,
        "urlparse": urlparse, "re": re,
        "ADDON_SOURCES": constant("ADDON_SOURCES"),
        "ADDON_CATALOG_SECTIONS": constant("ADDON_CATALOG_SECTIONS"),
        "ADDON_VERIFIED_ICONS": constant("ADDON_VERIFIED_ICONS"),
        "ADDON_PROJECT_BASE": constant("ADDON_PROJECT_BASE")
            if False else "https://www.curseforge.com/wow/addons/",
        "ADDON_ICON_HOSTS": frozenset((
            "media.forgecdn.net", "mediafilez.forgecdn.net", "edge.forgecdn.net")),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=nodes, type_ignores=[])), "bot.py", "exec"), scope)
    return scope


class CompactCatalogueLayoutTests(unittest.TestCase):
    def setUp(self):
        self.env = load()
        self.icons = constant("ADDON_VERIFIED_ICONS")
        self.catalogue = constant("ADDON_CATALOG_SECTIONS")
        self.catalogue_by_slug = {slug: name for slug, name, *_ in
                                  constant("ADDON_SOURCES")}

    def test_uses_three_single_containers_with_all_original_icons(self):
        count = 0
        for part, (_, _, slugs) in enumerate(self.catalogue):
            view = self.env["addon_catalogue_layout"](part)
            self.assertIsInstance(view, discord.ui.LayoutView)
            self.assertLessEqual(view.total_children_count, 40)
            self.assertLessEqual(view.content_length(), 4000)
            serialized = view.to_components()
            self.assertEqual(len(serialized), 1)
            panel = serialized[0]
            self.assertEqual(panel["type"], 17)  # Container
            self.assertEqual(panel["accent_color"], 0xA56D43)
            self.assertEqual(len(panel["components"]), len(slugs) + 2)
            self.assertLessEqual(len(panel["components"]), 10)
            self.assertEqual(panel["components"][0]["type"], 10)
            self.assertEqual(panel["components"][-1]["type"], 10)
            self.assertNotIn("corpsegrinder:addons-part",
                             str(serialized))
            for slug, row in zip(slugs, panel["components"][1:-1]):
                count += 1
                self.assertEqual(row["type"], 9)  # Section
                self.assertEqual(row["accessory"]["type"], 11)  # Thumbnail
                self.assertEqual(row["accessory"]["media"]["url"],
                                 self.icons[slug])
                name = self.catalogue_by_slug[slug]
                content = row["components"][0]["content"]
                self.assertIn(
                    "**[" + name + "](https://www.curseforge.com/wow/addons/"
                    + slug + ")**", content)
                self.assertNotIn("Zum Addon auf CurseForge", content)
                self.assertNotIn("Forever-Version: Auf CurseForge prüfen",
                                 content)
        self.assertEqual(count, 19)

    def test_short_dependent_and_german_language_notes(self):
        view = self.env["addon_catalogue_layout"](1)
        rows = view.to_components()[0]["components"][1:-1]
        guide = rows[0]["components"][0]["content"]
        german = rows[-1]["components"][0]["content"]
        self.assertIn("[Factoruide Profile](", guide)
        self.assertEqual(guide.count("Factoruide Profile"), 1)
        self.assertIn("CurseForge-App", german)
        self.assertNotIn("⚠️", german)

    def test_only_confirmed_versions_are_shown(self):
        view = self.env["addon_catalogue_layout"](
            1, versions={"azerothcompendium": "v1.0.1-forever"})
        rows = view.to_components()[0]["components"][1:-1]
        versions = [row["components"][0]["content"] for row in rows]
        self.assertIn("Forever-Datei: v1.0.1-forever", versions[2])
        self.assertEqual(sum("Forever-Datei:" in line for line in versions), 1)

    def test_in_place_migration_and_recovery_are_wired(self):
        self.assertIn("content=None, embeds=[], attachments=[], view=layout",
                      SOURCE)
        self.assertIn("layout = addon_catalogue_layout(part, icon_urls, versions)",
                      SOURCE)
        self.assertIn("for child in getattr(parent, \"children\", ())", SOURCE)
        self.assertIn("save_setting(key, existing.id)", SOURCE)
        self.assertNotIn("await existing.delete()", SOURCE)


if __name__ == "__main__":
    unittest.main()
