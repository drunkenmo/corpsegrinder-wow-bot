"""Regression tests for the 1.0.33 pinned icon catalogue and legacy pin reuse."""
import ast
import html
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
import re
import unittest

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
    def __init__(self, *, title, description, colour, url=None):
        self.title, self.description, self.colour = title, description, colour
        self.url = url
        self.fields = []
        self.footer = ""
        self.image_url = None
        self.thumbnail_url = None

    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))

    def set_footer(self, *, text):
        self.footer = text

    def set_thumbnail(self, *, url):
        self.thumbnail_url = url


def load():
    selected = (
        "addon_catalogue_sections", "addon_catalogue_embeds",
        "addon_simplified_embeds", "addon_project_url",
        "trusted_addon_icon_url", "CurseForgeProjectIcon",
        "extract_curseforge_project_icon",
    )
    nodes = [node for node in TREE.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))
             and node.name in selected]
    scope = {
        "discord": SimpleNamespace(
            Embed=FakeEmbed,
            Colour=SimpleNamespace(from_rgb=lambda *_: 1),
            utils=SimpleNamespace(escape_markdown=lambda x:x)),
        "ADDON_SOURCES": constant("ADDON_SOURCES"),
        "ADDON_CATALOG_SECTIONS": constant("ADDON_CATALOG_SECTIONS"),
        "ADDON_MARKER": "corpsegrinder:forever-addon-panel",
        "ADDON_PROJECT_BASE": "https://www.curseforge.com/wow/addons/",
        "ADDON_ICON_HOSTS": frozenset((
            "media.forgecdn.net", "mediafilez.forgecdn.net",
            "edge.forgecdn.net")),
        "HTMLParser": HTMLParser,
        "html": html,
        "urlparse": urlparse,
        "re": re,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=nodes, type_ignores=[])), "bot.py", "exec"), scope)
    return scope


class ThreePinnedAddonCatalogTests(unittest.TestCase):
    def setUp(self):
        self.env = load()
        self.pages = self.env["addon_catalogue_sections"]()

    def test_every_real_addon_appears_once_with_curseforge_project_link(self):
        sources = constant("ADDON_SOURCES")
        self.assertEqual(len(sources), 19)
        cards = [card for page in self.pages for card in page[1:]]
        self.assertEqual(len(cards), 19)
        self.assertEqual(len(set(slug for slug,*_ in sources)), 19)
        for slug, name, _category, summary in sources:
            matches = [c for c in cards if c.title == "✦ " + name]
            self.assertEqual(len(matches), 1, name)
            self.assertEqual(matches[0].url,
                             "https://www.curseforge.com/wow/addons/" + slug)
            self.assertIn(summary, matches[0].description)

    def test_blackthornes_first_then_requested_then_previous(self):
        first = [card.title for card in self.pages[0][1:]]
        self.assertEqual(first, [
            "✦ Blackthornes Farmer",
            "✦ Blackthornes Tradeskills",
            "✦ Blackthornes Equipment",
            "✦ Blackthornes Butler",
            "✦ Blackthornes Pets"])
        requested = [card.title for card in self.pages[1][1:]]
        self.assertIn("✦ Spoken: German", requested)
        self.assertIn("✦ SKTools", requested)
        other = [card.title for card in self.pages[2][1:]]
        self.assertIn("✦ Questie", other)
        self.assertIn("✦ Deadly Boss Mods", other)

    def test_discord_embed_limits_and_thumbnail_handling(self):
        self.assertEqual(len(self.pages), 3)
        for page in self.pages:
            self.assertLessEqual(len(page), 10)
            self.assertLess(sum(len(card.title) + len(card.description)
                                for card in page), 6000)
            self.assertIsNone(page[0].thumbnail_url)
        self.assertEqual(self.pages[0][0].footer,
                         "Corpsegrinder · Addon-Schmiede")
        self.assertEqual(self.pages[1][0].footer,
                         "corpsegrinder:addons-part:2")
        self.assertEqual(self.pages[2][0].footer,
                         "corpsegrinder:addons-part:3")
        # No guessed or decorative thumbnail URL for any addon.
        self.assertTrue(all(card.thumbnail_url is None
                            for page in self.pages for card in page))

    def test_only_a_verified_icon_appears_next_to_that_specific_project(self):
        icon = "https://media.forgecdn.net/avatars/1499/101/real-logo.png"
        pages = self.env["addon_catalogue_sections"](
            {"blackthornes-farmer": icon,
             "blackthornes-pets": "https://other.example/avatars/1499/101/fake.png"})
        self.assertEqual(pages[0][1].thumbnail_url, icon)
        self.assertIsNone(pages[0][5].thumbnail_url)

    def test_no_screenshots_author_avatars_or_unknown_urls(self):
        check = self.env["trusted_addon_icon_url"]
        good = "https://media.forgecdn.net/avatars/1499/101/farmer.png"
        self.assertEqual(check(good), good)
        for raw in (
            "https://media.forgecdn.net/gallery/2045/12/screenshot.png",
            "https://media.forgecdn.net/avatars/1/2/icon.svg",
            "http://media.forgecdn.net/avatars/1/2/icon.png",
            "https://evil.example/avatars/1/2/icon.png",
            "https://media.forgecdn.net.evil.example/avatars/1/2/icon.png",
            "https://media.forgecdn.net:8443/avatars/1/2/icon.png",
            "https://user:pass@media.forgecdn.net/avatars/1/2/icon.png",
        ):
            self.assertIsNone(check(raw))
        parse = self.env["extract_curseforge_project_icon"]
        self.assertEqual(parse("""
          <html><head>
            <meta property="og:image"
                  content="https://media.forgecdn.net/avatars/1499/101/farmer.png">
          </head><body><img src="https://media.forgecdn.net/avatars/1/2/owner.png">
          </body></html>"""), good)
        self.assertIsNone(parse("""
          <meta property="og:image"
                content="https://media.forgecdn.net/gallery/1/2/banner.jpg">
          <img src="https://media.forgecdn.net/avatars/1499/101/not-our-addon.png">
        """))

    def test_spoken_install_and_factoruide_dependency_are_explicit(self):
        requested = self.pages[1]
        german = next(c for c in requested if c.title == "✦ Spoken: German")
        self.assertTrue(any("CurseForge-App" in field[1] for field in german.fields))
        guide = next(c for c in requested if c.title == "✦ Factoruide Guide")
        self.assertTrue(any("factoruide-profile" in field[1]
                            for field in guide.fields))

    def test_existing_pin_reused_and_three_messages_not_reposted(self):
        self.assertIn('key = ("addons_intro_post_v114" if part == 0', SOURCE)
        self.assertIn('ADDON_MARKER = "corpsegrinder:forever-addon-panel"', SOURCE)
        self.assertIn("await existing.edit(embeds=cards, view=None)", SOURCE)
        self.assertIn("target.history(limit=90)", SOURCE)
        self.assertIn("for part in range(len(ADDON_CATALOG_SECTIONS))", SOURCE)
        self.assertIn("save_setting(key, existing.id)", SOURCE)
        self.assertIn("background(forever_addons_worker())", SOURCE)
        self.assertNotIn("bot.add_view(AddonForgeView())", SOURCE)
        self.assertIn("initial_curated = not is_new and previous is None", SOURCE)
        self.assertIn("await ensure_addons_channel(guild)\n        if errors:", SOURCE)


if __name__ == "__main__":
    unittest.main()
