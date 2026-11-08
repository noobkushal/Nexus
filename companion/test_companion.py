"""Unit tests for NEXUS companion workspace policy."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import nexus_companion as companion


class WorkspacePolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.patch = patch.object(companion, "WORKSPACE", self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_resolves_relative_path(self):
        self.assertEqual(companion.resolve_workspace_path("src/main.py"), self.root / "src" / "main.py")

    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            companion.resolve_workspace_path("../outside.txt")

    def test_rejects_absolute_path(self):
        with self.assertRaises(ValueError):
            companion.resolve_workspace_path(str(self.root / "secret.txt"))

    def test_rejects_symlink_escape(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir(exist_ok=True)
        link = self.root / "escape"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink creation unavailable.")
        try:
            with self.assertRaises(ValueError):
                companion.resolve_workspace_path("escape/file.txt")
        finally:
            link.unlink(missing_ok=True)
            outside.rmdir()

    def test_blocks_environment_and_hidden_files(self):
        self.assertFalse(companion.is_allowed_file(self.root / ".env"))
        self.assertFalse(companion.is_allowed_file(self.root / "settings.env"))
        self.assertFalse(companion.is_allowed_file(self.root / ".private.py"))

    def test_allows_source_and_documentation(self):
        self.assertTrue(companion.is_allowed_file(self.root / "main.py"))
        self.assertTrue(companion.is_allowed_file(self.root / "README.md"))
        self.assertFalse(companion.is_allowed_file(self.root / "photo.png"))


if __name__ == "__main__":
    unittest.main()
