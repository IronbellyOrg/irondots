# <Action-oriented title>

- List ID: <stable logical ID>
- Space file ID / expected version: <identity / read version; pending only before first create>
- Intent and source: <outcome; source IDs/version; authorization>
- Scope: <included work; explicit exclusions>
- State: <backlog | in_progress | blocked | done | cancelled>
- Coordinator / updated_at: <known owner; actual checkpoint time>
- Next permitted action: <one concrete step>
- Blockers: <none or exact gap>

| ID | Action | State | Owner / dependency | Acceptance check | Evidence / result / blocked next action |
|---|---|---|---|---|---|
| T1 | <action> | backlog | <known or unknown> | <observable outcome> | <not yet tested> |

## Mirror checkpoint
- Workspace / destination / sibling task IDs: <verified IDs or precise pending reason>
- Row remote IDs: <only where existing checklist/subtasks apply>
- Source status / owner / due date / dependencies: <observed values or unknown>
- Source updated_at / fetched_at: <separate actual times or unknown>
- Last successful sync: <verified time or never>
- Operation / payload identity: <durable receipt reference>
- Sync health and uncertain effects: <verified | pending | failed | uncertain; exact gap>
- Next permitted recovery: <reconcile before retry if uncertain>

## Resume checkpoint and history
<Verified work, remaining checks, human edits/conflicts, authorized scope removals with rationale. Keep raw/private logs out.>

## Completion
<Only after checks: completed_at, acceptance evidence, verified mirror result, same-ID folder move receipt. Preserve this history when reopened.>
