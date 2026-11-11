# Batch plan
Inputs: reviewed candidates, actual user instructions, source baselines and canonical work identity. Outputs: frozen versioned exact approval view plus local contract validation. No external effects.

For human replies or comments explicitly written as the profile owner, first apply [personalized writing](personalized-writing.md); ordinary task fields and dot reports do not acquire that authorship. Keep the exact validated content bound to the frozen approval view.

Use dot-approved-batch/0.1. Assign stable batch/action/attempt IDs. Plan only human message replies, narrow task-field updates and task comments; other kinds are unsupported pending separately reviewed capability. Human and agent recipients are not interchangeable. Record notifications/automations or unknown side effects. Never replace a human-edited body wholesale without safe guard and explicit authority. Use a DAG: prerequisites must be verified before dependent effects, not merely accepted.

Show target and recipient, exact content or before/after field changes, dependencies and consequential effects. Approval must cite an actual user instruction covering this version and exact scope. Freeze its fingerprint with the helper; a changed payload, recipient, target, dependency, baseline or scope revision invalidates the affected approval. Read-only preparation may continue without approval. Review and approval are not execution.

Before any future effect, load execution-gates and re-read pertinent live state. Current release intentionally blocks dispatch. Preserve verified/uncertain/failed actions and all prior attempts across resumes. Never infer successful execution from status prose, historical workers or a Brain claim. Cancellation stops undispatched actions; it cannot unsend or cancel already dispatched remote effects. In-flight ambiguity remains uncertain pending reconciliation.
