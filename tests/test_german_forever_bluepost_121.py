"""Offline regression tests for verified German Warcraft class summaries (1.0.21)."""
import ast
import re
import unittest
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class FakeEmbed:
    def __init__(self, *, title, description, url, colour, timestamp):
        self.title, self.description = title, description
        self.url, self.timestamp = url, timestamp
        self.fields, self.footer = [], ""
    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))
    def set_footer(self, *, text):
        self.footer = text


def helpers():
    selected = {
        "ForeverClassBulletParser", "german_forever_ability",
        "german_forever_quantity", "german_forever_change",
        "german_forever_class_digest", "forever_forum_embed"
    }
    nodes = [n for n in TREE.body
             if isinstance(n, (ast.ClassDef, ast.FunctionDef))
             and n.name in selected]
    constants = {
        "FOREVER_FORUM_CLASS_NAMES", "FOREVER_GERMAN_SPELLS",
        "FOREVER_GERMAN_CLASS_ICONS"
    }
    env = {
        "re": re, "HTMLParser": HTMLParser, "defaultdict": defaultdict,
        "datetime": datetime, "timezone": timezone,
        "discord": SimpleNamespace(
            Embed=FakeEmbed,
            Colour=SimpleNamespace(blue=lambda: 255))
    }
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in constants:
                    env[target.id] = ast.literal_eval(node.value)
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=nodes, type_ignores=[])), "bot.py", "exec"), env)
    return env


class GermanClassSummaryTests(unittest.TestCase):
    def setUp(self):
        self.e = helpers()

    def test_actual_patchnote_phrases_include_old_new_figures(self):
        translate = self.e["german_forever_change"]
        stance = translate(
            "Defensive Stance threat bonus increased to 80% (was 30%).")
        self.assertIn("Verteidigungshaltung", stance)
        self.assertIn("80 %", stance)
        self.assertIn("30 %", stance)
        self.assertIn("Bedrohung", stance)
        bear = translate(
            "Bear Form threat generation increased to 115% (was 50%).")
        self.assertIn("Bärengestalt", bear)
        self.assertIn("115 %", bear)
        slam = translate(
            "Slam's cooldown reduced to 15 seconds (was 18 seconds).")
        self.assertIn("Zerschmettern", slam)
        self.assertIn("15 Sekunden", slam)
        self.assertIn("18 Sekunden", slam)
        self.assertTrue(slam.startswith("🟢"))
        nerf = translate(
            "Furious Howl Attack Power bonus reduced 40%.")
        self.assertIn("40 %", nerf)
        self.assertTrue(nerf.startswith("🔻"))

    def test_class_html_is_organized_by_nested_section(self):
        cooked = """
            <ul><li><strong>Classes</strong><ul>
            <li><strong>Warrior</strong><ul>
                <li>Defensive Stance threat bonus increased to 80% (was 30%).</li>
                <li>Slam's cooldown reduced to 15 seconds (was 18 seconds).</li>
            </ul></li>
            <li><strong>Druid</strong><ul>
                <li>Bear Form threat generation increased to 115% (was 50%).</li>
            </ul></li>
            </ul></li></ul>
        """
        digest = self.e["german_forever_class_digest"](cooked)
        self.assertEqual(len(digest["Krieger"]), 2)
        self.assertEqual(len(digest["Druide"]), 1)
        self.assertNotIn("Paladin", digest)

    def test_heading_format_and_unrelated_general_bullets(self):
        cooked = """
            <h2>Bug Fixes</h2><ul>
              <li>Defensive Stance threat bonus increased to 80% (was 30%).</li>
            </ul>
            <h2>Classes</h2><h3>Warrior</h3><ul>
              <li>Slam's cooldown reduced to 15 seconds (was 18 seconds).</li>
            </ul><h2>World</h2><ul>
              <li>Defensive Stance threat bonus increased to 80% (was 30%).</li>
            </ul>
        """
        digest = self.e["german_forever_class_digest"](cooked)
        self.assertEqual(len(digest["Krieger"]), 1)

    def test_unknown_stat_not_invented_and_names_preserved(self):
        translate = self.e["german_forever_change"]
        self.assertIsNone(translate("Something was reworked in a complex way."))
        self.assertEqual(
            self.e["german_forever_ability"]("Righteous Fury"),
            "Zorn der Gerechtigkeit")
        self.assertEqual(
            self.e["german_forever_ability"]("Furious Howl"),
            "Wutgeheul")

    def test_existing_post_uses_same_discord_message_and_german_fields(self):
        digest = self.e["forever_forum_embed"]({
            "id": 13, "version": 1, "updated": 1793700000,
            "title": "WoW Forever Development Notes",
            "url": "https://us.forums.blizzard.com/en/wow/t/2360696/9",
            "cooked": """
                <ul><li><strong>Classes</strong><ul>
                <li><strong>Warrior</strong><ul>
                <li>Defensive Stance threat bonus increased to 80% (was 30%).</li>
                </ul></li></ul></li></ul>"""
        })
        self.assertIn("Deutsch", digest.title)
        self.assertTrue(any("Krieger" in name for name, _, _ in digest.fields))
        self.assertTrue(any("80 %" in value for _, value, _ in digest.fields))
        self.assertLessEqual(
            len(digest.description) + sum(len(n)+len(v)
            for n,v,_ in digest.fields), 6000)
        self.assertIn('if formats.get(post["id"], 0) >= 21:', SOURCE)
        self.assertIn("INSERT OR REPLACE INTO forever_forum_card_formats", SOURCE)


if __name__ == "__main__":
    unittest.main()
