"""Check declared isolation records. This does not observe or restrict agent access."""
import re


def validate_isolation(record):
    errors = []
    def check(ok, text):
        if not ok:
            errors.append('isolation: ' + text)
    def text(x):
        return isinstance(x, str) and bool(x.strip())
    def obj(x, label, keys):
        if not isinstance(x, dict):
            check(False, label + ' must be an object'); return {}
        for k in keys.split():
            check(k in x, label + ' missing ' + k)
        return x
    def array(x, label):
        if not isinstance(x, list):
            check(False, label + ' must be an array'); return []
        return x
    def strings(x, label):
        values = array(x, label)
        check(all(text(v) for v in values), label + ' needs nonempty strings')
        return [v for v in values if text(v)]
    def ids(x, label):
        values = strings(x, label)
        check(len(values) == len(set(values)), label + ' must be unique')
        return set(values)
    def digest(x):
        return isinstance(x, str) and re.fullmatch(r'[0-9a-f]{64}', x) is not None
    def enum(x, allowed):
        return isinstance(x, str) and x in allowed
    iso = obj(record.get('isolation'), 'record', 'protocol_version status claim limitations plan roles packets events controls verdict_lock prior_results')
    check(iso.get('protocol_version') == 'dot-debate-isolation/1.0', 'unsupported protocol_version')
    status = iso.get('status'); claim = iso.get('claim'); complete = record.get('state') == 'complete'
    check(enum(status, {'verified', 'procedural_only', 'contaminated', 'unknown'}), 'invalid status')
    check(enum(claim, {'controlled_comparison', 'independent_attempt', 'contaminated'}), 'invalid claim')
    limitations = strings(iso.get('limitations'), 'limitations')
    if status != 'verified':
        check(bool(limitations), 'non-verified status needs explicit limitations')
    check((status == 'contaminated') == (claim == 'contaminated'), 'contaminated status/claim must agree')
    check(not complete or status not in ('contaminated', 'unknown'), 'complete cannot have contaminated/unknown isolation')
    controls = obj(iso.get('controls'), 'controls', 'access_boundary read_audit evidence')
    check(enum(controls.get('access_boundary'), {'verified', 'unverified', 'unavailable'}), 'invalid access_boundary')
    check(enum(controls.get('read_audit'), {'complete', 'partial', 'unavailable'}), 'invalid read_audit')
    control_evidence = strings(controls.get('evidence'), 'controls.evidence')
    if status == 'verified' or claim == 'controlled_comparison':
        check(status == 'verified' and claim == 'controlled_comparison', 'verified status and controlled claim must agree')
        check(controls.get('access_boundary') == 'verified' and controls.get('read_audit') == 'complete' and bool(control_evidence), 'controlled claim requires verified boundary, complete audit and evidence')
    plan = obj(iso.get('plan'), 'plan', 'depth reviewer_required')
    check(enum(plan.get('depth'), {'quick', 'normal', 'deep'}), 'invalid planned depth')
    check(type(plan.get('reviewer_required')) is bool, 'reviewer_required must be boolean')
    if plan.get('depth') in ('normal', 'deep'):
        check(plan.get('reviewer_required') is True, 'normal/deep needs independent review')
    roles = {}; agent_ids = []; contamination = []
    for n, value in enumerate(array(iso.get('roles'), 'roles')):
        r = obj(value, 'role[%d]' % n, 'id agent_id role fork_turns fresh history_state dispatch_evidence')
        rid = r.get('id'); aid = r.get('agent_id')
        check(text(rid) and rid not in roles, 'role IDs must be nonempty and unique')
        check(text(aid), 'agent_id must be nonempty')
        check(enum(r.get('role'), {'coordinator', 'advocate', 'reviewer', 'generator', 'synthesizer'}), 'invalid role type')
        check(enum(r.get('history_state'), {'none', 'unverified', 'present'}), 'invalid history_state')
        check(type(r.get('fresh')) is bool, 'fresh must be boolean')
        check(text(r.get('fork_turns')), 'fork_turns must be explicit')
        check(text(r.get('dispatch_evidence')), 'role needs dispatch evidence')
        if r.get('history_state') == 'present' or r.get('fork_turns') != 'none' or r.get('fresh') is not True:
            contamination.append('role is reused or received inherited history')
        if status == 'verified':
            check(r.get('history_state') == 'none', 'verified roles need verified no-history state')
        if r.get('history_state') == 'unverified':
            check(bool(limitations), 'unverified history needs limitations')
        if text(rid): roles[rid] = r
        if text(aid): agent_ids.append(aid)
    check(len(agent_ids) == len(set(agent_ids)), 'role agent identities must be distinct')
    coordinators = {k for k, v in roles.items() if v.get('role') == 'coordinator'}
    advocates = {k for k, v in roles.items() if v.get('role') == 'advocate'}
    reviewers = {k for k, v in roles.items() if v.get('role') == 'reviewer'}
    check(len(coordinators) <= 1, 'at most one clean coordinator is allowed')
    if advocates or reviewers: check(len(coordinators) == 1, 'decision roles require exactly one fresh coordinator')
    if complete:
        check(len(coordinators) == 1 and len(advocates) >= 2, 'complete needs a coordinator and at least two advocates')
    probe = record.get('invariant_probe')
    if isinstance(probe, dict) and probe.get('state') == 'performed':
        check(bool(reviewers), 'performed probe needs a separate reviewer role')
    if complete and plan.get('reviewer_required') is True:
        check(bool(reviewers) and isinstance(probe, dict) and probe.get('state') == 'performed', 'complete requires the planned reviewer and performed probe')
    packets = {}
    source_ids = set(v for v in record.get('source_snapshot_ids', []) if text(v))
    for n, value in enumerate(array(iso.get('packets'), 'packets')):
        p = obj(value, 'packet[%d]' % n, 'id kind source_snapshot_ids digest origin_run_id')
        pid = p.get('id')
        check(text(pid) and pid not in packets, 'packet IDs must be nonempty and unique')
        check(enum(p.get('kind'), {'original', 'current_run', 'prior_run'}), 'invalid packet kind')
        sources = ids(p.get('source_snapshot_ids'), 'packet.source_snapshot_ids')
        check(digest(p.get('digest')), 'packet digest must be lowercase SHA-256 hex')
        if p.get('kind') == 'original':
            check(sources <= source_ids, 'original packet references unknown source snapshots')
            check(p.get('origin_run_id') is None, 'original packet origin_run_id must be null')
        elif p.get('kind') == 'current_run':
            check(p.get('origin_run_id') == record.get('run_id'), 'current packet must belong to this run')
        elif p.get('kind') == 'prior_run':
            check(text(p.get('origin_run_id')) and p.get('origin_run_id') != record.get('run_id'), 'prior packet must name a different run')
        if text(pid): packets[pid] = p
    events = []; last = 0; dispatched = set(); initial_packets = {}; completed = {}; exposure = []; locks = []
    stage_packets = {}; challenges = set(); original_packets = {}; read_packets = {}; current_reads = {}
    decision_roles = coordinators | advocates | reviewers
    output_exposures = {}; output_reads = {}; final_completed = set(); lock_state = None
    invalid_outputs = []
    def invalidate(rid, stages=None):
        for key in list(completed):
            if key[0] == rid and (stages is None or key[1] in stages):
                completed.pop(key, None); output_exposures.pop(key, None); output_reads.pop(key, None)
    for n, value in enumerate(array(iso.get('events'), 'events')):
        e = obj(value, 'event[%d]' % n, 'seq type role_ids packet_id stage evidence')
        seq = e.get('seq'); typ = e.get('type'); stage = e.get('stage')
        check(type(seq) is int and seq > last, 'event sequences must be positive and strictly increasing')
        if type(seq) is int: last = seq
        check(enum(typ, {'dispatch', 'read', 'disclose', 'stage_complete', 'verdict_lock', 'prior_reveal', 'contamination'}), 'invalid event type')
        check(text(stage) and text(e.get('evidence')), 'event stage/evidence must be nonempty')
        recipients = ids(e.get('role_ids'), 'event.role_ids')
        check(bool(recipients) and recipients <= roles.keys(), 'event needs known role recipients')
        pid = e.get('packet_id')
        check(pid is None or (text(pid) and pid in packets), 'event references unknown packet')
        packet = packets.get(pid, {}) if text(pid) else {}
        if typ != 'dispatch': check(recipients <= dispatched, 'role events must follow actual dispatch')
        if typ in ('dispatch', 'read', 'disclose', 'prior_reveal'):
            check(bool(packet), 'dispatch/read/disclose/reveal needs a packet')
            if typ == 'dispatch':
                check(not recipients & dispatched, 'a role must not be dispatched twice')
                dispatched |= recipients
            if stage == 'initial':
                for rid in recipients: initial_packets.setdefault(rid, set()).add(pid)
                if packet.get('kind') != 'original': contamination.append('initial exposure is not original-source-only')
            if packet.get('kind') == 'original':
                if recipients & decision_roles:
                    check(set(packet.get('source_snapshot_ids', [])) == source_ids, 'decision original packet must include every frozen source snapshot')
                for rid in recipients:
                    seen = original_packets.setdefault(rid, set())
                    if pid not in seen:
                        # New original evidence invalidates this role's dependent outputs.
                        invalidate(rid)
                        seen.add(pid)
                    if typ == 'read': read_packets.setdefault(rid, set()).add(pid)
            if packet.get('kind') == 'prior_run' or typ == 'prior_reveal': exposure.append(e)
            if locks and packet.get('kind') == 'current_run' and recipients & (advocates | reviewers):
                check(stage == 'post_lock', 'post-lock current-run discussion must be a separate post_lock appendix, not a debate/review round')
            if packet.get('kind') == 'current_run' and not (locks and stage == 'post_lock'):
                if recipients & advocates:
                    if stage not in ('rebuttal', 'final_round'):
                        contamination.append('advocate received current-run material outside declared round')
                    if stage == 'rebuttal': check(plan.get('depth') in ('normal', 'deep'), 'quick cannot add a rebuttal round')
                    if stage == 'final_round': check(plan.get('depth') == 'deep', 'only deep permits a targeted final round')
                    barrier = 'rebuttal' if stage == 'final_round' else 'independent'
                    if not all((rid, barrier) in completed for rid in advocates):
                        contamination.append('current-run round released before all advocates completed prior round')
                if recipients & reviewers:
                    if not all((rid, 'independent') in completed for rid in advocates):
                        contamination.append('reviewer challenge released before all advocate first statements')
                    challenges |= recipients & reviewers
                    if stage != 'probe_challenge': contamination.append('reviewer challenge disclosed outside challenge stage')
                for rid in recipients & (advocates | reviewers):
                    if (rid, 'independent') not in completed:
                        contamination.append('current-run material arrived before independent output')
                    received = stage_packets.setdefault(stage, {}).setdefault(rid, set())
                    if pid not in received:
                        if rid in final_completed and stage == 'final_round':
                            check(False, 'a completed targeted final round cannot start another final packet cycle')
                        invalidate(rid, {'rebuttal', 'final_round'} if stage == 'rebuttal' else {stage})
                        received.add(pid)
                    if typ == 'read': current_reads.setdefault((rid, stage), set()).add(pid)
        if typ == 'stage_complete':
            for rid in recipients:
                originals = original_packets.get(rid, set())
                ready = bool(originals) or rid not in decision_roles
                if stage in ('rebuttal', 'final_round', 'probe_challenge'):
                    current = stage_packets.get(stage, {}).get(rid, set())
                    ready = ready and bool(current)
                    if status == 'verified': ready = ready and current <= current_reads.get((rid, stage), set())
                if status == 'verified' and rid in decision_roles:
                    ready = ready and originals <= read_packets.get(rid, set())
                if not ready:
                    invalid_outputs.append((rid, stage, seq))
                    continue
                completed[(rid, stage)] = seq
                output_exposures[(rid, stage)] = frozenset(originals)
                output_reads[(rid, stage)] = frozenset(read_packets.get(rid, set()))
                if stage == 'final_round': final_completed.add(rid)
        if typ == 'verdict_lock':
            locks.append(e)
            # Freeze eligibility at lock. Later reads or outputs cannot retroactively repair it.
            lock_state = dict(completed=dict(completed), originals={r:set(v) for r,v in original_packets.items()}, reads={r:set(v) for r,v in read_packets.items()}, stages={s:{r:set(v) for r,v in values.items()} for s,values in stage_packets.items()}, initial={r:set(v) for r,v in initial_packets.items()}, dispatched=set(dispatched), challenges=set(challenges), output_exposures=dict(output_exposures), output_reads=dict(output_reads))
        if typ == 'contamination': contamination.append('explicit contamination event')
        events.append(e)
    lock = iso.get('verdict_lock'); lock_seq = None
    if lock is not None:
        lock = obj(lock, 'verdict_lock', 'seq digest artifact evidence')
        lock_seq = lock.get('seq')
        check(type(lock_seq) is int and lock_seq > 0, 'lock sequence must be positive integer')
        check(digest(lock.get('digest')), 'lock digest must be lowercase SHA-256 hex')
        check(text(lock.get('artifact')) and text(lock.get('evidence')), 'lock needs artifact and durable receipt')
        check(len(locks) == 1 and locks[0].get('seq') == lock_seq, 'lock must match exactly one verdict_lock event')
        if locks:
            check(set(locks[0].get('role_ids', [])) == coordinators, 'only the clean coordinator locks verdict')
    else:
        check(not locks, 'lock event needs verdict_lock artifact')
    if complete:
        check(lock is not None and lock_state is not None, 'complete needs a verdict lock')
        frozen = lock_state or dict(completed={}, originals={}, reads={}, stages={}, initial={}, dispatched=set(), challenges=set(), output_exposures={}, output_reads={})
        done = frozen['completed']; originals = frozen['originals']; reads = frozen['reads']
        check(set(roles) <= frozen['dispatched'], 'complete roles need dispatch before lock')
        check(all(frozen['initial'].get(r) for r in decision_roles), 'decision roles need original initial exposure before lock')
        exposure_sets = {tuple(sorted(originals.get(r, set()))) for r in decision_roles}
        check(len(exposure_sets) == 1 and all(originals.get(r) for r in decision_roles), 'decision roles need equal total original exposures before lock')
        if status == 'verified':
            check(all(originals.get(r, set()) and originals.get(r, set()) <= reads.get(r, set()) for r in decision_roles), 'verified complete needs original-source reads before verdict lock')
        check(all((r, 'independent') in done for r in advocates | reviewers), 'complete needs current independent output receipts before lock')
        independent_sets = {tuple(sorted(frozen['output_exposures'].get((r, 'independent'), set()))) for r in advocates | reviewers}
        check(len(independent_sets) == 1 and all(frozen['output_exposures'].get((r, 'independent')) == frozenset(originals.get(r, set())) for r in advocates | reviewers), 'independent outputs must cover equal current original exposures')
        required_rounds = {stage for stage in frozen['stages'] if stage in ('rebuttal', 'final_round')}
        if plan.get('depth') in ('normal', 'deep'): required_rounds.add('rebuttal')
        for stage in required_rounds:
            received = {r:p for r,p in frozen['stages'].get(stage, {}).items() if r in advocates}
            check(set(received) == advocates, stage + ' needs disclosure to every expected advocate before lock')
            check(len({tuple(sorted(v)) for v in received.values()}) == 1, stage + ' exposures must be equal for every advocate')
            check(all((rid, stage) in done for rid in advocates), stage + ' needs renewed completed outputs after latest exposure and before lock')
        check(all((rid, 'probe_challenge') in done for rid in frozen['challenges']), 'reviewer challenge needs renewed completion before lock')
    prior = obj(iso.get('prior_results'), 'prior_results', 'state reveal_seq')
    check(enum(prior.get('state'), {'withheld', 'revealed', 'not_present'}), 'invalid prior_results state')
    if prior.get('state') == 'revealed':
        reveal = prior.get('reveal_seq')
        check(type(reveal) is int and bool(exposure) and exposure[0].get('seq') == reveal, 'reveal_seq must match first actual prior exposure')
    else:
        check(prior.get('reveal_seq') is None and not exposure, 'withheld/not_present conflicts with prior exposure')
    for e in exposure:
        if type(lock_seq) is not int or type(e.get('seq')) is not int or e['seq'] <= lock_seq:
            contamination.append('prior results exposed before verdict lock')
    if contamination:
        check(status == 'contaminated', '; '.join(sorted(set(contamination))) + ' requires contaminated status')
    return errors
