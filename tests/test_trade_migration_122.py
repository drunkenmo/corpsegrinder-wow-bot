"""Offline tests for safe channel migration and the Horde marketplace (1.0.22)."""
import ast
import asyncio
import sqlite3
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(BOT)


def constant(name):
    for node in TREE.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(name)


class FakeChannel:
    def __init__(self, name, identity):
        self.name, self.id = name, identity
        self.messages, self.permissions = ["old message"], {"mods": "custom"}
        self.renamed = 0
    async def edit(self, *, name, reason):
        self.name = name
        self.renamed += 1


class FakeGuild:
    def __init__(self, channels):
        self.channels = self.text_channels = channels


def get(collection, *, name):
    return next((entry for entry in collection if entry.name == name), None)


class FakeEmbed:
    def __init__(self, *, title, description, colour):
        self.title, self.description, self.colour = title, description, colour
        self.fields, self.footer = [], ""
    def add_field(self, *, name, value, inline):
        self.fields.append((name, value, inline))
    def set_footer(self, *, text):
        self.footer = text


def load(*names, **extra):
    nodes = [node for node in TREE.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
             and node.name in names]
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    fake_discord = SimpleNamespace(
        utils=SimpleNamespace(
            get=get,
            escape_markdown=lambda s:s.replace("*", "\\*")),
        HTTPException=OSError,
        Colour=SimpleNamespace(
            dark_grey=lambda: 1, from_rgb=lambda *_: 2, gold=lambda: 3),
        Embed=FakeEmbed)
    namespace = {
        "discord": fake_discord, "logging": SimpleNamespace(
            warning=lambda *a, **k:None, exception=lambda *a, **k:None),
        "CHANNEL_RENAMES": constant("CHANNEL_RENAMES"),
        "TRADE_ICONS": constant("TRADE_ICONS"),
        "TRADE_MARKER": constant("TRADE_MARKER"),
        "GUILD_ID": 12345,
    }
    namespace.update(extra)
    exec(compile(module, "bot.py", "exec"), namespace)
    return namespace


class ChannelMigrationTests(unittest.TestCase):
    def test_rename_preserves_channel_ids_and_old_posts(self):
        objects = [FakeChannel("allgemein", 111),
                   FakeChannel("dungeons", 222)]
        guild = FakeGuild(objects)
        m = load("channel", "migrate_channel_names")
        result = asyncio.run(m["migrate_channel_names"](guild))
        self.assertEqual(objects[0].name, "lagerfeuer")
        self.assertEqual(objects[1].name, "dungeon-planer")
        self.assertEqual([obj.id for obj in objects], [111, 222])
        self.assertEqual(objects[0].messages, ["old message"])
        self.assertEqual(objects[1].permissions, {"mods": "custom"})
        self.assertEqual(len(result), 2)
        self.assertEqual(
            asyncio.run(m["migrate_channel_names"](guild)), [])
        self.assertEqual(m["channel"](guild, "dungeons").id, 222)

    def test_no_duplicate_when_both_names_exist(self):
        objects = [FakeChannel("allgemein", 111),
                   FakeChannel("lagerfeuer", 444)]
        m = load("channel", "migrate_channel_names")
        result = asyncio.run(m["migrate_channel_names"](FakeGuild(objects)))
        self.assertEqual(result, [])
        self.assertEqual(objects[0].name, "allgemein")
        self.assertEqual(objects[0].renamed, 0)

    def test_all_references_use_new_channel_names(self):
        structure = constant("STRUCTURE")
        self.assertIn(("lagerfeuer", "text"), structure[
            "🌋 WOW FOREVER | START"])
        self.assertIn(("dungeon-planer", "text"), structure[
            "⚔️ WOW FOREVER | PVE"])
        self.assertIn('channel(member.guild,"lagerfeuer")', BOT)
        self.assertIn('channel(guild, "dungeon-planer")', BOT)
        self.assertIn('("lagerfeuer", "Am Lagerfeuer', FEATURES)
        self.assertIn('("dungeon-planer",', FEATURES)
        self.assertIn("await migrate_channel_names(guild)", BOT)


class MarketplaceTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("""
            CREATE TABLE trade_posts (
             id INTEGER PRIMARY KEY, guild INTEGER, owner INTEGER,
             kind TEXT, item TEXT, details TEXT, conditions TEXT,
             status TEXT, channel_id INTEGER, message_id INTEGER,
             created_utc INTEGER)
        """)
        self.e = load("trade_post", "trade_embed", "trade_dashboard_embed",
                      db=self.db)

    def test_trade_board_and_safely_escaped_user_input(self):
        self.db.execute(
            "INSERT INTO trade_posts VALUES (1,12345,21,'Handwerksauftrag',"
            "'*Arkanitbarren*','Brauche 3 Stück',"
            "'Materialien vorhanden','open',77,88,10)")
        self.db.commit()
        record = self.e["trade_post"](1)
        card = self.e["trade_embed"](record)
        self.assertIn(r"\*Arkanitbarren\*", card.title)
        self.assertIn("🟢 Offen", str(card.fields))
        board = self.e["trade_dashboard_embed"]()
        self.assertIn("Handelsplatz".casefold(), board.title.casefold())
        self.assertIn("discord.com/channels/12345/77/88", str(board.fields))

    def test_done_status_and_private_owner_control(self):
        self.db.execute(
            "INSERT INTO trade_posts VALUES (1,12345,21,'Suche',"
            "'Eisenbarren','Für Handwerk','10 Gold','done',77,88,10)")
        self.db.commit()
        card = self.e["trade_embed"](self.e["trade_post"](1))
        self.assertIn("✅ Erledigt", str(card.fields))
        self.assertIn("Nur Ersteller oder Administratoren", BOT)
        self.assertIn('trade_posts SET status=\'done\'', BOT)

    def test_persistent_buttons_and_limits(self):
        self.assertIn('bot.add_view(TradeDashboardView())', BOT)
        self.assertIn('bot.add_view(TradeEntryView(trade_id), message_id=post_id)', BOT)
        self.assertIn('view=TradeEntryView(trade_id)', BOT)
        self.assertIn('TRADE_ACTIVE_LIMIT = 6', BOT)
        self.assertIn('allowed_mentions=discord.AllowedMentions.none()', BOT)
        self.assertIn('name="handel_aktualisieren"', BOT)


if __name__ == "__main__":
    unittest.main()
