#!/usr/bin/env python3
"""Save a new verdict snapshot without overwriting; hashes detect, not prevent, edits."""
import argparse
import hashlib
import json
from pathlib import Path

FIELDS = 'request_id parent_run_id run_id source_snapshot_ids state reason scope recommendation criteria issues unresolved_conflict_ids unresolved_conflict_count agreement invariant_probe'.split()
ISOLATION_FIELDS = 'protocol_version status claim limitations plan controls'.split()


def snapshot(record):
    if not isinstance(record, dict) or record.get('contract_version') != 'dot-adversarial-result/1.1':
        raise ValueError('A result/1.1 record is required for a new verdict lock.')
    missing = [k for k in FIELDS + ['isolation'] if k not in record]
    if missing:
        raise ValueError('Missing verdict fields: ' + ', '.join(missing))
    isolation = record['isolation']
    if not isinstance(isolation, dict) or any(k not in isolation for k in ISOLATION_FIELDS):
        raise ValueError('Missing isolation basis for verdict.')
    packets = isolation.get('packets')
    if not isinstance(packets, list) or any(not isinstance(p, dict) for p in packets):
        raise ValueError('Packet manifest is required for a verdict lock.')
    original_manifest = sorted((p for p in packets if p.get('kind') == 'original'), key=lambda p: str(p.get('id')))
    return dict(format='dot-debate-locked-verdict/1.0', verdict={k: record[k] for k in FIELDS}, isolation_basis={k: isolation[k] for k in ISOLATION_FIELDS}, original_packet_manifest=original_manifest)


def canonical_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def create_lock(record, destination):
    destination = Path(destination)
    resolved = destination.resolve()
    package = Path(__file__).resolve().parents[1]
    if resolved == package or package in resolved.parents:
        raise ValueError('Run artifacts must be outside the installed skill.')
    if destination.is_symlink():
        raise ValueError('Do not write a verdict through a symbolic link.')
    data = canonical_bytes(snapshot(record))
    # Exclusive creation prevents accidental replacement, not subsequent edits.
    with destination.open('xb') as handle:
        handle.write(data)
        handle.flush()
        import os
        os.fsync(handle.fileno())
    actual = destination.read_bytes()
    if actual != data:
        raise ValueError('Verdict readback differs from written bytes.')
    return dict(artifact=str(resolved), digest=hashlib.sha256(actual).hexdigest(), bytes=len(actual), limitation='Exclusive creation and a saved digest are tamper-evidence, not enforced immutability or access control.')


def verify_lock(record, path):
    errors = []
    try:
        data = Path(path).read_bytes()
        saved = json.loads(data)
        declared = record.get('isolation', {}).get('verdict_lock') or {}
        if hashlib.sha256(data).hexdigest() != declared.get('digest'):
            errors.append('locked verdict digest does not match exact file bytes')
        if saved != snapshot(record):
            errors.append('result differs from locked verdict; preserve original and issue a separate addendum')
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        errors.append('locked verdict cannot be verified: ' + str(exc))
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record',type=Path);parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    try:
        result=create_lock(json.loads(args.record.read_text(encoding='utf-8')),args.destination)
    except (OSError,ValueError,TypeError) as exc:
        print(json.dumps(dict(saved=False,error=str(exc))));return 1
    print(json.dumps(dict(saved=True,**result),indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
