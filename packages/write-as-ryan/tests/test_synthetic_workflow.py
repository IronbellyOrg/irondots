"""Fictional offline normal/negative checks; no real profile or provider calls."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
import check_receipt
import workflow_gate

spec = importlib.util.spec_from_file_location(
    'synthetic_writing_example', PACKAGE / 'examples' / 'run_synthetic.py')
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


class SyntheticWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic-writing-test-')
        self.addCleanup(self.temp.cleanup)
        self.p = example.create_case(self.temp.name)
        self.prepare()

    def read(self, key):
        return json.loads(self.p[key].read_text(encoding='utf-8'))

    def write(self, key, value):
        example.write_json(self.p[key], value)

    def prepare(self, selected=None):
        snapshot = workflow_gate.prepare(self.p['root'], self.p['input'],
                                         self.p['prepare_context'], selected)
        self.write('snapshot', snapshot)
        return snapshot

    def check(self):
        return workflow_gate.check(self.p['root'], self.p['input'],
                                   self.p['final_context'], self.p['snapshot'],
                                   self.p['receipt'], self.p['draft'])

    def assess(self, receipt=None, draft=None, include_input=True):
        return check_receipt.assess(
            self.read('receipt') if receipt is None else receipt,
            self.p['draft'].read_bytes() if draft is None else draft,
            root=self.p['root'],
            input_bytes=self.p['input'].read_bytes() if include_input else None)

    def hold(self, text):
        result = self.check()
        self.assertFalse(result['local_checks_pass'])
        self.assertEqual(result['decision'], 'hold')
        self.assertIn(text, '\n'.join(result['errors']))
        return result

    def waiver(self, receipt):
        receipt['style_exception'] = {
            'explicit': True, 'draft_sha256': example.digest(example.DRAFT),
            'limitation_disclosed': True,
            'evidence': 'SYNTHETIC explicit agreement, not real user consent.',
            'limitation': 'SYNTHETIC disclosed style limitation for exact fixture.',
        }
        return receipt

    def missing_guide_exception(self):
        (self.p['root'] / 'assets' / 'profile-manifest.json').unlink()
        context = self.read('final_context')
        context['registered_profile'] = {
            'status': 'unavailable',
            'evidence': 'SYNTHETIC unavailable registered-read declaration.',
            'limitation': 'Fictional guide deliberately removed by offline test.',
        }
        self.write('final_context', context)
        receipt = self.waiver(self.read('receipt'))
        receipt['profile_read_verified'] = False
        receipt['profile_version'] = None
        receipt['profile_sha256'] = None
        receipt['loaded_rule_ids'] = []
        self.write('receipt', receipt)

    def exception_check(self):
        return workflow_gate.check_exception(
            self.p['root'], self.p['input'], self.p['final_context'],
            self.p['receipt'], self.p['draft'])

    def newer_synthetic_profile(self):
        assets = self.p['root'] / 'assets'
        profile = json.loads((assets / 'profile-v0.0.0.json').read_text())
        profile['version'] = '0.0.1'
        new_file = assets / 'profile-v0.0.1.json'
        example.write_json(new_file, profile)
        manifest = json.loads((assets / 'profile-manifest.json').read_text())
        manifest.update(active_version='0.0.1', resource=new_file.name,
                        sha256=example.digest(new_file.read_bytes()))
        example.write_json(assets / 'profile-manifest.json', manifest)
        for key in ('prepare_context', 'final_context'):
            context = self.read(key)
            context['registered_profile'].update(version='0.0.1', sha256=manifest['sha256'])
            self.write(key, context)

    def test_normal_workflow_and_underlying_receipt(self):
        result = self.check()
        self.assertTrue(result['local_checks_pass'], result)
        self.assertTrue(result['input_binding_verified'])
        self.assertEqual(result['hard_gates_checked'], 7)
        self.assertEqual(result['style_dimensions_checked'], 10)
        self.assertEqual(result['decision'], 'declarations-consistent-not-send-authority')
        self.assertTrue(self.assess()['declared_send_gates_pass'])

    def test_both_helper_clis_with_real_fixture_bytes(self):
        gate = self.p['root'] / 'scripts' / 'workflow_gate.py'
        checker = self.p['root'] / 'scripts' / 'check_receipt.py'
        code, snap = example.invoke(gate, 'prepare', '--root', self.p['root'],
                                   '--input', self.p['input'], '--context', self.p['prepare_context'])
        self.assertEqual(code, 0, snap)
        self.write('snapshot', snap)
        code, result = example.invoke(gate, 'check', '--root', self.p['root'],
                                      '--input', self.p['input'], '--context', self.p['final_context'],
                                      '--snapshot', self.p['snapshot'], '--receipt', self.p['receipt'],
                                      '--draft', self.p['draft'])
        self.assertEqual(code, 0, result)
        code, result = example.invoke(checker, self.p['receipt'], self.p['draft'],
                                      '--input', self.p['input'])
        self.assertEqual(code, 0, result)
        self.assertTrue(result['input_binding_verified'])

    def test_unconfigured_public_root_has_no_active_profile(self):
        self.assertFalse((PACKAGE / 'assets' / 'profile-manifest.json').exists())
        with self.assertRaises(FileNotFoundError):
            workflow_gate.prepare(PACKAGE, self.p['input'], self.p['prepare_context'])

    def test_synthetic_profile_is_explicitly_not_personal(self):
        _, profile = workflow_gate.read_profiles(self.p['root'])
        self.assertFalse(profile['human_style_validated'])
        self.assertIn('synthetic-test-only', profile['status'])
        self.assertEqual(profile['recipient_overrides'], [])
        self.assertEqual(profile['purpose_overlays'], {})

    def test_each_changed_draft_byte_requires_revalidation(self):
        for draft in (example.DRAFT + b'Signature\n', example.DRAFT[:-1],
                      example.DRAFT.replace(b'6', b'7')):
            with self.subTest(draft=draft):
                self.p['draft'].write_bytes(draft)
                self.hold('draft digest mismatch')

    def test_changed_task_bytes_hold_even_if_json_semantics_match(self):
        self.p['input'].write_bytes(self.p['input'].read_bytes() + b'\n')
        self.hold('task input changed since preparation')

    def test_final_context_scope_channel_stage_and_hash_hold(self):
        original = self.read('final_context')
        changes = [('stage', 'prepare', 'stage mismatch'),
                   ('input_sha256', '0' * 64, 'context input mismatch'),
                   ('channel', 'email', 'scope/channel mismatch'),
                   ('scope', {**original['scope'], 'recipient': 'other fictional reader'},
                    'scope/channel mismatch'),
                   ('latest_context_reviewed', False, 'current context review declaration required'),
                   ('latest_context_evidence', '', 'current context review declaration required')]
        for key, value, error in changes:
            with self.subTest(key=key):
                context = copy.deepcopy(original)
                context[key] = value
                self.write('final_context', context)
                self.hold(error)

    def test_registered_profile_declaration_mismatch_holds(self):
        original = self.read('final_context')
        for key, value, error in (
            ('sha256', '0' * 64, 'registered profile declaration/local profile mismatch'),
            ('version', '9.9.9', 'registered profile declaration/local profile mismatch'),
            ('evidence', '', 'registered profile read declaration required')):
            with self.subTest(key=key):
                context = copy.deepcopy(original)
                context['registered_profile'][key] = value
                self.write('final_context', context)
                self.hold(error)

    def test_receipt_scope_and_channel_mismatch_hold(self):
        original = self.read('receipt')
        for key, value in (('channel', 'email'), ('scope', {
                **original['scope'], 'account': 'different fictional account'})):
            with self.subTest(key=key):
                receipt = copy.deepcopy(original)
                receipt[key] = value
                self.write('receipt', receipt)
                self.hold('receipt scope/channel mismatch')

    def test_receipt_input_profile_and_draft_hash_binding(self):
        original = self.read('receipt')
        for field, error in (('input_sha256', 'input digest mismatch'),
                             ('profile_sha256', 'receipt profile mismatch'),
                             ('draft_sha256', 'draft digest mismatch')):
            with self.subTest(field=field):
                receipt = copy.deepcopy(original)
                receipt[field] = '0' * 64
                self.write('receipt', receipt)
                self.hold(error)

    def test_manifest_changed_after_prepare_holds(self):
        manifest_file = self.p['root'] / 'assets' / 'profile-manifest.json'
        manifest_file.write_bytes(manifest_file.read_bytes() + b'\n')
        self.hold('manifest/profile changed since preparation')

    def test_profile_digest_corruption_holds(self):
        profile_file = self.p['root'] / 'assets' / 'profile-v0.0.0.json'
        profile_file.write_bytes(profile_file.read_bytes() + b'\n')
        self.hold('active manifest digest mismatch')

    def test_valid_new_profile_requires_new_preparation(self):
        self.newer_synthetic_profile()
        self.hold('manifest/profile changed since preparation')

    def test_missing_profile_is_not_silently_replaced(self):
        (self.p['root'] / 'assets' / 'profile-v0.0.0.json').unlink()
        self.hold('profile-v0.0.0.json')

    def test_json_duplicate_keys_and_nonfinite_numbers_hold(self):
        for body, error in ((b'{"schema":"x","schema":"y"}', 'duplicate JSON key'),
                            (b'{"value":NaN}', 'nonfinite JSON'),
                            (b'{"value":Infinity}', 'nonfinite JSON'),
                            (b'{', 'Expecting property name')):
            with self.subTest(body=body):
                self.p['receipt'].write_bytes(body)
                self.hold(error)

    def test_all_hard_gates_fail_closed_even_with_style_exception(self):
        for gate in check_receipt.HARD:
            for state in ('unknown', 'fail'):
                with self.subTest(gate=gate, state=state):
                    receipt = self.waiver(self.read('receipt'))
                    receipt['hard_gates'][gate] = state
                    result = self.assess(receipt)
                    self.assertFalse(result['declared_send_gates_pass'])
                    self.assertIn('hard gate: ' + gate, result['errors'])

    def test_missing_hard_gate_and_missing_rubric_dimension_hold(self):
        for gate in check_receipt.HARD:
            with self.subTest(gate=gate):
                receipt = self.read('receipt')
                del receipt['hard_gates'][gate]
                self.assertIn('hard gate: ' + gate, self.assess(receipt)['errors'])
        for dimension in check_receipt.STYLE:
            with self.subTest(dimension=dimension):
                receipt = self.read('receipt')
                del receipt['style_dimensions'][dimension]
                self.assertIn('style dimension incomplete: ' + dimension,
                              self.assess(receipt)['errors'])

    def test_ten_rubric_dimensions_require_reasons(self):
        for dimension in check_receipt.STYLE:
            with self.subTest(dimension=dimension):
                receipt = self.read('receipt')
                receipt['style_dimensions'][dimension]['reason'] = ''
                self.assertIn('style dimension incomplete: ' + dimension,
                              self.assess(receipt)['errors'])

    def test_limited_style_dimension_requires_disclosure(self):
        receipt = self.read('receipt')
        receipt['style_dimensions']['length']['status'] = 'acceptable-with-limitation'
        self.assertTrue(self.assess(receipt)['declared_send_gates_pass'])
        receipt['limitations'] = []
        self.assertIn('limited dimension needs recorded limitation: length',
                      self.assess(receipt)['errors'])

    def test_real_booleans_required_not_strings_or_numbers(self):
        for field in ('profile_read_verified', 'recipient_verified',
                      'material_style_mismatch', 'send_eligible'):
            for value in ('true', 1, None):
                with self.subTest(field=field, value=value):
                    receipt = self.read('receipt')
                    receipt[field] = value
                    self.assertIn('boolean required: ' + field, self.assess(receipt)['errors'])

    def test_false_recipient_or_eligibility_holds(self):
        for field, error in (('recipient_verified', 'recipient not verified'),
                             ('send_eligible', 'declared send_eligible is not true')):
            with self.subTest(field=field):
                receipt = self.read('receipt')
                receipt[field] = False
                self.assertIn(error, self.assess(receipt)['errors'])

    def test_draft_only_remains_send_ineligible(self):
        receipt = self.read('receipt')
        receipt.update(mode='draft-only', send_eligible=False)
        result = self.assess(receipt)
        self.assertIn('not a send-authorized route', result['errors'])
        self.assertIn('declared send_eligible is not true', result['errors'])

    def test_unknown_and_empty_rule_ids_hold(self):
        for ids in ([], ['SYN-NOT-A-RULE']):
            with self.subTest(ids=ids):
                receipt = self.read('receipt')
                receipt['loaded_rule_ids'] = ids
                self.assertIn('profile validation: loaded rules missing or unknown',
                              self.assess(receipt)['errors'])

    def test_style_mismatch_needs_exact_informed_exception(self):
        receipt = self.read('receipt')
        receipt['style_dimensions']['length']['status'] = 'mismatch'
        self.assertIn('unresolved style mismatch', self.assess(receipt)['errors'])
        receipt = self.waiver(receipt)
        self.assertTrue(self.assess(receipt)['declared_send_gates_pass'])
        for field, value in (('explicit', False), ('limitation_disclosed', False),
                             ('draft_sha256', '0' * 64), ('evidence', ''), ('limitation', '')):
            with self.subTest(field=field):
                invalid = copy.deepcopy(receipt)
                invalid['style_exception'][field] = value
                self.assertIn('unresolved style mismatch', self.assess(invalid)['errors'])

    def test_material_mismatch_flag_alone_holds(self):
        receipt = self.read('receipt')
        receipt['material_style_mismatch'] = True
        self.assertIn('unresolved style mismatch', self.assess(receipt)['errors'])

    def test_missing_profile_read_cannot_use_normal_route(self):
        receipt = self.waiver(self.read('receipt'))
        receipt['profile_read_verified'] = False
        self.write('receipt', receipt)
        self.hold('profile read cannot be waived')

    def test_exception_only_rejects_healthy_guide(self):
        result = self.exception_check()
        self.assertFalse(result['local_checks_pass'])
        self.assertIn('healthy local guide requires normal preparation/check', result['errors'])

    def test_exception_only_with_actual_guide_failure_is_labeled_unverified(self):
        self.missing_guide_exception()
        result = self.exception_check()
        self.assertTrue(result['local_checks_pass'], result)
        self.assertFalse(result['profile_read_verified'])
        self.assertEqual(result['decision'], 'exception-declarations-consistent-guide-unverified')

    def test_exception_only_requires_unavailable_read_evidence(self):
        self.missing_guide_exception()
        context = self.read('final_context')
        del context['registered_profile']['limitation']
        self.write('final_context', context)
        result = self.exception_check()
        self.assertFalse(result['local_checks_pass'])
        self.assertIn('explicit unavailable registered profile declaration required', result['errors'])

    def test_exception_only_cannot_waive_authorization_or_changed_text(self):
        self.missing_guide_exception()
        receipt = self.read('receipt')
        receipt['hard_gates']['authorization'] = 'unknown'
        self.write('receipt', receipt)
        result = self.exception_check()
        self.assertIn('hard gate: authorization', result['errors'])
        receipt['hard_gates']['authorization'] = 'pass'
        self.write('receipt', receipt)
        self.p['draft'].write_bytes(example.DRAFT + b'Altered.\n')
        result = self.exception_check()
        self.assertIn('draft digest mismatch', result['errors'])
        self.assertIn('profile unavailable without exact informed exception', result['errors'])

    def test_retained_basis_requires_exact_old_draft_and_receipt(self):
        self.newer_synthetic_profile()
        self.prepare(selected='0.0.0')
        self.hold('older version needs exact prior validated basis')
        receipt = self.read('receipt')
        receipt['prior_validated_basis'] = {
            'draft_sha256': receipt['draft_sha256'],
            'profile_sha256': receipt['profile_sha256'],
            'profile_version': receipt['profile_version'],
            'latest_context_reviewed': True,
            'receipt_id': 'synthetic-prior-receipt-not-a-private-identifier',
        }
        self.write('receipt', receipt)
        self.assertTrue(self.check()['local_checks_pass'])
        receipt['prior_validated_basis']['draft_sha256'] = '0' * 64
        self.write('receipt', receipt)
        self.hold('older version needs exact prior validated basis')

    def test_supported_channels_and_exact_scope_keys(self):
        original = self.read('input')
        for channel in sorted(workflow_gate.CHANNELS):
            with self.subTest(channel=channel):
                task = copy.deepcopy(original)
                task['channel'] = channel
                self.write('input', task)
                _, loaded = workflow_gate.read_task(self.p['input'])
                self.assertEqual(loaded['channel'], channel)
        invalid = copy.deepcopy(original)
        invalid['channel'] = 'unsupported-provider'
        self.write('input', invalid)
        with self.assertRaisesRegex(ValueError, 'invalid task channel'):
            workflow_gate.read_task(self.p['input'])
        invalid = copy.deepcopy(original)
        invalid['scope']['extra'] = 'unexpected'
        self.write('input', invalid)
        with self.assertRaisesRegex(ValueError, 'scope must contain exactly'):
            workflow_gate.read_task(self.p['input'])

    def test_invalid_utf8_draft_holds_even_with_matching_hash(self):
        receipt = self.read('receipt')
        draft = b'\xff'
        receipt['draft_sha256'] = example.digest(draft)
        self.assertIn('draft must be UTF-8', self.assess(receipt, draft)['errors'])

    def test_standalone_without_input_does_not_claim_binding(self):
        result = self.assess(include_input=False)
        self.assertTrue(result['declared_send_gates_pass'])
        self.assertFalse(result['input_binding_verified'])

    def test_concurrent_draft_change_detected(self):
        original = check_receipt.assess

        def change_draft(*args, **kwargs):
            result = original(*args, **kwargs)
            self.p['draft'].write_bytes(example.DRAFT + b'Late change.\n')
            return result

        with patch.object(check_receipt, 'assess', side_effect=change_draft):
            self.hold('draft changed during check')

    def test_profile_schema_and_manifest_path_fail_closed(self):
        assets = self.p['root'] / 'assets'
        manifest_file = assets / 'profile-manifest.json'
        manifest = json.loads(manifest_file.read_text())
        manifest['resource'] = '../other.json'
        example.write_json(manifest_file, manifest)
        self.hold('invalid manifest resource')
        manifest['resource'] = 'profile-v0.0.0.json'
        profile_file = assets / manifest['resource']
        profile = json.loads(profile_file.read_text())
        profile['human_style_validated'] = 'false'
        example.write_json(profile_file, profile)
        manifest['sha256'] = example.digest(profile_file.read_bytes())
        example.write_json(manifest_file, manifest)
        self.hold('invalid profile validation flag')

    def test_receipt_template_holds_without_fabricated_completion(self):
        receipt = json.loads((PACKAGE / 'assets' / 'receipt-template.json').read_text())
        self.assertFalse(self.assess(receipt)['declared_send_gates_pass'])

    def test_negative_cli_returns_failure_exit_and_hold(self):
        self.p['draft'].write_bytes(example.DRAFT + b'Changed.\n')
        code, result = example.invoke(self.p['root'] / 'scripts' / 'workflow_gate.py',
                                      'check', '--root', self.p['root'], '--input', self.p['input'],
                                      '--context', self.p['final_context'], '--snapshot', self.p['snapshot'],
                                      '--receipt', self.p['receipt'], '--draft', self.p['draft'])
        self.assertEqual(code, 1)
        self.assertEqual(result['decision'], 'hold')
        code, result = example.invoke(self.p['root'] / 'scripts' / 'check_receipt.py',
                                      self.p['receipt'], self.p['draft'], '--input', self.p['input'])
        self.assertEqual(code, 1)
        self.assertFalse(result['declared_send_gates_pass'])


if __name__ == '__main__':
    unittest.main()
