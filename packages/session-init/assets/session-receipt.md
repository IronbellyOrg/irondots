# Session receipt — session-init/1.1

Retain in existing authorized session/work context. No new business task or automatic write authority; record already-authorized briefing persistence separately. Fill from actual observations. Use null plus reason for unknowns. This is an instruction-level schema, not a runtime validator.

```yaml
contract_version: session-init/1.1
invocation_id: null # locally generated ID, never represented as provider identity
provider_call_id: null
call_identity_reason: null
prior_invocation_id: null
call_relationship: unknown # same | new | unknown; requires evidence
session_epoch: null # actual provider epoch if available, otherwise unknown
skill:
  name: session-init
  declared_version: 1.2.0
  resource_identity: null
  observed_revision_or_hash: null
  read_evidence: null
routing_ledger:
  contract_version: dot-skill-routing-ledger/1.0
  observed_revision: null
  resource_identity: null
  read_evidence: null
  applied_rule_ids: []
  unresolved_routes: []
trigger: manual # verified_event is reserved for a separately configured, verified binding
started_at: null
completed_at: null
mode: initialize # initialize | refresh | no_op
selected_resources: [] # identity, observed revision/hash, read evidence, reason
skipped_resources: [] # resource and reason
checkpoint: null # minimal relevant identity; no raw private history
objective: null
prepared_core_word_count: null
authority_scope: null
pending_approvals: []
capability_observations: [] # actual target, result, observation time; not a global probe
waiting_mode: best-effort # best-effort | verified-runtime | unavailable
technical_readiness: null # ready | degraded | blocked
readiness: null # functional: ready | degraded | blocked
briefing:
  approved_scope: null
  coverage: null # complete_within_scope | partial | unknown
  sources: [] # source ID, source_updated_at/as_of, fetched_at, last_successful_refresh, gaps
  generated_at: null
  item_refs: [] # canonical ID, initiative, owner, status, user ask, dependencies, waiting age, freshness
  priority_order: [] # ID, impact/unblocking, urgency, known age, can_finish_now, reason
  first_item_context: null
  missing_or_stale: []
persistence:
  target_id: null # resolved existing full report, not a narrow substitute
  prior_version: null
  observed_version: null
  authority_evidence: null
  state: pending # verified | no_change | pending | failed | uncertain | not_applicable
  material_change: null
  receipt: null
  last_good_ref: null
  gap: null
completed_external_effects: [] # inherited receipt references, not performed by init
uncertain_external_effects: []
new_external_effects: [] # normally empty; initialization alone authorizes none
unresolved_gates: []
acknowledgment: # do not equate prepared with spoken/heard
  state: not_sent
  evidence: null
reporting:
  protocol: dot-reporting/1.0
  external_publication: pending
  reason: null # ClickUp no-op and authorized Space persistence are distinct; state actual outcome.
```

Technical readiness means mandatory resources loaded and the compact core prepared. Functional ready additionally requires coverage-accounted briefing, reasoned priority, first-item context and verified persistence when due and authorized, evidenced no-change, or justified not-applicable. Overall invocation/full success additionally requires actual evidence for each applicable requested delivery gate. Degraded means usable preparation with explicit optional limitations; blocked means a missing mandatory initialization resource or material conflict. A downstream dependency blocks only that task.

For blocked/degraded readiness, name the affected behavior and smallest next permitted step. A blank array means none observed, not proof that none exist. Use a fresh local ID for another manual invocation with unknown call identity; don't invent a reconnect. Record actual selected resource loads, not every file in the package. Keep the full receipt out of the spoken acknowledgment.

Version 1.1 adds functional briefing/persistence fields; old 1.0 receipts remain immutable historical evidence with absent fields unknown. Never silently reinterpret old ready as full functional success. Delivery state remains independent of both readiness fields.
