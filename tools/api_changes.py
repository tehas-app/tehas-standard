#!/usr/bin/env python3
# Copyright 2026 Jani Tarvainen
# SPDX-License-Identifier: Apache-2.0
"""The API changes between two commits of a part, from its `api/` files.

Python 3.11 or later and git; no network, no third-party packages.

What it reads, at each of the two commits (contracts C2 and C3):

- the newest `api/surface-<major>.<minor>.txt`: one public name per line;
- `api/commands.txt`: a command per line, its flags and its marks. Only
  what is public is compared: a command marked `building=<feature>`, a flag
  marked `--flag:building=<feature>` and a flag named in
  `internal=<flag>,...` are not, so a feature that ships shows as added;
- every other list `api/<name>.txt` (`events.txt`, `features.txt`, ...),
  one entry per line, except the frozen `<name>-<x.y.z>.txt` records;
- every `api/*.schema.json`: each property's path, type, enum, const and
  whether it is required.

Lines that are empty or start `#` are comments. A name is compared as
written, so a reworded comment is no change.

What it writes: Markdown (or JSON with `--format json`) listing what was
added, removed and changed. A CI job appends it to the job summary on every
pull request; a release workflow writes it as "API changes in vX.Y.Z".

When it knows what kind of release the head is (`--kind`, or `--from` and
`--to` versions), it marks what C4 and C3 forbid:

- a major: nothing is marked;
- a minor: every removal and change is marked (only additions are allowed);
- a patch: every difference is marked (a patch changes no surface).

A pre-release is judged as the release it leads to: `2.0.0-alpha.2` is a
major, `2.1.0-beta.1` a minor.

Exit 0, or 1 with `--strict` when something is marked, or 2 on a usage or
git error.

    api_changes.py --base v2.0.0 --head HEAD --to 2.1.0
    api_changes.py --base origin/main            # head: the working tree
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field

SURFACE = re.compile(r"surface-([0-9]+)\.([0-9]+)\.txt")
FROZEN = re.compile(r".+-[0-9]+\.[0-9]+\.[0-9]+\.txt")
SEMVER = re.compile(
    r"v?([0-9]+)\.([0-9]+)\.([0-9]+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?"
)
KINDS = ("major", "minor", "patch")


class Failure(Exception):
    """A usage or git error: exit 2."""


# --- reading a commit ------------------------------------------------------


class Tree:
    """The `api/` files of one commit, or of the working tree."""

    def __init__(self, repo: pathlib.Path, ref: str | None, api: str):
        self.repo, self.ref, self.api = repo, ref, api.strip("/")

    def names(self) -> list[str]:
        """The file names directly under `api/`."""
        if self.ref is None:
            folder = self.repo / self.api
            if not folder.is_dir():
                return []
            return sorted(p.name for p in folder.iterdir() if p.is_file())
        git(self.repo, "rev-parse", "--verify", "--quiet", f"{self.ref}^{{commit}}")
        out = git(self.repo, "ls-tree", "--name-only", self.ref, "--", f"{self.api}/")
        prefix = f"{self.api}/"
        return sorted(line[len(prefix):] for line in out.splitlines()
                      if line.startswith(prefix) and "/" not in line[len(prefix):])

    def read(self, name: str) -> str:
        if self.ref is None:
            return (self.repo / self.api / name).read_text(encoding="utf-8")
        return git(self.repo, "show", f"{self.ref}:{self.api}/{name}")


def git(repo: pathlib.Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                         text=True)
    if run.returncode != 0:
        why = run.stderr.strip() or f"exit {run.returncode}"
        raise Failure(f"git {' '.join(args)}: {why}")
    return run.stdout


def entries(text: str) -> list[str]:
    """The lines of a list that are not comments, stripped, in order."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


# --- what a commit's API is ------------------------------------------------


@dataclass
class Api:
    surface_file: str | None = None
    surface: list[str] = field(default_factory=list)
    commands: dict[str, "Command"] = field(default_factory=dict)
    lists: dict[str, list[str]] = field(default_factory=dict)
    schemas: dict[str, dict[str, dict]] = field(default_factory=dict)


def load(tree: Tree) -> Api:
    api = Api()
    names = tree.names()
    surfaces = [(tuple(map(int, m.groups())), n) for n in names
                if (m := SURFACE.fullmatch(n))]
    if surfaces:
        api.surface_file = max(surfaces)[1]
        api.surface = entries(tree.read(api.surface_file))
    for name in names:
        if name == "commands.txt":
            api.commands = commands(tree.read(name))
        elif (name.endswith(".txt") and not SURFACE.fullmatch(name)
              and not FROZEN.fullmatch(name)):
            api.lists[name] = entries(tree.read(name))
        elif name.endswith(".schema.json"):
            try:
                doc = json.loads(tree.read(name))
            except json.JSONDecodeError as err:
                raise Failure(f"{tree.api}/{name} at {tree.ref or 'the working tree'}"
                              f": not JSON ({err})") from err
            api.schemas[name] = flatten(doc)
    return api


@dataclass
class Command:
    public: bool
    flags: dict[str, bool]  # flag -> public


def commands(text: str) -> dict[str, Command]:
    """`api/commands.txt`: the command words, then its flags and marks.

    A line is `<command> [<subcommand>] [--flag[:building=f] ...]
    [building=f] [internal=--a,--b]`; the words before the first flag or
    mark name the command.
    """
    out: dict[str, Command] = {}
    for line in entries(text):
        words: list[str] = []
        flags: dict[str, bool] = {}
        public, internal = True, set()
        for token in line.split():
            if token.startswith("-"):
                name, _, mark = token.partition(":")
                flags[name] = not mark.startswith("building=")
            elif token.startswith("building="):
                public = False
            elif token.startswith("internal="):
                internal |= {f for f in token[len("internal="):].split(",") if f}
            elif "=" in token or flags:
                raise Failure(f"api/commands.txt: cannot read {token!r} in {line!r}")
            else:
                words.append(token)
        for name in internal:
            flags[name] = False
        out[" ".join(words)] = Command(public, flags)
    return out


def flatten(doc: object, path: str = "", required: bool = False,
            out: dict[str, dict] | None = None) -> dict[str, dict]:
    """Each property of a JSON Schema by its path: `a.b`, `a[]` for items.

    The root is `.`. Composition (`allOf`, `anyOf`, `oneOf`) and `$defs`
    are walked under the same path; a `$ref` is kept as written, not
    followed, so a change in the referenced file shows there.
    """
    out = {} if out is None else out
    if not isinstance(doc, dict):
        return out
    here = out.setdefault(path or ".", {})
    if path:
        here["required"] = here.get("required", False) or required
    for key in ("type", "const", "$ref", "format"):
        if key in doc:
            here[key] = doc[key]
    if "enum" in doc and isinstance(doc["enum"], list):
        here["enum"] = sorted(json.dumps(v, sort_keys=True) for v in doc["enum"])
    needed = set(doc.get("required", []) if isinstance(doc.get("required"), list)
                 else [])
    props = doc.get("properties")
    if isinstance(props, dict):
        for name, sub in props.items():
            flatten(sub, f"{path}.{name}" if path else name, name in needed, out)
    items = doc.get("items")
    if isinstance(items, dict):
        flatten(items, f"{path}[]" if path else "[]", False, out)
    for key in ("allOf", "anyOf", "oneOf"):
        for sub in doc.get(key, []) if isinstance(doc.get(key), list) else []:
            flatten(sub, path, False, out)
    defs = doc.get("$defs")
    if isinstance(defs, dict):
        for name, sub in defs.items():
            flatten(sub, f"$defs.{name}", False, out)
    return out


# --- the delta -------------------------------------------------------------


@dataclass
class Change:
    where: str      # "surface", "commands", "events.txt", "x.schema.json"
    what: str       # "added", "removed", "changed"
    name: str
    detail: str = ""
    marked: str = ""  # why C3/C4 forbids it for this release, or empty

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v}


def diff(base: Api, head: Api) -> list[Change]:
    out: list[Change] = []
    out += diff_names("surface", base.surface, head.surface)
    out += diff_commands(base.commands, head.commands)
    for name in sorted(base.lists.keys() | head.lists.keys()):
        if name not in head.lists:
            out.append(Change(name, "removed", name, "the list"))
        elif name not in base.lists:
            out.append(Change(name, "added", name, "the list"))
        out += diff_names(name, base.lists.get(name, []), head.lists.get(name, []))
    for name in sorted(base.schemas.keys() | head.schemas.keys()):
        if name not in head.schemas:
            out.append(Change(name, "removed", name, "the schema"))
        elif name not in base.schemas:
            out.append(Change(name, "added", name, "the schema"))
        else:
            out += diff_schema(name, base.schemas[name], head.schemas[name])
    return out


def diff_commands(base: dict[str, Command], head: dict[str, Command]
                  ) -> list[Change]:
    out: list[Change] = []
    for name in sorted(base.keys() | head.keys()):
        was, now = base.get(name), head.get(name)
        was_public = bool(was and was.public)
        now_public = bool(now and now.public)
        if was_public and not now_public:
            out.append(Change("commands", "removed", name,
                              "now building" if now else ""))
            continue
        if now_public and not was_public:
            assert now is not None
            flags = sorted(f for f, public in now.flags.items() if public)
            detail = ("was building; " if was else "") + " ".join(flags)
            out.append(Change("commands", "added", name, detail.strip("; ")))
            continue
        if not (was_public and now_public):
            continue
        assert was is not None and now is not None
        old = {f for f, public in was.flags.items() if public}
        new = {f for f, public in now.flags.items() if public}
        for flag in sorted(new - old):
            out.append(Change("commands", "added", f"{name} {flag}",
                              "flag, was building or internal" if flag in was.flags
                              else "flag"))
        for flag in sorted(old - new):
            out.append(Change("commands", "removed", f"{name} {flag}",
                              "flag, now building or internal" if flag in now.flags
                              else "flag"))
    return out


def diff_names(where: str, base: list[str], head: list[str]) -> list[Change]:
    was, now = set(base), set(head)
    return ([Change(where, "added", n) for n in head if n not in was]
            + [Change(where, "removed", n) for n in base if n not in now])


def diff_schema(where: str, base: dict[str, dict], head: dict[str, dict]
                ) -> list[Change]:
    out: list[Change] = []
    for path in sorted(base.keys() | head.keys()):
        if path not in head:
            out.append(Change(where, "removed", path))
            continue
        if path not in base:
            out.append(Change(where, "added", path, describe(head[path])))
            continue
        was, now = base[path], head[path]
        for key in ("type", "const", "$ref", "format"):
            if was.get(key) != now.get(key):
                out.append(Change(where, "changed", path,
                                  f"{key}: {show(was.get(key))} -> {show(now.get(key))}"))
        old, new = set(was.get("enum", [])), set(now.get("enum", []))
        if "enum" in was or "enum" in new:
            for value in sorted(new - old):
                out.append(Change(where, "added", path, f"enum value {value}"))
            for value in sorted(old - new):
                out.append(Change(where, "removed", path, f"enum value {value}"))
        if was.get("required", False) != now.get("required", False):
            out.append(Change(where, "changed", path,
                              "now required" if now.get("required") else "now optional"))
    return out


def describe(prop: dict) -> str:
    bits = []
    if "type" in prop:
        bits.append(f"type {show(prop['type'])}")
    if prop.get("required"):
        bits.append("required")
    return ", ".join(bits)


def show(value: object) -> str:
    return "none" if value is None else json.dumps(value)


# --- what the release may change -------------------------------------------


def kind_of(base: str | None, head: str) -> str:
    """The release kind of `head` against the version `base`."""
    to = SEMVER.fullmatch(head)
    if not to:
        raise Failure(f"--to {head!r} is not a SemVer version")
    major, minor, patch = (int(x) for x in to.groups()[:3])
    if base is not None:
        frm = SEMVER.fullmatch(base)
        if not frm:
            raise Failure(f"--from {base!r} is not a SemVer version")
        was = tuple(int(x) for x in frm.groups()[:3])
        if (major, minor, patch) < was:
            raise Failure(f"--to {head} is lower than --from {base}")
        if major != was[0]:
            return "major"
        if minor != was[1]:
            return "minor"
        if patch != was[2]:
            return "patch"
    # Same core (a pre-release step) or no base: the release it leads to.
    if minor == 0 and patch == 0:
        return "major"
    return "minor" if patch == 0 else "patch"


def mark(changes: list[Change], kind: str | None) -> None:
    for change in changes:
        if kind == "patch":
            change.marked = "a patch changes no surface (C3)"
        elif kind == "minor" and change.what != "added":
            change.marked = f"{change.what} in a minor; only additions (C4)"


# --- writing ---------------------------------------------------------------


def markdown(changes: list[Change], title: str, kind: str | None,
             base: Api, head: Api) -> str:
    lines = [f"## {title}", ""]
    if kind:
        lines += [f"Judged as a {kind} release.", ""]
    if base.surface_file != head.surface_file:
        lines += [f"Surface list: `{base.surface_file or 'none'}` -> "
                  f"`{head.surface_file or 'none'}`.", ""]
    if not changes:
        lines += ["No API changes.", ""]
        return "\n".join(lines)
    marked = [c for c in changes if c.marked]
    if marked:
        lines += [f"**{len(marked)} not allowed in this release.**", ""]
    order = {"surface": 0, "commands": 1}
    groups: dict[str, list[Change]] = {}
    for change in changes:
        groups.setdefault(change.where, []).append(change)
    for where in sorted(groups, key=lambda w: (order.get(w, 2 if w.endswith(".txt") else 3), w)):
        label = {"surface": "Surface", "commands": "Commands and flags"}.get(
            where, f"`{where}`")
        lines += [f"### {label}", ""]
        for what in ("added", "removed", "changed"):
            for c in (c for c in groups[where] if c.what == what):
                text = f"- {what}: `{c.name}`"
                if c.detail:
                    text += f" ({c.detail})"
                if c.marked:
                    text += f" **not allowed: {c.marked}**"
                lines.append(text)
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List the API changes between two commits from api/.")
    parser.add_argument("--repo", default=".", help="the repository (default .)")
    parser.add_argument("--base", required=True, help="the earlier commit or tag")
    parser.add_argument("--head", help="the later commit (default: the working tree)")
    parser.add_argument("--api", default="api", help="the API folder (default api)")
    parser.add_argument("--kind", choices=KINDS, help="the head's release kind")
    parser.add_argument("--from", dest="frm", metavar="VERSION",
                        help="the base's version, with --to")
    parser.add_argument("--to", metavar="VERSION", help="the head's version")
    parser.add_argument("--title", help="the heading (default from the versions)")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when something is not allowed")
    args = parser.parse_args(argv)
    try:
        if args.kind and args.to:
            raise Failure("give --kind or --to, not both")
        if args.frm and not args.to:
            raise Failure("--from needs --to")
        repo = pathlib.Path(args.repo)
        kind = args.kind or (kind_of(args.frm, args.to) if args.to else None)
        base = load(Tree(repo, args.base, args.api))
        head = load(Tree(repo, args.head, args.api))
    except Failure as err:
        print(f"api_changes: {err}", file=sys.stderr)
        return 2
    changes = diff(base, head)
    mark(changes, kind)
    title = args.title or (f"API changes in {'v' + args.to.lstrip('v')}" if args.to
                           else f"API changes against {args.base}")
    if args.format == "json":
        print(json.dumps({"title": title, "kind": kind,
                          "surface": [base.surface_file, head.surface_file],
                          "changes": [c.as_dict() for c in changes]}, indent=2))
    else:
        print(markdown(changes, title, kind, base, head))
    return 1 if args.strict and any(c.marked for c in changes) else 0


if __name__ == "__main__":
    sys.exit(main())
