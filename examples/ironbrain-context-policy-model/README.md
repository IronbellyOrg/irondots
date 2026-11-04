# Synthetic team-context policy model

This reproducible **offline Python model** explores team-authorized context pools. It is not an AnythingLLM integration, production gateway, deployed permission system or proof that a real service is secure. No network, credentials, private source documents, real account identifiers or company ACLs are used. Python standard library only.

## Run

```sh
python3 run_tests.py
```

The runner saves unique timestamped text and JSON receipts in `runs/`, including code SHA-256 values. Existing receipts are not overwritten. `python3 -m unittest -v` also runs tests. The initial 16-method run passed on November 2, 2026 at 19:28:17 UTC; this is initial evidence, not final independent acceptance. Later receipts govern corrected code.

## Model boundary

The trusted fixture controller creates synthetic users, team membership, session tokens, pool grants, document ACLs and archive approvals. These administrative methods are not exposed to a model or user. Authentication is a trusted dictionary lookup, not implemented OAuth, JWT or SSO. The policy combines verified active team, explicit directional pool grant, source readership, finer allowed teams, reviewed-source status and named-Archive approval. Owner/project tags confer no rights. A multi-team user's active team is explicit, not an implicit privilege union.

`context_sink` is a synthetic boundary that receives only policy-approved text. No LLM or reranker is called. An immutable prepared envelope is revalidated before delivery; a monotonically increasing policy epoch conservatively invalidates caches and derived text on any administrative change. Dependencies and document versions remain attached to synthetic summaries (concatenations). This deliberately sacrifices availability rather than allowing stale authorization. Tests cannot establish an acceptable real refresh latency, service-key boundary or restoration procedure.

Archive discovery is separate from inclusion: exact case-insensitive Archive containers require versioned approval even beneath selected parents; OLD/Archived labels receive quality flags without inheriting that mandate. Archive authorization does not replace source/pool authorization or evidence freshness. User-facing pool toggles are not implemented; arbitrary source-ID requests are tested to ensure they do not grant access.

## Coverage and unsupported portions

- T1–T7: modeled positive/negative grants, cross-sharing, inner restrictions, active-team identity, discovery and envelope binding. No real authentication/API or timing-side-channel testing.
- T8–T9: modeled quarantine/review and inability of document text to grant rights. No actual parser, OCR, hidden-sheet extraction or classifier implementation.
- T10–T11: modeled revoked grants/membership/source ACL, changed versions, deletion, cached envelopes and derived dependencies. No source change feed or embedding/vector deletion.
- T12: modeled summary audience intersection and data-not-authority handling. No inference detector, real summarizer, tool executor or LLM prompt-injection defense is tested. Financial/HR inference remains a runtime/design gap.
- T13: modeled unavailable authority/unknown target. No real exports, shortcuts or history endpoints.
- T14: 100 requests using 20 worker threads through a locked in-memory model. This proves fixture isolation only, **not 100 concurrent agent-session capacity** or a latency SLA.
- T15: stale envelope reinsertion cannot restore authority. No real backup restore or optional toggle UI.
- T16: modeled archive discovery/approval/revocation and revision changes for two synthetic source types. No real source discovery integration.

All 16 matrix requirements therefore retain runtime acceptance gates even if every model method passes. There is no automatic grant, ingestion, deployment or public publication.

## Brownfield compatibility

The accepted design and 16-case matrix are preserved. This stage adds synthetic evidence without altering the existing product, connectors, data or configuration. Runtime architecture remains uninspected. No migration is executed. Recovery is to discard/recreate synthetic fixtures; that is not a production rollback plan. Performance/cost improvements are not claimed.

## Archive regression correction (November 2, 2026)

Independent review found that unknown revision `None` compared equal to absent approval `None`, permitting an Archive without approval. The initial failed independent receipt and regression run are retained; the prior 16-method pass did not catch this. The minimal corrected invariant requires a valid revision plus explicit approved state and matching approved revision. Invalid discovery is retained as unapproved, invalid approval is denied, invalid rediscovery clears prior approval, and revocation clears approval explicitly.

This fixture uses positive integer revisions (excluding bool); real providers may use opaque revision strings and need their own validated representation. The integer rule is not a production requirement. Two regression methods cover nine invalid values plus valid approval→invalid rediscovery→reapproval→revocation. Fresh independent review of corrected code is required.
