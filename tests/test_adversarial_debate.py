"""Include the shipped skill's synthetic record checks in repository CI."""
import importlib.util
from pathlib import Path
import unittest


def load_tests(loader, tests, pattern):
    path = Path(__file__).resolve().parents[1] / 'packages/adversarial-debate/tests/test_validate_record.py'
    spec = importlib.util.spec_from_file_location('adversarial_record_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return loader.loadTestsFromModule(module)
