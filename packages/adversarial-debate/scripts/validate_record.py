#!/usr/bin/env python3
"""Check selected dot-adversarial-result/1.0 invariants, not factual validity."""
import argparse
import json
import math
from pathlib import Path

REQUIRED = set('contract_version request_id parent_run_id run_id source_snapshot_ids state stage reason scope recommendation criteria issues unresolved_conflict_ids unresolved_conflict_count agreement invariant_probe artifacts execution effects reporting reporting_gap next_action'.split())
STATES = {'complete', 'partial', 'blocked', 'failed', 'cancelled'}
VERDICTS = {'met', 'not_met', 'unknown', 'not_applicable'}


def _validate(record):
    """Return errors; passing does not prove truth, authority or agent independence."""
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    def obj(value, label, keys=()):
        if not isinstance(value, dict):
            errors.append(label + ' must be an object')
            return {}
        for key in keys:
            check(key in value, label + ' missing ' + key)
        return value
    def seq(value, label):
        if not isinstance(value, list):
            errors.append(label + ' must be a list')
            return []
        return value
    def ids(value, label):
        values = seq(value, label)
        check(all(isinstance(x, str) and x.strip() for x in values), label + ' must contain nonempty strings')
        clean = [x for x in values if isinstance(x, str)]
        check(len(set(clean)) == len(clean), label + ' must be unique')
        return set(clean)
    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())
    if not isinstance(record, dict):
        return ['record must be an object']
    for key in sorted(REQUIRED - record.keys()):
        errors.append('missing ' + key)
    check(record.get('contract_version') == 'dot-adversarial-result/1.0', 'unsupported contract_version')
    for key in ('request_id', 'run_id', 'stage'):
        check(nonempty(record.get(key)), key + ' must be nonempty')
    check(record.get('parent_run_id') is None or nonempty(record.get('parent_run_id')), 'parent_run_id must be string or null')
    check(record.get('state') in STATES, 'invalid state')
    if record.get('state') != 'complete':
        check(nonempty(record.get('reason')), 'non-complete state needs reason')
    ids(record.get('source_snapshot_ids'), 'source_snapshot_ids')
    obj(record.get('scope'), 'scope')
    obj(record.get('execution'), 'execution')
    rec = obj(record.get('recommendation'), 'recommendation', ('selected_ids', 'rationale', 'conditions', 'alternatives'))
    selected = ids(rec['selected_ids'], 'recommendation.selected_ids') if rec.get('selected_ids') is not None else set()
    check(nonempty(rec.get('rationale')), 'recommendation needs rationale')
    seq(rec.get('conditions'), 'recommendation.conditions')
    seq(rec.get('alternatives'), 'recommendation.alternatives')
    criteria = seq(record.get('criteria'), 'criteria')
    criterion_keys = []
    for i, value in enumerate(criteria):
        c = obj(value, 'criteria[%d]' % i, ('id', 'candidate_id', 'critical', 'verdict', 'evidence', 'rationale'))
        check(nonempty(c.get('id')), 'criterion id must be nonempty')
        candidate = c.get('candidate_id')
        check(candidate is None or nonempty(candidate), 'candidate_id must be string or null')
        criterion_keys.append((c.get('id'), candidate))
        check(type(c.get('critical')) is bool, 'critical must be boolean')
        check(c.get('verdict') in VERDICTS, 'invalid criterion verdict')
        if selected and c.get('critical') is True and c.get('verdict') in {'not_met', 'unknown'} and (candidate is None or candidate in selected):
            check(bool(rec.get('conditions')), 'critical failure/unknown requires explicit recommendation conditions')
    # Candidate-specific rows may repeat a criterion ID, but not the same pair.
    check(len({str(k) for k in criterion_keys}) == len(criterion_keys), 'duplicate criterion/candidate pair')
    issue_ids = []
    for i, value in enumerate(seq(record.get('issues'), 'issues')):
        item = obj(value, 'issues[%d]' % i, ('id', 'type', 'severity', 'classification', 'resolution', 'source_locations'))
        issue_ids.append(item.get('id'))
        seq(item.get('source_locations'), 'issue.source_locations')
    known = ids(issue_ids, 'issue IDs')
    conflicts = ids(record.get('unresolved_conflict_ids'), 'unresolved_conflict_ids')
    check(conflicts <= known, 'conflict IDs must reference issues')
    count = record.get('unresolved_conflict_count')
    check(type(count) is int and count == len(conflicts), 'unresolved_conflict_count mismatch')
    a = obj(record.get('agreement'), 'agreement', ('numerator', 'denominator', 'included_issue_ids', 'excluded_issue_ids', 'agreed_issue_ids', 'ratio', 'limitations'))
    included = ids(a.get('included_issue_ids'), 'agreement.included_issue_ids')
    excluded = ids(a.get('excluded_issue_ids'), 'agreement.excluded_issue_ids')
    agreed = ids(a.get('agreed_issue_ids'), 'agreement.agreed_issue_ids')
    check(agreed <= included, 'agreed IDs must be included')
    check(not included & excluded, 'included/excluded IDs overlap')
    check(included | excluded <= known, 'agreement IDs must reference issues')
    check(type(a.get('numerator')) is int and a['numerator'] == len(agreed), 'agreement numerator mismatch')
    check(type(a.get('denominator')) is int and a['denominator'] == len(included), 'agreement denominator mismatch')
    ratio = a.get('ratio')
    if not included:
        check(ratio is None, 'zero denominator requires null ratio')
    else:
        check(type(ratio) in (int, float) and 0 <= ratio <= 1 and math.isfinite(ratio) and math.isclose(ratio, len(agreed) / len(included), rel_tol=1e-9, abs_tol=1e-9), 'agreement ratio mismatch')
    probe = obj(record.get('invariant_probe'), 'invariant_probe', ('state', 'reviewer_provenance', 'coverage', 'finding_ids', 'reason'))
    check(probe.get('state') in {'performed', 'partial', 'not_required', 'blocked'}, 'invalid invariant_probe state')
    ids(probe.get('finding_ids'), 'invariant_probe.finding_ids')
    if probe.get('state') == 'performed':
        check(bool(probe.get('reviewer_provenance')), 'performed probe needs reviewer provenance')
    if record.get('state') == 'complete':
        check(probe.get('state') not in {'blocked', 'partial'}, 'complete cannot have incomplete required probe')
    for i, value in enumerate(seq(record.get('artifacts'), 'artifacts')):
        obj(value, 'artifacts[%d]' % i, ('role', 'locator', 'revision_or_hash', 'access_state', 'validation_state'))
    for i, value in enumerate(seq(record.get('effects'), 'effects')):
        effect = obj(value, 'effects[%d]' % i, ('id', 'requested', 'reported', 'observed', 'state', 'evidence'))
        check(effect.get('state') in {'verified', 'pending', 'failed', 'uncertain', 'not_run', 'not_applicable'}, 'invalid effect state')
        if effect.get('state') == 'verified':
            check(bool(effect.get('observed')) and bool(effect.get('evidence')), 'verified effect needs observation and evidence')
    reporting = record.get('reporting')
    gap = record.get('reporting_gap')
    if reporting is None:
        g = obj(gap, 'reporting_gap', ('resource', 'expected_version', 'access_state', 'reason', 'next_action'))
        for key in ('resource', 'expected_version', 'access_state', 'reason', 'next_action'):
            check(nonempty(g.get(key)), 'reporting_gap.' + key + ' must be nonempty')
    else:
        check(isinstance(reporting, (dict, str)) and bool(reporting), 'reporting must be a result object or accessible reference')
        check(gap is None, 'reporting_gap must be null when reporting is present')
    return errors


def validate(record):
    """Reject malformed field types without crashing the caller."""
    try:
        return _validate(record)
    except (TypeError, ValueError) as exc:
        return ["invalid field type: " + str(exc)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding='utf-8'), parse_constant=lambda value: (_ for _ in ()).throw(ValueError('non-finite JSON number: ' + value)))
        errors = validate(record)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    print(json.dumps({'valid': not errors, 'errors': errors, 'scope': 'selected structural/arithmetic checks only'}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
