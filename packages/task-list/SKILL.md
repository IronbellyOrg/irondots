---
name: task-list
description: Create, resume, update, complete or reopen a simple Markdown task list in Space with basic evidence gates and an appropriate ClickUp sibling. Use for requested task-list management, not automatic execution, independent backlog ownership or a recurring synchronization service.
---

# Simple task lists

Version **1.0.0**. Keep one readable, resumable file per logical list. Use [the template](assets/task-list.md); omit irrelevant fields, not required checks. Do not add a workflow engine, scheduler, new database or mandatory phase ceremony.

## Resolve and plan

1. Recover the existing list and private coordination receipts by stable identity before any provider calls just to remember progress. Read the current Space file/version before writing. Reuse a matching logical list; title alone is insufficient. Ambiguity blocks creation, not independent planning.
2. Record intent, source, authorized scope, stable list ID, Space identity/version, coordinator, state, next permitted action and blockers. Make each required step actionable with a stable row ID, dependency if any, observable acceptance and evidence/result. Leave unknown owners/dates unknown. Planning does not authorize execution, outreach, assignments, access changes or listed actions.
3. Resolve the existing Task Lists root and its To Do/Done folders in the user's Space using the current Library skill. These are account configuration, not universal hardcoded IDs. Create missing structure only if authorized. Backlog, active, blocked and cancelled-but-not-completed lists belong in **To Do**.

## Work and checkpoint

Use `backlog`, `in_progress`, `blocked`, `done`, `cancelled`. Update at a meaningful verified milestone, material blocker/decision change or handoff, not every step or unchanged read. Separate attempted, failed, uncertain and verified outcomes. A worker's assertion or successful command is not evidence that its acceptance outcome happened; inspect applicable outputs/tests/readbacks.

Before replacing, compare the current Library version with the version you read. Preserve human edits; conflicting edits stop the affected overwrite for reconciliation. Use the same Library file ID and expected-current-version guard. Never delete/create to update. Follow the current Library write/identity metadata workflow. Keep detailed raw receipts private; include concise useful evidence in the list.

On interruption, recover this list, existing ClickUp sibling and operation identity. Reconcile uncertain effects before any retry; never replay verified work. If Space saved and the mirror failed, retain the good file, mark mirror pending with exact gap and next permitted recovery. A missing reply is unknown, not success or no change. Retain old source timestamps; fetched_at is not source freshness.

## Mirror through the ClickUp skill

Actually load the registered `clickup` entrypoint, its `references/task-list-progress-v0.1.md`, execution contract referenced there, and reporting profile before remote readiness. If these cannot be loaded or the required capability is unvalidated, label mirroring blocked/partial and continue safe local work. Do not reproduce provider connectors or override legacy reporting.

Pass stable list/Space/task/row IDs, approved milestone delta, evidence, expected source revision, audience and authority to that ClickUp-owned module. ClickUp AI performs **all** domain discovery, lookups, synthesis, execution and report creation; coordinator owns necessary transport, independent verification, local continuity and faithful separately authorized Space delivery. No direct domain-read/write fallback.

Reuse one canonical sibling parent with compact progress by default; reuse existing row-level remote objects where already canonical. Never create a whole ClickUp List by default. Resolve appropriate existing destination and audience: AI/skill work belongs in IronFlow HUMAN planning, not results buckets; other personal work defaults to CEO with project/privacy exceptions. Unknown destination blocks remote creation. Record stable IDs and dedup identity before any send.

ClickUp is authoritative for shared status, owner, due date and dependencies. Preserve current source fields and human conflicts; local proposals stay pending until authorized and verified. Map semantic states to actual observed destination statuses, never guessed labels. Blocking/cancellation are not completion. Use only verified capabilities. Batch authorized initial establishment, material milestone/blocker/decision and final closure; no per-row chatter or timer polling. One final effect/receipt serves the agreed final-reporting obligation, not a duplicate publication. Durable local recovery uses the ClickUp-owned store, no competing truth.

## Complete or reopen

Mark a row done only when its observable acceptance passes with evidence. Required cancelled/removed rows are excluded only by an authorized scope decision recorded with rationale; cancellation alone is not successful completion.

Before closing the whole list, verify every required check, required delivery (including mirror/repository when in scope), and unresolved effect. Any required gap prevents the completed claim. Record completed_at and completion evidence. Move the **same** Library file ID to Done, then verify actual destination/identity. A definitively failed move remains pending in To Do. An uncertain response leaves the actual destination unknown: reconcile the same file ID before retrying. Do not create a second copy or claim archived success. Underlying work complete and file movement complete are distinct.

On authorized reopening, preserve completion history, move the same ID back to To Do and verify it; reconcile the existing sibling rather than creating another. Record the new scope/reason and next permitted step. Never silently reopen unrelated completed work.

## Report faithfully

State the verified result, exact gap and next permitted action. Distinguish local completion, mirrored source state, installation and operational validation. Static scenarios do not prove live provider effects. For final reporting actually load ClickUp's `dot-reporting/1.0` request/result resources and acknowledge the current AI reporting profile plus opted-in milestone contract. Non-opted-in callers keep final-only reporting unchanged. Missing authorization is blocked, not a no-op; a legitimate no-op states why no external reporting is required.
