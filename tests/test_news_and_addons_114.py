"""Isolated regression tests for Corpsegrinder 1.0.14 news and addons."""
import ast
import email.utils
import html
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

SOURCE = (Path(__file__).resolve().parents[1] /
          "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTIONS = {
    "clean_official_text", "parse_blizzard_publication_date",
    "wowhead_forever_link", "WowheadForeverIndex",
    "parse_community_rss", "inspect_wowhead_article", "ForeverArticleParser",
    "addon_project_url", "CurseForgeText",
    "extract_curseforge_forever_version", "CurseForgeDiscovery",
    "gather_community_forever_news", "scan_forever_addons",
}


def isolated():
    nodes = [n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
             and n.name in FUNCTIONS]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    env = {
        "re": re, "html": html, "HTMLParser": HTMLParser, "urljoin": urljoin,
        "urlparse": urlparse, "ET": ET, "email": email,
        "datetime": datetime, "timezone": timezone, "timedelta": timedelta,
        "FOREVER_WOWHEAD_INDEX": "https://www.wowhead.com/forever/news",
        "FOREVER_COMMUNITY_HOSTS": frozenset((
            "wow-forever.gg", "www.wow-forever.gg",
            "www.wowhead.com", "wowhead.com",
            "worldofwarcraft.blizzard.com", "news.blizzard.com")),
        "ADDON_PROJECT_BASE": "https://www.curseforge.com/wow/addons/",
        "ADDON_SOURCES": (
            ("leatrix-plus","Leatrix Plus","Komfort","QoL"),
            ("tomtom","TomTom","Navigation","Wegpunkte")),
        "FOREVER_COMMUNITY_RSS": ("https://wow-forever.gg/rss.xml",),
        "FOREVER_COMMUNITY_LOOKBACK": 7 * 86400,
        "FOREVER_COMMUNITY_LIMIT": 5,
        "FOREVER_WOWHEAD_INDEX": "https://www.wowhead.com/forever/news",
        "ADDON_DISCOVERY_URL": "https://www.curseforge.com/wow/search",
        "logging": __import__("logging"),
    }
    exec(compile(module, "bot.py", "exec"), env)
    return env


class TestCommunityNews(unittest.TestCase):
    def setUp(self):
        self.env = isolated()

    def test_wowhead_article_urls_are_restricted(self):
        fn=self.env["wowhead_forever_link"]
        self.assertEqual(
            fn("/forever/news/druid-talent-changes-383670")[0],"383670")
        self.assertEqual(
            fn("https://www.wowhead.com/news/new-forever-news-383632")[0],
            "383632")
        self.assertIsNone(fn("https://evil.example/news/forever-383670"))
        self.assertIsNone(fn("http://www.wowhead.com/news/forever-383670"))
        self.assertIsNone(fn("/wow/news/unrelated"))

    def test_rss_parses_original_dates_and_excludes_retail(self):
        feed="""<rss><channel>
          <item><title>Forever: Server-Kapazität</title>
            <link>https://wow-forever.gg/news/forever-servers</link>
            <pubDate>Mon, 02 Nov 2026 19:00:00 GMT</pubDate>
            <description>Eine neue Forever-Meldung</description>
          </item>
          <item><title>Retail Midnight Neuigkeiten</title>
            <link>https://wow-forever.gg/news/retail</link>
            <pubDate>Mon, 02 Nov 2026 19:00:00 GMT</pubDate>
          </item>
        </channel></rss>"""
        items=self.env["parse_community_rss"](feed, "Forever-Community")
        self.assertEqual(len(items),1)
        self.assertEqual(items[0][2],"Forever: Server-Kapazität")
        self.assertEqual(items[0][0],int(datetime(
            2026,11,2,19,tzinfo=timezone.utc).timestamp()))

    def test_undated_article_is_ignored(self):
        raw="""<html><head>
        <meta property="og:title" content="Forever: Änderungen">
        </head><body><h1>Forever: Änderungen</h1></body></html>"""
        self.assertIsNone(self.env["inspect_wowhead_article"](raw,"Forever"))

    def test_integration_news_from_mocked_sources(self):
        when=datetime.now(timezone.utc).isoformat()
        index='<a href="/forever/news/forever-update-383670">WoW Forever Update</a>'
        article=f"""<html><head><meta property="og:description"
        content="WoW Forever updates for everyone.">
        <meta property="article:published_time" content="{when}">
        </head><body><h1>WoW Forever Update</h1></body></html>"""
        rss="""<rss><channel></channel></rss>"""
        env=self.env
        env["fetch_community_page"] = (
            lambda url: index if url.endswith("/forever/news") else
            article if url.endswith("383670") else rss)
        posts,errors=env["gather_community_forever_news"]()
        self.assertEqual(errors,[])
        self.assertEqual(len(posts),1)
        self.assertEqual(posts[0][4],"Wowhead")
        self.assertEqual(env["gather_community_forever_news"](
            {posts[0][1]})[0],[])


class TestAddons(unittest.TestCase):
    def setUp(self):
        self.env=isolated()

    def test_only_curseforge_project_links(self):
        fn=self.env["addon_project_url"]
        self.assertEqual(
            fn("leatrix-plus"),
            "https://www.curseforge.com/wow/addons/leatrix-plus")
        with self.assertRaises(ValueError):
            fn("../unknown")
        with self.assertRaises(ValueError):
            fn("bad?url")

    def test_never_takes_retail_version(self):
        page="""<h4>WoW Retail</h4><span>12.1.15 Latest release R Retail</span>
        <h4>WoW Forever</h4><span>1.60.25-forever Latest release R Forever</span>
        <h4>WoW Classic</h4><span>1.15.9 Latest release R Classic</span>"""
        fn=self.env["extract_curseforge_forever_version"]
        self.assertEqual(fn(page),"1.60.25-forever")
        self.assertIsNone(fn(
            "<h4>WoW Retail</h4>12.1.5 Latest release R Retail"))
        self.assertEqual(fn("R v4.3.12-release 1.60.1 Forever"),
                         "v4.3.12-release")

    def test_discovery_rejects_external_links(self):
        p=self.env["CurseForgeDiscovery"]()
        p.feed('''<a href="/wow/addons/questie">Questie</a>
            <a href="https://malicious.example/wow/addons/suspect">Suspect</a>
            <a href="/wow/addons/leatrix-maps">Leatrix Maps</a>''')
        self.assertEqual(p.slugs,["questie","leatrix-maps"])

    def test_scan_recommends_only_actual_forever_files(self):
        env=self.env
        page="""<h4>WoW Retail</h4>12.1.5 Latest release R Retail
        <h4>WoW Forever</h4>1.60.1-forever Latest release R Forever"""
        env["read_curseforge_page"]=lambda url: (
            '<a href="/wow/addons/fresh-addon">Fresh addon</a>'
            if "search" in url else
            page if url.endswith(("leatrix-plus","fresh-addon")) else
            '<h4>WoW Retail</h4>12.1.5 Latest release R Retail')
        results,errors=env["scan_forever_addons"]()
        self.assertFalse(errors)
        self.assertEqual([row[0] for row in results],
                         ["leatrix-plus","fresh-addon"])
        self.assertEqual(env["scan_forever_addons"](
            {"fresh-addon"})[0][0][0],"leatrix-plus")


class TestIntegrationHooks(unittest.TestCase):
    def test_channels_and_worker_hooks(self):
        for substring in (
            '("forever-news", "text"), ("addons", "text")',
            "background(forever_addons_worker())",
            "FOREVER_COMMUNITY_RSS",
            "FOREVER_WOWHEAD_INDEX",
            "ADDON_CHECK_INTERVAL = 6 * 3600",
            "CREATE TABLE IF NOT EXISTS forever_community_posts",
            "CREATE TABLE IF NOT EXISTS forever_addon_files",
            'name="addons_pruefen"',
            'name="addons_status"',
        ):
            self.assertIn(substring, SOURCE)


if __name__=="__main__":
    unittest.main()
