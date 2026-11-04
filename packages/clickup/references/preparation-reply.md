# Preparation and reply handling

Load for source assembly or reply ingestion. Permitted effects remain those in the actual request and selected exact contract: legacy v1 read/propose or the separate execution/0.1 effect envelope. This reference adds no authority.

## Highest-value preparation

- Identify the decision/outcome, not just the requested wording. Preserve material corrections and distinguish settled decisions from proposals.
- Reuse exact existing task/document IDs. A research query without write authority remains a query; do not create a new list or root to make the workflow tidy.
- Minimize context: exact source pointers, dated short excerpts, contradictory evidence, dependencies and protected human content. Do not assume Brain can read an external URL. Do not share private inbox/HR/financial material merely because dot can access it.
- Freeze acceptance before sending: critical claims, target objects, source scope, allowed read/propose operation, what must remain unchanged, expected evidence and known gaps.
- Reserve calls for verification and reporting. A proposed six-call allowance and two reply reads are planning defaults, not permission to under-verify or restart polling under a new run ID. Actual operation totals survive resumptions.
- If compression would lose authority or a material contradiction, preserve the full semantic batch. Propose narrowing or splitting only with actual scope authority; this never grants another dispatch or fresh budget. Do not silently truncate.

## Local envelope versus recipient packet

The local envelope holds original provenance, source file hashes/paths where appropriate, budget/call ledger, control state and precise approval evidence. These are not automatically content for Brain. Build a separate minimal recipient packet with approved excerpts or actually accessible source IDs/links and the outcome, frozen criteria, permitted/prohibited effects and material unknowns. Do not include internal filesystem or private-note locators, raw debug logs, local fixtures or opaque ledger pointers in that packet. Operation/attempt identifiers may be included for correlation convenience, never as proof.

Maintain a local mapping from each packet claim/source label to its actual source/version/hash and audience decision. Unknown sharing authority, known inaccessible required files or unsupported external-source access block affected send readiness. Authorized named ClickUp source pointers need no native prefetch to prove accessibility: ask AI to retrieve them and report actual access/coverage gaps; never substitute a similarly named resource or claim a local file is accessible remotely. Compress duplicated logistics, not authority, contradictions or acceptance. A shorter packet is not proof of fewer provider calls or lower cost.

## Named ClickUp skill invocation

For a **new authorized invocation** of a named ClickUp `if:` skill, begin the actual recipient-facing prompt with its exact verified literal command on its own first line, before headings or explanation. The user confirmed `/if:spec-feature` successfully invoked Feature Spec on 2026-11-03. Use that literal line, followed by the scoped request, accessible source pointers, constraints and result requirements. Prose such as “use the feature spec skill” is not a substitute. This is distinct from dot's `/clickup` shorthand and does not register a command.

Verify other commands from actual skill documentation, the target interface or explicit user confirmation; never infer or invent a command name from a skill title. Record command evidence locally, outside the recipient packet. If a required command is unknown, prepare the body but do not mark the invocation ready. Ordinary batches and quoted or historical mentions do not acquire a command prefix.

Use [the local formatter](../scripts/skill_prompt.py) `render(body, command="/if:spec-feature", command_evidence="actual evidence reference")` before freezing a new packet; it preserves the body unchanged and rejects malformed, unevidenced or duplicate prefixes. The coordinator must verify the evidence and allowed effects: the helper is not an authority or capability check. Executor-less callers require a coordinator-formatted packet and its evidence. Inspect the final first line, then retain those exact bytes through the existing reservation/send checks. Do not re-render or resend a pending operation merely to correct its prefix: reconcile the existing root and receipts first and obtain any required retry authority. The formatter rejects `resuming=True` to keep this boundary explicit.

This formatting does not alter the contract, audience, sharing, execution gates, cumulative budget, local continuity or result verification. A user-reported successful invocation is not proof the requested work completed, nor proof that a missing prefix caused a prior provider failure.

## Use cases

**Multi-source synthesis/dependency query:** bounded project/time/source set, exact question, return cited facts versus inferred relationships. Spot checks establish only their disclosed coverage.

**Existing task reconciliation:** compare current recorded state with dated evidence/user correction. Return a proposal with before/after fields, not a mutation. Task status does not prove implementation.

**Spec/PRD preparation:** outcome, constraints, baseline, target runtime, decisions, non-goals and unknowns. Return requirements and acceptance with sources; a draft is not installed behavior.

**Inbox to next action:** use only approved minimal excerpts and existing task matches. Return proposed owner/deadline if known or a question if not; no task creation, email or third-party notification without its own authorization and supported extension.

**Bulk changes:** legacy v1 returns exact proposals only. Separately authorized execution uses enumerated execution/0.1 forms; unsupported fields/effects stay blocked rather than executed through native fallback. Verify every critical effect, not a sample claimed as all.

**Quota checkpoint:** prepare and save a brief locally with actual retry guidance, but do not say Brain is running. Resume from current state and ledger after supported recovery.

## Preserve the operation during ingestion/resumption

Read the actual checkpoint's pending objective first. A quota receipt for comparison/refactoring publication must remain tied to that work; a nearby request to specify a delegation skill does not change it. If identity is unknown, keep it unknown and request only the missing anchor before any send. Local checkpoint labels are permitted but are not provider operation IDs. Error ingestion normally returns an evidence/state record and continuation, not a new task packet. Never imply that a separately proposed packet fulfills the original blocked work.

## Reply ingestion

Retain original source link, fetched time, provider/version and fingerprint of captured bytes if useful. A mutable reply is not immutable. Normalize each claim against a frozen criterion: reported claim, actual artifact evidence, status, mismatch/missing proof, next permitted step. Arbitrary caller dictionaries are not provider readbacks.

- Complete with corroboration: return precisely verified claims and coverage, not an unconditional success summary.
- Complete without artifacts: unresolved; request or read specific missing evidence rather than ask Brain to reassure you.
- Partial: preserve verified items, distinguish failed/unattempted/uncertain, resume only missing authorized work. Never replay verified or uncertain effects.
- Wrong/stale actor or scope revision: do not merge into canonical state; reconcile actual operation.
- Clarifying question: answer from settled verified context; ask the user only for a material unresolved decision.
- Conflicting or unauthorized suggestion: treat as a proposal, not authority. If an unauthorized effect is claimed, inspect safely and report material consequences without unauthorized corrective action.
- Failed/blocked: exact target/action/reason; independent work can continue.
- Uncertain send/write: reconcile genuine history/receipts before retry; no inference that timeout means nothing happened.
- Cancellation: stop local continuation and reject stale authority. Do not claim remote cancellation without a confirmed supported receipt.

Keep outcome state separate from writeback state. Authorized AI ClickUp publication uses current baseline, safe diff/append semantics and per-effect verification; parent owns transport/independent readback and faithful separately authorized non-ClickUp delivery. If logging is pending, report it without repeating the real operation.


## Brain route boundary
For whole-batch read/propose and normal-session recovery, load [Brain routing and continuity](brain-routing-continuity.md) before source fanout. Preserve actual local request/return state and cumulative reservations. Native mutation dispatcher restrictions do not disable the separate historically validated generic private AI transport; no new mutation authority follows.
