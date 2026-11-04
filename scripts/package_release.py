#!/usr/bin/env python3
"""Create a deterministic allowlisted release candidate; never publish or install."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from validate_registry import InvalidRegistry, VERSION, require, validate


def build(root, output, version, commit):
    require(isinstance(version, str) and VERSION.fullmatch(version), "invalid release version")
    require(isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit), "commit must be a full lowercase Git SHA")
    root, output = Path(root).resolve(), Path(output).resolve()
    require(output != root and root not in output.parents, "output must be outside the source checkout")
    data = validate(root)
    require(data["packages"], "refusing to release an empty registry")
    require(all(p["publication_approved"] for p in data["packages"]), "every package needs explicit publication_approved")
    payloads = {"registry.json": (json.dumps(data, sort_keys=True, indent=2) + "\n").encode()}
    for package in data["packages"]:
        for relative, expected in package["public_files"].items():
            target = f"{package['path']}/{relative}"
            content = (root / target).read_bytes()
            require(hashlib.sha256(content).hexdigest() == expected, f"file changed after validation: {target}")
            payloads[target] = content
    manifest = {"schema_version": 1, "release_version": version, "source_commit": commit,
                "files": {name: hashlib.sha256(content).hexdigest() for name, content in sorted(payloads.items())},
                "runtime_certification": "not_performed"}
    payloads["release-manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    require(not output.exists(), f"output directory must be new: {output}")
    output.mkdir(parents=True, exist_ok=False)
    archive = output / f"irondots-{version}.zip"
    require(not archive.exists(), f"refusing to overwrite existing release candidate: {archive}")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as handle:
        for name, content in sorted(payloads.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            handle.writestr(info, content)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    (output / "release-manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    try:
        archive = build(args.root, args.output, args.version, args.commit)
    except (InvalidRegistry, OSError, UnicodeError) as error:
        parser.exit(1, f"Release blocked: {error}\n")
    print(archive)

if __name__ == "__main__":
    main()
