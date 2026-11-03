"""Offline formatting regressions; no live invocation claims."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from skill_prompt import render

class SkillPromptTests(unittest.TestCase):
    def test_01_literal_command_first(self):
        result = render('# Specification\nRead only.', command='/if:spec-feature', command_evidence='User confirmed command')
        self.assertEqual(result.splitlines()[0], '/if:spec-feature')
    def test_02_preserve_full_body(self):
        body = '# Scope\nSource: task123\nDo not publish.\nUnknown: due date.\nReturn evidence.\n'
        self.assertEqual(render(body, command='/if:spec-feature', command_evidence='User confirmation'), '/if:spec-feature\n\n' + body)
    def test_03_ordinary_batch_unchanged(self):
        body = 'Summarize task123; no writes.'
        self.assertEqual(render(body), body)
    def test_04_unknown_command_needs_evidence(self):
        with self.assertRaises(ValueError):
            render('Scope', command='/if:unverified')
    def test_05_historical_mention_is_not_invocation(self):
        body = 'The earlier prompt mentioned /if:spec-feature. Summarize its result.'
        self.assertEqual(render(body), body)
    def test_06_resume_cannot_duplicate(self):
        with self.assertRaises(ValueError):
            render('Scope', command='/if:spec-feature', command_evidence='User confirmation', resuming=True)
    def test_07_malformed_or_existing_prefix_rejected(self):
        for command in ['Use /if:spec-feature', ' /if:spec-feature', '/if:<skill>', '/if:spec-feature\nextra']:
            with self.assertRaises(ValueError): render('Scope', command=command, command_evidence='fixture')
        with self.assertRaises(ValueError):
            render('/if:spec-feature\nScope', command='/if:spec-feature', command_evidence='fixture')

    def test_08_input_boundary_coverage(self):
        for body in ['', '  ', None, 1]:
            with self.assertRaises(ValueError): render(body)
        with self.assertRaises(ValueError): render('Scope', command_evidence='orphan evidence')
        for evidence in ['', '  ', None, 1]:
            with self.assertRaises(ValueError): render('Scope', command='/if:spec-feature', command_evidence=evidence)
        with self.assertRaises(ValueError):
            render('  /if:spec-feature\nScope', command='/if:spec-feature', command_evidence='fixture')
        self.assertEqual(render('Scope', command='/if:verified-fixture', command_evidence='Synthetic offline fixture only'), '/if:verified-fixture\n\nScope')

if __name__ == '__main__': unittest.main()
