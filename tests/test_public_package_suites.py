"""Run bundled offline package suites; none calls external providers."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicPackageSuites(unittest.TestCase):
    def test_offline_package_suites(self):
        for package, folder in [
            ('clickup', 'tests'),
            ('create-level-design', 'scripts'),
            ('task-list', 'tests'),
            ('adversarial-debate', 'tests'),
            ('write-as-ryan', 'tests'),
        ]:
            with self.subTest(package=package):
                result = subprocess.run(
                    [sys.executable, '-m', 'unittest', 'discover', '-s',
                     str(ROOT / 'packages' / package / folder), '-p', 'test_*.py'],
                    cwd=ROOT, text=True, capture_output=True,
                    env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=90,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('Ran 0 tests', result.stderr)


if __name__ == '__main__':
    unittest.main()
