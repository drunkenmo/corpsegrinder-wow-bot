"""Offline tests for the official WoW Forever Blizzard forum reader (1.0.20)."""
import ast
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
import email
import html
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def load_helpers():
    selected = {
        "clean_official_text", "parse_blizzard_publication_date",
        "extract_forever_forum_staff_posts", "forever_forum_embed"
    }
    nodes = [n for n in TREE.body
             if isinstance(n, ast.FunctionDef) and n.name in selected]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    env = {
        "html": html, "re": re, "email": email, "datetime": datetime,
        "timezone": timezone, "timedelta": timedelta,
        "FOREVER_FORUM_ROOT": "https://us.forums.blizzard.com/en/wow",
        "FOREVER_FORUM_LOOKBACK": 7 * 86400,
        "FOREVER_FORUM_CLASS_NAMES": (
            ("warrior", "Krieger"), ("shaman", "Schamane"),
            ("druid", "Druide"), ("hunter", "Jäger")),
        "discord": SimpleNamespace(
            Embed=None, Colour=SimpleNamespace(blue=lambda: 1)),
    }
    exec(compile(module, "bot.py", "exec"), env)
    return env


class ForeverForumTests(unittest.TestCase):
    def setUp(self):
        self.helpers = load_helpers()
        self.now = int(datetime(2026, 11, 3, 17, tzinfo=timezone.utc).timestamp())

    def test_official_staff_post_and_updated_notes_are_detected(self):
        doc = {
            "title": "WoW Forever Beta Development Notes",
            "post_stream": {"posts": [
                {"id": 10, "post_number": 5, "version": 4, "staff": True,
                 "created_at": "2026-09-25T10:00:00Z",
                 "updated_at": "2026-11-02T18:00:00Z",
                 "cooked": "<p>Warrior and Shaman class changes</p>"},
                {"id": 11, "post_number": 6, "version": 1, "staff": False,
                 "created_at": "2026-11-03T12:00:00Z",
                 "cooked": "<p>Warrior nerf</p>"},
            ]}
        }
        posts = self.helpers["extract_forever_forum_staff_posts"](
            doc, 2360696, self.now)
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["version"], 4)
        self.assertIn("Krieger", posts[0]["classes"])
        self.assertIn("Schamane", posts[0]["classes"])
        self.assertTrue(posts[0]["url"].endswith("/2360696/5"))

    def test_stale_and_unrelated_posts_are_ignored(self):
        post = {"id": 21, "post_number": 3, "version": 1,
                "staff": True, "created_at": "2026-10-10T10:00:00Z",
                "cooked": "<p>nothing changed</p>"}
        parse = self.helpers["extract_forever_forum_staff_posts"]
        self.assertEqual(parse(
            {"title": "Forever notes", "post_stream": {"posts": [post]}},
            2360696, self.now), [])
        post["updated_at"] = "2026-11-03T10:00:00Z"
        self.assertEqual(parse(
            {"title": "Midnight notes", "post_stream": {"posts": [post]}},
            2360696, self.now), [])

    def test_pending_edited_post_does_not_duplicate_on_same_version(self):
        self.assertIn("if prior and prior[0] >= post[\"version\"]:", SOURCE)
        self.assertIn("await message.edit(embed=forever_forum_embed(post))", SOURCE)
        self.assertIn("INSERT OR REPLACE INTO forever_forum_posts", SOURCE)

    def test_status_and_poll_integrate_forum(self):
        self.assertIn("added, updated = await check_forever_forum_news(target)", SOURCE)
        self.assertIn("Blueposts: **{forum_total}**", SOURCE)


if __name__ == "__main__":
    unittest.main()
