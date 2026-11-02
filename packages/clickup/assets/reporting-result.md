# Reporting result template — dot-reporting-result/1.0

Return every field, including blocked/no-op results. Preserve exact request correlation. Nulls require reasons under `gaps`. A local schema check is not provider verification. No bare filenames as external receipts.

```yaml
contract_version: dot-reporting-result/1.0
protocol_version: dot-reporting/1.0
request_id: null
parent_run_id: null
operation_id: null
mode: prepare # prepare | normalize_receipt
preparation_state: blocked # prepared | partial | blocked | no_op
protocol_access:
  resource: https://github.com/IronbellyOrg/irondots/blob/main/packages/clickup/references/reporting-protocol-v1.md
  observed_version: null
  read_evidence: null
payload:
  identity: null
  local_artifact: null
  recipient_payload: null # approved accessible contents, not private debug/ledger data
readiness:
  final_trigger_met: false
  authority_verified: false
  capability_verified: false
  audience_verified: false
  writer: null
  pending_gates: []
publication_state: not_run # not_run | pending | partial | verified | failed | uncertain | not_applicable
sequence:
  local_ledger: pending
  finalized: pending
  final_batch: not_run
  bounded_readback: not_run
  durable_receipt: pending
  # each: pending | verified | partial | failed | uncertain | not_run | not_applicable
  # 'verified' describes only that stage, not overall publication
components: []
# Each component: effect_id, requested_effect, reported_effect, observed_effect,
# state (verified|pending|failed|uncertain|not_run|not_applicable), reason,
# evidence {provider, target_id_or_link, observed_fields, observed_at,
# revision_or_hash, operation_id, evidence_status}; unknowns stay null with reason.
receipt:
  local_location: null
  protocol_version: dot-reporting/1.0
  payload_identity: null
  canonical_refs: [] # observed provider IDs/links only
  verification_evidence: []
validation:
  checks_performed: []
  checks_not_run: []
effort:
  calls_observed: null
  actual_remaining_limits: null
gaps: [] # field/question, reason, affected stage/effect, needed evidence
next_permitted_step: null
```

`prepare` returns publication `not_run`/`pending`/`not_applicable`, never verified. `normalize_receipt` may report verified only for observed effects whose acceptance checks passed; copied claims or an API acknowledgment are insufficient. Any required unresolved component prevents overall verified publication. Access/authority failures for intended publication are blocked/pending, not successful no-op. Reconcile uncertain effects before retry; never replay completed work. Caller alone performs an authorized final batch and readback; this skill's result cannot grant authority or prove a transport exists.
