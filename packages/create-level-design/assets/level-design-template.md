# Level Design Document contract v0.1 — proposed reusable extension

This contract preserves the seven-section game template and its heading order. Template field names remain stable across options. Every field is filled, explicitly unknown with impact/owner, or not applicable with reason. No arbitrary mandatory page count. Optional appendices may hold detail; the overview stays concise.

Metadata: level_id; title; project/release; document_version; template_version; author/reviewer roles; lifecycle_state; generated_at; source_manifest[] (id, URL/path, actual revision/hash, source_updated_at or unknown, fetched_at, authority); changed_fields; unresolved_gaps. Never replace underlying source time with generation time.

## 1. Level design brief
Required: intended player experience in plain language; player objective; start/end state; success/failure; release scope/exclusions; design pillars and supporting decision IDs; level's contribution to game; audience/format; actual concept image with caption/alt text and source (or explicit pending).
Proportional: short narrative/location summary and critical canon links; broader economy context only if relevant release.

## 2. Learning and mechanic boundaries
Required mechanic matrix: mechanic_id | accepted/proposed/deferred/unknown | source | introduced/practiced/transferred zone | player choice | observable learning evidence | exclusion.
Required authority conflict register and teach/transfer sequence. Proposed ideas must not be promoted by a document editor.
Proportional: separate multiplayer/role variations only where in scope; R1/R2/R3 boundary notes for the target game.

## 3. Spatial layout and circulation
Required labelled diagram with legend, orientation, scale status, stable zone IDs, entrances/exits, route direction, local alternatives, commitments, sightlines, cover and gameplay boundaries. Beat IDs refer to these exact zones.
Metrics register: metric_id | approved/trial/unknown | units/value/range | constraint/source | validation owner/method.
For relevant levels: elevations/section views, pressure zones, exterior recovery envelope, collision/camera clearance, AI routes, streaming boundaries. Mark N/A rather than manufacture systems.

## 4. Encounter flow and pacing
Beat table: beat_id | zone | entering state | readable cue | permitted player choices | trigger | resulting state | tension intent | failure/recovery | exit condition | source/test links.
State contract: state_id | preconditions | transition/event | consequence | reset/persistence behavior | system dependency | unresolved decision.
Do not script an assumed single player solution. Include bypass, out-of-order interaction and resource-loss cases when applicable.

## 5. Interaction and sensory direction
Required: visual hierarchy, materials/lighting function, critical feedback and redundant cues; mechanic-specific art captions; art references versus geometry specification clearly separated.
Asset register: asset_id | function/zone/state | discipline | reuse/new/unknown | source/style constraint | variations | dependency | owner role | readiness.
Canon register: claim_id | approved source/revision | spatial expression | required/optional comprehension | conflict/proposal | reviewer role.
Proportional: audio/VFX/animation interaction tables, accessibility review, narrative beats, cinematics. No image merely decorative without explanatory purpose in mechanics documents.

## 6. Prototype scope and tuning
Dependency register: dependency_id | dependent zone/beat/asset/test | prerequisite | existing evidence/needed work | hard blocker/sequence/reference | owner role | readiness | resolution evidence.
Required: implementation boundaries, trial tunables, risks, mitigations, cut order and explicit exclusions; no fabricated estimates/deadlines.
Applicable engineering topics: collision, camera, navigation, dynamic geometry, event interfaces, authority/replication, save/reset, streaming, performance budgets and target hardware. Unknown implementation choices become questions, not implied decisions.

## 7. Validation and review handoff
Test register: test_id | requirement/beat | setup/build required | action | expected observable result | evidence | result (not_run/pass/fail/blocked) | owner role.
Coverage: approved requirement → zone/beat → dependency → acceptance test. Missing links block affected readiness.
Review record: template and formatting checks; source/lore/discipline consistency; five improvement proposals; strongest pro/con; revised proposal; adopt/reject rationale; changes; regression check.
Actual human sign-offs separate from agent review. Document readiness separate from blockout validated or implementation ready.
Include sources, change log, open decisions, requested next approval and publication receipt when one exists.

## Format and structural checks
Seven headings appear once in fixed order. IDs unique, references resolve, diagram and prose names agree, numerical units consistent, captions explain art applicability, tables readable, no overflow/clipping, searchable/editable source preserved, no raw internal paths in team-facing publication. Actual unavailable inputs remain visibly missing. If a slide deck is chosen, maintain the same section IDs plus appendix references; slides alone must not hide implementation detail.
