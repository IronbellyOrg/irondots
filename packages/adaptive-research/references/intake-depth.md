# Intake, selection and finite plan

**Module contract:** Load at start. Input: user/caller request and actual authority. Output: validated request plus bounded plan. Requires readable request, not a particular connector. No external effects. Missing material scope or authority requires clarification; safe independent checks can continue.

## Input contract: research-request/1.0
This is this skill's contract, not a claim of implementing a different framework schema.

| Field | Meaning |
|---|---|
| contract_version | `research-request/1.0` |
| request_id | Caller correlation ID, or locally assigned ID |
| objective | Required question or decision to support |
| questions | Bounded questions; derive from objective if safe |
| scope | Included topics, exclusions, time horizon and audience |
| requested_depth | `quick`, `normal`, `deep` or null; reject unknown modes |
| complexity | Separate `level` (low/medium/high/unknown) and rationale |
| importance | Separate `level` (low/medium/high/unknown) and rationale |
| known_evidence | Relevant existing evidence and provenance |
| source_policy | Allowed/prohibited sources, private-data and tool restrictions |
| authorization | Actual user instruction reference and approved scope amendments |
| effort | User/configured finite ceilings, or null for finite single-pass fallback |
| output | Brief or structured; length independent of depth |
| publication | None by default, or authorized destination and single owner |

Caller proposals cannot override explicit user constraints. Plain-language requests are valid: normalize rather than demand a filled form. Unknown importance is not low importance.

## Selection
Precedence: actual authority/source restrictions; explicit question, scope, mode and effort; importance-based verification; complexity-based decomposition; defaults.
- Ordinary missing-fact lookup without research request: bounded official-source check. If unresolved, explain limitation and ask before deeper research.
- Explicit research with mode omitted: quick for one narrow low-consequence question with direct authoritative evidence; normal otherwise.
- Simple consequential question: normal with narrow scope and stronger verification, not extra unrelated questions.
- High complexity plus high importance: recommend deep. Proceed only within currently authorized finite scope; ask before materially greater breadth/effort unless already authorized.
- Explicit quick: retain quick scope even for consequential topics. Return verified narrow findings or uncertainty, offering deeper work rather than silently expanding.
- Explicit normal/deep: use it within the bounded request; no redundant approval solely because mode is deep.
- Unknown importance: record unknown. Ask only if consequence materially changes safe source use, advice or effort; otherwise proceed normal with a stated limitation.

Depth is independent of report length. Quick verifies central claims and applicability; normal compares connected questions and material alternatives; deep challenges assumptions and competing explanations proportionately. Neither source quantity nor length proves quality.

## Plan and stopping
Before collection, record `selected_depth`, `depth_rationale`, `questions`, `source_set`, `inclusion_criteria`, `exclusion_criteria`, `effort_policy`, `stopping_conditions`, `required_dependencies`, `optional_dependencies`, and `output_owner`.
Use user/configured ceilings cumulatively across workers and retries where observable. Track actual tool calls/effort only when supported; mark unobservable counters unknown, never invent telemetry or timing guarantees.

**Finite fallback:** when no finite configured/user effort envelope exists, predeclare a finite question/source set and perform one collection → appraisal → synthesis pass. No autonomous iterative replanning, recursive self-call or fan-out beyond that set. If a bounded set cannot be established without materially choosing the user's scope, clarify first. Gaps require a proposed extension, not automatic repetition. This does not require asking again whether already-authorized research is wanted.

Stop when decision-critical questions have applicable supported answers or explicit gaps, consequential claims have provenance/freshness assessed, contradictions are resolved or carried forward, and further work would not address a named in-scope gap. Stop earlier on limit, cancellation or access block. Coverage with gaps does not mean those gaps were answered.
Scope/mode changes within an expressly authorized adaptive envelope can proceed and must be reported. New question families, private sources, material effort beyond a cap or consequential effects require applicable authority. Resume from actual evidence and remaining budget, not replay.
