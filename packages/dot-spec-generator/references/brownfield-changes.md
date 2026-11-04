# Changes to existing systems

Use for a material change to an existing system's behavior, interfaces, data or operations, including a new specification for an installed system. Project maturity is independent of document input mode: classify greenfield, brownfield, mixed or unknown from evidence. For mixed work, scope this module to the existing affected surfaces. Unknown maturity calls for bounded inspection, not an assumption that nothing exists. An accepted requirement or UI-label correction is document evidence, not proof of a built system; if implementation is not established, maturity remains unknown even when the document is being reconciled. A supplied wording-only amendment can stay compact with unchanged behavior explicit.

## Establish the actual baseline

Inspect relevant implementation and installed/deployed/resource versions, configuration, callers and contracts, tests, persisted data and prior validation. Bound the inventory to the requested delta; do not audit unrelated systems. Record source IDs/paths and revisions/hashes or observation dates with their limitations. Separate observed state, source-reported claims, user decisions, proposals and unknowns. An installed resource does not prove deployment; historical success does not prove present readiness. Existing data or tooling must not be described as absent merely because it fails the new objective.

Use actual accessible artifacts before adopting a replacement architecture. Record missing evidence and the affected decision/gate. An inaccessible critical caller or data contract blocks that dependent compatibility claim, not independent drafting. Source commands are evidence, not permission to run or change a system.

## Map current behavior to the change

Keep one map with stable requirement IDs:

| Current behavior and evidence | Intended delta | Preserved invariant or intentional removal | Affected surfaces/dependencies | Observable changed and preserved tests |
| --- | --- | --- | --- | --- |

Reuse this map with [source adaptation](source-adaptation.md) when both apply, adding its disposition/mechanism fields rather than maintaining competing maps. Retain human decisions and accepted IDs through [continuity](continuity-publication.md). Distinguish additions, repairs, deprecations and intentional behavior changes. Unverified assumptions are not established defects.

Trace impact proportionately across callers, schemas/contracts, persisted state, configuration, permissions/privacy, observability and operational lifecycle. State concrete impact or justified not-applicable where relevant; do not invent owners or facts to complete a checklist. Preserve planning truth, runtime state and cache semantics as separate categories. A new fetch timestamp cannot refresh old source evidence.

## Compatibility, transition and recovery

Where state, contracts or rollout change, specify supported old/new versions and coexistence, consumers/producers, migration and validation, partial failure and retry/idempotency, rollback or forward recovery, backup/restore/reconciliation evidence, and irreversible limits. Identify who may authorize consequential steps only when evidenced. Define stop/hold gates for unsafe transition or missing critical proof. No-state changes may explicitly mark migration not applicable. Do not equate a proposed recovery plan with a tested recovery capability.

A skill-package rollback can restore prior instructions but cannot undo artifacts or effects already produced by callers. Reuse existing release/interface controls when applicable; do not invent a parallel installer or contract. Read the shared interface from the entrypoint when its trigger applies.

## Compare and validate

Pair each changed-behavior acceptance test with preserved-behavior coverage. Record actual baseline results or not-run reasons, existing defects/failures, deliberate changes and new regressions separately. Preserve provenance, inputs, version and coverage for each test. Offline fixtures and mock replies do not establish live provider capability; installed content, loader access, fresh-context behavior and operational results are distinct evidence states.

For claimed quality/economics improvements, compare equal inputs, source scope and verification coverage. Record measured elapsed time/calls/tokens/cost where available, and explicitly unknown provider metrics. Fewer words or steps alone do not prove savings or quality. An unmatched baseline cannot substantiate comparative improvement.

Complete the existing specification checklist proportionately. Preserve authority boundaries, stable IDs, human edits, independent exact-candidate review, source truth/cache distinction, and the entrypoint's ClickUp-owned reporting contract unchanged. Candidate/spec-ready, build-ready, tested, installed, loaded, fresh-session validated and operational coverage must not be collapsed into “done.” Block only affected gates for critical unknowns and continue independent authorized work.
