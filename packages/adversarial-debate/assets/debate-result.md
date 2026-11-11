# Result contract

Return `dot-adversarial-result/1.1` on every new-run path. Legacy result/1.0 remains readable but does not establish isolation. All top-level fields below are required. A compact human response may accompany the structured record. Nulls require a reason at the affected field or in reason/execution. No external success follows from a local record.

- contract_version: the exact string `dot-adversarial-result/1.1`; request_id and run_id: nonempty strings; parent_run_id: nonempty string or null.
- source_snapshot_ids: an array of unique nonempty string IDs, not source objects. Keep each snapshot’s hash, locator and read coverage in artifacts or execution and reference its ID.
- state: complete, partial, blocked, failed or cancelled; stage; reason.
- scope: requested/performed modes/depth/variants/focus/effects, amendments and skipped work.
- recommendation: an object with exact keys `selected_ids` (array of unique nonempty candidate-ID strings or null), `rationale` (nonempty string), `conditions` (array, empty when none), and `alternatives` (array, empty when none; put a prose no-selection explanation in rationale). Add decision owner only if known. An unknown critical criterion prevents an unconditional recommendation.
- criteria: an array of records {id, candidate_id, critical, verdict, evidence, rationale}. Use the exact key `candidate_id`: a nonempty candidate-ID string for per-candidate rows, or null for a genuinely global criterion. Each (id, candidate_id) pair is unique. critical is boolean; verdict is met/not_met/unknown/not_applicable. Add applicability and requested scores as needed.
- issues: records {id, type, severity, classification, resolution, source_locations}; preserve dissent.
- unresolved_conflict_ids: unique list; unresolved_conflict_count: exactly its length.
- agreement: {numerator, denominator, included_issue_ids, excluded_issue_ids, agreed_issue_ids, ratio, limitations}. Lists have unique IDs; agreed is a subset of included. Counts derive from those sets; ratio null for zero denominator. Record expected advocates and explicit dispositions when computed. No probability claim.
- invariant_probe: {state, reviewer_provenance, coverage, finding_ids, reason}; state performed/partial/not_required/blocked. A skipped probe is not an empty pass.
- artifacts: typed records {role, locator, revision_or_hash, access_state, validation_state}; use null locator for unproduced outputs.
- isolation: the complete [isolation record](isolation-record.md), including fresh role provenance, source/packet identities, disclosure and read events, control limitations, verdict lock and optional post-lock reveal. A complete evidence assessment may be procedural-only; never call it controlled without verified enforcement and audit.
- execution: actual dispatches/roles, expected roster, completed rounds, omissions/fallbacks, observed effort or unknown, checks not run and validation method.
- effects: records {id, requested, reported, observed, state, evidence}; state verified/pending/failed/uncertain/not_run/not_applicable. An API acknowledgment is not readback.
- reporting: genuine dot-reporting-result/1.0 result or validated accessible reference. If authoritative resources/version are unavailable, null with reporting_gap {resource, expected_version, access_state, reason, next_action}; otherwise reporting_gap is null. This outer fallback is not a replacement reporting protocol.
- next_action: bounded next step and missing input/authority, if any.

A complete evidence assessment may conclude no selection when all promised checks occurred. Missing a required source, reviewer, round or validation means partial/blocked. Failed means unable to continue; cancelled records the user's stop. Debate completion and reporting/publication states remain separate.

`scripts/validate_record.py` checks selected structural/arithmetic invariants and declared isolation sequencing only. It cannot verify truthful source reads, factual claims, actual agent independence, user authority, policy compliance, or the external reporting schema. Check those against real evidence separately.
