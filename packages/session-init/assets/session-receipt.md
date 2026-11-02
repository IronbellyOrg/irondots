# Session receipt — session-init/1.0

Retain in existing authorized session/work context; do not create a business task or publish by default. Fill from actual observations. Use null plus reason for unknowns. This is an instruction-level schema, not a runtime validator.

```yaml
contract_version: session-init/1.0
invocation_id: null # locally generated ID, never represented as provider identity
provider_call_id: null
call_identity_reason: null
prior_invocation_id: null
call_relationship: unknown # same | new | unknown; requires evidence
session_epoch: null # actual provider epoch if available, otherwise unknown
skill:
  name: session-init
  declared_version: 1.1.1
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
readiness: null # ready | degraded | blocked
completed_external_effects: [] # inherited receipt references, not performed by init
uncertain_external_effects: []
new_external_effects: [] # normally empty; initialization alone authorizes none
unresolved_gates: []
acknowledgment: # do not equate prepared with spoken/heard
  state: not_sent
  evidence: null
reporting:
  protocol: dot-reporting/1.0
  external_publication: not_applicable
  reason: Routine initialization returns a minimal receipt within the existing session; no external publication is required or authorized by activation.
```

Ready means the mandatory resources loaded and the bounded core was prepared, not guaranteed behavior. Degraded means usable preparation with explicit optional limitations; blocked means a missing mandatory initialization resource or material conflict. A downstream dependency blocks only that task.

For blocked/degraded readiness, name the affected behavior and smallest next permitted step. A blank array means none observed, not proof that none exist. Use a fresh local ID for another manual invocation with unknown call identity; don't invent a reconnect. Record actual selected resource loads, not every file in the package. Keep the full receipt out of the spoken acknowledgment.
