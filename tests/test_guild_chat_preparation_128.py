"""Safe PvE and PvP guild-chat preparation for WoW Forever."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class GuildChatChannelTests(unittest.TestCase):
    def test_separate_guild_chats_are_in_correct_sections(self):
        structure = next(node for node in TREE.body
                         if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name)
                                 and target.id == "STRUCTURE"
                                 for target in node.targets))
        data = ast.literal_eval(structure.value)
        self.assertIn(("pve-gildenchat", "text"), data["⚔️ WOW FOREVER | PVE"])
        self.assertIn(("pvp-gildenchat", "text"), data["🏹 WOW FOREVER | PVP"])
        self.assertNotIn(("wow-gildenchat", "text"), data["🌋 WOW FOREVER | START"])
        self.assertEqual(sum(ch == "pve-gildenchat" for items in data.values()
                             for ch, typ in items), 1)
        self.assertEqual(sum(ch == "pvp-gildenchat" for items in data.values()
                             for ch, typ in items), 1)

    def test_creation_is_independent_idempotent_and_not_a_bridge(self):
        fragment = SOURCE[
            SOURCE.index("async def ensure_wow_guild_chat_channel(guild, area):"):
            SOURCE.index("async def ensure_guild_chat_channel_on_start():")]
        for text in ('"pve": ("pve-gildenchat", "⚔️ WOW FOREVER | PVE")',
                     '"pvp": ("pvp-gildenchat", "🏹 WOW FOREVER | PVP")',
                     "if existing is not None:", "return existing",
                     "category.create_text_channel(", "await organize_start_channels(guild)"):
            self.assertIn(text, fragment)
        for forbidden in ("create_webhook", "on_message", "send_messages", "bot.send"):
            self.assertNotIn(forbidden, fragment)

    def test_startup_prepares_both_and_version_is_correct(self):
        self.assertIn('for area in ("pve", "pvp"):', SOURCE)
        self.assertIn("background(ensure_guild_chat_channel_on_start())", SOURCE)
        # Versions must not be frozen to the release that introduced this feature.
        version = next(line.split('"')[1] for line in FEATURES.splitlines()
                       if line.startswith("VERSION = ")).split(".")
        self.assertGreaterEqual(tuple(map(int, version)), (1, 0, 28))
        self.assertIn("#pve-gildenchat", FEATURES)
        self.assertIn("#pvp-gildenchat", FEATURES)


if __name__ == "__main__":
    unittest.main()
