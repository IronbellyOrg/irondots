# Independent invariant and sufficiency probe

Load for normal/deep debates, consequential claims, or any claim that a proposed approach/fix alone achieves an outcome. Inputs: initially original sources, constraints and candidate artifacts; later only disclosed current-run debate, emerging consensus and relevant traces. Previous-run analysis stays withheld until verdict lock. Output: findings, coverage and limitations. No source execution or external effects.

Follow the two-stage reviewer barrier in [isolation](isolation.md). Start with `fork_turns: "none"` and retain a raw-source assessment before disclosing any current-run debate or emerging consensus. Log both phases and changes in findings. Use a fresh native internal reviewer that did not generate or advocate the candidate it reviews. Give raw evidence and the current candidate, not the desired verdict. A missing required reviewer yields partial/blocked. A quick consequential debate keeps a narrow independent check; if it cannot be performed, report the limitation rather than silently upgrade depth or declare success.

Probe applicable categories using domain-appropriate wording:
- State: what must persist, initialize or remain consistent?
- Guards: which preconditions, boundaries or validation steps protect the result?
- Counts: are quantity, index, threshold and inclusive/exclusive assumptions consistent?
- Collections: empty, singleton, maximum size, ordering and uniqueness.
- Interactions: do individually sound choices conflict in combination or order?
- Sufficiency: what downstream condition could defeat “this approach alone solves the problem”?

For sufficiency, enumerate intervening gates and cite actual sources. Read an available relevant branch trace and cite the specific branches; otherwise use source enumeration appropriate to the domain. No trace/source access means unverified sufficiency, not invented evidence. Zero findings must state checked coverage and limitations, not imply universal safety.

Record INV-ID, category, assumption/claim, addressed/unaddressed/unknown, severity, evidence and affected requirement. A high-severity critical unresolved finding blocks unconditional recommendation regardless of agreement. Medium/low findings stay visible proportionately. Recheck changed claims after a deep final round; do not demand a fresh whole-document attack for a localized correction. Preserve old IDs and record resolved/open/regressed findings.
