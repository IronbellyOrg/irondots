# Capability and caller adapter

**Module contract:** Load for tool selection, caller handoffs or access errors. Input: request, actual tool metadata and failures. Output: feasible source plan or exact blocker. No new permissions or external effects.

Inspect actual tool schemas, formats, authorization and availability. Do not inherit MCP names, model names, execution paths or installation claims from source templates. Required capabilities are readable request/evidence, a ledger and cited synthesis; connectors, media, delegation and persistence are optional unless the particular request makes them required. Media processing requires explicit scope and actual capability.

Distinguish absent capability, inaccessible resource, denied action, missing authentication, quota, transient failure and uncertain execution. Do not bypass restrictions, change credentials or repeatedly replay an uncertain write. Reconcile uncertain state before retrying; retry a known denial only on materially new authority/evidence. Report completed work and exact remaining blocker.

Skill callers discover the actual registered skill, read its entrypoint, then pass `research-request/1.0`. Merely naming a skill or recalling its protocol is not native invocation. If missing, report the dependency unavailable; do not invent installation, a sibling skill or a successful execution. Never invoke adaptive-research recursively. Caller owns final artifact; this skill returns `research-result/1.0` without automatic publication.
Native persistence is preferred where available. External storage is a fallback for an observed limitation, not an assumed requirement. Metadata does not enforce tool permissions, context eviction, timing, permanent agents or model selection.
