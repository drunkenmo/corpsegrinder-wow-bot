"""Offline-Tests: echte CurseForge-Projektlogos über CFWidget-Fallback."""
import ast
import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from urllib.request import Request

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


def load():
    names = (
        "addon_project_url", "trusted_addon_icon_url",
        "read_cfwidget_project", "extract_cfwidget_project_icon",
        "extract_cfwidget_forever_version",
        "CurseForgeProjectIcon", "extract_curseforge_project_icon",
        "scan_forever_addons",
    )
    nodes = [node for node in TREE.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))
             and node.name in names]
    scope = {
        "json": json, "html": html, "re": re,
        "urlparse": urlparse, "Request": Request, "HTMLParser": HTMLParser,
        "ADDON_PROJECT_BASE": constant("ADDON_PROJECT_BASE"),
        "ADDON_DISCOVERY_URL": "https://www.curseforge.com/wow/search",
        "ADDON_ICON_HOSTS": constant("ADDON_ICON_HOSTS"),
        "ADDON_SOURCES": constant("ADDON_SOURCES"),
        "clean_official_text": lambda s, limit: s[:limit],
    }
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=nodes, type_ignores=[])), "bot.py", "exec"), scope)
    return scope


class Response:
    def __init__(self, payload, url):
        self.payload, self.url = payload, url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def geturl(self):
        return self.url

    def read(self, size):
        return self.payload[:size]


class CFWidgetIconFallbackTests(unittest.TestCase):
    def setUp(self):
        self.env = load()

    def test_reads_exact_project_json_without_api_key(self):
        url = "https://api.cfwidget.com/wow/addons/blackthornes-farmer"
        metadata = {"id": 1710618, "game": "wow",
                    "slug": "blackthornes-farmer",
                    "thumbnail": "https://media.forgecdn.net/avatars/123/45/farmer.png"}
        def get(request, timeout):
            self.assertEqual(request.full_url, url)
            self.assertEqual(request.get_header("Accept"), "application/json")
            self.assertLessEqual(timeout, 15)
            return Response(json.dumps(metadata).encode(), url)
        self.env["urlopen"] = get
        p = self.env["read_cfwidget_project"]("blackthornes-farmer")
        self.assertEqual(p["id"], 1710618)
        self.assertEqual(self.env["extract_cfwidget_project_icon"](p), metadata["thumbnail"])

    def test_mismatched_project_and_redirects_are_rejected(self):
        base = "https://api.cfwidget.com/wow/addons/blackthornes-farmer"
        for data, actual in [
            ({"id": 17, "slug": "other", "game": "wow"}, base),
            ({"id": 17, "game": "minecraft"}, base),
            ({"id": 17, "game": "wow"}, "https://untrusted.example/wow/addons/x"),
            ({"error": "not ready"}, base),
        ]:
            self.env["urlopen"] = lambda request, timeout: Response(
                json.dumps(data).encode(), actual)
            with self.assertRaises(ValueError):
                self.env["read_cfwidget_project"]("blackthornes-farmer")

    def test_never_mistakes_screenshots_for_icons(self):
        icon = self.env["extract_cfwidget_project_icon"]
        self.assertIsNone(icon({
            "thumbnail": "https://media.forgecdn.net/gallery/1/4/cover.jpg",
            "screenshots": [{"url": "https://media.forgecdn.net/avatars/1/2/logo.png"}]
        }))
        self.assertIsNone(icon({"thumbnail": "https://evil.example/avatars/2/3/icon.png"}))
        self.assertIsNone(icon({"thumbnail": "https://static-beta.curseforge.com/placeholder.png"}))

    def test_forever_versions_only_from_explicit_file_names(self):
        version = self.env["extract_cfwidget_forever_version"]
        self.assertEqual(version({
            "download": {"name": "v1.5.2-forever", "version": "1.60.1"},
            "files": [{"name": "v22-retail"}]
        }), "v1.5.2-forever")
        self.assertIsNone(version({
            "download": {"name": "v22-retail", "version": "12.0.1"},
            "files": [{"name": "classic-release-1.15.9"}]
        }))

    def test_curseforge_403_recovers_curated_images_without_spam(self):
        def blocked(_):
            raise OSError("HTTP Error 403")
        self.env["read_curseforge_page"] = blocked
        self.env["read_cfwidget_project"] = lambda slug: {
            "id": 100001, "game": "wow", "slug": slug,
            "thumbnail": ("https://media.forgecdn.net/avatars/100/12/"
                          + slug + ".png"),
            "download": {"name": slug + "-1.0.0-forever"}
        }
        rows, errors, icons = self.env["scan_forever_addons"](include_icons=True)
        self.assertEqual(len(rows), 19)
        self.assertEqual(len(icons), 19)
        self.assertEqual(len(set(icons.values())), 19)
        self.assertTrue(all(name.startswith("https://media.forgecdn.net/avatars/")
                            for name in icons.values()))
        self.assertTrue(any("CurseForge-Suche" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
