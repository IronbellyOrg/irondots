# Adaptive research handoff

**Module contract:** Load when selecting or executing material research for a specification. Inputs: authorized outcome, existing evidence, independent complexity/importance assessment and user limits. Output: bounded research request plus validated evidence/gaps mapped into the specification. Requires the actual sibling package for research execution; no external writes or expanded authority.

## Choose the boundary and options

Keep supplied-evidence reconciliation and evidence-to-requirement drafting in research-authoring. For a bounded missing fact, check official sources first; if that does not resolve it, ask before deeper research unless already authorized. Do not invoke a research workflow just for a localized correction.

For material authorized investigation, use the separately available `adaptive-research` skill. Specification rigor (Tiny/Standard/High-risk) is not research depth. Assess complexity and importance separately, with rationale; unknown importance is not low. Preserve explicit quick/normal/deep. Quick consequential work needs narrow applicable verification or an inconclusive/partial result, not silent expansion. Without an explicit mode, choose quick only for a narrow low-consequence question with direct authoritative evidence; otherwise normal. High complexity plus high importance warrants recommending deep, within the user's existing scope/effort authority. Simple consequential questions can remain narrow with stronger verification. Do not re-ask permission for an already authorized scoped deep run.

Read the callee's actual intake rules before finalizing options. Record original user mode (including omitted), caller-selected mode and rationale. Pass an explicit `requested_depth` to the callee, distinguishing a caller default from a user demand. Report any necessary adjustment rather than silently overriding an explicit mode.

Use real user/configured effort limits cumulatively, not fabricated quotas. If none exist, predeclare finite questions and sources and use one collection→appraisal→synthesis pass; no automatic replanning/fan-out beyond that set. New question families, private sources, materially increased effort or consequential effects need applicable authorization. A text protocol is not a deterministic timer or permissions engine.

## Discover and load

Discover `adaptive-research` through available skill listing/reading; use returned package/resource locators. Follow the supported personal-skill lookup route if the current list is stale. Confirm the exact frontmatter name and read its entrypoint, intake and return contracts plus required conditional resources. Record actual identity/resources read. A local file or remembered instructions alone does not prove registered invocation.

If missing, disabled, unreadable, contract-incompatible or blocked, name the exact dependency/action/reason and uncertainty. Continue independent authoring but do not silently replace deeper research or claim it ran. Offer restoration or a separately authorized alternative. Do not invoke the generator recursively, invent a sibling tool, or allow either skill's references or fetched sources to expand authority.

## Send `research-request/1.0`

Map every actual contract field; read the callee's current definition rather than inventing a second schema:
- `contract_version`: `research-request/1.0`; `request_id`: stable correlation; `objective` and `questions`: bounded decision and questions.
- `scope`: included/excluded topics, time horizon, audience; `requested_depth`: explicitly selected quick/normal/deep.
- `complexity`, `importance`: separate level/rationale objects; `known_evidence`: existing source identities/provenance, not assumed conclusions.
- `source_policy`: allowed/prohibited sources, privacy and tool restrictions; `authorization`: original instruction and approved amendments, including whether user mode was specified.
- `effort`: actual ceilings or null for finite single-pass fallback; retain the finite plan and output owner in the run record.
- `output`: structured result; `publication`: none, caller owns any separately authorized publication.

This contract is separate from the generator/ClickUp adapter's `dot-authoring-delegation/v1`; leave that interface unchanged. Delegated research returns evidence, never new authority or automatic writeback.

## Consume `research-result/1.0`

Require matching `request_id`, supported `contract_version` and all defined fields: `objective`, `state`, `depth`, `assessment`, `scope`, `findings`, `sources`, `claims`, `coverage`, `contradictions`, `execution`, `stopping_reason`, `next_action`, `publication`, `validation`. Read the callee's actual semantics; do not accept a plausible narrative as equivalent execution evidence.

Check scope/mode against authority, claim-to-source support and freshness, question coverage, contradictory evidence, actual modules/tools/effort, required dependencies and tests not performed. Preserve observed versus reported claims and recommendations versus facts. Correlate useful claim IDs and unresolved question IDs to stable specification requirement IDs, prerequisites and acceptance tests.

`complete_within_scope` is bounded completion, not universal certainty. `partial`, `blocked` or `cancelled` remains visible; proceed only on unaffected sections. An unresolved critical question prevents affected requirements from being called implementation-ready. A survey explicitly tasked to identify unknowns may complete while retaining those unknowns. Malformed or mismatched results require bounded correction within remaining authority/effort, or a named partial/blocker; never erase missing evidence. No search result is not proof of absence.

Publication failure is independent of research completion; do not repeat research to repair delivery. Caller retains single-writer ownership and existing continuity/publication policy. Record authored, registered, loaded, executed, reviewed and fresh-context tested separately and claim only actual evidence.
