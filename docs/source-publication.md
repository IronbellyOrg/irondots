# Source publication — 2026-11-02

Canonical repository: https://github.com/IronbellyOrg/irondots

Six source packages are included: ClickUp 1.3.1 public export, the brownfield-aware specification generator, adaptive research, the Codex-to-dot porter, task-list 1.0.0, and Session Init 1.1.1. Export versions for packages without an explicit native semantic version are repository identifiers, not invented native releases.

## Intentional export differences

- Private workspace/channel/task/message identities and business names were removed from historical ClickUp validation examples; evidence scope and limitations remain.
- Account-specific native skill resource locators became public source links. Consumers must discover/read actual installed skills by name; a GitHub link is not a runtime locator or installation. Main-branch source links are intended post-merge references and may not resolve while this change is only on a draft branch.
- The named personal reviewer in one review instruction became “the user.”
- Source SHA-256 and exported SHA-256 per file are recorded in `source-export-manifest.json`; unchanged helper code retains exact bytes.
- Private continuity databases, logs, receipts, test captures, user notes, business spreadsheets and credentials are excluded.
- Distribution/license terms require maintainer review before a release; no open-source license is invented. Registry publication approval is false, so release packaging fails closed. Source publication is not release or installation.

## Runtime and compatibility limits

Session Init 1.1.1 includes the independently reviewed routing-ledger 1.0.1 compatibility repair. Native entrypoint, ledger and receipt-template readback passed; real voice-call acceptance remains pending. Its development task identity and private runtime resource locators are sanitized in this source export. The icon is the current local materialized asset, not a claim of candidate-byte parity. Task-list 1.0.0 source is installed and statically reviewed; actual native entrypoint/template readback and an installed-resource decision scenario passed. Live progress append/status verification remains separately pending; do not claim operational end-to-end completion. ClickUp 1.3.1 adds the reviewed opt-in task-list progress module and execution/0.2; no live progress mutation is proved by synthetic tests.

The specification generator and porter retain their named legacy reporting interface. As the ClickUp reporting profile specifies, publication requires actual acknowledgement of the current AI reporting/execution profile; source availability alone does not prove readiness.

## Validation

- Repository registry validation and 26 offline registry tests passed.
- Exported ClickUp helpers passed the existing local 110-test suite: 109 passed, one optional private-capture test skipped. Private tests/fixtures are not shipped.
- The ClickUp progress extension passed 18 focused synthetic tests. Task-list passed eight static contract checks; its exported test changes only the default root from an account-specific path to package-relative discovery.
- These checks do not certify live provider access, fresh runtime behavior, runner eligibility, branch protection or universal execution support.
- Self-hosted workflows retain organization/trusted-context guards; no workflow run, merge, release or deployment is implied by this source commit.

## ClickUp 1.3.1 follow-up

The typed task-update readback now explicitly requests both description and dependencies, matching the observed compact connector schema. Missing dependency details remain fail-closed; a count is not field-preservation proof. Exact code received independent review and regression coverage before this source update.
