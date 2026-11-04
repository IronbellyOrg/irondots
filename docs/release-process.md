# Release preparation and publication gates

Registry validation, release candidate creation, draft release creation, final
publication and runtime installation are distinct outcomes. Do not report a
later stage as complete merely because an earlier stage passed.

## Local preparation

After validation and public-content approval, use a new output directory outside
the checkout:

```sh
python3 scripts/package_release.py \
  --version 0.1.0 \
  --commit FULL_40_CHARACTER_LOWERCASE_GIT_SHA \
  --output /tmp/irondots-release-candidate
```

The command requires a nonempty registry and `publication_approved: true` for
every package. It never executes package code, contacts an external service,
publishes a release or installs anything. It creates:

- `irondots-<version>.zip`: deterministic, uncompressed ZIP with fixed timestamps
  and regular-file permissions; only the registry, listed package files and
  generated release manifest are included.
- `release-manifest.json`: release version, declared source commit, content hashes
  and an explicit `runtime_certification: not_performed` field.
- `SHA256SUMS`: checksum of the ZIP.

The source commit argument is metadata. The caller or workflow must independently
verify that the checkout corresponds to that commit. The script validates file
hashes again while assembling the package. A new output directory prevents
accidental reuse of old artifacts; identical source bytes, version and commit
produce identical ZIP bytes.

## Gated workflow

The manual release workflow must validate the selected trusted ref and expected
commit before preparing a candidate. All jobs use self-hosted runners. Do not
run public fork pull-request code on those runners or copy private credentials
into the checkout. See the workflow itself for exact inputs and guards.

A draft release is only a staging result. The responsible maintainer must inspect
the package manifest, public-content/license review, exact commit and real-runtime
evaluation evidence before publishing. Workflow text alone does not establish
that protected environments, required reviewers, branch protection or runner-group
permissions are configured. Those account settings must be verified separately.

No release should be created from the initial empty registry. No runtime install,
production deployment, external agent invocation or automatic ClickUp update is
part of these scripts. Keep private evaluations and reports in the approved
private storage, not in public release assets.

## Current workflow inputs and failure behavior

Use a stable numeric release version such as `0.1.0` (the local package CLI also
accepts prerelease suffixes, but the workflow deliberately does not). Dispatch
from `main`, provide its exact 40-character commit and type `CREATE REVIEWED
DRAFT`. This is an explicit maintainer gate, not independent reviewer approval.

The workflow rejects an existing version-tag prefix, atomically creates the new
lightweight tag at the reviewed commit, verifies that binding, then creates only
a draft release using `--verify-tag`. The tag is public even while the release
remains a draft; dispatching the workflow authorizes that tag creation. It does
not overwrite existing tags or
releases. If draft creation fails after tag creation, the tag may remain; inspect
the actual state and choose a new version or arrange authorized recovery rather
than blindly rerunning or deleting the tag.

Both workflows are restricted to `IronbellyOrg/irondots` on `main`, with
`runs-on: [self-hosted, small]`. The canonical repository is now
[IronbellyOrg/irondots](https://github.com/IronbellyOrg/irondots); the transfer was
verified on 2 November 2026. Repository identity does not establish organization
runner eligibility, runner availability or protection settings; verify those
separately before expecting a workflow to run. The repository guard still skips
other repositories. There is no GitHub-hosted fallback. The release runner additionally
requires GitHub CLI (`gh`); Python 3 is required for validation and packaging.
