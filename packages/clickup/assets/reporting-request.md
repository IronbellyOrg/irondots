# Reporting request template — dot-reporting-request/1.0

Use all fields below. This is a local envelope, not a recipient-facing message or permission to send. Explicit null/unknown values require reasons under `unknowns`; never invent values. The protocol fixes workflow; only the six `parameters` are contextual configuration. Other fields describe actual run/evidence, not alternative workflows.

```yaml
contract_version: dot-reporting-request/1.0
protocol_version: dot-reporting/1.0
request_id: null
parent_run_id: null
operation_id: null
mode: prepare # prepare | normalize_receipt
protocol_source:
  resource: https://github.com/IronbellyOrg/irondots/blob/main/packages/clickup/references/reporting-protocol-v1.md
  observed_version: null
  read_evidence: null
parameters:
  destination: null # established canonical location and audience
  target: null # existing record identity, or explicit unassigned/no-op reason
  payload: null # final history/artifact references/status; no private debug leakage
  acceptance: [] # stable effect/criterion IDs and observable checks
  privacy: null # permitted audience/content and exclusions
  access:
    authority: null # actual instruction and permitted effects, not a boolean
    writer: null # one authorized parent/coordinator; never inferred
    transport: null # actual supported operation and capability evidence, or unknown
    resource_read_route: null # supported runtime discovery/read route and evidence
ledger:
  location: null # authorized output/ ledger or existing handoff route for no-op
  identity: null
  completed_work: []
  effects: [] # exact effect IDs, current states and actual evidence
  actual_limits_remaining: null # real bounds or unknown, never fabricated telemetry
finalization:
  authorized_work_and_reporting_complete: false
  payload_identity: null # actual version/hash when available
  no_op_reason: null # only justified unnecessary/direct-parent handoff, not access failure
supplied_receipts: [] # normalize_receipt only; actual provider/effect/readback evidence
unknowns: [] # field, reason, affected readiness, next permitted resolution
```

Reject missing required keys, unknown modes or versions, mismatched run/operation identities and unsupported protocol sources. `prepare` may run before completion but must return prepared with pending trigger, never send-ready or verified publication. Unknown authority/writer/transport/audience blocks publication readiness; a legitimate parent-owned handoff is not evidence that publication occurred. Include only authorized recipient-accessible material in any final payload; local ledger paths may remain in this local envelope but cannot masquerade as published artifact links.
