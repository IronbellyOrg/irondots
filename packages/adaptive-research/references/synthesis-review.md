# Synthesis, review and return

**Module contract:** Load before output. Input: actual plan and evidence ledger. Output: truthful research result. Required dependencies: consequential claim evidence and any explicitly required review; optional persistence is not required for research completion. Only the authorized output owner publishes.

Answer the objective first. Tie consequential claims to sources or explicit gaps. Separate recommendations from findings, show material alternatives and uncertainty, and state what would change the conclusion. No numeric confidence without a justified method; no source-count proxies for truth. A required independent review must actually occur, not be renamed self-review.

## Result contract: research-result/1.0
| Field | Meaning |
|---|---|
| contract_version | `research-result/1.0` |
| request_id | Input correlation ID |
| objective | Actual supported decision/question |
| state | `complete_within_scope`, `partial`, `blocked`, or `cancelled` |
| depth | Requested, selected and rationale |
| assessment | Separate complexity and importance objects |
| scope | Actual included/excluded scope and amendments |
| findings | Claim IDs and conclusions; recommendations explicitly separate |
| sources | Evidence protocol source ledger |
| claims | Evidence protocol claim ledger |
| coverage | Question states, supporting claim IDs and gaps |
| contradictions | Resolved and unresolved material conflicts |
| execution | Actual skill identity/resource; modules read and skipped with reasons; tools used; observable effort, limits and remaining budget, or unknown with reason |
| stopping_reason | Actual coverage, limit, access, cancellation or other stop |
| next_action | Bounded proposal, whether new authorization is needed |
| publication | `not_requested`, `pending`, `verified`, `failed`, or `uncertain`; actual artifact/readback receipts only |
| validation | Checks actually performed, outcomes and unexecuted cases |

For skill callers return the structured fields with stable claim IDs; do not collapse away uncertainty or actual execution evidence. For chat, use a proportionate readable summary, keeping consequential sources, coverage limits and stopping state. Load report template only when useful/requested, not automatically for a tiny question.

`complete_within_scope` means the authorized bounded objective was met, not universal certainty. An unresolved critical question required by the objective means partial/blocked, not complete. A bounded survey can be complete while explicitly identifying unknowns when identifying those unknowns is the objective. No search result is not evidence of absence.

## Authorized storage
No automatic file, ClickUp task, message or artifact creation. If saving is authorized, use the established private central destination and broad category, preserve existing artifact identity, and read back to verify. Parent/caller is the single writer unless explicitly delegated. Native persistent storage is preferred; Git/ClickUp fallback requires an observed limitation and appropriate authority.
Publication failure is separate from research state: report exact action/target/reason and whether denied, pending or uncertain. Reconcile uncertain writes before retrying; do not redo research merely because delivery failed.
Authored, saved, registered, loaded, executed, reviewed and fresh-context tested are distinct; claim each only with actual evidence.
