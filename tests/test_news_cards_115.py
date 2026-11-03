"""Corpsegrinder v1.0.15 – WoW Forever news directly readable in Discord."""
import ast
import html
from pathlib import Path
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTIONS = {
    "clean_official_text", "german_forever_news_title",
    "german_forever_news_summary"
}


def load_formatters():
    env = {"re": re, "html": html}
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for dest in node.targets:
                if isinstance(dest, ast.Name) and dest.id in (
                        "GERMAN_NEWS_COUNTS", "GERMAN_CLASS_NAMES"):
                    env[dest.id] = ast.literal_eval(node.value)
    body = [node for node in TREE.body if isinstance(node, ast.FunctionDef)
            and node.name in FUNCTIONS]
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    exec(compile(module, "bot.py", "exec"), env)
    return env


class TestGermanNewsCards(unittest.TestCase):
    def setUp(self):
        self.env = load_formatters()
        self.headline = self.env["german_forever_news_title"]
        self.summary = self.env["german_forever_news_summary"]

    def test_beta_build_title_german(self):
        self.assertIn(
            "Beta-Build 70707",
            self.headline("Beta build 70707 is out: 64 new spells"))

    def test_changelog_headline_german(self):
        self.assertEqual(
            self.headline("Build 1.60.1.70707: what changed since 1.60.1.70532"),
            "Build 1.60.1.70707: Änderungen seit 1.60.1.70532")

    def test_changelog_summary_facts(self):
        txt = self.summary(
            "Build 1.60.1.70707: what changed since 1.60.1.70532",
            "Spells: 68 added, 0 removed, 127 changed. "
            "Items: 10 added, 0 removed, 58 changed. "
            "Talents in the Forever class trees: 465.")
        self.assertIn("68 neu, 0 entfernt, 127 geändert", txt)
        self.assertIn("10 neu, 0 entfernt, 58 geändert", txt)
        self.assertIn("465", txt)
        self.assertIn("Buildnummer", txt)
        self.assertNotIn("Spells:", txt)
        self.assertNotIn("what changed since", txt)

    def test_short_beta_article_german(self):
        txt = self.summary(
            "Beta build 70707 is out: 64 new spells",
            "Build 1.60.1.70707 of WoW Forever beta, against build "
            "1.60.1.70532: 64 new spells, 10 new items.")
        self.assertIn("64 neu", txt)
        self.assertIn("10 neu", txt)
        self.assertNotIn("68 neu", txt)

    def test_classes_and_talents_german(self):
        title = "Massive Talent Tree Changes to Druids and Paladins"
        self.assertIn("Druiden", self.headline(title))
        self.assertIn("Paladine", self.headline(title))
        self.assertIn("Erwähnte Klassen", self.summary(
            title, "World of Warcraft Forever class tuning and talent updates"))

    def test_fallback_does_not_invent_statistics(self):
        txt = self.summary("WoW Forever Community", "Please see our news for more.")
        self.assertIn("nicht zuverlässig", txt)
        self.assertNotRegex(txt, r"\b\d+ neue")
        self.assertLessEqual(len(txt), 1550)

    def test_no_read_more_button_in_news_cards(self):
        cards = SOURCE[SOURCE.index("def community_news_embed("):
                       SOURCE.index("FOREVER_STARTER_READING", SOURCE.index(
                           "def community_news_embed("))]
        self.assertNotIn("Ausführlicher lesen", cards)
        self.assertNotIn("discord.ui.Button", cards)
        self.assertIn("german_forever_news_summary", cards)
        official = SOURCE[SOURCE.index("def forever_news_embed("):
                          SOURCE.index("async def check_blizzard_forever_news(")]
        self.assertIn("german_forever_news_summary", official)

    def test_preexisting_posts_are_edited_not_reposted(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS forever_news_card_versions", SOURCE)
        self.assertIn("pending_upgrade = known - upgraded", SOURCE)
        self.assertIn("await old.edit(embed=community_news_embed(post))", SOURCE)
        self.assertIn('"SELECT canonical_url,discord_message_id FROM forever_community_posts"', SOURCE)


if __name__ == "__main__":
    unittest.main()
