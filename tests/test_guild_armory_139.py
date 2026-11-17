"""WoW Forever Corpsegrinder guild armory v1.0.39 offline regression tests.

No Blizzard credentials, Discord token, Home Assistant or network required.
"""
import ast
import asyncio
import json
import re
from pathlib import Path
from types import SimpleNamespace
import unittest
from urllib.parse import urlparse, quote

import discord

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text("utf-8")
CONFIG = (ROOT / "corpsegrinder_wow_bot" / "config.yaml").read_text("utf-8")
UPDATER = (ROOT / "corpsegrinder_wow_bot" / "updater_core.py").read_text("utf-8")
TREE = ast.parse(BOT)

SAMPLE_ROSTER = {
    "members": [
        {"character": {
            "name": "Zaraku", "surname": "Erdmann",
            "slug": "zaraku-erdmann", "level": 27,
            "playable_class": {"id": 7}, "playable_race": {"id": 8}
        }, "rank": 1},
        {"character": {
            "name": "Treukrieger", "surname": "Eisenfaust",
            "slug": "treukrieger-eisenfaust", "level": 31,
            "playable_class": {"id": 1}
        }, "rank": 2},
        {"character": {
            "name": "Jungtroll", "surname": "Knurrbart",
            "slug": "jungtroll-knurrbart", "level": 5,
            "playable_class": {"id": 3}
        }, "rank": 3},
    ]
}


def ast_const(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("Missing " + name)


def isolated(*names, extras=None):
    nodes = [
        node for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.name in names]
    env = {
        "discord": discord,
        "asyncio": asyncio,
        "ArmoryError": type("ArmoryError", (RuntimeError,), {}),
        "re": re,
        "json": json,
        "urlparse": urlparse,
        "quote": quote,
        "_ARMORY_CLASS_NAMES": {
            1: "Krieger", 3: "Jäger", 7: "Schamane",
        },
        "_ARMORY_CLASS_ICONS": {
            "Krieger": "⚔️", "Jäger": "🏹", "Schamane": "🌩️",
        },
        "ARMORY_PANEL_MARKER": "corpsegrinder:armory:v139",
        "ARMORY_GUILD_URL": (
            "https://worldofwarcraft.blizzard.com/de-de/"
            "forever/eu/armory/guild/corpsegrinder"),
        "ARMORY_PAGE_SIZE": 4,
        "ARMORY_API": "https://eu.api.blizzard.com",
        "ARMORY_NAMESPACE": "profile-forever-eu",
        "ARMORY_GUILD_SLUG": "corpsegrinder",
    }
    env.update(extras or {})
    exec(compile(ast.fix_missing_locations(
        ast.Module(body=nodes, type_ignores=[])),
        "bot.py", "exec"), env)
    return env


class ArmoryTests(unittest.TestCase):
    def test_configuration_is_only_in_ha_not_git_and_requires_app_update(self):
        self.assertIn('version: "1.0.7"', CONFIG)
        for line in ('blizzard_client_id: ""',
                     'blizzard_client_secret: ""',
                     "blizzard_client_secret: password?"):
            self.assertIn(line, CONFIG)
        self.assertIn('BUILTIN_VERSION = "1.0.7"', UPDATER)
        self.assertIn('CONFIG.get("blizzard_client_secret")', BOT)
        self.assertIn("BLIZZARD_CLIENT_SECRET", BOT)

    def test_member_list_includes_low_levels_and_full_surnames(self):
        normalize = isolated("_armory_normalize_roster")["_armory_normalize_roster"]
        members = normalize(SAMPLE_ROSTER)
        self.assertEqual(len(members), 3)
        self.assertEqual([m["slug"] for m in members], [
            "jungtroll-knurrbart", "treukrieger-eisenfaust", "zaraku-erdmann"
        ])
        self.assertEqual(members[0]["level"], 5)
        self.assertEqual(members[1]["klass"], "Krieger")
        self.assertEqual(members[2]["name"], "Zaraku Erdmann")

    def test_unicode_characters_remain_supported(self):
        normalize = isolated("_armory_normalize_roster")["_armory_normalize_roster"]
        members = normalize({"members": [{"character": {
            "slug": "büro-kämpfer", "name": "Büro",
            "surname": "Kämpfer", "level": 13,
            "playable_class": {"id": 1}}}]})
        self.assertEqual(members[0]["slug"], "büro-kämpfer")
        url = isolated("armory_profile_url")["armory_profile_url"](
            members[0]["slug"])
        self.assertIn("b%C3%BCro-k%C3%A4mpfer", url)

    def test_rejects_invalid_member_slugs_and_duplicate_entries(self):
        normalize = isolated("_armory_normalize_roster")["_armory_normalize_roster"]
        samples = [
            {"character": {"name": "X", "slug": "x/../../other", "level": 12}},
            {"character": {"name": "Zaraku", "slug": "zaraku-erdmann", "level": 20}},
            SAMPLE_ROSTER["members"][0],
        ]
        self.assertEqual(len(normalize({"members": samples})), 1)
        with self.assertRaises(RuntimeError):
            normalize({"members": []})
        with self.assertRaises(RuntimeError):
            normalize({"not_the_members": []})

    def test_accepts_only_blizzard_cdn_https_images(self):
        safe = isolated("_armory_safe_image_url")["_armory_safe_image_url"]
        image = "https://render.worldofwarcraft.com/forever-eu/character/test.jpg"
        self.assertEqual(safe(image), image)
        for bad in [
            "http://render.worldofwarcraft.com/img.png",
            "https://render.worldofwarcraft.com.bad.example/path",
            "https://evil.example/forever-eu/x.png",
            "file:///etc/passwd", "javascript:alert(1)", 0,
        ]:
            self.assertIsNone(safe(bad))

    def test_no_secret_in_error_and_client_credentials_only(self):
        self.assertIn("https://oauth.battle.net/token", BOT)
        self.assertIn('grant_type": "client_credentials"', BOT)
        self.assertIn('namespace": ARMORY_NAMESPACE', BOT)
        self.assertIn("urllib.error.HTTPError", BOT)
        self.assertIn("Blizzard antwortet mit HTTP ", BOT)
        self.assertNotIn("logger.exception(exc)", BOT)

    def test_gallery_reuses_existing_channel_without_any_new_channel(self):
        self.assertIn('target = channel(guild, "charaktere-und-berufe")', BOT)
        self.assertIn("await existing.edit(", BOT)
        self.assertIn("save_setting(ARMORY_PANEL_KEY, str(existing.id))", BOT)
        self.assertIn("ARMORY_PANEL_MARKER", BOT)
        self.assertIn("guild.get_member", BOT)  # Existing HMB unaffected
        armory = BOT[BOT.index("# --- Corpsegrinder Forever Gilden-Arsenal"):
                     BOT.index("# --- Hold My Beer (PvP-Ableger)")]
        self.assertNotIn("create_text_channel", armory)
        self.assertNotIn("create_role", armory)
        self.assertNotIn("delete()", armory)
        self.assertIn("interaction.response.defer(ephemeral=True", armory)
        self.assertIn("allowed_mentions=discord.AllowedMentions.none()", armory)

    def test_embed_contains_real_character_thumbnail_or_fallback(self):
        cache = {"members": isolated("_armory_normalize_roster")[
            "_armory_normalize_roster"](SAMPLE_ROSTER)}
        async def image(slug):
            if slug == "zaraku-erdmann":
                return "https://render.worldofwarcraft.com/forever-eu/a.jpg"
            return None
        env = isolated(
            "armory_summary", "armory_profile_url", "armory_page_embeds",
            extras={
                "_armory_cache": cache,
                "armory_image": image,
                "ARMORY_PANEL_MARKER": "corpsegrinder:armory:v139",
            })
        embeds = asyncio.run(env["armory_page_embeds"](0, intro=True))
        self.assertEqual(len(embeds), 4)
        self.assertEqual(embeds[0].footer.text, "corpsegrinder:armory:v139")
        self.assertIn("3 Charaktere", embeds[0].description)
        self.assertTrue(embeds[3].thumbnail.url.endswith("/a.jpg"))
        self.assertIn("Stufe 5", embeds[1].description)
        self.assertIn("noch nicht verfügbar", embeds[1].fields[0].name)
        self.assertNotIn("@everyone", str([e.to_dict() for e in embeds]))

    def test_discord_component_structure_is_valid(self):
        env = isolated(
            "ArmoryIndexView", "ArmoryMemberSelect", "ArmoryBrowseView",
            extras={
                "_armory_cache": {"members": [
                    {"slug": "aaa-bbb", "name": "Test Char", "klass": "Krieger",
                     "level": 11}]},
                "armory_summary": lambda m: "Krieger · Stufe 11",
            })
        async def inspect_views():
            board = env["ArmoryIndexView"]()
            self.assertTrue(board.is_persistent())
            self.assertEqual(len(board.children), 2)
            self.assertIn("corpse_armory_open_v139",
                          [c.custom_id for c in board.children])
            browse = env["ArmoryBrowseView"](0)
            self.assertEqual(browse.timeout, 240)
            self.assertEqual(len(browse.children), 3)
            self.assertTrue(browse.prev.disabled)
            self.assertTrue(browse.next.disabled)
        asyncio.run(inspect_views())

    def test_discord_ui_has_private_gallery_and_select(self):
        src = BOT[BOT.index("class ArmoryMemberSelect"):
                  BOT.index("async def publish_armory_panel")]
        self.assertIn("ArmoryBrowseView", src)
        self.assertIn("ephemeral=True", src)
        self.assertIn("timeout=240", src)
        self.assertIn("discord.ui.Select", src)
        self.assertIn('label="Mitglieder ansehen"', src)
        self.assertIn("ARMORY_GUILD_URL", src)

    def test_existing_server_guilds_remain_separate(self):
        self.assertIn('"⚔️ WOW FOREVER | PVE": [', BOT)
        self.assertIn('"🍺 HOLD MY BEER | PVP": [', BOT)
        self.assertIn('name="hmb_einsatzzentrale"', BOT)
        self.assertIn("corpsegrinder:welcome", (ROOT/"corpsegrinder_wow_bot"/"community_features.py").read_text("utf-8"))
        self.assertNotIn("BLIZZARD_CLIENT_SECRET = \"", BOT)


if __name__ == "__main__":
    unittest.main()
