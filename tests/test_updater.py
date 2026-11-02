"""Offline tests: no Discord token, no Home Assistant, no network."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from corpsegrinder_wow_bot import updater_core as updater


class UpdaterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = (
            updater.ROOT, updater.RELEASES, updater.ACTIVE, updater.LAST_GOOD,
            updater.request_bytes,
        )
        updater.ROOT = Path(self.temp.name) / "bot_updates"
        updater.RELEASES = updater.ROOT / "releases"
        updater.ACTIVE = updater.ROOT / "active.json"
        updater.LAST_GOOD = updater.ROOT / "last_good.json"
        self.bot_bytes = b'print("new bot")\n'
        self.features_bytes = b'VERSION="1.0.7"\n'
        self.manifest = {
            "version": "1.0.7",
            "commit": "a" * 40,
            "min_bootstrap": "1.0.6",
            "files": {
                "bot.py": hashlib.sha256(self.bot_bytes).hexdigest(),
                "community_features.py": hashlib.sha256(self.features_bytes).hexdigest(),
            },
        }
        updater.request_bytes = lambda url, max_size=updater.MAX_DOWNLOAD: (
            self.bot_bytes if url.endswith("/bot.py") else self.features_bytes
        )

    def tearDown(self):
        (updater.ROOT, updater.RELEASES, updater.ACTIVE,
         updater.LAST_GOOD, updater.request_bytes) = self.previous
        self.temp.cleanup()

    def test_install_preserves_persistent_data(self):
        data = updater.ROOT.parent / "corpsegrinder.sqlite"
        data.write_bytes(b"test database")
        self.assertEqual(updater.installed(), "1.0.6")
        self.assertEqual(updater.install_update(self.manifest), "1.0.7")
        self.assertEqual(updater.installed(), "1.0.7")
        self.assertEqual(data.read_bytes(), b"test database")
        self.assertEqual(
            (updater.release_dir("1.0.7") / "bot.py").read_bytes(),
            self.bot_bytes,
        )

    def test_tampered_file_rejected(self):
        self.manifest["files"]["bot.py"] = "0" * 64
        with self.assertRaises(updater.UpdateError):
            updater.install_update(self.manifest)
        self.assertEqual(updater.installed(), "1.0.6")

    def test_path_traversal_rejected(self):
        self.manifest["files"]["../../evil.py"] = "0" * 64
        with self.assertRaises(updater.UpdateError):
            updater.validate_manifest(self.manifest)

    def test_downgrade_rejected(self):
        self.manifest["version"] = "1.0.5"
        with self.assertRaises(updater.UpdateError):
            updater.install_update(self.manifest)

    def test_rollback_to_builtin(self):
        updater.install_update(self.manifest)
        self.assertEqual(updater.rollback("test"), "1.0.6")
        self.assertEqual(updater.installed(), "1.0.6")

    def test_minimum_bootstrap_enforced(self):
        self.manifest["min_bootstrap"] = "1.1.0"
        with self.assertRaises(updater.UpdateError):
            updater.validate_manifest(self.manifest)


if __name__ == "__main__":
    unittest.main()
