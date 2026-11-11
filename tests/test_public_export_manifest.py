"""Public export identity and privacy regression checks, not a secret detector."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExportManifestTests(unittest.TestCase):
    def test_export_hashes(self):
        manifest = json.loads((ROOT / 'source-export-manifest.json').read_text())
        for package in manifest['packages']:
            for record in package['source_files'] + package.get('public_only_files', []):
                with self.subTest(package=package['id'], path=record['path']):
                    data = (ROOT / 'packages' / package['id'] / record['path']).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), record['export_sha256'])

    def test_generic_writing_has_no_active_profile(self):
        package = ROOT / 'packages/write-as-ryan'
        self.assertFalse((package / 'assets/profile-manifest.json').exists())
        self.assertFalse(list((package / 'assets').glob('profile-v*.json')))
        manifest = json.loads((ROOT / 'source-export-manifest.json').read_text())
        writing = next(p for p in manifest['packages'] if p['id'] == 'write-as-ryan')
        self.assertFalse(any('profile' in r['path'].lower() for r in writing['source_files']))
        self.assertIn('synthetic', (package / 'SKILL.md').read_text().lower())

    def test_refreshed_packages_have_no_private_bindings(self):
        for name in ['clickup', 'session-init', 'adversarial-debate', 'write-as-ryan']:
            for path in (ROOT / 'packages' / name).rglob('*'):
                if path.is_file():
                    with self.subTest(path=path.relative_to(ROOT)):
                        text = path.read_text()
                        self.assertNotIn('skill://user/', text)
                        self.assertNotRegex(text, r'/workspace/(?:scratch|shared)/')
                        self.assertNotRegex(text, r'https://app\.clickup\.com/(?:t|[0-9]+)/[A-Za-z0-9]')
                        self.assertNotRegex(text, r'\b(?:IronFlow|CEO)\b')


if __name__ == '__main__':
    unittest.main()
