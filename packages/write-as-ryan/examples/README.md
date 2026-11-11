# Synthetic offline example

Every fact, identity, date, rule and declaration here is fictional. The example
states: “The sample tray contains 6 square tiles.” It is not copied from personal
correspondence, style preferences, feedback or evaluation outputs. The isolated
profile has version 0.0.0 solely to exercise the existing numeric version schema.
Its manifest SHA-256 identifies only these synthetic bytes, not a private profile.

Run from the repository root:

```sh
python3 -B packages/write-as-ryan/examples/run_synthetic.py
python3 -B -m unittest discover -s packages/write-as-ryan/tests -v
```

The [example runner](run_synthetic.py) copies both unchanged helper scripts and
the [synthetic manifest](synthetic/assets/profile-manifest.json) and
[profile](synthetic/assets/profile-v0.0.0.json) into a temporary root. It builds
clearly labeled fictional task/context/receipt/draft files, invokes the real
`prepare` and `check` CLIs and the standalone receipt CLI, then demonstrates a
changed-draft hold. Temporary working artifacts are deleted when the run exits.
Only source fixtures are shipped; generated receipts and snapshots are not.

The checker is intentionally a send-gate checker. Its positive branch requires
`mode: send-authorized`, true eligibility and pass declarations. The fixture uses
those values **only to test parser and consistency behavior**. It explicitly
prohibits sending, carries no real permission, and proves that the helpers cannot
authenticate consent or truth. Never transfer its declarations to a real task.
A genuine draft-only request must keep draft-only/false and correctly remains
ineligible for sending.

The negative tests cover missing guides, corrupt JSON, input/profile/draft drift,
scope/channel disagreement, booleans, all hard gates and rubric dimensions,
unknown rules, version retention, exact style exceptions and unavailable-guide
exception boundaries. No connector or external communication is used. Passing
these tests does not validate voice quality, live integrations or native loading.

For real use, follow [private profile configuration](../references/workflow-safeguards.md)
and the actual channel's permission requirements. Do not replace the fictional
public fixtures with a real profile or evidence.
