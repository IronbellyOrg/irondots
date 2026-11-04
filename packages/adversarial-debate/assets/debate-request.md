# Request contract

Use `dot-adversarial-request/1.0`. Natural-language input is valid; normalize it rather than demand a filled form. Preserve nulls with reasons, reject unknown versions/modes, and never invent authority.

Required fields:
- contract_version; request_id; parent_run_id (null for direct use).
- objective; decision_question; audience.
- authority: original request/provenance, caller chain, allowed_effects, restrictions, amendments and cancellation state.
- mode: compare or generate_compare.
- artifacts: compare requires 2–10 records with ID, content/accessible locator, source type, revision/hash or dated snapshot, and read_coverage. For generate_compare this may initially be empty.
- generation: null for compare; otherwise source/brief, requested artifact type and 2–10 perspectives, with explicit supported model choice only if requested.
- constraints; criteria; focus: explicit decision basis and gaps; preserve non-negotiable gates.
- depth: quick, normal or deep. Omitted becomes normal; source `standard` can be normalized to normal only with the alias recorded.
- evidence_policy: allowed/excluded sources, freshness, privacy, known evidence and research authority.
- output: recommendation by default or requested merged_draft; authorized destination or null.
- mask_authorship: boolean, default false.
- interaction: requested decision checkpoints; silence never supplies required approval.
- effort: real bounds or null plus finite topic/source/variant/round plan.
- resume: prior run/checkpoint and changed inputs, or null.

Generation preflight validates planned count/brief before dispatch; artifact preflight validates actual surviving outputs before debate. No result or caller suggestion supplies missing permission.
