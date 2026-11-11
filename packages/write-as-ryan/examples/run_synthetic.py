#!/usr/bin/env python3
"""Offline, fictional declaration example. No real reads, consent or send.

Creates temporary fixtures, invokes both unmodified helper CLIs, demonstrates
one successful fictional send-gate declaration and one draft-drift hold, then
removes the temporary files. Do not use these declarations for a real task.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
DRAFT = b"The sample tray contains 6 square tiles.\n"
HARD = ('identity', 'channel', 'authorization', 'meaning', 'privacy',
        'exact_strings', 'current_context')
STYLE_REASONS = {
    'opening_closing': 'Fictional inventory line needs no salutation or sign-off.',
    'directness': 'The fixture states only the supplied inventory fact.',
    'request_framing': 'The fictional request asks for a statement, not an action.',
    'rhythm': 'One complete sentence is sufficient for this artificial case.',
    'length': 'The fixture contains exactly the requested single statement.',
    'structure': 'A single line matches the fictional task.',
    'vocabulary_contractions': 'The requested count and shape are preserved.',
    'warmth_humor': 'No emotion, joke or relationship is invented.',
    'punctuation': 'The fixture sentence has its original final period.',
    'recipient_context_fit': 'Only a fictional inventory reviewer is modeled.',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')


def create_case(directory):
    """Populate an empty private temporary directory with ONLY fictional data."""
    base = Path(directory)
    root = base / 'fixture-root'
    state = base / 'fixture-state'
    shutil.copytree(PACKAGE / 'examples' / 'synthetic' / 'assets', root / 'assets')
    (root / 'scripts').mkdir()
    for name in ('workflow_gate.py', 'check_receipt.py'):
        shutil.copyfile(PACKAGE / 'scripts' / name, root / 'scripts' / name)
    state.mkdir()
    paths = {'root': root, **{name: state / filename for name, filename in {
        'input': 'task.json', 'prepare_context': 'prepare-reads.json',
        'final_context': 'final-reads.json', 'snapshot': 'snapshot.json',
        'receipt': 'receipt.json', 'draft': 'draft.txt',
    }.items()}}
    task = {
        'schema': 'personal-writing-input/1.0', 'synthetic': True,
        'request': 'Fictional offline test only. Preserve this exact inventory '
                   'line: The sample tray contains 6 square tiles. Do not send it.',
        'channel': 'document',
        'scope': {'purpose': 'synthetic declaration test',
                  'account': 'fictional fixture account',
                  'recipient': 'fictional inventory reviewer',
                  'thread': 'not-applicable: fictional new document'},
        'notice': 'No real authority. The send-authorized receipt is a simulated '
                  'test branch, not permission to perform any external effect.',
    }
    write_json(paths['input'], task)
    profile_bytes = (root / 'assets' / 'profile-v0.0.0.json').read_bytes()
    for stage, key in (('prepare', 'prepare_context'), ('final', 'final_context')):
        ctx = {
            'schema': 'personal-writing-context/1.0', 'stage': stage,
            'input_sha256': digest(paths['input'].read_bytes()),
            'channel': task['channel'], 'scope': task['scope'],
            'latest_context_reviewed': True,
            'latest_context_evidence': 'SYNTHETIC declaration for this offline '
                                       'fixture, not a real source review.',
            'registered_profile': {
                'version': '0.0.0', 'sha256': digest(profile_bytes),
                'evidence': 'SYNTHETIC registered-read declaration only; no '
                            'registered resource was actually read.',
            },
        }
        write_json(paths[key], ctx)
    receipt = json.loads((PACKAGE / 'assets' / 'receipt-template.json').read_text())
    receipt.update({
        'profile_version': '0.0.0', 'profile_read_verified': True,
        'profile_sha256': digest(profile_bytes), 'draft_sha256': digest(DRAFT),
        'channel': task['channel'], 'recipient_verified': True,
        'scope': task['scope'],
        'read_evidence': ['SYNTHETIC fixture declaration, not real read evidence.'],
        'hard_gates': {key: 'pass' for key in HARD},
        'style_dimensions': {key: {'status': 'matches', 'reason': reason}
                             for key, reason in STYLE_REASONS.items()},
        'mode': 'send-authorized', 'send_eligible': True,
        'limitations': ['All gates and read/consent claims are fictional test '
                       'declarations; not valid for any real task or send.'],
        'input_sha256': digest(paths['input'].read_bytes()),
        'loaded_rule_ids': ['SYN-CORE-1', 'SYN-OBS-1'],
        'synthetic': True,
    })
    write_json(paths['receipt'], receipt)
    paths['draft'].write_bytes(DRAFT)
    return paths


def invoke(script, *args):
    result = subprocess.run([sys.executable, '-B', str(script), *map(str, args)],
                            capture_output=True, text=True, check=False)
    return result.returncode, json.loads(result.stdout)


def main():
    with tempfile.TemporaryDirectory(prefix='synthetic-writing-') as directory:
        p = create_case(directory)
        gate = p['root'] / 'scripts' / 'workflow_gate.py'
        checker = p['root'] / 'scripts' / 'check_receipt.py'
        code, snapshot = invoke(gate, 'prepare', '--root', p['root'], '--input',
                                p['input'], '--context', p['prepare_context'])
        if code or snapshot.get('decision') != 'prepared-local-context':
            raise RuntimeError('Synthetic preparation failed: ' + str(snapshot))
        write_json(p['snapshot'], snapshot)
        check_args = ('check', '--root', p['root'], '--input', p['input'],
                      '--context', p['final_context'], '--snapshot', p['snapshot'],
                      '--receipt', p['receipt'], '--draft', p['draft'])
        code, normal = invoke(gate, *check_args)
        if code or not normal.get('local_checks_pass'):
            raise RuntimeError('Synthetic workflow failed: ' + str(normal))
        code, receipt_result = invoke(checker, p['receipt'], p['draft'],
                                      '--input', p['input'])
        if code or not receipt_result.get('input_binding_verified'):
            raise RuntimeError('Synthetic receipt check failed: ' + str(receipt_result))
        p['draft'].write_bytes(DRAFT + b'Extra fictional text.\n')
        code, changed = invoke(gate, *check_args)
        if code != 1 or changed.get('decision') != 'hold' or \
                'draft digest mismatch' not in changed.get('errors', []):
            raise RuntimeError('Changed draft was not held: ' + str(changed))
        print('PASS: fictional preparation, workflow check and receipt CLI.')
        print('PASS: changed draft held. Temporary artifacts removed on exit.')
        print('Synthetic declarations only; no actual consent, native reads or send.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
