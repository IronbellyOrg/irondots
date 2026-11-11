import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'validate_record.py'
spec = importlib.util.spec_from_file_location('validator', SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def record():
    return dict(contract_version='dot-adversarial-result/1.0', request_id='q1', parent_run_id=None, run_id='r1', source_snapshot_ids=['s1', 's2'], state='complete', stage='finalized', reason=None, scope={}, recommendation=dict(selected_ids=['A'], rationale='Supported by supplied evidence.', conditions=[], alternatives=[]), criteria=[dict(id='cost', candidate_id='A', critical=True, verdict='met', evidence=['s1'], rationale='Within cap.')], issues=[dict(id='C1', type='difference', severity='low', classification='source-claim', resolution='agreed', source_locations=['s1'])], unresolved_conflict_ids=[], unresolved_conflict_count=0, agreement=dict(numerator=1, denominator=1, included_issue_ids=['C1'], excluded_issue_ids=[], agreed_issue_ids=['C1'], ratio=1.0, limitations=['Alignment, not correctness.']), invariant_probe=dict(state='not_required', reviewer_provenance=None, coverage=[], finding_ids=[], reason='Synthetic quick fixture.'), artifacts=[], execution={}, effects=[], reporting=None, reporting_gap=dict(resource='reporting-protocol-v1.md', expected_version='dot-reporting/1.0', access_state='unavailable', reason='Synthetic fixture has no resource reader.', next_action='Resolve authoritative resource.'), next_action=None)


class ValidationTests(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(validator.validate(record()), [])

    def invalid(self, change):
        r = record()
        change(r)
        self.assertTrue(validator.validate(r))

    def test_missing_field(self): self.invalid(lambda r: r.pop('execution'))
    def test_unknown_version(self): self.invalid(lambda r: r.update(contract_version='2'))
    def test_missing_partial_reason(self): self.invalid(lambda r: r.update(state='partial'))
    def test_count_mismatch(self): self.invalid(lambda r: r.update(unresolved_conflict_count=1))
    def test_boolean_count(self): self.invalid(lambda r: r.update(unresolved_conflict_count=False))
    def test_duplicate_ids(self): self.invalid(lambda r: r['agreement'].update(included_issue_ids=['C1', 'C1']))
    def test_unknown_issue(self): self.invalid(lambda r: r.update(unresolved_conflict_ids=['C2'], unresolved_conflict_count=1))
    def test_agreement_overlap(self): self.invalid(lambda r: r['agreement'].update(excluded_issue_ids=['C1']))
    def test_non_subset_agreement(self): self.invalid(lambda r: r['agreement'].update(agreed_issue_ids=['C2']))
    def test_bad_ratio(self): self.invalid(lambda r: r['agreement'].update(ratio=.9))
    def test_huge_ratio(self): self.invalid(lambda r: r['agreement'].update(ratio=10**400))
    def test_nan_ratio(self): self.invalid(lambda r: r['agreement'].update(ratio=float('nan')))
    def test_zero_denominator_null(self):
        r = record(); r['agreement'].update(included_issue_ids=[], agreed_issue_ids=[], numerator=0, denominator=0, ratio=None)
        self.assertEqual(validator.validate(r), [])
    def test_zero_denominator_number(self): self.invalid(lambda r: r['agreement'].update(included_issue_ids=[], agreed_issue_ids=[], numerator=0, denominator=0, ratio=1))
    def test_missing_candidate_id(self): self.invalid(lambda r: r['criteria'][0].pop('candidate_id'))
    def test_explicit_global_candidate_id(self):
        r = record(); r['criteria'][0]['candidate_id'] = None
        self.assertEqual(validator.validate(r), [])
    def test_critical_unknown(self): self.invalid(lambda r: r['criteria'][0].update(verdict='unknown'))
    def test_other_candidate_unknown_allowed(self):
        r = record(); r['criteria'].append(dict(r['criteria'][0], candidate_id='B', verdict='unknown'))
        self.assertEqual(validator.validate(r), [])
    def test_conditional_unknown(self):
        r = record(); r['criteria'][0]['verdict']='unknown'; r['recommendation']['conditions']=['Verify cost before adoption.']
        self.assertEqual(validator.validate(r), [])
    def test_probe_provenance(self): self.invalid(lambda r: r['invariant_probe'].update(state='performed'))
    def test_incomplete_probe(self): self.invalid(lambda r: r['invariant_probe'].update(state='blocked'))
    def test_reporting_gap_missing(self): self.invalid(lambda r: r.update(reporting_gap=None))
    def test_reporting_conflicting(self): self.invalid(lambda r: r.update(reporting='https://example.org/receipt'))
    def test_false_verified_effect(self): self.invalid(lambda r: r['effects'].append(dict(id='e1', requested=True, reported='ok', observed=None, state='verified', evidence=[])))
    def test_malformed_shapes_no_crash(self):
        r = record()
        for key in r:
            for malformed in (None, {}, [], True, 0, ""):
                bad = copy.deepcopy(r); bad[key] = malformed
                validator.validate(bad)
    def test_cli_success_and_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'r.json'; p.write_text(json.dumps(record()))
            good=subprocess.run([sys.executable, '-B', str(SCRIPT), str(p)], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stdout)
            p.write_text('{bad json')
            bad=subprocess.run([sys.executable, '-B', str(SCRIPT), str(p)], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)


if __name__ == '__main__': unittest.main()
