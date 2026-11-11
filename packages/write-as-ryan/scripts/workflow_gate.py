#!/usr/bin/env python3
"""Local preparation/final declaration gate; never a sender or consent verifier.

CLI:
  workflow_gate.py prepare --root SKILL --input task.json --context reads.json
  workflow_gate.py check --root SKILL --input task.json --context final-reads.json \
      --snapshot snapshot.json --receipt receipt.json --draft draft.txt

Redirect prepare stdout to a private snapshot file. Task JSON requires schema
personal-writing-input/1.0, nonempty request, channel, and scope (purpose,
account, recipient, thread). Additional task constraints are allowed and hashed.
Context JSON requires schema personal-writing-context/1.0, stage prepare/final,
input_sha256, matching channel/scope, latest_context_reviewed=true,
latest_context_evidence (nonempty string), and registered_profile containing
version, sha256, evidence (nonempty string). Those are caller declarations of
real current registered-resource/context reads, NOT proof that reads occurred.
The declared registered profile must match the locally observed active profile.
For an unreadable local guide only, check --exception-only omits --snapshot
and requires registered_profile {status: unavailable, evidence, limitation};
it checks the exact informed style exception and all other gates, never claiming
guide verification. It is not a bypass for a changed healthy profile.
--profile-version selects an older retained basis at preparation; final still
requires the existing checker's exact prior_validated_basis declaration.

Snapshots and receipts are unsigned caller-controlled data. A caller can forge
consent, evidence, and snapshots. This helper detects ordinary stale/inconsistent
files, not malicious writers; a pass is not authorization, semantic truth,
remote freshness, installed routing, or permission to create a native draft.
Any changes after check require a fresh check. No atomic transport interlock.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import check_receipt

WORKFLOW_VERSION = '1.2.0'
CHANNELS = {'email', 'slack-dm', 'slack-channel', 'clickup-dm',
            'clickup-channel', 'text', 'document'}
NOTICE = ('Private local consistency/declaration checks only. Context freshness, '
          'registered-resource reads, scope, rubric judgments, retained basis and '
          'user consent are unverified caller declarations. Local files do not '
          'prove current registered resources. No transport or authorization '
          'guarantee; no native draft or send performed.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def read_json(path):
    raw = Path(path).read_bytes()
    return raw, check_receipt.strict_load(raw.decode('utf-8'))


def scope_of(value):
    require(isinstance(value, dict), 'scope must be object')
    require(set(value) == {'purpose', 'account', 'recipient', 'thread'},
            'scope must contain exactly purpose/account/recipient/thread')
    require(all(nonempty(v) for v in value.values()), 'scope strings required')
    return value


def read_task(path):
    raw, task = read_json(path)
    require(isinstance(task, dict) and task.get('schema') == 'personal-writing-input/1.0',
            'invalid task input schema')
    require(nonempty(task.get('request')), 'task request required')
    require(task.get('channel') in CHANNELS, 'invalid task channel')
    scope_of(task.get('scope'))
    return raw, task


def read_profiles(root, selected=None):
    root = Path(root)
    manifest_raw, manifest = read_json(root / 'assets/profile-manifest.json')
    require(isinstance(manifest, dict) and manifest.get('schema') == 'personal-writing-manifest/1.0',
            'invalid manifest schema')
    active = manifest.get('active_version')
    require(isinstance(active, str) and re.fullmatch(r'\d+\.\d+\.\d+', active),
            'invalid manifest version')
    resource = 'profile-v' + active + '.json'
    require(manifest.get('resource') == resource, 'invalid manifest resource')
    active_raw, active_profile = read_json(root / 'assets' / resource)
    check_receipt.validate_profile(active_profile, active)
    require(manifest.get('sha256') == sha(active_raw), 'active manifest digest mismatch')
    selected = active if selected is None else selected
    require(isinstance(selected, str) and re.fullmatch(r'\d+\.\d+\.\d+', selected),
            'invalid selected version')
    if selected == active:
        raw, profile = active_raw, active_profile
    else:
        raw, profile = read_json(root / 'assets' / ('profile-v' + selected + '.json'))
        check_receipt.validate_profile(profile, selected)
    return {
        'manifest_sha256': sha(manifest_raw),
        'active_profile_version': active,
        'active_profile_sha256': sha(active_raw),
        'profile_version': selected,
        'profile_sha256': sha(raw),
    }, profile


def validate_context(path, task, input_hash, observed, stage):
    raw, ctx = read_json(path)
    require(isinstance(ctx, dict) and ctx.get('schema') == 'personal-writing-context/1.0',
            'invalid context schema')
    require(ctx.get('stage') == stage, 'context declaration stage mismatch')
    require(ctx.get('input_sha256') == input_hash, 'context input mismatch')
    require(ctx.get('channel') == task['channel'] and ctx.get('scope') == task['scope'],
            'context scope/channel mismatch')
    require(ctx.get('latest_context_reviewed') is True and nonempty(ctx.get('latest_context_evidence')),
            'current context review declaration required')
    rp = ctx.get('registered_profile')
    require(isinstance(rp, dict) and nonempty(rp.get('evidence')),
            'registered profile read declaration required')
    if observed is None:
        require(rp.get('status') == 'unavailable' and nonempty(rp.get('limitation')),
                'explicit unavailable registered profile declaration required')
        return sha(raw)
    require(rp.get('version') == observed['active_profile_version'] and
            rp.get('sha256') == observed['active_profile_sha256'],
            'registered profile declaration/local profile mismatch')
    return sha(raw)


def prepare(root, input_path, context_path, profile_version=None):
    raw, task = read_task(input_path)
    observed, _ = read_profiles(root, profile_version)
    context_hash = validate_context(context_path, task, sha(raw), observed, 'prepare')
    return {'schema': 'personal-writing-snapshot/1.0', 'workflow_version': WORKFLOW_VERSION,
            'decision': 'prepared-local-context',
            'evidence_class': 'observed-local-bytes-plus-unverified-context-declarations',
            'input_sha256': sha(raw), 'channel': task['channel'], 'scope': task['scope'],
            'observed': observed, 'preparation_context_sha256': context_hash,
            'notice': NOTICE}


def check(root, input_path, context_path, snapshot_path, receipt_path, draft_path):
    errors = []
    summary = {'schema': 'personal-writing-workflow-result/1.0',
               'workflow_version': WORKFLOW_VERSION,
               'evidence_class': 'observed-local-bytes-plus-unverified-declarations',
               'local_checks_pass': False, 'errors': errors, 'notice': NOTICE}
    try:
        raw, task = read_task(input_path)
        snapshot_raw, snapshot = read_json(snapshot_path)
        require(isinstance(snapshot, dict) and snapshot.get('schema') == 'personal-writing-snapshot/1.0',
                'invalid snapshot schema')
        require(snapshot.get('input_sha256') == sha(raw), 'task input changed since preparation')
        require(snapshot.get('channel') == task['channel'] and snapshot.get('scope') == task['scope'],
                'snapshot scope/channel mismatch')
        require(isinstance(snapshot.get('preparation_context_sha256'), str) and
                re.fullmatch(r'[0-9a-f]{64}', snapshot['preparation_context_sha256']),
                'invalid preparation context digest')
        old = snapshot.get('observed')
        require(isinstance(old, dict) and nonempty(old.get('profile_version')), 'missing profile snapshot')
        observed, _ = read_profiles(root, old['profile_version'])
        summary.update(observed)
        require(old == observed, 'manifest/profile changed since preparation; prepare again')
        context_hash = validate_context(context_path, task, sha(raw), observed, 'final')
        receipt_raw, receipt = read_json(receipt_path)
        require(isinstance(receipt, dict), 'receipt must be object')
        require(receipt.get('channel') == task['channel'] and receipt.get('scope') == task['scope'],
                'receipt scope/channel mismatch')
        require(receipt.get('profile_read_verified') is True, 'profile read cannot be waived')
        require(receipt.get('profile_version') == observed['profile_version'] and
                receipt.get('profile_sha256') == observed['profile_sha256'], 'receipt profile mismatch')
        draft = Path(draft_path).read_bytes()
        result = check_receipt.assess(receipt, draft, root=root, input_bytes=raw)
        errors.extend(result['errors'])
        # Detect ordinary concurrent file changes during assessment; no atomicity claim.
        after, _ = read_profiles(root, old['profile_version'])
        require(after == observed, 'manifest/profile changed during check')
        require(Path(input_path).read_bytes() == raw, 'input changed during check')
        require(Path(draft_path).read_bytes() == draft, 'draft changed during check')
        require(Path(receipt_path).read_bytes() == receipt_raw, 'receipt changed during check')
        require(Path(snapshot_path).read_bytes() == snapshot_raw, 'snapshot changed during check')
        require(sha(Path(context_path).read_bytes()) == context_hash, 'context changed during check')
        summary.update(input_sha256=sha(raw), draft_sha256=sha(draft),
                       receipt_sha256=sha(receipt_raw), snapshot_sha256=sha(snapshot_raw),
                       final_context_sha256=context_hash, input_binding_verified=result['input_binding_verified'],
                       hard_gates_checked=len(check_receipt.HARD),
                       style_dimensions_checked=len(check_receipt.STYLE))
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        errors.append(str(exc))
    summary['local_checks_pass'] = not errors
    summary['decision'] = ('hold' if errors else 'declarations-consistent-not-send-authority')
    return summary


def check_exception(root, input_path, context_path, receipt_path, draft_path):
    """Explicit unavailable-guide route, not a stale-snapshot escape hatch."""
    errors = []
    summary = {'schema': 'personal-writing-workflow-result/1.0',
               'workflow_version': WORKFLOW_VERSION,
               'evidence_class': 'observed-local-guide-failure-plus-unverified-exception-declarations',
               'local_checks_pass': False, 'exception_only': True,
               'profile_read_verified': False, 'errors': errors, 'notice': NOTICE}
    try:
        raw, task = read_task(input_path)
        try:
            read_profiles(root)
        except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
            summary['observed_profile_error'] = str(exc)
        else:
            raise ValueError('healthy local guide requires normal preparation/check')
        context_hash = validate_context(context_path, task, sha(raw), None, 'final')
        receipt_raw, receipt = read_json(receipt_path)
        require(isinstance(receipt, dict), 'receipt must be object')
        require(receipt.get('channel') == task['channel'] and receipt.get('scope') == task['scope'],
                'receipt scope/channel mismatch')
        require(receipt.get('profile_read_verified') is False,
                'exception route must explicitly declare profile unreadable')
        draft = Path(draft_path).read_bytes()
        result = check_receipt.assess(receipt, draft, root=root, input_bytes=raw)
        errors.extend(result['errors'])
        require(Path(input_path).read_bytes() == raw, 'input changed during check')
        require(Path(draft_path).read_bytes() == draft, 'draft changed during check')
        require(Path(receipt_path).read_bytes() == receipt_raw, 'receipt changed during check')
        require(sha(Path(context_path).read_bytes()) == context_hash, 'context changed during check')
        summary.update(input_sha256=sha(raw), draft_sha256=sha(draft),
                       receipt_sha256=sha(receipt_raw), final_context_sha256=context_hash,
                       input_binding_verified=result['input_binding_verified'],
                       hard_gates_checked=len(check_receipt.HARD),
                       style_dimensions_checked=len(check_receipt.STYLE))
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        errors.append(str(exc))
    summary['local_checks_pass'] = not errors
    summary['decision'] = ('hold' if errors else 'exception-declarations-consistent-guide-unverified')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'check'):
        p = sub.add_parser(name)
        p.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
        p.add_argument('--input', required=True)
        p.add_argument('--context', required=True)
        if name == 'prepare':
            p.add_argument('--profile-version')
        else:
            p.add_argument('--snapshot')
            p.add_argument('--exception-only', action='store_true')
            for key in ('receipt', 'draft'):
                p.add_argument('--' + key, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            result = prepare(args.root, args.input, args.context, args.profile_version)
            ok = True
        else:
            if args.exception_only:
                require(args.snapshot is None, 'exception-only must not reuse a snapshot')
                result = check_exception(args.root, args.input, args.context, args.receipt, args.draft)
            else:
                require(args.snapshot is not None, '--snapshot required for normal check')
                result = check(args.root, args.input, args.context, args.snapshot, args.receipt, args.draft)
            ok = result['local_checks_pass']
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        result = {'workflow_version': WORKFLOW_VERSION, 'decision': 'hold',
                  'local_checks_pass': False, 'errors': [str(exc)], 'notice': NOTICE}
        ok = False
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
