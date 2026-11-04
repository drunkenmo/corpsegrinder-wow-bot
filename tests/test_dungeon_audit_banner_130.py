"""1.0.30: missing dungeon cards and banner safety regression tests.

Tests inspect and execute only the audited function bodies. No Discord
connection, bot token or Home Assistant instance is required.
"""
import ast
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def get_async(name, env):
    node = next(x for x in TREE.body
                if isinstance(x, ast.AsyncFunctionDef) and x.name == name)
    obj = ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[]))
    exec(compile(obj, "bot.py", "exec"), env)
    return env[name]


class NotFound(Exception):
    pass


class Forbidden(Exception):
    pass


class HTTPException(Exception):
    pass


class ClientException(Exception):
    pass


class FakeTextChannel:
    def __init__(self, mode):
        self.mode = mode

    async def fetch_message(self, message_id):
        if self.mode == "missing":
            raise NotFound()
        if self.mode == "forbidden":
            raise Forbidden()
        return SimpleNamespace(author=SimpleNamespace(id=77))


class DungeonAuditTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE planned_groups "
            "(id INTEGER, guild INTEGER, instance TEXT, "
            "start_utc INTEGER, channel INTEGER, message INTEGER, status TEXT)")
        self.db.execute(
            "CREATE TABLE event_meta "
            "(kind TEXT, group_id INTEGER, archived_at INTEGER)")
        now = int(datetime.now(timezone.utc).timestamp())
        self.db.executemany(
            "INSERT INTO planned_groups VALUES (?,42,?,?,?,?,'open')",
            [(1, "Flammenschlund", now + 7200, 10, 100),
             (2, "Düsterbruch", now + 7200, 20, 200),
             (3, "Höhlen des Wehklagens", now + 7200, 30, 300),
             (4, "Ohne Nachricht", now + 7200, 40, None)])
        self.db.executemany(
            "INSERT INTO event_meta VALUES ('dungeon', ?, NULL)",
            [(1,), (2,), (3,), (4,)])
        self.db.commit()
        self.channels = {
            10: FakeTextChannel("valid"),
            20: FakeTextChannel("missing"),
            30: FakeTextChannel("forbidden"),
            40: FakeTextChannel("valid"),
        }
        self.guild = SimpleNamespace(
            get_channel=lambda channel_id: self.channels.get(channel_id))
        self.calls = []
        async def fetch_channel(channel_id):
            raise NotFound()
        self.env = {
            "db": self.db,
            "GUILD_ID": 42,
            "datetime": datetime,
            "timezone": timezone,
            "bot": SimpleNamespace(user=SimpleNamespace(id=77),
                                   fetch_channel=fetch_channel),
            "discord": SimpleNamespace(NotFound=NotFound, Forbidden=Forbidden,
                                       HTTPException=HTTPException,
                                       ClientException=ClientException,
                                       TextChannel=FakeTextChannel),
            "logging": SimpleNamespace(info=lambda *args: None),
        }
        self.audit = get_async("audit_dungeon_cards", self.env)

    def tearDown(self):
        self.db.close()

    def test_read_only_finds_missing_but_keeps_data(self):
        report = asyncio.run(self.audit(self.guild, repair=False))
        self.assertEqual(report["checked"], 4)
        self.assertEqual(report["valid"], 1)
        self.assertEqual(report["missing"], [2])
        self.assertEqual(report["unverifiable"], [3])
        self.assertEqual(report["unlinked"], [4])
        self.assertEqual(report["repaired"], [])
        self.assertEqual(
            self.db.execute("SELECT status FROM planned_groups WHERE id=2")
                   .fetchone()[0], "open")

    def test_repair_archives_only_confirmed_not_found(self):
        report = asyncio.run(self.audit(self.guild, repair=True))
        self.assertEqual(report["repaired"], [2])
        statuses = self.db.execute(
            "SELECT id,status FROM planned_groups ORDER BY id").fetchall()
        self.assertEqual(statuses,
                         [(1, "open"), (2, "archived"),
                          (3, "open"), (4, "open")])
        self.assertIsNotNone(
            self.db.execute("SELECT archived_at FROM event_meta "
                            "WHERE group_id=2").fetchone()[0])
        self.assertEqual(asyncio.run(self.audit(self.guild, repair=True))
                         ["repaired"], [])

    def test_raw_delete_listener_hides_card_instantly(self):
        calls = []
        async def refresh(kind):
            calls.append(kind)
        env = dict(self.env)
        env["refresh_event_dashboard"] = refresh
        raw_delete = get_async("on_raw_message_delete", env)
        payload = SimpleNamespace(guild_id=42, channel_id=10,
                                  message_id=100)
        asyncio.run(raw_delete(payload))
        self.assertEqual(
            self.db.execute("SELECT status FROM planned_groups WHERE id=1")
                   .fetchone()[0], "archived")
        self.assertEqual(calls, ["dungeon"])

    def test_invalid_guild_does_nothing(self):
        calls = []
        async def refresh(kind):
            calls.append(kind)
        env = dict(self.env)
        env["refresh_event_dashboard"] = refresh
        raw_delete = get_async("on_raw_message_delete", env)
        asyncio.run(raw_delete(SimpleNamespace(
            guild_id=999, channel_id=10, message_id=100)))
        self.assertEqual(calls, [])
        self.assertEqual(self.db.execute(
            "SELECT status FROM planned_groups WHERE id=1").fetchone()[0],
            "open")


class BannerTests(unittest.TestCase):
    def test_old_dungeon_banner_is_gone(self):
        block = SOURCE[
            SOURCE.index("def planner_dashboard_embed():"):
            SOURCE.index("def wizard_state(", SOURCE.index(
                "def planner_dashboard_embed():"))]
        self.assertNotIn("embed.set_image(url=DUNGEON_ART_URL)", block)

    def test_new_banner_is_put_in_both_existing_cards(self):
        start = SOURCE.index('name="willkommensbanner_setzen"')
        end = SOURCE.index("async def publish_info(", start)
        section = SOURCE[start:end]
        self.assertIn("await existing.edit(", section)
        self.assertIn("await ensure_planner_dashboard(interaction.guild)",
                      section)
        self.assertIn("await planner_post.edit(", section)
        self.assertEqual(
            section.count('filename="corpsegrinder_banner.png"'), 2)

    def test_dungeon_persists_banner_on_restart(self):
        block = SOURCE[SOURCE.index("async def ensure_planner_dashboard(guild):"):
                       SOURCE.index("async def ensure_planner_dashboard_on_start():")]
        self.assertIn('attachment.filename == "corpsegrinder_banner.png"',
                      block)
        self.assertIn('attachments=existing.attachments', block)
        self.assertIn('url="attachment://corpsegrinder_banner.png"', block)

    def test_startup_and_admin_lookups(self):
        self.assertIn("await audit_dungeon_cards(guild, repair=True)", SOURCE)
        self.assertIn('name="dungeon_pruefen"', SOURCE)
        self.assertIn("bereinigen: bool = False", SOURCE)
        self.assertIn('VERSION = "1.0.30"', FEATURES)


if __name__ == "__main__":
    unittest.main()
