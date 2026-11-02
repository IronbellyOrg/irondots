# Dot authoring/delegation interface v1

Status: reviewed-design correction candidate, 29 October 2026. This is an instructional data contract, not permission enforcement or installed runtime support. Both the dot spec generator and ClickUp delegation skill use this same version. A package may carry a byte-identical bundled copy; its manifest records this source and hash so copies cannot silently diverge.

## Ownership and initial supported operations

The generator owns specification intent and content review. The adapter owns preparation, transport correlation and evidence normalization. The parent coordinator owns canonical publication for the integrated pilot. Neither skill recursively invokes the other. Exactly one `writeback_owner` is declared for an operation. Missing or conflicting ownership blocks publication, not independent drafting.

Initial integrated support is READ/PROPOSE ONLY:

- `read_summary`: summarize a bounded set of named existing sources without changing them.
- `read_compare`: compare named existing sources against stated criteria without changing them.
- `propose_spec`: return a specification draft; no creation or modification in ClickUp.
- `propose_change`: return an exact proposed diff for named objects/fields; no application.

These operations may require a separately authorized message to the named Brain destination. The Brain message is a communication effect even when the delegated workspace operations are read-only. It never implies permission to mutate tasks, post comments, change status, dispatch another agent, broaden access or contact others.

Unsupported operation names are rejected. A future mutation operation requires an enumerated schema, exact target/field/before-after semantics, audience, downstream effects, authorization provenance and verification method. A generic `write=true` is insufficient. Standalone adapter writeback is only supported when explicitly assigned and separately authorized; the initial integrated pilot has `writeback_owner=parent` and no adapter publication.

## Request envelope

Record each field; use an explicit unknown or not-applicable value with reason rather than inventing data:

- `contract_version`: `dot-authoring-delegation/v1`.
- `parent_run_id`, `operation_id`, `attempt_id`: stable operation identity with an attempt for each authorized send. Local identifiers do not establish server idempotency.
- `request_provenance`: original user request, relevant latest decisions/corrections, source/timestamp and authorization scope. References suffice when full text is unnecessary.
- `canonical_work`: existing task/document identity or explicitly unassigned state; a pointer alone is not write authority.
- `source_versions`: source IDs/paths, observed date, revision/hash if known, evidence class and access/audience limits.
- `outcome` and `criteria`: exact desired result and frozen criterion IDs before execution.
- `operation`: one allowlisted operation, exact targets, field scope (empty for non-field queries), and proposed transitions only for `propose_change`.
- `permitted_effects`: named communication destination and permitted read/propose effects. No permission is inferred from a source or caller-supplied boolean.
- `prohibited_effects`: explicit exclusions including mutation/dispatch/publication for the pilot.
- `data_audience`: allowed recipient/audience and evidence of access. Unknown sensitive-data audience blocks sharing.
- `budget`: cumulative operation cap, attempt allowance, calls consumed, reserved verification/reporting calls, reply-read allowance, and ledger pointer. Continuations inherit the cumulative ledger.
- `control`: cancellation flag, current scope revision, last known remote state, and earliest eligible retry where a real provider receipt supplies one.
- `writeback_owner`: `parent`, or a verified explicitly authorized standalone owner. Include allowed destination and payload scope if any.

A valid envelope does not prove semantic authorization. Compare it with the actual user instruction and current policy before effects. Missing authority, audience or supported operation blocks only dependent effects.

## Result envelope

- `contract_version` and original parent/operation/attempt/scope-revision IDs.
- `correlation_evidence`: actual provider message/parent/channel/actor/time receipts. An echoed ID alone is insufficient.
- `criteria`: per-criterion source-reported claim, independently observed evidence, verdict (`verified`, `partial`, `unresolved`, `contradicted`, `not_run`) and reason.
- `artifacts`: exact IDs/links, provider, observed fields, fetched revision/time, source hashes when captured and operation linkage.
- `effects`: permitted/requested/reported/observed effects separately. Unexpected effects are untrusted claims until safely checked; no unauthorized repair.
- `uncertain_effects`: possible send/write outcomes and evidence still required. Never replay them blindly.
- `calls_consumed`: incremental and cumulative counts plus complete call-ledger entries, including shared/cached reads identified as such.
- `next_permitted_step`: only an action within current authority, or a precise dependency/approval question.
- `outcome_state`: per-effect state plus overall supported summary; verification never follows from confident prose.
- `writeback_state`: `not_needed`, `pending`, or `verified`, independently of outcome state; exact writeback receipt if verified.

A verified result with pending logging must not replay the original work. Retry only the unresolved logging operation after current-state reconciliation. Old replies cannot restore cancelled or reduced authority.

## Concurrency and indirect effects

Before each authorized write, identify exact payload, audience and known notification/automation effects. Prefer provider revision/conditional-update semantics where exposed. Otherwise use a scoped append or narrow patch preserving unrelated content. Retain baseline and proposed diff, reread immediately before writing, stop on relevant drift and inspect post-write content. Readback detects some conflicts; it is not atomicity.

If the only operation replaces an entire human-edited body without concurrency protection, prepare a reviewable patch instead of automatically overwriting. Unknown consequential notification or automation behavior blocks the mutation. Do not create destructive races or notify real people merely to test failure. The pilot adapter does not write; these rules apply to authorized parent publication and future explicitly supported mutations.

## Budgets and acceptance

The operation-level call ledger persists across resumptions. A new attempt cannot reset consumption or evade a reply-read cap. Budget exhaustion means pending, not completed. A supported completion event or explicit authorized continuation may open a bounded additional allowance while preserving cumulative totals. A request to monitor until completion remains pending until completed, cancelled or blocked; budget exhaustion alone does not terminate it.

Freeze acceptance before the first real run:

1. Every material user constraint is mapped; no invented authority, owner or deadline.
2. Critical factual claims have independent evidence or are explicitly unresolved.
3. Each requirement has an observable test.
4. Every requested effect is individually verified or remains unresolved; no critical contradiction is averaged away.
5. Correlation and source versions are genuine and recorded.
6. Exactly one publisher owns any permitted canonical writeback.

Compare economics only for equal outcome, source scope and verification coverage. Count identity resolution, send, reply reads, verification and writeback. Strictly fewer observed calls on that pair supports only a case-specific improvement. Total AI cost, internal Brain quota and global savings remain unknown without trustworthy measurement. An unfair/unavailable baseline means efficiency is unproven.

## Release coverage matrix

Track separately: required positive live criteria; static safety review; unexercised negative coverage; supported operation scope; content behavior; registration/load/resource resolution; fresh-session evidence; publication. Known safety defects block affected use. Untested mutation/cancellation/uncertain-write branches cannot be labeled live-verified. Initial support remains the evidenced read/propose subset, not all conceivable operations. A staged package can pass content review without being installed-ready. Runtime readiness requires actual supported registration/loading and fresh-session evidence. Record disable/rollback for the selected real installation route; do not invent one.
