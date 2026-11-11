# Sanitized source publication

Canonical repository: https://github.com/IronbellyOrg/irondots

## 2026-11-11 synchronization

This snapshot contains nine custom skill source exports. The current source
inventory was compared against the prior export manifest before updating files.
Five packages already matched their recorded source hashes and retain their
existing sanitized exports: adaptive research, the specification generator,
Codex-to-dot porter, task-list and create-level-design.

The changed and added packages are:

- **ClickUp 1.3.3-public.1:** conditional profile-based writing validation, with
  the existing AI-first ownership, separate effect authorization and exact-text
  publication gates preserved. Project destinations are configuration, not
  author-specific defaults. Private pilot details and receipts are excluded.
- **Session Init 1.2.3-public.1:** current debate and writing routes, recipient
  history continuity and receipt guidance. The routing ledger is a reusable
  template requiring local adoption, not inherited permission for another user.
  Account-specific locators, routes and live briefing content are excluded.
- **Adversarial debate 1.1.0-public.1:** current source-only role briefing,
  independent statements, staged disclosure, verdict locking and structural
  validators. Only reusable templates and synthetic tests are included, never
  real debate prompts, source documents, run logs or verdicts.
- **write-as-ryan 1.2.0-generic.1:** a generic adaptation retaining its compatibility
  name. It does not reproduce a real person's voice. Private profile content,
  profile history and hashes, correspondence, feedback and evaluation outputs
  are excluded. Synthetic examples are not production evidence; a separately
  configured, authorized private profile is required for profile-based use.

These suffixes identify repository exports, not new native releases. Public
source links are not installed resource locators. Links targeting main for new
packages become available only after an authorized merge. Discover and read the actual
skills available in the consuming runtime. Optional writing/research/debate
routes remain conditional and must be resolved at their task boundary; merely
including a package does not activate its routing or grant effects.

## Provenance, privacy and release gates

The export manifest records source and export SHA-256 for included reusable
source files, and export hashes for new public-only files. Excluded private
profile identities and digests are not recorded. Helpers retain source bytes
unless an intentional adaptation is documented. Adversarial debate retains its
upstream MIT notice and public provenance. No additional open-source license
grant is invented for original or newly adapted material.

Publication approval flags remain false. Review and license clearance for a
packaged release are separate from this authorized source PR. There is no merge,
release, installation, deployment, runtime certification or live provider pilot
implied by the source export.

Private continuity stores, user notes, conversation history, connector receipts,
credentials, production IDs, task links and actual evaluations are not package
content. Historical commits and existing remote branches are not rewritten.
Publication uses the connected GitHub account's commit metadata.

## Validation scope

Run the repository validator and unit tests from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_registry.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The aggregate tests also run the bundled ClickUp, level-design, task-list,
adversarial-debate and generic-writing suites. These use offline synthetic
fixtures and local temporary files. Registry hashes and link checks establish
structure and file identity, not semantic correctness or live runtime behavior.
Verdict hashes provide tamper evidence, not enforced immutability. Writing
receipts are local checks, not proof of authority, delivery or authentic style.

Before publication, inspect the exact candidate diff, scan its full tree and
accessible public Git history with an offline secret scanner, and review
potential findings without transmitting candidate secrets to verification APIs.
Private source history is never imported into the public repository. Automated
scanning cannot guarantee the absence of every secret or identifying detail.

## Existing offline context-policy example

The five files under `examples/ironbrain-context-policy-model` remain unchanged.
They are an offline synthetic reference model, not a production ACL system,
AnythingLLM integration or deployment. Their README explains the limitations.
No automatic publication, access grant or ingestion is performed by the model.
