#!/usr/bin/env python3
"""Validate the local irondots registry contract without executing package code."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

SCHEMA_VERSION = 1
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
FORBIDDEN = {"private", "secrets", "output", "outputs", "receipts", "evals", "evaluations", "agent_notes", "user_notes", "node_modules", "__pycache__"}

class InvalidRegistry(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidRegistry(message)


def keys(value, expected, context):
    require(isinstance(value, dict), f"{context}: expected object")
    require(set(value) == set(expected), f"{context}: unexpected or missing fields")


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value, "invalid relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and str(path) == value, f"noncanonical path: {value}")
    require(all(part not in {".", ".."} and not part.startswith(".") and part.lower() not in FORBIDDEN for part in path.parts), f"forbidden path: {value}")
    require(all(re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", part) for part in path.parts), f"unsafe path characters: {value}")
    require(path.suffix.lower() not in {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}, f"forbidden file type: {value}")
    return path


def safe_file(root, relative):
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), f"symlink forbidden: {relative}")
    require(path.is_file(), f"missing file: {relative}")
    return path


def check_markdown(path, package_root, allowed):
    text = path.read_text(encoding="utf-8")
    # Inline Markdown links/images and reference-definition destinations. The
    # deliberately narrow syntax rejects ambiguous local targets rather than
    # claiming to be a full Markdown renderer.
    destinations = re.findall(r"!?\[[^\]\n]*\]\(([^\n)]*)\)", text)
    destinations += re.findall(r"^\s*\[[^\]\n]+\]:\s*(\S+)", text, re.MULTILINE)
    for raw in destinations:
        target = raw.strip()
        require(target, f"empty Markdown link: {path.name}")
        if target.startswith("<"):
            require(">" in target, f"invalid Markdown link: {path.name}")
            target = target[1:target.index(">")]
        else:
            target = target.split()[0]
        parsed = urlsplit(target)
        if parsed.scheme:
            require(parsed.scheme in {"https", "mailto"}, f"unsupported link scheme: {target}")
            continue
        require(not parsed.netloc, f"protocol-relative link forbidden: {target}")
        if not parsed.path:
            continue  # Same-document fragment; heading anchors not validated.
        decoded = unquote(parsed.path)
        require("\\" not in decoded and not decoded.startswith("/"), f"unsafe link: {target}")
        candidate = path.parent / decoded
        require(not candidate.is_symlink(), f"symlink link: {target}")
        try:
            relative = candidate.resolve().relative_to(package_root.resolve()).as_posix()
        except ValueError:
            raise InvalidRegistry(f"link escapes package: {target}") from None
        require(relative in allowed, f"link target not in public_files: {target}")
        safe_file(package_root, relative_path(relative))


def validate(root):
    root = Path(root)
    require(not root.is_symlink(), "registry root cannot be a symlink")
    registry_path = safe_file(root, PurePosixPath("registry.json"))
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise InvalidRegistry(f"invalid registry JSON: {error}") from error
    keys(data, {"schema_version", "packages"}, "registry")
    require(type(data["schema_version"]) is int and data["schema_version"] == SCHEMA_VERSION, "unsupported schema_version")
    require(isinstance(data["packages"], list), "packages must be an array")
    known = set()
    paths = set()
    for package in data["packages"]:
        keys(package, {"id", "version", "path", "entrypoint", "runtimes", "dependencies", "provenance", "public_files", "publication_approved"}, "package")
        name = package["id"]
        require(isinstance(name, str) and ID.fullmatch(name), "invalid package id")
        require(name not in known, f"duplicate package id: {name}")
        known.add(name)
        require(isinstance(package["version"], str) and VERSION.fullmatch(package["version"]), f"invalid version: {name}")
        rel = relative_path(package["path"])
        require(len(rel.parts) == 2 and rel.parts[0] == "packages" and rel.parts[1] == name, f"package path must be packages/{name}")
        require(str(rel) not in paths, "duplicate package path")
        paths.add(str(rel))
        package_root = root / str(rel)
        require(not (root / "packages").is_symlink() and not package_root.is_symlink() and package_root.is_dir(), f"missing or symlink package directory: {name}")
        require(isinstance(package["runtimes"], list) and package["runtimes"] and all(isinstance(r, str) and ID.fullmatch(r) for r in package["runtimes"]), f"invalid runtimes: {name}")
        require(len(set(package["runtimes"])) == len(package["runtimes"]), f"duplicate runtimes: {name}")
        require(isinstance(package["dependencies"], list) and all(isinstance(d, str) and ID.fullmatch(d) for d in package["dependencies"]), f"invalid dependencies: {name}")
        require(len(set(package["dependencies"])) == len(package["dependencies"]), f"duplicate dependencies: {name}")
        require(type(package["publication_approved"]) is bool, f"publication_approved must be boolean: {name}")
        provenance = package["provenance"]
        keys(provenance, {"source", "license", "license_file"}, f"provenance {name}")
        require(isinstance(provenance["source"], str) and urlsplit(provenance["source"]).scheme == "https" and urlsplit(provenance["source"]).netloc, f"missing HTTPS provenance: {name}")
        require(isinstance(provenance["license"], str) and bool(provenance["license"].strip()), f"missing license: {name}")
        files = package["public_files"]
        require(isinstance(files, dict) and files, f"empty public_files: {name}")
        for filename, digest in files.items():
            target = safe_file(package_root, relative_path(filename))
            require(isinstance(digest, str) and SHA256.fullmatch(digest), f"invalid digest: {filename}")
            require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, f"digest mismatch: {name}/{filename}")
        for target in package_root.rglob("*"):
            relative = target.relative_to(package_root).as_posix()
            relative_path(relative)
            require(not target.is_symlink(), f"symlink forbidden: {relative}")
            if target.is_file():
                require(relative in files, f"unlisted package file: {name}/{relative}")
            else:
                require(target.is_dir(), f"unsupported filesystem entry: {relative}")
        entry = str(relative_path(package["entrypoint"]))
        require(entry in files and entry.endswith(".md"), f"entrypoint must be a listed Markdown file: {name}")
        license_file = str(relative_path(provenance["license_file"]))
        require(license_file in files, f"license_file must be listed: {name}")
        for filename in files:
            if filename.lower().endswith(".md"):
                check_markdown(package_root / filename, package_root, files)
    graph = {p["id"]: p["dependencies"] for p in data["packages"]}
    visiting, visited = set(), set()
    def visit(name):
        require(name in known, f"missing dependency: {name}")
        require(name not in visiting, f"dependency cycle: {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in graph[name]:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
    for name in known:
        visit(name)
    if (root / "packages").exists():
        require(not (root / "packages").is_symlink(), "packages directory cannot be symlink")
        for child in (root / "packages").iterdir():
            require(child.is_dir() and not child.is_symlink() and child.name in known, f"unregistered package: {child.name}")
    return data


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        data = validate(args.root)
    except (InvalidRegistry, OSError, UnicodeError) as error:
        parser.exit(1, f"Registry invalid: {error}\n")
    print(f"Registry valid: {len(data['packages'])} package(s); structure only, not runtime certification")

if __name__ == "__main__":
    main()
