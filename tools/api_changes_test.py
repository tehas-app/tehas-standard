# Copyright 2026 Jani Tarvainen
# SPDX-License-Identifier: Apache-2.0
"""Tests of api_changes.py: python3 -I -m unittest discover -s tools -p '*_test.py'"""
import contextlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest

import api_changes as ac

SURFACE_10 = """# The surface of 1.x
command status
flag status --json
field status.api
setting X_ONE
"""

COMMANDS_1 = """# commands
status --json
limit --json
limit set --for --plan internal=--plan
panel --json building=panel
deploy --app-id:building=app --dry
"""

STATUS_1 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["api", "state"],
    "properties": {
        "api": {"const": 1},
        "state": {"enum": ["idle", "running"]},
        "running": {"type": "array", "items": {
            "type": "object", "properties": {"id": {"type": "string"}}}},
        "note": {"type": "string"},
    },
}


class Repo:
    """A throwaway git repository with one commit per call of `commit`."""

    def __init__(self, root: pathlib.Path):
        self.root = root
        self.git("init", "-q")

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.name=t", "-c",
             "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args],
            check=True, capture_output=True, text=True).stdout

    def commit(self, files: dict[str, object], tag: str) -> None:
        api = self.root / "api"
        if api.exists():
            for p in api.iterdir():
                p.unlink()
        api.mkdir(exist_ok=True)
        for name, body in files.items():
            text = body if isinstance(body, str) else json.dumps(body)
            (api / name).write_text(text, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", tag)
        self.git("tag", "-f", tag)


def base_files() -> dict[str, object]:
    return {"surface-1.0.txt": SURFACE_10, "commands.txt": COMMANDS_1,
            "events.txt": "# events\ncycle.started\ncycle.ended\n",
            "settings-1.0.0.txt": "X_OLD\n",
            "status.schema.json": STATUS_1}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Repo(pathlib.Path(self.tmp.name))
        self.repo.commit(base_files(), "v1.0.0")

    def tearDown(self):
        self.tmp.cleanup()

    def head(self, change) -> None:
        files = base_files()
        change(files)
        self.repo.commit(files, "head")

    def run_tool(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ac.main(["--repo", str(self.repo.root), "--base", "v1.0.0",
                          "--head", "head", *args])
        return rc, out.getvalue(), err.getvalue()

    def changes(self, *args: str) -> list[dict]:
        rc, out, err = self.run_tool("--format", "json", *args)
        self.assertEqual(rc, 0, err)
        return json.loads(out)["changes"]

    def names(self, *args: str) -> set[tuple[str, str, str]]:
        return {(c["where"], c["what"], c["name"]) for c in self.changes(*args)}


class NoChange(Base):
    def test_same_files(self):
        self.head(lambda f: None)
        self.assertEqual(self.changes(), [])
        rc, out, _ = self.run_tool()
        self.assertEqual(rc, 0)
        self.assertIn("No API changes.", out)

    def test_comments_are_no_change(self):
        def change(f):
            f["surface-1.0.txt"] = "# reworded\n\n" + SURFACE_10.split("\n", 1)[1]
            f["events.txt"] = "cycle.started\n   cycle.ended  \n# new comment\n"
        self.head(change)
        self.assertEqual(self.changes(), [])


class Lists(Base):
    def test_surface_added_and_removed(self):
        def change(f):
            f["surface-1.0.txt"] = SURFACE_10.replace("setting X_ONE\n", "") + "setting X_TWO\n"
        self.head(change)
        self.assertEqual(self.names(), {("surface", "added", "setting X_TWO"),
                                        ("surface", "removed", "setting X_ONE")})

    def test_newest_surface_file_wins(self):
        def change(f):
            f["surface-1.1.txt"] = SURFACE_10 + "command freeze\n"
            f["surface-1.9.txt"] = SURFACE_10 + "command other\n"
            f["surface-1.10.txt"] = SURFACE_10 + "command newest\n"
        self.head(change)
        self.assertEqual(self.names(), {("surface", "added", "command newest")})
        _, out, _ = self.run_tool()
        self.assertIn("`surface-1.0.txt` -> `surface-1.10.txt`", out)

    def test_event_list(self):
        self.head(lambda f: f.update({"events.txt": "cycle.started\nticket.closed\n"}))
        self.assertEqual(self.names(), {("events.txt", "added", "ticket.closed"),
                                        ("events.txt", "removed", "cycle.ended")})

    def test_frozen_record_is_not_compared(self):
        self.head(lambda f: f.update({"settings-1.0.0.txt": "X_CHANGED\n"}))
        self.assertEqual(self.changes(), [])

    def test_new_and_dropped_list(self):
        def change(f):
            del f["events.txt"]
            f["features.txt"] = "status\n"
        self.head(change)
        self.assertEqual(self.names(), {
            ("features.txt", "added", "features.txt"),
            ("features.txt", "added", "status"),
            ("events.txt", "removed", "events.txt"),
            ("events.txt", "removed", "cycle.started"),
            ("events.txt", "removed", "cycle.ended")})


class Commands(Base):
    def edit(self, old: str, new: str) -> None:
        self.head(lambda f: f.update({"commands.txt": COMMANDS_1.replace(old, new)}))

    def test_flag_added(self):
        self.edit("status --json", "status --json --wide")
        self.assertEqual(self.names(), {("commands", "added", "status --wide")})

    def test_command_removed(self):
        self.edit("limit --json\n", "")
        self.assertEqual(self.names(), {("commands", "removed", "limit")})

    def test_building_command_is_not_public(self):
        self.edit("panel --json building=panel", "panel --json --all building=panel")
        self.assertEqual(self.changes(), [])

    def test_shipped_feature_is_an_addition(self):
        self.edit("panel --json building=panel", "panel --json")
        [c] = self.changes("--kind", "minor")
        self.assertEqual((c["what"], c["name"]), ("added", "panel"))
        self.assertIn("was building", c["detail"])
        self.assertNotIn("marked", c)

    def test_back_to_building_is_a_removal(self):
        self.edit("status --json", "status --json building=redo")
        [c] = self.changes("--kind", "minor")
        self.assertEqual((c["what"], c["name"]), ("removed", "status"))
        self.assertIn("marked", c)

    def test_building_flag_ships(self):
        self.edit("--app-id:building=app", "--app-id")
        self.assertEqual(self.names(), {("commands", "added", "deploy --app-id")})

    def test_internal_flag_is_not_public(self):
        self.edit("limit set --for --plan internal=--plan", "limit set --for")
        self.assertEqual(self.changes(), [])
        self.edit("limit set --for --plan internal=--plan", "limit set --for --plan")
        self.assertEqual(self.names(), {("commands", "added", "limit set --plan")})

    def test_unreadable_line_is_refused(self):
        self.edit("status --json", "status odd=1 --json")
        rc, _, err = self.run_tool()
        self.assertEqual(rc, 2)
        self.assertIn("cannot read", err)


class Schemas(Base):
    def edit(self, change) -> None:
        def apply(f):
            doc = json.loads(json.dumps(STATUS_1))
            change(doc)
            f["status.schema.json"] = doc
        self.head(apply)

    def test_property_added_and_removed(self):
        def change(d):
            del d["properties"]["note"]
            d["properties"]["running"]["items"]["properties"]["by"] = {"type": "string"}
        self.edit(change)
        self.assertEqual(self.names(), {
            ("status.schema.json", "added", "running[].by"),
            ("status.schema.json", "removed", "note")})

    def test_type_change(self):
        self.edit(lambda d: d["properties"]["note"].update({"type": ["string", "null"]}))
        [c] = self.changes()
        self.assertEqual((c["what"], c["name"]), ("changed", "note"))
        self.assertIn('type: "string" -> ["string", "null"]', c["detail"])

    def test_enum_values(self):
        self.edit(lambda d: d["properties"]["state"].update({"enum": ["idle", "parked"]}))
        self.assertEqual({(c["what"], c["detail"]) for c in self.changes()}, {
            ("added", 'enum value "parked"'), ("removed", 'enum value "running"')})

    def test_required(self):
        def change(d):
            d["required"] = ["api", "note"]
        self.edit(change)
        self.assertEqual({(c["name"], c["detail"]) for c in self.changes()}, {
            ("note", "now required"), ("state", "now optional")})

    def test_const_and_ref(self):
        def change(d):
            d["properties"]["api"] = {"const": 2}
            d["properties"]["note"] = {"$ref": "note.schema.json"}
        self.edit(change)
        details = {c["detail"] for c in self.changes()}
        self.assertIn("const: 1 -> 2", details)
        self.assertIn('$ref: none -> "note.schema.json"', details)
        self.assertIn('type: "string" -> none', details)

    def test_composition_walked(self):
        self.edit(lambda d: d.update({"allOf": [{"properties": {"extra": {"type": "integer"}}}]}))
        self.assertEqual(self.names(), {("status.schema.json", "added", "extra")})

    def test_schema_file_added_and_removed(self):
        def change(f):
            del f["status.schema.json"]
            f["limit.schema.json"] = {"type": "object", "properties": {"set": {"type": "string"}}}
        self.head(change)
        self.assertEqual(self.names(), {
            ("limit.schema.json", "added", "limit.schema.json"),
            ("status.schema.json", "removed", "status.schema.json")})

    def test_bad_json_is_a_failure(self):
        self.head(lambda f: f.update({"status.schema.json": "{not json"}))
        rc, _, err = self.run_tool()
        self.assertEqual(rc, 2)
        self.assertIn("not JSON", err)


class Kinds(unittest.TestCase):
    def test_kind_from_versions(self):
        cases = [("1.4.1", "2.0.0-alpha.1", "major"), ("2.0.0", "2.1.0", "minor"),
                 ("2.1.0", "2.1.1", "patch"), ("v2.0.0-alpha.1", "v2.0.0-alpha.2", "major"),
                 ("2.0.0", "2.1.0-beta.1", "minor"), ("2.1.0-beta.1", "2.1.0", "minor"),
                 ("2.1.1-rc.1", "2.1.1", "patch"), (None, "3.0.0", "major"),
                 (None, "3.2.0", "minor"), (None, "3.2.4", "patch")]
        for frm, to, kind in cases:
            with self.subTest(frm=frm, to=to):
                self.assertEqual(ac.kind_of(frm, to), kind)

    def test_bad_versions(self):
        for frm, to in [(None, "2.1"), ("x", "2.1.0"), ("2.1.0", "2.0.9")]:
            with self.subTest(frm=frm, to=to), self.assertRaises(ac.Failure):
                ac.kind_of(frm, to)


class Marking(Base):
    def setUp(self):
        super().setUp()

        def change(f):
            f["events.txt"] = "cycle.started\nticket.closed\n"
        self.head(change)

    def test_major_marks_nothing(self):
        self.assertTrue(all("marked" not in c for c in self.changes("--kind", "major")))

    def test_minor_marks_removals_only(self):
        marked = {(c["what"], c["name"]) for c in self.changes("--kind", "minor")
                  if "marked" in c}
        self.assertEqual(marked, {("removed", "cycle.ended")})

    def test_patch_marks_everything(self):
        self.assertTrue(all("marked" in c for c in self.changes("--kind", "patch")))

    def test_strict_exit(self):
        self.assertEqual(self.run_tool("--from", "1.0.0", "--to", "1.1.0", "--strict")[0], 1)
        self.assertEqual(self.run_tool("--from", "1.0.0", "--to", "1.1.0")[0], 0)
        self.assertEqual(self.run_tool("--from", "1.0.0", "--to", "2.0.0", "--strict")[0], 0)

    def test_markdown_title_and_mark(self):
        rc, out, _ = self.run_tool("--from", "1.0.0", "--to", "1.1.0")
        self.assertEqual(rc, 0)
        self.assertTrue(out.startswith("## API changes in v1.1.0\n"))
        self.assertIn("Judged as a minor release.", out)
        self.assertIn("**1 not allowed in this release.**", out)
        self.assertIn("- removed: `cycle.ended` **not allowed: removed in a minor", out)

    def test_usage_errors(self):
        self.assertEqual(self.run_tool("--kind", "minor", "--to", "1.1.0")[0], 2)
        self.assertEqual(self.run_tool("--from", "1.0.0")[0], 2)


class WorkingTreeAndMissing(Base):
    def test_working_tree_head(self):
        (self.repo.root / "api" / "events.txt").write_text("cycle.started\n")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ac.main(["--repo", str(self.repo.root), "--base", "v1.0.0",
                          "--format", "json"])
        self.assertEqual(rc, 0, err.getvalue())
        names = {(c["what"], c["name"]) for c in json.loads(out.getvalue())["changes"]}
        self.assertEqual(names, {("removed", "cycle.ended")})

    def test_base_without_api_folder(self):
        self.repo.git("checkout", "-q", "--orphan", "empty")
        self.repo.git("rm", "-rq", "--cached", ".")
        self.repo.git("commit", "-q", "--allow-empty", "-m", "empty")
        self.repo.git("tag", "empty")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = ac.main(["--repo", str(self.repo.root), "--base", "empty",
                          "--head", "v1.0.0", "--format", "json"])
        self.assertEqual(rc, 0)
        changes = json.loads(out.getvalue())["changes"]
        self.assertTrue(changes and all(c["what"] == "added" for c in changes))

    def test_unknown_ref(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ac.main(["--repo", str(self.repo.root), "--base", "nope"])
        self.assertEqual(rc, 2)
        self.assertIn("api_changes: git", err.getvalue())


if __name__ == "__main__":
    unittest.main()
