# Registry contract, version 1

This is the **local irondots repository contract**, not an official dot, Codex,
ClickUp or Claude schema. `registry.json` contains exactly `schema_version: 1`
and `packages`, an array. An empty array is valid for repository validation and
invalid for release preparation.

Each package declares exactly these fields:

- `id`: unique lowercase slug, starting with a letter, at most 64 characters.
- `version`: three-part numeric version, optionally with a prerelease suffix.
- `path`: exactly `packages/<id>`.
- `entrypoint`: relative path to a listed Markdown file.
- `runtimes`: nonempty, unique list of runtime slugs. These are declarations, not
  proof that the package works or is installed in those runtimes.
- `dependencies`: unique list of other package IDs in this registry. Missing
  dependencies and cycles are rejected. External runtime capabilities must be
  explained in the package's entrypoint and evaluated before installation.
- `provenance`: an HTTPS `source`, nonempty `license` description or identifier,
  and a `license_file` included in the public file allowlist. License correctness
  and distribution rights still require human review.
- `public_files`: object mapping package-relative filenames to lowercase SHA-256
  digests. All files in the package directory must be listed and match their
  digests. The entrypoint, references and license must be included.
- `publication_approved`: boolean. This records a maintainer's reviewed decision;
  it does not grant authority or provide a cryptographic attestation. It must be
  true for all packages before release preparation succeeds.

## Boundaries

Paths must be canonical, relative and composed of ASCII filename characters.
Absolute paths, traversal, symlinks, hidden entries, credential-style file types,
and known private output/receipt/evaluation directories are rejected. Every
package file is explicit. Unregistered package directories are rejected.

For Markdown, inline links/images and reference-definition targets are checked.
Local destinations must resolve to allowlisted files within the same package.
HTTPS and mailto links are accepted but not fetched. Same-document heading
fragments are not checked. This narrow parser is not a complete Markdown renderer.
Use ordinary Markdown links, not HTML or dynamically generated resource paths.

No package instructions or code are executed during structural validation.
Checksums establish content identity, not safety. These checks are **not** a
secret detector, license adjudicator, prompt-injection defense, dependency
installer or proof of real-runtime behavior. A public-content review remains
mandatory before adding files to this public repository, even when checks pass.

## Adding a package

1. Prepare a sanitized package in `packages/<id>` and review distribution rights.
2. Include only reviewed public files and a license/attribution file.
3. Add exact SHA-256 hashes and all required registry fields.
4. Leave `publication_approved` false until the maintainer approves that exact
   public payload. Update hashes and repeat review after content changes.
5. Run structural validation and the offline unit tests.
6. Perform actual target-runtime import/readback and the required live evaluations
   separately. Keep private inputs and raw outputs outside this public repository.
7. Record the reviewed package/version, evidence location and decision through the
   organization's authorized private tracking process. This repository does not
   automatically update ClickUp or install a skill.
