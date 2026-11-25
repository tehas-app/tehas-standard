#!/usr/bin/env python3
# Copyright 2026 Jani Tarvainen
# SPDX-License-Identifier: Apache-2.0
"""Checks for tehas-standard. Python 3.11 or later and git; no network.

1. Every relative link in a Markdown file resolves to a file.
2. A tagged version directory is unchanged: for each tag vN or vN.M, the
   directory of the same name equals its state at the tag.
3. Every tagged version has its directory.

Exit 0 when all hold, 1 otherwise, naming each failure.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)")
TAG = re.compile(r"v[1-9][0-9]*(\.[0-9]+)?")


def links() -> list[str]:
    bad = []
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue
            path = (md.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                bad.append(f"{md.relative_to(ROOT)}: broken link {target}")
    return bad


def tagged_directories() -> list[str]:
    out = subprocess.run(["git", "tag", "--list"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    bad = []
    for tag in sorted(t for t in out.split() if TAG.fullmatch(t)):
        if not (ROOT / tag).is_dir():
            bad.append(f"{tag}: the tag has no directory {tag}/")
            continue
        diff = subprocess.run(["git", "diff", "--quiet", tag, "--", f"{tag}/"], cwd=ROOT)
        if diff.returncode != 0:
            bad.append(f"{tag}/: changed since the tag {tag}; a correction is a new version")
    return bad


def main() -> int:
    bad = links() + tagged_directories()
    for line in bad:
        print(line)
    print("ok" if not bad else f"{len(bad)} failure(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
