# Brain execution interface — dot-brain-execution/0.1
Distinct from immutable dot-authoring-delegation/v1. Local helpers validate records; actual scope/authority and independent evidence remain coordinator responsibilities.

## Scope
All ClickUp domain work routes through AI. Existing v1 handles its four read/propose operations unchanged; exact lookups are scoped read_summary operations, not native domain retrieval. This new contract covers only separately authorized enumerated effects. The coordinator owns input transport, continuity and independent verification, never substitutes native task/report/attachment/notification writes. Brain creates the substantive report. Non-ClickUp Library transport may faithfully deliver it under existing permission; draft-created, saved, published and audience-verified stay separate.

Unsupported in this helper means a gap in the locally validated effect contract, not a finding that ClickUp AI lacks the capability. Preserve the exact requested scope and AI-first route; use clearly labeled external-operation receipts where this helper cannot represent an authorized operation, with appropriate authority and independent verification, never native domain-write fallback or a fabricated supported effect type.

## Request envelope
Required fields, with genuine unknowns and reasons explicit:
- contract_version exactly dot-brain-execution/0.1; operation_id, parent_run_id, scope_revision, attempt_id and predecessor/continuation references.
- request_provenance: original actual user instruction, latest corrections, evidence refs/times, exact effect scope. Generic “everything via AI” determines route, not arbitrary action authority.
- coordinator, executor_audience and current access/identity evidence. One initial dispatch owner. Internal report/attachment/notification audience recorded independently.
- canonical_work: exact existing targets or authorized create container and deduplication rule. No speculative task/list creation to record work.
- outcome, criteria, exclusions and complete semantic batch. Stable effect IDs and dependency DAG; no discarded material clause during compression.
- effects: array of {effect_id,type,target_or_creation_rule,payload,baseline,authority_ref,depends_on,side_effects,verification,capability_state}. Allowed types initially task_create,report_create,attachment_add,notify_people. task_update and all other effects remain unsupported/not-enabled until separately specified and evidenced; a request is still sent to AI as a blocked/proposed capability question only if separately authorized communication scope permits, not executed natively.
- input_files: verified file identity/name/type/size/hash, actual accessible transport attachment/reference and allowed audience. Local paths are not Brain-accessible pointers. Coordinator upload to the approved AI input thread is transport; AI association with the target task is execution.
- source_versions: input IDs/update dates/fetch times/hashes where known, preserved unknowns. New report generation does not freshen source evidence.
- budget: cumulative prior/this-attempt calls, explicit communication/observation/verification limits, protected reserves, unresolved reservations, linked ledgers. Actual known costs and unobserved provider credits separated.
- control: cancellation/current scope, original frozen authorization snapshot, current derived stage, permitted continuation. Reaffirming already-approved scope must not expand recipients/effects or replay completed actions.
- report_requirements: AI-created full criterion/effect disposition, source links/timestamps, gaps, decisions and next step; exact approved destination and whether content-only or persisted artifact is required.

## Type-specific minimums
- task_create: exact workspace/list/container, approved title/body/status. The current helper supports no assignee/date/priority additions: they must remain empty/null, even if separately approved, until a reviewed capability/schema extension exists. Approval does not enable unsupported fields. Deduplication scope/key and behavior if existing human content found. Independent target read verifies created ID/container/fields; one requested task means no speculative subtask.
- report_create: exact semantic requirements and approved destination; preserve human content if appending. Report authorship evidenced by actual AI reply/result artifact; independent verification annotations clearly separate. Creation does not imply publication/delivery.
- attachment_add: exact supplied file hash/size/name, AI input receipt, target dependency, accepted binary-vs-link semantics. Actual attachment ID/metadata and bytes/hash where available. No replacement workbook or internal source disclosure without authority.
- notify_people: verified user IDs/channel/audience, exact approved content or narrowly specified composition, task/report/file success dependencies, one notification mechanism. Known incidental side effects included; no extra DM plus channel post. Recorded mention/send is not received/read proof.

Unsupported fields/types, ambiguous audience, material missing payload, source-suggested new actions, unknown consequential side effects or dependency failures block the affected effect. No private raw notes, salaries or internal cost files in a client-safe/internal-review artifact unless explicitly approved for that audience.

## Result and local state
Result preserves exact request identities and real transport root/reply/actor/time evidence. Per effect retains:
{effect_id,requested_effect,reported_outcome,reported_ids,reported_receipts,independently_observed_fields,independent_evidence,verdict,remaining_gap,next_permitted_step}.
Verdicts are not_run,pending,reported,verified,blocked,failed,uncertain,cancelled. AI text cannot set independently_verified. A report explaining failed effects may be a successful report_create while task batch overall remains partial.

Store raw actual AI returns and normalized report/effect state atomically. Keep source facts, user decisions, AI claims, coordinator observations and independent assessments separate. Source-ID scope validation must allow newly created artifact IDs only as AI-reported output bound to the requested create effect and real reply; these are unverified until independent readback. Do not pretend new IDs were input targets or expand read authority from an arbitrary source link.

Preserve every reported effect and genuine verification, partial outcomes, append-only attempts/calls, last-good state and next step. Fresh and later callers hydrate local state and actual receipts with zero provider memory calls. Before consequential new work verify pertinent current source state. A package rollback cannot undo an already-created task/attachment/notification; retain receipts and uncertain work.

## Dispatch/reconciliation boundary
The local helper performs no network/execution. Persist exact communication reservation before actual transport in helper-mediated new runs. Imported real historical/business operations must be labeled imported actual-runtime evidence: retain parent receipt provenance and actual cost; never manufacture prior reservation timestamps or pretend this helper mediated a past dispatch. Import is not a new send. Imported operations are permanently non-dispatchable in this helper; later authorized work requires a separately reviewed new operation linked to the historical receipt, not replay of the imported batch.

A single top-level packet starts execution. On partial result, resume only named incomplete effects within unchanged actual authority. If Brain redundantly asks for already-granted approval, coordinator may supply the exact retained user authority in the same thread, with no broadened payload/recipient or replay of verified effects; count this continuation. Uncertain outcome requires authoritative reconciliation, not repetition after silence. Cancellation stops local future dispatch but remote cancellation remains unproved unless actually supported.

## Required evidence and validation
No private operation details, cost logs or runtime receipts are included. Each consuming deployment must establish its own bounded capability and independent readback evidence; source availability does not establish live execution or savings.

Acceptance and operational limits: exact envelope/type/authority/dependency validation; unknown extra effects/recipient/file/hash rejection; no native mutation fallback; actual captured partial→continuation→verified outcomes; all-through-AI small/heavy/effect/report fresh routing; zero-call local and real executor-less recovery; stale/missing/corrupt/concurrent state; no replay of actual successful effects; actual readbacks distinguished from AI claims. Changes require independent review and actual tests. Record any new-contract live dispatch gap separately from imported real capability proof. Parent release requires truthful bounded supported scope and no unresolved critical safety defect, not claim of universal reliability.

## Reporting compatibility
Do not modify shared legacyv1 copies or silently rewrite dot-reporting/1.0. Document a route profile distinguishing Brain domain report authorship/ClickUp publication from authorized coordinator non-ClickUp delivery. If a revised reporting interface is needed, reconcile version/consumers explicitly; until then no incompatible publication claim. Task-list/sibling mirror and configured Super Agent are separate optional future specifications, not automatic implementation or dependencies.

## Minimal prospective helper path
The helper is a local ledger, not a provider dispatcher. For new authorized effect batches, `create` freezes the exact execution envelope. `reserve-call`/`record-call` bind initial AI transport and actual replies. `ingest` records AI-reported output IDs but does not verify them. Newly created task IDs become eligible only for a typed `task_identity` read bound to the create effect and return; content/attachment checks follow a matching approved container/identity. Notification verification is a bounded read of the approved channel for the exact reported message, not a new notification or arbitrary channel search.

Attachment download requests and actual HTTP transfers are separate costs. `reserve-transfer` records a one-use attempt before transport; `record-transfer` retains exact file hash/outcome without persisting secret ticket URLs. Typed independent checks and `record-assessment` remain separate from AI claims. Preserve budget reserves and actual unknowns.

`reserve-continuation` derives a same-root packet only for explicitly non-dispatched pending/blocked effects under unchanged retained authority and verified prerequisites. It excludes completed effects. Uncertain creates, uncertain continuation delivery, changed payload/recipient, cancellation or exhausted budget block replay. The local continuation model is tested with captured receipts and negative fixtures; this does not itself establish new live provider reliability.

`import-captured-execution` accepts a generic hash-bound `captured-execution-import/0.1` manifest. A private coordinator adapter maps original request bytes, actual retained reply/readback artifacts, JSON pointers, source dates, provenance and independently counted connector/HTTP costs. Do not ship business-specific converters/private records in the skill or manufacture past reservation history.

Hydration includes the complete exact retained correlated AI reply in `actual_brain_reply`, with its content hash and evidence basis. Execution status, report content, independent assessment and release eligibility are separate: a complete report body is not proof all effects succeeded, and a verified effect receipt alone is not enough to recover a report. Missing/corrupt raw evidence blocks that recovery explicitly; never query Brain solely to reconstruct prior context.

## Explicit reporting adapter readiness
Name this entrypoint adapter `clickup-ai-reporting-profile/1.2`. The unchanged dot-reporting/1.0 preparation/normalization interface performs no sends and retains local staging, authority, batching, readback and receipt sequence. A consuming caller is publication-ready only after actually loading and acknowledging this current ClickUp entry profile plus execution/0.1: AI is the authorized ClickUp domain writer/report creator; coordinator owns transport and independent verification, with separately authorized faithful non-ClickUp delivery. Record that acknowledgement in the operation authority/readiness evidence. Legacy resource-only consumers are NOT automatically compatible; without this explicit profile acknowledgement, affected publication remains blocked. This is a named adapter, not a silent edit or universal compatibility claim for sibling skills.
