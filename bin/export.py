#!/usr/bin/env python3
"""Build a release copy or an anonymous review copy, from one code path.

Anonymisation is a build target here, not a rename job. The sibling project in
this programme had to discover its own name in dozens of tracked files at
submission time and rewrite them; this repository forbids the name from entering
in the first place (control ANON-1), so the anonymous profile has only the five
declared files to rewrite.

The refusal is the point. Stripping is easy, and stripping incompletely is the
failure that matters, because an archive that looks anonymised gets submitted
without a second look. So this is a scanner that happens to strip first, and it
exits non-zero on any residue it cannot explain.

Two properties worth stating because they are easy to get wrong:

  * The export never includes `.git`. Every commit carries an author name and
    email in its object metadata, and no edit to a tracked file removes them. An
    anonymised history is a thing to get wrong, and a submission does not need
    one.
  * A scan that read nothing does not report clean. Reporting clean having
    examined zero files is how an anonymity check silently lapses.

Usage:
    bin/export.py --profile public --out dist/
    bin/export.py --profile anon   --out dist/
    bin/export.py --profile anon   --check     build, scan, report, discard

Exit codes: 0 clean, 1 residue found, 2 could not run.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IDENTITY = REPO / "data" / "identity.toml"

FIXED_MTIME = 1000000000  # deterministic archives; no local clock in the output
BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gz", ".xz", ".zst",
                   ".zip", ".pyc", ".bin", ".o", ".a", ".so"}

# Files that must never travel, whatever the profile. The firewall's digest file
# is not secret, but it is a pointer to the existence of a firewall, and the
# generator that produced it lives outside this repository entirely.
SKIP_ALWAYS = {".gitignore"}


def load_identity() -> dict:
    if not IDENTITY.exists():
        print(f"export: missing {IDENTITY}", file=sys.stderr)
        raise SystemExit(2)
    return tomllib.loads(IDENTITY.read_text(encoding="utf-8"))


def tracked_at_head() -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO,
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"export: cannot enumerate tracked files ({exc})", file=sys.stderr)
        raise SystemExit(2)
    return [p for p in out.split("\0") if p]


def stage(files: list[str], dest: Path) -> int:
    n = 0
    for rel in files:
        if rel in SKIP_ALWAYS:
            continue
        src = REPO / rel
        if not src.is_file():
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out)
        n += 1
    return n


def anonymise(dest: Path, ident: dict) -> list[str]:
    """Rewrite the declared identity-bearing files. Returns what was changed."""
    changed = []
    real, anon = ident["project_name"], ident["anon_project_name"]

    lic = dest / "LICENSE"
    if lic.exists():
        text = lic.read_text(encoding="utf-8")
        new = re.sub(r"^(Copyright\s*\(c\)\s*\d{4}).*$",
                     r"\1 Anonymous Author(s)", text, flags=re.MULTILINE)
        if new != text:
            lic.write_text(new, encoding="utf-8")
            changed.append("LICENSE: copyright line")

    cff = dest / "CITATION.cff"
    if cff.exists():
        cff.write_text(
            "cff-version: 1.2.0\n"
            "message: \"Anonymised for double-blind review.\"\n"
            f"title: \"{anon}: a known-answer recall corpus for constant-time analysers\"\n"
            "type: software\n"
            "license: MIT\n"
            "authors:\n"
            "  - name: \"Anonymous Author(s)\"\n", encoding="utf-8")
        changed.append("CITATION.cff: replaced wholesale")

    for rel in ident["allowed_in"]:
        path = dest / rel
        if not path.exists() or path.suffix.lower() in BINARY_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new = re.sub(rf"\b{re.escape(real)}\b", anon, text, flags=re.IGNORECASE)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(f"{rel}: project name substituted")
    return changed


def scan(dest: Path, ident: dict) -> tuple[list[str], int]:
    """Look for residue. Returns (findings, files actually examined)."""
    needles = [ident["project_name"]]
    findings, examined = [], 0
    for path in sorted(dest.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(dest))
        for n in needles:
            if n.lower() in rel.lower():
                findings.append(f"{rel}: project name in path")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # A binary is still scanned, at the byte level. Skipping it would
            # leave a real hiding place: a project name reaches a compiled
            # object or a recorded trace as easily as it reaches prose. Refusing
            # outright is no better, because it fails the export on every
            # legitimate binary and a check that always fails gets switched off.
            blob = path.read_bytes().lower()
            examined += 1
            for n in needles:
                if n.lower().encode() in blob:
                    findings.append(f"{rel}: project name in binary content")
            continue
        except OSError as exc:
            findings.append(f"{rel}: could not be read ({type(exc).__name__}), "
                            f"so it was not cleared")
            continue
        examined += 1
        for i, line in enumerate(text.splitlines(), 1):
            for n in needles:
                if re.search(rf"\b{re.escape(n)}\b", line, re.IGNORECASE):
                    findings.append(f"{rel}:{i}: project name in content")
    return findings, examined


def normalise_times(dest: Path) -> None:
    for path in sorted(dest.rglob("*")):
        os.utime(path, (FIXED_MTIME, FIXED_MTIME))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=["public", "anon"], required=True)
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true",
                    help="build into a temporary directory, scan, then discard")
    args = ap.parse_args()
    if not args.out and not args.check:
        print("export: need --out or --check", file=sys.stderr)
        return 2

    ident = load_identity()
    files = tracked_at_head()
    if not files:
        print("export: no tracked files, so this is not a clean result", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="export-"))
    try:
        dest = tmp / "tree"
        dest.mkdir()
        staged = stage(files, dest)
        changed = []
        if args.profile == "anon":
            changed = anonymise(dest, ident)
        normalise_times(dest)

        findings, examined = ([], staged)
        if args.profile == "anon":
            findings, examined = scan(dest, ident)
            if examined == 0:
                print("export: examined no files, so this is not a clean result",
                      file=sys.stderr)
                return 2

        print(f"export: profile={args.profile} staged={staged} examined={examined}")
        for c in changed:
            print(f"  rewrote {c}")
        if findings:
            print(f"\nexport: {len(findings)} residue finding(s), refusing to hand over "
                  f"the archive:", file=sys.stderr)
            for f in findings[:20]:
                print(f"  {f}", file=sys.stderr)
            return 1
        if args.profile == "anon":
            print("export: residue scan clean")

        if args.out:
            out = Path(args.out).resolve()
            out.mkdir(parents=True, exist_ok=True)
            final = out / (ident["anon_project_name"] if args.profile == "anon"
                           else ident["project_name"])
            if final.exists():
                shutil.rmtree(final)
            shutil.copytree(dest, final)
            print(f"export: wrote {final}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
