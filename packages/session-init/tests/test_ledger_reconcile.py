from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ledger_reconcile import plan, VERSION, FIELDS

L = {"workspace_id": "fake-w", "list_id": "fake-l", "task_id": "fake-t"}
MAP = {"To Do": "todo", "Progress": "in progress", "Complete": "done", "Cancelled": "cancelled"}


def row(**overrides):
    return {"item_id": "fake-item", "in_approved_scope": True, "link": dict(L),
            "local_status": "todo",
            "local_projection": dict.fromkeys(FIELDS),
            "uncertain_effect": False,
            "remote": {**L, "invocation_id": "test", "status": "To Do", "revision": "r", "independently_verified": True,
                       "evidence_ref": "remote", "fields": {f: {"known": True, "value": None} for f in FIELDS}},
            "baseline": {**L, "status": "todo", "raw_status": "To Do", "verified": True, "receipt_ref": "last"},
            "status_map": {**L, "verified_for_list": True, "evidence_ref": "map",
                           "pull": dict(MAP), "push": {v: k for k, v in MAP.items()}}, **overrides}


def request(*rows, **kw):
    return {"contract_version": VERSION, "trigger": "manual", "invocation_id": "test",
            "scope_inventory_complete": True, "items": list(rows), **kw}


class ReconciliationTests(unittest.TestCase):
    def disposition(self, r):
        return plan(request(r))["rows"][0]

    def test_exact_no_op(self):
        o = plan(request(row()))
        self.assertEqual((o["state"], o["coverage"], o["counts"]), ("plan_only", "complete_within_scope", {"unchanged": 1}))
        self.assertIsNone(o["rows"][0]["push"])

    def test_pull_remote_closure_and_explicit_clear(self):
        r = row()
        r["local_projection"]["due_date"] = "2026-01-01"
        r["remote"].update(status="Complete", terminal_evidence_ref="closed exact task")
        self.assertEqual(self.disposition(r)["pull"], {"status": "done", "due_date": None})

    def test_remote_terminal_without_evidence_blocks(self):
        r = row()
        r["remote"]["status"] = "Complete"
        self.assertEqual(self.disposition(r)["state"], "blocked")

    def test_conflict_even_if_remote_newer(self):
        r = row(local_status="done")
        r["remote"].update(status="Progress", revision="newest")
        self.assertEqual(self.disposition(r)["state"], "conflict")
        self.assertIsNone(self.disposition(r)["push"])

    def authorized(self):
        bound = {**L, "before": "To Do", "after": "Progress", "baseline_ref": "last", "evidence_ref": "exact"}
        return row(local_status="in progress",
                   authority={**bound, "explicit_user_status_decision": True, "scope_current": True, "transition_allowed": True},
                   capability={**bound, "independently_verified": True, "effects_known": True, "readback_supported": True})

    def test_outbound_only_candidate(self):
        o = self.disposition(self.authorized())
        self.assertEqual(o["state"], "push_candidate")
        self.assertEqual((o["push"]["from"], o["push"]["to"]), ("To Do", "Progress"))

    def test_aba_remote_raw_status_change_bars_push(self):
        r = self.authorized()
        r["status_map"]["pull"]["Backlog"] = "todo"
        r["remote"]["status"] = "Backlog"
        self.assertEqual(self.disposition(r)["state"], "conflict")

    def test_nontransferable_capability_and_authority(self):
        for field, key, value in [("authority","list_id","bad"),("authority","scope_current",False),
                                  ("capability","task_id","bad"),("capability","after","Complete"),
                                  ("capability","effects_known",False),("capability","baseline_ref","old")]:
            with self.subTest(field=field,key=key):
                r=self.authorized()
                r[field][key]=value
                self.assertEqual(self.disposition(r)["state"], "blocked")

    def test_partial_missing_independent_field_never_clears(self):
        r=row()
        r["local_projection"]["due_date"]="2026-01-01"
        del r["remote"]["fields"]["due_date"]
        x=plan(request(r))
        self.assertEqual(x["coverage"],"partial")
        self.assertNotIn("due_date",x["rows"][0]["pull"])

    def test_uncertainty_blocks_replay(self):
        r=self.authorized()
        r["uncertain_effect"]=True
        self.assertEqual(self.disposition(r)["state"], "blocked")

    def test_same_result_does_not_push_again(self):
        r=self.authorized()
        r["remote"]["status"]="Progress"
        self.assertEqual(self.disposition(r)["state"],"converged")
        self.assertIsNone(self.disposition(r)["push"])

    def test_unknown_links_and_scope_are_not_enlarged(self):
        a=row(link=None)
        b=row(in_approved_scope=False,item_id="other")
        o=plan(request(a,b))
        self.assertEqual(o["counts"], {"unmatched":1,"excluded":1})

    def test_same_canonical_id_conflict_across_records(self):
        self.assertEqual(plan(request(row(),row(item_id="duplicate")))["counts"],{"conflict":2})

    def test_missing_baseline_agreement_not_completed_sync(self):
        self.assertEqual(self.disposition(row(baseline=None))["state"], "bootstrap_candidate")
        self.assertEqual(self.disposition(row(baseline=None,local_status="done"))["state"], "conflict")

    def test_no_background_event_or_unknown_inventory_claim(self):
        with self.assertRaises(ValueError):
            plan({**request(row()), "trigger": "call_connected"})
        self.assertEqual(plan({**request(row()),"scope_inventory_complete":False})["coverage"], "partial")

    def test_replayed_observation_requires_new_read_even_if_revision_is_same(self):
        item = row()
        replay = {**request(item), "invocation_id": "new-invocation"}
        rejected = plan(replay)
        self.assertEqual(rejected["coverage"], "partial")
        self.assertEqual(rejected["rows"][0]["state"], "blocked")
        item["remote"].pop("invocation_id")
        self.assertEqual(plan(replay)["rows"][0]["state"], "blocked")
        item["remote"].update(invocation_id="new-invocation", evidence_ref="new-read-proof")
        self.assertEqual(plan(replay)["rows"][0]["state"], "unchanged")

    def test_wrong_identity_fails_closed_without_poisoning_independent_rows(self):
        bad=row()
        bad["remote"]={**bad["remote"],"task_id":"other"}
        good=row(item_id="good",link={**L,"task_id":"yet-another"})
        for key in ("remote","status_map","baseline"):
            good[key]={**good[key],"task_id":"yet-another"}
        result=plan(request(bad,good))
        self.assertEqual(result["counts"],{"blocked":1,"unchanged":1})


if __name__ == "__main__":
    unittest.main()
