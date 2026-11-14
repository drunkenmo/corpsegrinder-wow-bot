"""Hold My Beer 1.0.38: separate PvP branding, persisted alerts and safe roles.

Tests use the real discord.py UI components without contacting Discord.
Corpsegrinder PvE and the common onboarding are explicitly unchanged.
"""
import ast
import asyncio
import sqlite3
from pathlib import Path
from types import SimpleNamespace
import unittest

import discord

ROOT=Path(__file__).resolve().parents[1]
CODE=(ROOT/"corpsegrinder_wow_bot"/"bot.py").read_text("utf-8")
FEATURES=(ROOT/"corpsegrinder_wow_bot"/"community_features.py").read_text("utf-8")
TREE=ast.parse(CODE)


def literal(name):
    for node in TREE.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("Missing " + name)


def functions(*names, extras=None):
    wanted=set(names)
    nodes=[n for n in TREE.body if
           isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))
           and n.name in wanted]
    env={"discord":discord,"GUILD_ID":123,
         "HMB_ROLE_NAME":literal("HMB_ROLE_NAME"),
         "HMB_CATEGORY_NAME":literal("HMB_CATEGORY_NAME"),
         "HMB_LEGACY_CATEGORY":literal("HMB_LEGACY_CATEGORY"),
         "HMB_PANEL_MARKER":literal("HMB_PANEL_MARKER"),
         "ART_BASE":"https://raw.githubusercontent.com/drunkenmo/corpsegrinder-wow-bot/main/assets/",
         "HMB_BEACON_TTL":literal("HMB_BEACON_TTL")}
    env.update(extras or {})
    exec(compile(ast.fix_missing_locations(ast.Module(
        body=nodes,type_ignores=[])),"bot.py","exec"),env)
    return env


class GuildBoundaryTests(unittest.TestCase):
    def test_pve_and_shared_start_are_unchanged(self):
        structure=literal("STRUCTURE")
        self.assertEqual(list(structure),[
            "🌋 WOW FOREVER | START",
            "⚔️ WOW FOREVER | PVE",
            "🍺 HOLD MY BEER | PVP",
            "🔨 WOW FOREVER | CHARAKTERE"])
        self.assertEqual(structure["⚔️ WOW FOREVER | PVE"],[
            ("pve-gruppensuche","text"),("pve-gildenchat","text"),
            ("dungeon-planer","text"),("raids-und-termine","text"),
            ("pve-guides","text"),("PvE – Leveln","voice"),
            ("PvE – Dungeon","voice"),("PvE – Raid","voice"),
            ("➕ PvE-Gruppe erstellen","voice")])
        self.assertIn(("pvp-gildenchat","text"),
                      structure["🍺 HOLD MY BEER | PVP"])
        self.assertIn('title="🌋 CORPSEGRINDER · WILLKOMMEN',FEATURES)
        self.assertIn("Corpsegrinder",FEATURES)
        self.assertIn('name="ingame_nickname"',CODE)
        self.assertEqual(literal("HMB_BEACON_TTL"),1200)

    def test_pvp_only_category_migration_preserves_channel_ids(self):
        class FakeCategory:
            def __init__(self,name,id):
                self.name,self.id=name,id
                self.edits=[]
            async def edit(self,**kwargs):
                self.edits.append(kwargs)
                self.name=kwargs["name"]
        original_pve=FakeCategory("⚔️ WOW FOREVER | PVE",11)
        old_pvp=FakeCategory("🏹 WOW FOREVER | PVP",22)
        guild=SimpleNamespace(categories=[original_pve,old_pvp],roles=[])
        async def create_role(**kwargs):
            new=SimpleNamespace(name=kwargs["name"],colour=kwargs["colour"])
            guild.roles.append(new)
            return new
        guild.create_role=create_role
        env=functions("hmb_role","prepare_hmb_guild",
                      extras={"logging":SimpleNamespace(warning=lambda *a:None)})
        asyncio.run(env["prepare_hmb_guild"](guild))
        self.assertEqual(original_pve.name,"⚔️ WOW FOREVER | PVE")
        self.assertEqual(original_pve.edits,[])
        self.assertEqual(old_pvp.name,"🍺 HOLD MY BEER | PVP")
        self.assertEqual(old_pvp.id,22)
        self.assertEqual(len(guild.roles),1)
        self.assertEqual(guild.roles[0].name,"🍺 Hold My Beer")
        asyncio.run(env["prepare_hmb_guild"](guild))
        self.assertEqual(len(old_pvp.edits),1)
        self.assertEqual(len(guild.roles),1)

    def test_hmb_panel_is_separate_from_corpsegrinder_panels(self):
        self.assertIn("background(publish_hmb_hq(guild))",CODE)
        self.assertIn('target = channel(guild, "pvp-gruppensuche")',CODE)
        self.assertIn("HMB_PANEL_MARKER",CODE)
        self.assertIn('name="hmb_einsatzzentrale"',CODE)
        self.assertNotIn("🍺 HOLD MY BEER",FEATURES)
        env=functions("hmb_hq_embed",
                      extras={"channel":lambda guild,name:SimpleNamespace(
                          mention="#"+name)})
        embed=env["hmb_hq_embed"](SimpleNamespace())
        self.assertEqual(embed.colour.value,0xD9A441)
        self.assertIn("HOLD MY BEER",embed.title)
        self.assertIn("Signalfeuer",embed.fields[1].name)
        self.assertEqual(embed.footer.text,"hmb:headquarters:v138")
        self.assertTrue(embed.image.url.endswith("/assets/hold_my_beer.png"))
        self.assertNotIn("@everyone",str(embed.to_dict()))

    def test_dm_optin_defaults_to_off_and_is_guild_scoped(self):
        db=sqlite3.connect(":memory:")
        db.execute("CREATE TABLE hmb_alert_preferences("
                   "guild INTEGER,user INTEGER,enabled INTEGER,"
                   "PRIMARY KEY(guild,user))")
        env=functions("hmb_notifications_on",extras={"db":db})
        self.assertFalse(env["hmb_notifications_on"](7))
        db.execute("INSERT INTO hmb_alert_preferences VALUES(123,7,1)")
        self.assertTrue(env["hmb_notifications_on"](7))
        db.execute("INSERT INTO hmb_alert_preferences VALUES(999,8,1)")
        self.assertFalse(env["hmb_notifications_on"](8))
        db.close()

    def test_persistent_buttons_and_safe_expiring_signal(self):
        env=functions("HMBHQView","HMBBeaconView")
        async def render():
            panel=env["HMBHQView"]()
            beacon=env["HMBBeaconView"](54)
            return panel,beacon
        panel,beacon=asyncio.run(render())
        self.assertIsNone(panel.timeout)
        self.assertIsNone(beacon.timeout)
        names={x.custom_id for x in panel.children}
        self.assertEqual(len(names),4)
        self.assertIn("hmb_role_toggle_v138",names)
        self.assertIn("hmb_signal_new_v138",names)
        self.assertIn("hmb_dm_toggle_v138",names)
        self.assertEqual({x.custom_id for x in beacon.children},{
            "hmb_signal_join_v138_54","hmb_signal_done_v138_54"})
        self.assertIn("message.author.id == bot.user.id",CODE)
        self.assertIn("embed.footer.text or",CODE)
        self.assertIn("HMB_BEACON_TTL",CODE)
        self.assertIn("background(hmb_dm_signals(",CODE)


if __name__=="__main__":
    unittest.main()
