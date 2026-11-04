"""Offline tests for official Blizzard Forever news (no bot credentials)."""
import ast
from datetime import datetime, timezone, timedelta
from pathlib import Path
import email.utils
import html
from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
import re
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
NAMES = {
    "clean_official_text", "official_article_link", "official_forever_title",
    "ForeverNewsIndexParser", "ForeverArticleParser",
    "parse_blizzard_publication_date", "parse_blizzard_article",
    "gather_official_forever_articles", "extract_blizzard_forever_api_items"
}


def load_helpers():
    nodes = [node for node in TREE.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))
             and node.name in NAMES]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    env = {
        "html": html, "HTMLParser": HTMLParser,
        "re": re, "urljoin": urljoin, "urlparse": urlparse,
        "email": email, "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
        "FOREVER_NEWS_HOSTS": frozenset({
            "worldofwarcraft.blizzard.com", "news.blizzard.com"
        }), "json": __import__("json"), "FOREVER_NEWS_MAX_ARTICLES": 15
    }
    exec(compile(module, "bot.py", "exec"), env)
    return env


class ForeverNewsTests(unittest.TestCase):
    def setUp(self):
        self.e = load_helpers()

    def test_only_official_blizzard_news_links(self):
        resolve = self.e["official_article_link"]
        base = "https://worldofwarcraft.blizzard.com/de-de/news"
        self.assertEqual(
            resolve("/de-de/news/24315820/forever", base)[0], 24315820)
        self.assertEqual(
            resolve("https://news.blizzard.com/de-de/article/24315820/name", base)[0],
            24315820)
        self.assertIsNone(resolve("http://news.blizzard.com/de-de/article/24315820", base))
        self.assertIsNone(resolve("https://evil.example/de-de/news/24315820", base))
        self.assertIsNone(resolve("javascript:alert(1)", base))

    def test_filter_forever_only_and_not_mixed_news(self):
        relevant = self.e["official_forever_title"]
        self.assertTrue(relevant("WoW: Forever erscheint weltweit am 5. November!"))
        self.assertTrue(relevant("Kehrt in World of Warcraft: Forever nach Azeroth zurück"))
        self.assertFalse(relevant("Die Demo von Ruf der Legenden in WoW: Midnight ist live"))
        self.assertFalse(relevant("World of Warcraft Classic: neue Realm-News"))
        self.assertFalse(relevant("Diese Woche in WoW: Forever, Midnight und mehr"))

    def test_linked_heading_and_news_index(self):
        index = self.e["ForeverNewsIndexParser"](
            "https://worldofwarcraft.blizzard.com/de-de/news")
        index.feed("""
            <a href="/de-de/news/24315820/forever"><h3>World of Warcraft:
            Forever erscheint weltweit am 5. November!</h3></a>
            <a href="/de-de/news/24315821/midnight">Midnight ist jetzt live</a>
            <a href="https://attacker.example/de-de/news/24315822/forever">
            WoW: Forever</a>
        """)
        self.assertEqual(len(index.results), 1)
        self.assertEqual(index.results[0][0], 24315820)

    def test_publication_date_from_metadata(self):
        parse = self.e["parse_blizzard_article"]
        article = """
        <html><head>
        <meta property="og:title" content="WoW: Forever – Neues Abenteuer!"/>
        <meta property="article:published_time" content="2026-11-02T19:00:00+00:00"/>
        <meta property="og:description" content="Offizielles Blizzard-Update"/>
        </head><body><h1>WoW: Forever – Neues Abenteuer!</h1></body></html>
        """
        title, desc, ts = parse(article, "WoW: Forever")
        self.assertEqual(ts, int(datetime(
            2026, 11, 2, 19, tzinfo=timezone.utc).timestamp()))
        self.assertIn("Neues Abenteuer", title)

    def test_publication_date_json_ld(self):
        parse = self.e["parse_blizzard_article"]
        article = """<html><head><script type="application/ld+json">
        {"@type": "NewsArticle", "datePublished": "2026-11-01T18:00:00Z"}
        </script></head><body><h1>World of Warcraft: Forever startet</h1></body></html>"""
        self.assertEqual(parse(article, "WoW Forever")[2],
                         int(datetime(2026,11,1,18,tzinfo=timezone.utc).timestamp()))

    def test_undated_article_is_not_posted(self):
        article = """<h1>World of Warcraft: Forever startet!</h1>
        <div>5. November 2026, 21:00 Uhr – geplanter Spielstart</div>"""
        self.assertIsNone(self.e["parse_blizzard_article"](article, "Forever"))

    def test_english_rfc_and_german_publication_date(self):
        parse = self.e["parse_blizzard_publication_date"]
        self.assertIsNotNone(parse("Mon, 02 Nov 2026 19:00:00 GMT"))
        self.assertIsNotNone(parse("2. November 2026 um 19:00 GMT"))
        self.assertIsNone(parse("5. November Spielstart"))

    def test_embedded_json_news_links_recovered_and_dated(self):
        now = datetime.now(timezone.utc)
        stamp = now.isoformat()
        index = """
          <script>
          {"article":"/de-de/news/24315820/forever-launch",
           "title":"World of Warcraft: Forever wird veröffentlicht"}
          </script>
        """
        article = f"""
          <html><head>
          <meta property="article:published_time" content="{stamp}">
          <meta property="og:title" content="World of Warcraft: Forever wird veröffentlicht">
          </head><body><h1>World of Warcraft: Forever wird veröffentlicht</h1></body></html>
        """
        env = self.e
        env["FOREVER_NEWS_API"] = (
            "https://news.blizzard.com/de-de/api/news/blizzard?"
            "feedCxpProductIds%5B%5D=world-of-warcraft-forever")
        env["FOREVER_NEWS_INDEXES"] = (
            "https://worldofwarcraft.blizzard.com/de-de/news",)
        env["FOREVER_NEWS_BACKFILL"] = 48 * 3600
        env["FOREVER_NEWS_MAX_ARTICLES"] = 15
        env["logging"] = __import__("logging")
        env["read_official_blizzard_page"] = lambda url: (
            index if url.endswith("/de-de/news") else article)
        rows = env["gather_official_forever_articles"]()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], 24315820)
        self.assertEqual(env["gather_official_forever_articles"]({24315820}), [])

    def test_official_blizzard_forever_api_schema(self):
        fixture = """
        {"feed":{"contentItems":[
          {"properties":{"title":"World of Warcraft: Forever – Launch!",
           "newsId":"24315820",
           "newsUrl":"https://news.blizzard.com/de-de/article/24315820/forever-launch",
           "summary":"Forever startet."}},
          {"properties":{"title":"Ruf der Legenden: Midnight",
           "newsUrl":"https://news.blizzard.com/de-de/article/24315821/midnight"}},
          {"properties":{"title":"Forever auf unbekannter Webseite",
           "newsUrl":"https://not-blizzard.example/de-de/article/24315822/forever"}}
        ]}}
        """
        items = self.e["extract_blizzard_forever_api_items"](fixture)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0][0], 24315820)
        self.assertEqual(items[0][2], "World of Warcraft: Forever – Launch!")

    def test_channel_and_checks_are_in_bootstrap(self):
        self.assertIn('("forever-news", "text")', SOURCE)
        self.assertIn("background(forever_news_worker())", SOURCE)
        self.assertIn("FOREVER_NEWS_PERIOD = 30 * 60", SOURCE)
        self.assertIn("FOREVER_NEWS_BACKFILL = 14 * 86400", SOURCE)
        self.assertIn("CREATE TABLE IF NOT EXISTS blizzard_news_posts", SOURCE)
        self.assertIn('name="forever_news_status"', SOURCE)
        self.assertIn('name="forever_news_pruefen"', SOURCE)


if __name__ == "__main__":
    unittest.main()
