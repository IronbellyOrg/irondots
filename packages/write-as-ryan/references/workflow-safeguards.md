# Workflow safeguards

Workflow **1.2.0** checks supplied artifacts when invoked. It is not a global
send interceptor. The profile version is independent of the workflow version.

## Profile configuration

Use a separately authorized private deployment root, outside the public source
checkout. Copy the two public Python helpers into its `scripts/` directory and
place the private manifest and profile in its `assets/` directory. Register or
reconcile that private deployment through the runtime's supported workflow.
Local file presence alone is not evidence of installation or registered loading.

The manifest must use `schema: personal-writing-manifest/1.0`, a three-part
numeric `active_version`, `resource: profile-v<active_version>.json`, and the
lowercase SHA-256 of the exact selected profile bytes. The profile must satisfy
`check_receipt.validate_profile`: schema/version; nonempty owner, status,
generated_at, source_date_range, retrieved_at, privacy and retention strings;
a boolean human_style_validated; nonempty precedence, gaps, excluded and
refresh_triggers string lists; nonempty core and observations rule arrays with
id/status/rule/scope; nonempty channels with status/guidance; recipient_overrides
list and purpose_overlays object. This is minimum structural validity, not proof
of adequate evidence. Preserve truthful empty-evidence limitations rather than
inventing observations to satisfy a schema. A placeholder observation may
explicitly state that no personal observation is available, with limited scope.
Never relabel generated or synthetic data as human evidence.

The demonstration under `examples/synthetic` is isolated test data. There is no
active profile at the public package root. **Do not copy the example profile into
a real personal deployment or claim that it grants any sending authority.**

## Entry and final reads

Read the actual generic writing and channel skills, this registered template,
then the current private manifest and its selected profile. Record actual
resource identity, version/hash and read evidence. Another writer's version is
a comparison hint, never your own read. If saved and registered versions conflict,
reconcile using a supported fresh context. Do not silently substitute a scratch
copy or call a cached reader proof of the latest release.

Before native use, reread the current manifest and relevant profile and check
latest instructions, account/channel/recipient/thread and replies. If changed,
prepare a new snapshot and review applicable differences. An unchanged previously
validated draft may retain its old profile basis only with the exact prior basis,
healthy current guide, retained old artifact and current context review. Changed
text never inherits that exception. Perform the [recipient-history check](recipient-history.md) and retain its actual private coverage evidence.

## Bounded handoff and resume

Pass actual current task input, exact strings/no-additions constraints,
authorship/purpose/channel, verified audience, actual permission evidence,
operation and uncertain-effect state, current registered skill identity, and
observed profile/version/hash as a comparison hint. Pass the minimal recipient
nuances and readable private source references needed. Avoid unnecessary sample
bodies. Include prior draft/receipt identity only if reusing exact text.

The receiving writer reads the current guide and latest relevant exchange itself,
reviews task-local history evidence, then returns exact final text and compact
private validation evidence. The coordinator independently checks the bytes and
scope before any separately authorized effect. On resume, recover real read and
validation evidence rather than trusting old status language. Reconcile uncertain
external effects before retry. A voice caller without execution can delegate
validation or clearly use the manual path, never claim remote script execution.

## Executable gate

Keep live working artifacts outside the installed package and public repository.
Use `python3 scripts/workflow_gate.py --help` for the CLI. With the correct private
root, the commands are:

```sh
python3 scripts/workflow_gate.py prepare --input task.json --context prepare-reads.json --root PRIVATE_ROOT > snapshot.json
python3 scripts/workflow_gate.py check --input task.json --context final-reads.json --snapshot snapshot.json --receipt receipt.json --draft draft.txt --root PRIVATE_ROOT
```

`task.json` uses `personal-writing-input/1.0`, a nonempty actual request, a
supported channel, and scope containing exactly purpose, account, recipient,
thread as nonempty strings. Include real constraints, not a fabricated digest
surrogate. Explicit not-applicable is valid only where actually true.

Context uses `personal-writing-context/1.0`, stage prepare/final, exact task-byte
input_sha256, matching channel/scope, latest_context_reviewed true, nonempty
latest_context_evidence, and registered_profile with observed version, sha256,
and actual read evidence. These are declarations, not authenticated read proofs.
The helper separately reads local bytes and checks consistency.

The full private receipt uses `personal-writing-receipt/1.0`, seven hard gates,
ten style dimensions with reasons, actual loaded rule IDs, exact input/profile/
draft hashes, permission scope and limitations. Hash the entire UTF-8 body without
normalization, including greeting, punctuation and signature. The final check
binds task, snapshot, receipt, context and guide and detects ordinary drift. Any
text change requires a new check. Account/audience/thread/context changes also
require renewed semantic and permission review. Do not append or rewrite after
validation. The standalone receipt CLI uses its own script parent as profile
root and accepts `--input`; use the workflow CLI for an explicit `--root`.

## Holds and exceptions

Unreadable guides, stale evidence, material mismatch or failed checks hold the
affected native effect. Correct and revalidate first. Only the user's informed
explicit agreement to a disclosed style limitation for exact unchanged text is a
style exception. Generic send approval is insufficient. Keep the actual question,
answer and draft identity privately. No style exception grants send authority or
waives identity, meaning, privacy, exact strings, current context or channel gates.

`check --exception-only` omits a snapshot and requires actual local-guide failure,
valid input/final context, registered_profile status unavailable with evidence
and limitation, exact informed style-exception evidence, and all hard gates.
A healthy guide cannot use this path to bypass stale preparation. If only the
registered reader is unavailable, use a clearly labeled manual exception review
rather than claiming that healthy local files are absent.

Without execution, explicitly perform equivalent source/manifest/hash, input/
scope, exact-text, seven-gate and ten-dimension checks through supported tools.
Label them manual. If evidence or required comparison is missing, hold the effect
or seek the narrow style-only exception where permitted. Never invent hashes,
reads, consent or checks. A hash does not measure quality or prove authorization.

## Evidence and limits

Private results should identify workflow/profile versions and hashes, exact task/
draft identities, actual reads, origin, method, pass/hold/exception and limitations.
Do not attach receipts to ordinary outgoing messages. Unsigned caller-controlled
snapshots and declarations can be forged; neither helper authenticates them,
semantics, user consent or transport state. There is no atomic send interlock.
For ClickUp, its authorized AI/domain route and supported pre-publication staging
remain mandatory. A local pass cannot substitute native mutation, authorize
profile disclosure or retroactively validate published text.
