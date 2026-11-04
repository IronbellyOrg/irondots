"""Offline synthetic fixtures for structure checks, not live skill evaluations."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from validate_registry import InvalidRegistry, validate
from package_release import build


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.data = {"schema_version": 1, "packages": []}
        self.save()

    def save(self):
        (self.root / "registry.json").write_text(json.dumps(self.data))

    def package(self, name="example"):
        path = self.root / "packages" / name
        path.mkdir(parents=True)
        contents = {"SKILL.md": "# Example\nSee [reference](reference.md).\n", "reference.md": "# Reference\nSynthetic fixture only.\n", "LICENSE.txt": "Synthetic test fixture; not a production license.\n"}
        for filename, text in contents.items():
            (path / filename).write_text(text)
        p = {"id": name, "version": "0.1.0", "path": f"packages/{name}", "entrypoint": "SKILL.md", "runtimes": ["dot"], "dependencies": [], "provenance": {"source": "https://example.com/source", "license": "test-only", "license_file": "LICENSE.txt"}, "public_files": {f: hashlib.sha256(t.encode()).hexdigest() for f, t in contents.items()}, "publication_approved": True}
        self.data["packages"].append(p)
        self.save()
        return p

    def expect_invalid(self):
        self.save()
        with self.assertRaises((InvalidRegistry, OSError)):
            validate(self.root)

    def test_empty_registry_valid(self):
        self.assertEqual(validate(self.root)["packages"], [])

    def test_valid_package(self):
        self.package()
        self.assertEqual(len(validate(self.root)["packages"]), 1)

    def test_unknown_schema(self):
        self.data["schema_version"] = 2
        self.expect_invalid()

    def test_boolean_schema_not_integer(self):
        self.data["schema_version"] = True
        self.expect_invalid()

    def test_unknown_fields(self):
        self.data["unexpected"] = True
        self.expect_invalid()

    def test_duplicate_json_key(self):
        (self.root / "registry.json").write_text('{"schema_version":1,"schema_version":1,"packages":[]}')
        with self.assertRaises(InvalidRegistry):
            validate(self.root)

    def test_bad_digest(self):
        p = self.package()
        p["public_files"]["SKILL.md"] = "0" * 64
        self.expect_invalid()

    def test_missing_file(self):
        self.package()
        (self.root / "packages/example/reference.md").unlink()
        self.expect_invalid()

    def test_path_traversal(self):
        p = self.package()
        p["public_files"]["../private.txt"] = "0" * 64
        self.expect_invalid()

    def test_symlink(self):
        self.package()
        p = self.root / "packages/example/reference.md"
        p.unlink()
        p.symlink_to(self.root / "registry.json")
        self.expect_invalid()

    def test_parent_symlink(self):
        self.package()
        package_dir = self.root / "packages"
        package_dir.rename(self.root / "actual")
        package_dir.symlink_to(self.root / "actual", target_is_directory=True)
        self.expect_invalid()

    def test_unlisted_file(self):
        self.package()
        (self.root / "packages/example/unlisted.txt").write_text("not allowed")
        self.expect_invalid()

    def test_hidden_file(self):
        self.package()
        (self.root / "packages/example/.env").write_text("synthetic")
        self.expect_invalid()

    def test_forbidden_directory(self):
        self.package()
        (self.root / "packages/example/receipts").mkdir()
        self.expect_invalid()

    def test_missing_dependency(self):
        p = self.package()
        p["dependencies"] = ["missing"]
        self.expect_invalid()

    def test_cycle(self):
        p = self.package()
        p["dependencies"] = ["example"]
        self.expect_invalid()

    def test_missing_license(self):
        p = self.package()
        p["provenance"]["license"] = ""
        self.expect_invalid()

    def test_missing_provenance(self):
        p = self.package()
        p["provenance"]["source"] = ""
        self.expect_invalid()

    def test_broken_link(self):
        p = self.package()
        content = "[broken](missing.md)"
        (self.root / "packages/example/SKILL.md").write_text(content)
        p["public_files"]["SKILL.md"] = hashlib.sha256(content.encode()).hexdigest()
        self.expect_invalid()

    def test_escaping_link(self):
        p = self.package()
        content = "[outside](../../registry.json)"
        (self.root / "packages/example/SKILL.md").write_text(content)
        p["public_files"]["SKILL.md"] = hashlib.sha256(content.encode()).hexdigest()
        self.expect_invalid()

    def test_unregistered_package(self):
        (self.root / "packages/orphan").mkdir(parents=True)
        self.expect_invalid()

    def test_release_empty_blocked(self):
        with self.assertRaises(InvalidRegistry):
            build(self.root, Path(self.temp.name)/"out", "0.1.0", "a"*40)

    def test_release_unapproved_blocked(self):
        p = self.package()
        p["publication_approved"] = False
        self.save()
        with self.assertRaises(InvalidRegistry):
            build(self.root, Path(self.temp.name)/"out", "0.1.0", "a"*40)

    def test_release_deterministic_and_allowlisted(self):
        self.package()
        (self.root / "unrelated-private.txt").write_text("must not be packaged")
        first = build(self.root, Path(self.temp.name)/"one", "0.1.0", "a"*40)
        second = build(self.root, Path(self.temp.name)/"two", "0.1.0", "a"*40)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as z:
            self.assertEqual(set(z.namelist()), {"registry.json", "release-manifest.json", "packages/example/SKILL.md", "packages/example/reference.md", "packages/example/LICENSE.txt"})
            manifest = json.loads(z.read("release-manifest.json"))
            self.assertEqual(manifest["runtime_certification"], "not_performed")
            self.assertEqual(manifest["source_commit"], "a"*40)

    def test_release_output_in_checkout_blocked(self):
        self.package()
        with self.assertRaises(InvalidRegistry):
            build(self.root, self.root / "dist", "0.1.0", "a"*40)

    def test_release_cannot_overwrite(self):
        self.package()
        out = Path(self.temp.name)/"out"
        build(self.root, out, "0.1.0", "a"*40)
        with self.assertRaises(InvalidRegistry):
            build(self.root, out, "0.1.0", "a"*40)

if __name__ == "__main__":
    unittest.main()
