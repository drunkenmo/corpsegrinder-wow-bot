"""1.0.32: real, dated Forever news and verified publisher images."""
import ast
from datetime import datetime, timezone
from html.parser import HTMLParser
import html
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT/"corpsegrinder_wow_bot"/"bot.py").read_text(encoding="utf-8")
TREE = ast.parse(BOT)
SELECTED = {"clean_official_text", "ForeverArticleParser",
            "trusted_forever_media_url", "media_from_forever_article",
            "verified_news_excerpt", "parse_community_rss",
            "community_news_embed", "forever_news_embed"}


class FakeEmbed:
    def __init__(self, **kwargs):
        self.title = kwargs.get("title")
        self.description = kwargs.get("description")
        self.url = kwargs.get("url")
        self.timestamp = kwargs.get("timestamp")
        self.image = None
        self.fields = []
        self.footer = None

    def add_field(self, **kwargs):
        self.fields.append(kwargs)

    def set_footer(self, **kwargs):
        self.footer = kwargs["text"]

    def set_image(self, **kwargs):
        self.image = kwargs["url"]


def load():
    nodes=[n for n in TREE.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))
           and n.name in SELECTED]
    assigns={}
    for n in TREE.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id in (
                        "FOREVER_MEDIA_HOSTS","FOREVER_VIDEO_HOSTS",
                        "FOREVER_COMMUNITY_HOSTS"):
                    assigns[t.id]=ast.literal_eval(n.value.args[0])
    env={
        "re":re, "html":html, "HTMLParser":HTMLParser, "ET":ET,
        "datetime":datetime, "timezone":timezone,
        "urlparse":urlparse, "urljoin":urljoin,
        "parse_blizzard_publication_date":lambda v:
            (int(datetime.strptime(v, "%a, %d %b %Y %H:%M:%S GMT")
                 .replace(tzinfo=timezone.utc).timestamp()) if v else None),
        "discord":SimpleNamespace(
            Embed=FakeEmbed,
            Colour=SimpleNamespace(from_rgb=lambda *args:0)),
        **{k:frozenset(v) for k,v in assigns.items()},
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
                 "bot.py","exec"),env)
    return env


class RealForeverNewsTests(unittest.TestCase):
    def setUp(self):
        self.f=load()

    def test_new_rss_domains_and_curation(self):
        self.assertIn("https://wowforever-community.de/feed.xml",BOT)
        self.assertIn("https://wow.4fansites.de/rss_feed.xml",BOT)
        self.assertIn("https://www.wowhead.com/news&rss",BOT)
        self.assertIn("FOREVER_COMMUNITY_LOOKBACK = 14 * 86400",BOT)
        self.assertIn("FOREVER_NEWS_BACKFILL = 14 * 86400",BOT)
        self.assertNotIn("await seed_forever_news_reading(target)",BOT)

    def test_generic_wow_feed_filters_other_products_and_undated(self):
        xml = """<rss><channel>
          <item><title>WoW Forever: Neue Klassenbalance</title>
          <link>https://wow.4fansites.de/news/forever</link>
          <pubDate>Tue, 03 Nov 2026 11:00:00 GMT</pubDate>
          <description>Änderungen in WoW Forever</description></item>
          <item><title>Handelsposten November</title>
          <link>https://wow.4fansites.de/news/handelsposten</link>
          <pubDate>Tue, 03 Nov 2026 10:00:00 GMT</pubDate></item>
          <item><title>WoW Forever: Gerücht</title>
          <link>https://wow.4fansites.de/news/undated</link>
          <description>Kein Veröffentlichungsdatum</description></item>
          <item><title>WoW Midnight &amp; Forever</title>
          <link>https://wow.4fansites.de/news/midnight</link>
          <pubDate>Tue, 03 Nov 2026 09:00:00 GMT</pubDate></item>
        </channel></rss>"""
        posts=self.f["parse_community_rss"](xml,"WoW Source")
        self.assertEqual(len(posts),1)
        self.assertIn("Forever",posts[0][2])

    def test_unauthorized_hosts_and_fake_media_urls_are_blocked(self):
        url=self.f["trusted_forever_media_url"]
        base="https://www.wowhead.com/news/forever-383670"
        self.assertIsNone(url("http://www.wowhead.com/picture.jpg",base))
        self.assertIsNone(url("https://evil.example/picture.jpg",base))
        self.assertIsNone(url("https://127.0.0.1/private",base))
        self.assertIsNone(url("https://wow.zamimg.com:8080/img.jpg",base))
        self.assertIsNone(url("https://user:pass@wow.zamimg.com/img.jpg",base))
        self.assertEqual(url("https://wow.zamimg.com/img.jpg",base),
                         "https://wow.zamimg.com/img.jpg")
        self.assertIsNone(url("https://www.youtube.com/watch?v=123",base))
        self.assertEqual(
            url("https://www.youtube.com/watch?v=123",base,video=True),
            "https://www.youtube.com/watch?v=123")

    def test_real_media_only_from_page_meta(self):
        page = """<head>
          <meta property="og:image" content="https://wow.zamimg.com/large.jpg">
          <meta property="og:video" content="https://www.youtube.com/watch?v=123">
        </head>"""
        self.assertEqual(self.f["media_from_forever_article"](
            page,"https://www.wowhead.com/news/forever-383670"),
            ("https://wow.zamimg.com/large.jpg",
             "https://www.youtube.com/watch?v=123"))
        self.assertEqual(self.f["media_from_forever_article"](
            "<h1>Keine Medien</h1>","https://wow-forever.gg/news/news"), (None,None))

    def test_news_embed_contains_real_image_and_original_link(self):
        card=self.f["community_news_embed"](
            (1793703600,"https://wow-forever.gg/news/true",
             "Beta-Build mit Änderungen", "49 neue Zauber im Client",
             "Forever-Community"),
            "https://wow-forever.gg/news/image.jpg",
            "https://www.youtube.com/watch?v=123")
        self.assertEqual(card.image,"https://wow-forever.gg/news/image.jpg")
        self.assertIn("Beta-Build",card.title)
        self.assertIn("49 neue Zauber",card.description)
        self.assertIn("Originalbericht",card.fields[-1]["name"])
        self.assertIn("nicht Blizzard",card.footer)
        self.assertEqual(len(card.fields),2)

    def test_blizzard_card_is_distinct_and_does_not_invent(self):
        row=(1793703600,24315820,"WoW Forever: Offizielle Meldung",
             "", "https://worldofwarcraft.blizzard.com/de-de/news/24315820/forever")
        card=self.f["forever_news_embed"](row)
        self.assertIsNone(card.image)
        self.assertIn("Keine Kurzbeschreibung",card.description)
        self.assertIn("Blizzard",card.footer)
        self.assertEqual(card.url,row[-1])
        self.assertIn("Originalquelle",card.fields[-1]["name"])


if __name__ == "__main__":
    unittest.main()
