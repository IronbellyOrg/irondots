"""Offline, fail-closed Session Init reconciliation planner. Never sends or writes state."""
import argparse
from collections import Counter
import json
import sys

VERSION = "dot-ledger-reconciliation/0.1"
FIELDS = {"owner_ids", "due_date", "priority", "dependency_ids", "title"}
STATES = {"todo", "in progress", "done", "cancelled"}
KEYS = ("workspace_id", "list_id", "task_id")
CAP_CHECKS = ("independently_verified", "effects_known", "readback_supported")
AUTH_CHECKS = ("explicit_user_status_decision", "scope_current", "transition_allowed")


def _identity(value):
    return isinstance(value, dict) and all(isinstance(value.get(k), str) and value[k].strip() for k in KEYS)


def _bound(record, link):
    return _identity(record) and all(record[k] == link[k] for k in KEYS)


def _ref(value):
    return isinstance(value, str) and bool(value.strip())


def _guard(record, link, checks, baseline, before, after):
    return (_bound(record, link) and all(record.get(k) is True for k in checks)
            and _ref(record.get("evidence_ref"))
            and record.get("baseline_ref") == baseline
            and record.get("before") == before and record.get("after") == after)


def _row(item, id_count, link_count, invocation_id):
    item_id, link = item.get("item_id"), item.get("link")
    out = {"item_id": item_id, "state": "blocked", "reason": "", "pull": {}, "push": None, "unknown_fields": []}
    def result(state, reason):
        out.update(state=state, reason=reason)
        return out

    if not _ref(item_id) or id_count != 1:
        return result("conflict", "invalid or duplicate local item identity")
    if item.get("in_approved_scope") is not True:
        return result("excluded", "not within approved branch/scope")
    if not _identity(link):
        return result("unmatched", "no verified workspace/list/task mapping; never match by title")
    if link_count != 1:
        return result("conflict", "multiple rows share canonical task; reconcile before any effect")
    remote = item.get("remote")
    if not (_bound(remote, link) and remote.get("independently_verified") is True
            and remote.get("invocation_id") == invocation_id
            and _ref(remote.get("evidence_ref")) and _ref(remote.get("revision"))):
        return result("blocked", "missing/failed/mismatched current ClickUp observation")
    if item.get("uncertain_effect") is not False:
        return result("blocked", "reconcile unresolved or unknown write first")
    mapping = item.get("status_map")
    if (not _bound(mapping, link) or mapping.get("verified_for_list") is not True
            or not _ref(mapping.get("evidence_ref"))):
        return result("blocked", "exact ClickUp list status mapping is unverified")
    read_map, write_map = mapping.get("pull"), mapping.get("push")
    if (not isinstance(read_map, dict) or not isinstance(write_map, dict)
            or any(not isinstance(v, str) or v not in STATES for v in read_map.values())
            or any(k not in STATES or not isinstance(v, str) or read_map.get(v) != k
                   for k, v in write_map.items())):
        return result("blocked", "invalid or non-roundtripping status mapping")
    current_raw = remote.get("status")
    remote_state = read_map.get(current_raw) if isinstance(current_raw, str) else None
    local_state = item.get("local_status")
    if not isinstance(local_state, str) or local_state not in STATES or remote_state is None:
        return result("blocked", "unmapped local or observed ClickUp status")
    base = item.get("baseline")
    if base is not None and (not _bound(base, link) or base.get("verified") is not True or not _ref(base.get("receipt_ref"))
            or not isinstance(base.get("status"), str) or base["status"] not in STATES
            or not isinstance(base.get("raw_status"), str)
            or read_map.get(base["raw_status"]) != base["status"]):
        return result("blocked", "last common verified baseline is corrupt, stale mapping, or mismatched")

    # Nonstatus fields are ClickUp-owned and only update its private projection.
    # Null means observed absence; a missing/non-verified field is not a clear.
    fields = remote.get("fields")
    local_projection = item.get("local_projection")
    if not isinstance(fields, dict):
        fields = {}
    if not isinstance(local_projection, dict):
        local_projection = {}
    out["unknown_fields"] = sorted(FIELDS - {name for name, o in fields.items()
                                            if isinstance(o, dict) and o.get("known") is True and "value" in o})
    for name, observation in fields.items():
        if (name in FIELDS and isinstance(observation, dict) and observation.get("known") is True
                and "value" in observation and
                (name not in local_projection or local_projection[name] != observation["value"])):
            out["pull"][name] = observation["value"]

    if base is None:
        if local_state != remote_state:
            return result("conflict", "no prior common baseline and current statuses disagree")
        if remote_state in {"done", "cancelled"} and not _ref(remote.get("terminal_evidence_ref")):
            return result("blocked", "terminal remote state lacks exact task evidence")
        return result("bootstrap_candidate", "first agreed status; establish baseline only after verified local save")

    base_state = base["status"]
    remote_changed = current_raw != base["raw_status"]
    if local_state == remote_state:
        if remote_changed and remote_state in {"done", "cancelled"} and not _ref(remote.get("terminal_evidence_ref")):
            return result("blocked", "terminal remote state lacks exact task evidence")
        state = "converged" if local_state != base_state or remote_changed else "unchanged"
        if out["pull"]:
            state = "pull"
        return result(state, "status agrees; no outbound write")
    if local_state == base_state:
        if remote_state in {"done", "cancelled"} and not _ref(remote.get("terminal_evidence_ref")):
            return result("blocked", "terminal remote state lacks exact task evidence")
        out["pull"]["status"] = remote_state
        return result("pull", "ClickUp status changed; preserve local-only fields")
    if remote_changed:
        return result("conflict", "both sides changed differently; neither status is overwritten")
    target = write_map.get(local_state)
    if not target:
        return result("blocked", "no exact outbound mapping for this transition")
    authority = item.get("authority")
    if local_state == "done" and (not isinstance(authority, dict) or not _ref(authority.get("completion_evidence_ref"))):
        return result("blocked", "terminal success lacks accepted completion evidence")
    if not _guard(authority, link, AUTH_CHECKS, base["receipt_ref"], current_raw, target):
        return result("blocked", "no current exact authorization for this local status transition")
    if not _guard(item.get("capability"), link, CAP_CHECKS, base["receipt_ref"], current_raw, target):
        return result("blocked", "no typed exact-transition capability/readback evidence or known effects")
    out["push"] = {**{k: link[k] for k in KEYS}, "from": current_raw, "to": target,
                   "revision": remote["revision"], "baseline_ref": base["receipt_ref"],
                   "authority_ref": item["authority"]["evidence_ref"],
                   "capability_ref": item["capability"]["evidence_ref"]}
    return result("push_candidate", "plan only; reverify exact preconditions through ClickUp route")


def plan(request):
    if not isinstance(request, dict) or request.get("contract_version") != VERSION:
        raise ValueError("unsupported reconciliation request")
    items, invocation_id = request.get("items"), request.get("invocation_id")
    if (request.get("trigger") != "manual" or not _ref(invocation_id)
            or not isinstance(items, list) or not all(isinstance(x, dict) for x in items)):
        raise ValueError("explicit manual invocation and actual item inventory required")
    ids = Counter(x["item_id"] for x in items if _ref(x.get("item_id")))
    tasks = Counter((x["link"]["workspace_id"], x["link"]["task_id"]) for x in items if _identity(x.get("link")))
    rows = [_row(x, ids.get(x.get("item_id"), 0) if _ref(x.get("item_id")) else 0,
                 tasks[(x["link"]["workspace_id"], x["link"]["task_id"])] if _identity(x.get("link")) else 0,
                 invocation_id) for x in items]
    counts = dict(Counter(x["state"] for x in rows))
    partial = request.get("scope_inventory_complete") is not True or any(
        x["state"] in {"blocked", "conflict", "unmatched"} or x["unknown_fields"] for x in rows)
    return {"contract_version": VERSION, "invocation_id": invocation_id,
            "state": "plan_only", "coverage": "partial" if partial else "complete_within_scope",
            "counts": counts, "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=argparse.FileType("r"))
    args = parser.parse_args()
    try:
        result = plan(json.load(args.request))
    except (ValueError, TypeError) as exc:
        parser.exit(2, f"Invalid reconciliation input: {exc}\n")
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
