"""1.0.31: staged banner upload and precise Discord error reporting."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOT = (ROOT / "corpsegrinder_wow_bot" / "bot.py").read_text(encoding="utf-8")
FEATURES = (ROOT / "corpsegrinder_wow_bot" / "community_features.py").read_text(encoding="utf-8")
TREE = ast.parse(BOT)


class BannerErrorDiagnosticsTests(unittest.TestCase):
    def test_command_upload_before_embeds(self):
        start = BOT.index("async def set_welcome_banner_command(")
        end = BOT.index("async def publish_info(", start)
        command = BOT[start:end]
        self.assertLess(command.index("uploaded = await existing.edit("),
                        command.index("await uploaded.edit("))
        self.assertLess(command.index("dungeon_upload = await planner_post.edit("),
                        command.index("await dungeon_upload.edit("))
        self.assertIn('stage = "Bildanhang zur Willkommensnachricht hochladen"', command)
        self.assertIn('stage = "Bild in der Willkommenskarte anzeigen"', command)
        self.assertIn('stage = "Bildanhang zur Dungeon-Halle hochladen"', command)
        self.assertIn('stage = "Bild in der Dungeon-Halle anzeigen"', command)

    def test_error_includes_http_status_code_stage_not_generic_guess(self):
        block = BOT[BOT.index("async def set_welcome_banner_command("):
                    BOT.index("async def publish_info(")]
        self.assertIn("str(exc.status)", block)
        self.assertIn('getattr(exc, "code", "?")', block)
        self.assertIn('"**Schritt:** " + stage', block)
        self.assertIn('"**Fehler:** " + status', block)
        self.assertNotIn("Bitte Bot-Rechte und Dateiformat prüfen.", block)
        self.assertIn("dungeon_note", block)

    def test_upload_keeps_true_image_extension(self):
        block = BOT[BOT.index("async def set_welcome_banner_command("):
                    BOT.index("async def publish_info(")]
        for extension in (".png", ".jpg", ".webp"):
            self.assertIn(extension, block)
        self.assertIn('filename = "corpsegrinder_banner" + extension', block)
        self.assertIn('a.filename.startswith("corpsegrinder_banner.")', block)
        self.assertEqual(block.count("discord.File(io.BytesIO(data), filename=filename)"), 2)

    def test_existing_panels_still_preserve_image_by_filename(self):
        welcome = BOT[BOT.index("async def publish_info("):
                      BOT.index("@bot.tree.command(", BOT.index("async def publish_info("))]
        planner = BOT[BOT.index("async def ensure_planner_dashboard(guild):"):
                      BOT.index("async def ensure_planner_dashboard_on_start():")]
        self.assertIn('a.filename.startswith("corpsegrinder_banner.")', welcome)
        self.assertIn('attachment.filename.startswith("corpsegrinder_banner.")', planner)
        self.assertIn('embed.set_image(url="attachment://" + banner.filename)', welcome)
        self.assertIn('refreshed.set_image(url="attachment://" + artwork.filename)', planner)
        self.assertGreaterEqual(
            tuple(int(p) for p in next(line.split('"')[1]
                for line in FEATURES.splitlines()
                if line.startswith("VERSION = ")).split(".")),
            (1, 0, 31))


if __name__ == "__main__":
    unittest.main()
