---
name: create-level-design
description: Create or reconcile evidence-backed level design documents from approved game mechanics, lore, research and concept art, with consistent structure, cross-discipline dependencies and review gates. Use for level-layout briefs, populated LDDs and comparisons; not game implementation, invented canon or automatic publication.
---

# Create level design

## Establish authority and inputs
Read the actual approved mechanics/lore/release sources and existing level document, if any. Record source IDs, versions/dates, approval state and missing inputs. Preserve accepted decisions, historical evidence, hypotheses, trial measurements and unknowns as distinct categories. Unread sources are not evidence. Conflict pauses the affected section, not independent work. Do not infer that a fresh generated document or imported wiki changes the date of underlying decisions.

Use the common [LDD template](assets/level-design-template.md) and [research basis](references/research-basis.md). For authorized new research, invoke the registered adaptive-research skill with bounded questions rather than inventing sources or copying inaccessible studio templates. This is a professional adaptable format, not a universal industry certification.

## Author one coherent design
1. Define the player's experience, objective, choices and observable completion/failure conditions; bind the release scope and exclusions.
2. Draw a zone graph and annotated spatial diagram with stable zone/route IDs. Separate exact approved dimensions, proposed trial values and uncalibrated inputs. Match critical/optional paths, commitment boundaries, sightlines and verticality to the beat sheet.
3. Populate the seven template sections in order. Keep engineering, art, design, narrative, QA and production dependencies explicit. Use role owners when actual people are unknown; never invent assignments, dates, estimates, engine budgets or sign-offs.
4. Describe state transitions with triggers, preconditions, resulting states and recovery/reset behavior. Test alternative player responses instead of prescribing a single inevitable action sequence.
5. Embed only actual permitted art. Caption each image with source identity, depicted mechanic, intended use and limitations. Art is illustrative, not playable geometry, balance proof or canon approval. Missing art remains pending; do not insert fake links or pretend it was embedded.
6. Link consequential lore/design claims to authority. New fiction is a proposal. Preserve narrative sequencing and routes that could bypass required comprehension.
7. Use the registered document/presentation/PDF skills for the requested format. Keep an editable source and perform actual render inspection; do not infer format quality from a successful file save.

## Validate and improve
Run `scripts/validate_ldd.py` on the Markdown authoring source. This checks only structure and declared identity/state; it does not establish design quality or playability. Independently compare diagrams, prose, tables, links, assets and source constraints. Review missing dependencies and contradictions.

When the request calls for the user's full review workflow, assign one independent reviewer per document. Have each verify template and format consistency, propose exactly five improvements, argue the strongest case for and against each, refine or reject suggestions, implement justified improvements, and revalidate. Preserve raw and improved versions plus evidence of decisions. Improvements cannot silently change approved mechanics, lore, scope or permissions. A rejected change is a valid outcome; five proposals do not require five unsafe edits.

Keep states separate: authored, static-validated, independently reviewed, human accepted, blockout tested, implementation ready. A document-only run cannot pass blockout or runtime gates. Record actual build/setup/observations only when supplied or tested with authorization.

## Compare two pipelines fairly
For comparison, freeze the same two briefs, source bundle, research, template and permitted art for both systems. Preserve raw outputs before revision. Use the [comparison rubric](references/comparison.md); blind identity where feasible. Distinguish first-pass quality from reviewer-assisted quality and generated claims from observed effects. Unknown tool cost/time remains unknown. Two examples support a conditional recommendation, not universal superiority.

## Resume, deliver and report
Keep a local `output/` checkpoint with source hashes, candidate identity, completed and pending effects, review and uncertainty. Preserve existing artifact identity/history where supported. On a source revision change, compare the actual prior and new source, identify impacted sections, diagrams, state tables, dependencies and tests, and preserve user edits and stable IDs. Pause only conflicting writes for owner resolution while independent updates continue. Record the delta and rerun affected checks before a new version. Resume failed delivery without replaying completed authoring.

Use the registered ClickUp skill's exact `dot-reporting/1.0` resource at `https://github.com/IronbellyOrg/irondots/blob/main/packages/clickup/references/reporting-protocol-v1.md`, plus its `assets/reporting-request.md` and `assets/reporting-result.md`, through supported skill discovery/reading. Define only destination, target, payload, acceptance, privacy and access parameters. Do not copy connector logic or fork the protocol. Follow local ledger → final evidence/payload → one authorized coordinator-owned final batch → bounded readback → durable receipt. No initial task or ongoing reporting writes are implied. Subskill return to its parent uses the protocol's justified no-op publication route; missing authority for intended publication is blocked, not successful no-op. If the resource cannot be read, keep independent local authoring possible but mark reporting readiness blocked.

No external publication, access changes, implementation, team messages, backlog creation or status changes are authorized merely by invoking this skill. Use actual caller authority and verified audiences for each effect.
