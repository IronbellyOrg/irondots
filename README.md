# irondots

Canonical repository: [IronbellyOrg/irondots](https://github.com/IronbellyOrg/irondots).
Clone via HTTPS: `https://github.com/IronbellyOrg/irondots.git`, or via SSH:
`git@github.com:IronbellyOrg/irondots.git`.

A small, public-safe registry and packaging contract for reviewed skill packages.
This is repository infrastructure, **not a dot installer or runtime certification
service**. The registry contains sanitized source exports, not installed runtime packages.
Private conversations, customer data, connector receipts and live evaluation
outputs are excluded. See [source publication](docs/source-publication.md).

## Local checks

Python 3.10 or newer is required. No third-party Python dependencies are needed.

```sh
python3 scripts/validate_registry.py
python3 -m unittest discover -s tests -v
```

The validator checks the [local registry contract](docs/registry-contract.md),
explicit file hashes, declared dependencies, relative Markdown destinations and
package boundaries. Unit tests use synthetic offline fixtures; they do not prove
that any skill executes correctly in dot, Codex or another runtime.

## Workflow boundaries

Registry validation and manual gated release are intended to run on the
organization's self-hosted runners. Public fork pull requests must never execute
code on those runners. Consult the committed workflow files for exact triggers
and job guards; do not infer runner registration, repository access or protection
settings merely from a `runs-on` declaration.

A release candidate is built from an explicit package file allowlist. Empty
registries and packages without recorded publication approval are rejected.
A workflow-created draft release is not permission to publish it or install it.
Actual runtime acceptance, privacy review and final publication are separate
checks by the responsible maintainer.

See [release preparation](docs/release-process.md) for the local packaging command
and the gates that must remain distinct.
