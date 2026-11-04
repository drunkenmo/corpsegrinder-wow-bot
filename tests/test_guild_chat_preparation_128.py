"""Safe channel preparation for WoW Forever's official guild chat sync."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


class GuildChatChannelTests(unittest.TestCase):
    def test_channel_exists_in_start_structure_once(self):
        structure = next(node for node in TREE.body
                         if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name)
                                 and target.id == "STRUCTURE"
                                 for target in node.targets))
        data = ast.literal_eval(structure.value)
        start = data["🌋 WOW FOREVER | START"]
        self.assertEqual(start.count(("wow-gildenchat", "text")), 1)
        self.assertLess(start.index(("lagerfeuer", "text")),
                        start.index(("wow-gildenchat", "text")))

    def test_creation_is_idempotent_and_no_bridge(self):
        fragment = SOURCE[SOURCE.index("async def ensure_wow_guild_chat_channel(guild):"):
                          SOURCE.index("async def ensure_guild_chat_channel_on_start():")]
        self.assertIn('existing = channel(guild, "wow-gildenchat")', fragment)
        self.assertIn("if existing is not None:", fragment)
        self.assertIn("return existing", fragment)
        self.assertIn("category.create_text_channel(", fragment)
        self.assertIn("await organize_start_channels(guild)", fragment)
        for forbidden in ("create_webhook", "on_message", "send_messages", "bot.send"):
            self.assertNotIn(forbidden, fragment)

    def test_startup_hook_and_version(self):
        self.assertIn("background(ensure_guild_chat_channel_on_start())", SOURCE)
        self.assertIn('VERSION = "1.0.28"', FEATURES)
        self.assertIn("Die tatsächliche WoW-Verknüpfung", FEATURES)


if __name__ == "__main__":
    unittest.main()
