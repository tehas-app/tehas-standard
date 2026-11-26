#!/usr/bin/env python3
# Copyright 2026 Jani Tarvainen
# SPDX-License-Identifier: Apache-2.0
"""Tests of tools/architecture.py, on throwaway git repositories. No
network. Run: python3 -I -m unittest discover -s tools -p '*_test.py'"""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from contextlib import redirect_stderr, redirect_stdout

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import architecture  # noqa: E402

URL = architecture.STANDARD_URL

CONFIG = '''version = 1

[[check]]
id = "routes"
rule = "R1"
what = "routes only in the adapter"
pattern = '/api/'
files = ["src/**/*.rs"]
allowed = ["src/adapter.rs"]
comment = "//"
max = {routes}
{why}

[[check]]
id = "untyped"
rule = "R4"
what = "no Value in a signature"
mode = "spans"
start = '\\bfn\\s+\\w+'
end = '[{{;]'
pattern = '\\bValue\\b'
files = ["src/**/*.rs"]
max = {untyped}
why = "the page's handler, until step 3"

[[report]]
id = "pub"
rule = "R5"
what = "public items"
pattern = '^pub '
files = ["src/**"]
'''


def config(routes=1, untyped=1, why="the page, until step 4"):
    return CONFIG.format(routes=routes, untyped=untyped, why=f'why = "{why}"' if why else "")


class Repo:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        unittest.addModuleCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "test")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def write(self, path, text):
        full = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(text)
        self.git("add", path)

    def commit(self):
        self.git("commit", "-q", "-m", "x")

    def run(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = architecture.main(["--root", self.root, "--summary", os.devnull, *args])
        return code, out.getvalue() + err.getvalue()


def pointer(standard):
    """`tehas.toml` naming `standard`, or the text as given when it
    is already TOML (it holds a table)."""
    if "[" in standard:
        return standard + "\n"
    return f'[standard]\nurl = "{URL}"\nversion = "{standard}"\n'


def base_repo(standard="v2", **kw):
    r = Repo()
    if standard:
        r.write("tehas.toml", pointer(standard))
    r.write("architecture.toml", config(**kw))
    r.write("src/adapter.rs", 'fn get() { call("/api/a"); call("/api/b") }\n')
    r.write("src/web.rs", '// a comment naming /api/x is not counted\nfn page(v: Value) {\n  call("/api/c")\n}\n')
    r.write("src/core.rs", "pub fn decide(\n    a: u32,\n) -> u32 {\n    a\n}\n")
    return r


class Checks(unittest.TestCase):
    def test_holds_at_its_max(self):
        r = base_repo()
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 |  | 1 | 1 | holds |", out)

    def test_a_count_that_rises_fails_and_names_the_place(self):
        r = base_repo()
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)
        self.assertIn("src/core.rs:1:", out)

    def test_a_count_that_falls_asks_for_the_new_max(self):
        r = base_repo()
        r.write("src/web.rs", "fn page(v: Value) {}\n")
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("Set max = 0", out)

    def test_a_max_above_0_needs_a_why(self):
        r = base_repo(why="")
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): max is 1 with no why", out)
        self.assertIn("| `routes` | R1 |  | 1 | 1 | no why |", out)

    def test_a_blank_why_is_no_why(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        r.write("architecture.toml", config().replace('why = "the page, until step 4"', 'why = "  "'))
        r.write("src/adapter.rs", 'fn get() { call("/api/a") }\n')
        r.write("src/web.rs", 'fn page(v: Value) { call("/api/c") }\n')
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): max is 1 with no why", out)

    def test_a_max_of_0_needs_no_why(self):
        r = base_repo(routes=0, untyped=0, why="")
        r.write("src/web.rs", "fn page() {}\n")
        code, out = r.run()
        self.assertEqual(code, 0, out)

    def test_no_why_fails_with_base_too(self):
        r = base_repo(why="")
        r.commit()
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): max is 1 with no why", out)

    def test_spans_cover_signatures_over_several_lines(self):
        r = base_repo()
        r.write("src/core.rs", "pub fn decide(\n    a: Value,\n) -> u32 {\n    let v: Value = 1;\n}\n")
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("untyped (R4): 2 places, 1 allowed", out)
        self.assertIn("src/core.rs:1:", out)

    def test_the_body_after_the_end_is_not_part_of_the_span(self):
        r = base_repo()
        r.write("src/web.rs", 'fn page() { let v: Value = 1; call("/api/c") }\n')
        code, out = r.run()
        self.assertEqual(code, 1)
        self.assertIn("untyped (R4): 0 places, fewer than 1", out)

    def test_report_lists_without_failing(self):
        r = base_repo()
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("**pub** (R5, reported, not checked)", out)
        self.assertIn("- `src/core.rs`: 1", out)

    def test_untracked_files_are_not_read(self):
        r = base_repo()
        with open(os.path.join(r.root, "src", "scratch.rs"), "w") as f:
            f.write('call("/api/z")\n')
        code, out = r.run()
        self.assertEqual(code, 0, out)


class Base(unittest.TestCase):
    def test_a_max_raised_without_a_new_why_fails(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config(routes=2))
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("max raised from 1 to 2 without a new why", out)

    def test_a_max_raised_with_a_new_why_holds(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config(routes=2, why="the legacy page, until step 5"))
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 | 1 | 2 | 2 | holds |", out)

    def test_a_wider_scope_without_a_new_why_fails(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace('allowed = ["src/adapter.rs"]\n', ""))
        code, out = r.run("--base", "main", "--force")
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): allowed changed from the base without a new why", out)
        self.assertIn("rescoped", out)

    def test_a_changed_pattern_and_files_without_a_new_why_fails(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace("pattern = '/api/'", "pattern = '/api/c'")
                .replace('files = ["src/**/*.rs"]\nallowed', 'files = ["src/*.rs"]\nallowed'))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): files, pattern changed from the base without a new why", out)

    def test_a_changed_start_end_and_comment_need_a_new_why(self):
        r = base_repo()
        r.commit()
        text = (config().replace("end = '[{;]'", "end = '[{]'").replace('comment = "//"', 'comment = "#"')
                .replace("start = '\\bfn\\s+\\w+'", "start = '\\bfn\\b'"))
        r.write("architecture.toml", text)
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): comment changed from the base without a new why", out)
        self.assertIn("untyped (R4): end, start changed from the base without a new why", out)

    def test_a_changed_mode_needs_a_new_why(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace('mode = "spans"\n', 'mode = "lines"\n')
                .replace("start = '\\bfn\\s+\\w+'\n", "").replace("end = '[{;]'\n", ""))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("untyped (R4): end, mode, start changed from the base without a new why", out)

    def test_a_narrowed_scope_at_max_0_without_a_why_fails(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config(routes=0, why="").replace("pattern = '/api/'", "pattern = '/api/zzz'"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("routes (R1): pattern changed from the base without a new why", out)
        self.assertIn("| `routes` | R1 | 1 | 0 | 0 | rescoped |", out)

    def test_a_removed_report_fails(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().split("[[report]]")[0])
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("pub (R5): the report is in the base and gone here", out)

    def test_a_narrowed_report_needs_a_new_why(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace("pattern = '^pub '", "pattern = '^pub fn '"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("pub (R5): pattern changed from the base without a new why", out)

    def test_a_lowered_top_needs_a_new_why(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace('files = ["src/**"]\n', 'files = ["src/**"]\ntop = 3\n'))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("pub (R5): top changed from the base without a new why", out)

    def test_a_rescoped_report_with_a_why_holds(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace("pattern = '^pub '", "pattern = '^pub fn '") + 'why = "functions only, as the types are counted elsewhere"\n')
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def test_a_report_top_written_at_its_default_is_not_a_change(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config() + "top = 10\n")
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def test_a_key_written_at_its_default_is_not_a_change(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config().replace('id = "routes"\n', 'id = "routes"\nmode = "lines"\n'))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def test_a_changed_scope_with_a_new_why_holds(self):
        r = base_repo()
        r.commit()
        r.write("architecture.toml", config(routes=2, why="the adapter counted too, until step 4")
                .replace('allowed = ["src/adapter.rs"]\n', ""))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 | 1 | 2 | 2 | holds |", out)

    def test_a_check_removed_from_the_base_fails(self):
        r = base_repo()
        r.commit()
        text = config()
        r.write("architecture.toml", text[: text.index("[[check]]\nid = \"untyped\"")] + text[text.index("[[report]]"):])
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("untyped (R4): the check is in the base and gone here", out)

    def test_a_base_without_the_file_is_noted(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        r.write("readme", "x\n")
        r.commit()
        r.write("architecture.toml", config(routes=0, untyped=0))
        r.write("src/a.rs", "fn a() {}\n")
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("has no architecture.toml", out)


class Standard(unittest.TestCase):
    def breaking(self, standard):
        r = base_repo(standard=standard)
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        return r

    def test_v2_is_enforced(self):
        code, out = self.breaking("v2").run()
        self.assertEqual(code, 1, out)

    def test_v1_is_skipped(self):
        code, out = self.breaking("v1").run()
        self.assertEqual(code, 0, out)
        self.assertIn("Skipped: this repository's standard is v1", out)

    def test_no_file_is_skipped(self):
        code, out = self.breaking(None).run()
        self.assertEqual(code, 0, out)
        self.assertIn("is not set (no tehas.toml)", out)

    def test_force_runs_the_checks_at_v1(self):
        code, out = self.breaking("v1").run("--force")
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)

    def test_comments_and_blank_lines_before_the_value(self):
        code, _ = self.breaking(f'# the architecture method\n\n[standard]\n# the version\nurl = "{URL}"\nversion = "v2"').run()
        self.assertEqual(code, 1)

    def test_a_later_standard_needs_a_later_script(self):
        # v3 is this script's own; the first later one is v4
        code, out = self.breaking("v4").run()
        self.assertEqual(code, 2)
        self.assertIn("standard v4 is newer than this script; this script is tehas-standard v3, "
                      "take the script of v4 for v4", out)

    def test_another_value_is_refused(self):
        code, out = self.breaking("strict").run()
        self.assertEqual(code, 2)
        self.assertIn("'strict' is not a standard", out)

    def test_a_table_without_a_version_is_refused(self):
        code, out = self.breaking("[standard]").run()
        self.assertEqual(code, 2)
        self.assertIn("[standard] has no version", out)

    def test_an_unknown_key_in_the_table_is_refused(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v2"\nstrict = true').run()
        self.assertEqual(code, 2)
        self.assertIn("keys this script does not know: strict", out)

    def test_other_tables_are_left_to_their_owners(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v2"\n\n[kit]\nversion = "3"').run()
        self.assertEqual(code, 1, out)

    def test_a_file_without_the_table_is_refused(self):
        for text in ['[kit]\nversion = "3"', '[Standard]\nversion = "v2"', '[standards]\nversion = "v2"', 'version = "v2"\n[x]', "# empty\n[x]"]:
            with self.subTest(text=text):
                code, out = self.breaking(text).run()
                self.assertEqual(code, 2, out)
                self.assertIn("no [standard] table", out)

    def test_standard_that_is_not_a_table_is_refused(self):
        for text in ['standard = "v2"\n[x]', '[[standard]]\nversion = "v2"']:
            with self.subTest(text=text):
                code, out = self.breaking(text).run()
                self.assertEqual(code, 2, out)
                self.assertIn("[standard] must be a table", out)

    def test_an_old_file_that_is_not_utf8_is_refused(self):
        r = self.breaking(None)
        os.makedirs(os.path.join(r.root, ".tehas"), exist_ok=True)
        with open(os.path.join(r.root, ".tehas/coding-standard"), "wb") as f:
            f.write(b"v\xff\n")
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("not UTF-8", out)

    def test_a_symlink_is_refused_even_dangling(self):
        r = self.breaking(None)
        r.write(".tehas/coding-standard", "v1\n")
        os.symlink("nowhere.toml", os.path.join(r.root, "tehas.toml"))
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("a symlink", out)

    def downgrade(self, before, after):
        r = base_repo(standard=None)
        if before:
            r.write(*before)
        r.commit()
        for name in ("tehas.toml", ".tehas/coding-standard"):
            path = os.path.join(r.root, name)
            if os.path.lexists(path):
                os.remove(path)
        if after:
            r.write(*after)
        return r.run("--base", "main")

    def test_a_lower_standard_than_the_base_is_refused(self):
        code, out = self.downgrade(("tehas.toml", pointer("v2")), ("tehas.toml", pointer("v1")))
        self.assertEqual(code, 2, out)
        self.assertIn("the standard goes down from v2 at main to v1", out)

    def test_removing_the_file_the_base_has_is_refused(self):
        code, out = self.downgrade(("tehas.toml", pointer("v2")), None)
        self.assertEqual(code, 2, out)
        self.assertIn("goes down from v2 at main to none", out)

    def test_the_move_from_the_old_file_is_not_a_downgrade(self):
        code, out = self.downgrade((".tehas/coding-standard", "v2\n"), ("tehas.toml", pointer("v2")))
        self.assertNotIn("goes down", out)
        self.assertNotEqual(code, 2, out)

    def test_going_up_is_fine(self):
        code, out = self.downgrade(("tehas.toml", pointer("v1")), ("tehas.toml", pointer("v2")))
        self.assertNotIn("goes down", out)
        self.assertNotEqual(code, 2, out)

    def test_platform_names_the_toolchains(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v2"\n\n[platform]\nrust = "1.x"\ntypescript = "7.x"').run()
        self.assertEqual(code, 1, out)

    def test_platform_refuses_an_unknown_key(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v2"\n\n[platform]\nos = "linux"').run()
        self.assertEqual(code, 2, out)
        self.assertIn("[platform] has a key this script does not know: os", out)

    def test_platform_refuses_a_major_the_standard_does_not_allow(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v2"\n\n[platform]\nrust = "2.x"').run()
        self.assertEqual(code, 2, out)
        self.assertIn("[platform] rust = '2.x'; this standard allows 1.x", out)

    def test_platform_must_be_a_table(self):
        code, out = self.breaking(f'platform = "rust"\n[standard]\nurl = "{URL}"\nversion = "v2"').run()
        self.assertEqual(code, 2, out)
        self.assertIn("[platform] must be a table", out)

    def test_platform_is_checked_at_v1_too(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = "v1"\n\n[platform]\nrust = "0.x"').run()
        self.assertEqual(code, 2, out)

    def test_an_unresolvable_base_is_refused(self):
        r = base_repo(standard="v1")
        r.commit()
        code, out = r.run("--base", "no-such-ref")
        self.assertEqual(code, 2, out)
        self.assertIn("--base no-such-ref: not a commit", out)

    def test_a_base_outside_a_repository_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = architecture.main(["--root", root, "--summary", os.devnull, "--base", "main"])
            self.assertEqual(code, 2, out.getvalue() + err.getvalue())

    def test_a_directory_is_refused_at_either_name(self):
        for name in ("tehas.toml", ".tehas/coding-standard"):
            with self.subTest(name=name):
                r = self.breaking(None)
                os.makedirs(os.path.join(r.root, name))
                code, out = r.run()
                self.assertEqual(code, 2, out)

    def test_a_symlink_is_refused_at_the_old_name(self):
        r = self.breaking(None)
        r.write(".tehas/v1.txt", "v1\n")
        os.symlink("v1.txt", os.path.join(r.root, ".tehas/coding-standard"))
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("a symlink", out)

    def test_a_symlink_to_a_good_file_is_refused(self):
        r = self.breaking(None)
        r.write("real.toml", pointer("v2"))
        os.symlink("real.toml", os.path.join(r.root, "tehas.toml"))
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("a symlink", out)

    def test_a_symlink_at_the_base_is_named(self):
        r = base_repo(standard=None)
        r.write("real.toml", pointer("v2"))
        os.symlink("real.toml", os.path.join(r.root, "tehas.toml"))
        r.git("add", "tehas.toml")
        r.commit()
        os.remove(os.path.join(r.root, "tehas.toml"))
        r.write("tehas.toml", pointer("v2"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("not a regular file (mode 120000)", out)

    def test_a_table_without_a_url_is_refused(self):
        code, out = self.breaking('[standard]\nversion = "v2"').run()
        self.assertEqual(code, 2, out)
        self.assertIn("[standard] has no url", out)

    def test_another_standard_is_refused(self):
        code, out = self.breaking('[standard]\nurl = "https://example.org/other-standard"\nversion = "v2"').run()
        self.assertEqual(code, 2, out)
        self.assertIn("another standard brings its own script", out)

    def test_removing_a_platform_key_the_base_has_is_refused(self):
        code, out = self.downgrade(("tehas.toml", pointer("v2") + '\n[platform]\nrust = "1.x"\ntypescript = "7.x"\n'),
                                   ("tehas.toml", pointer("v2") + '\n[platform]\nrust = "1.x"\n'))
        self.assertEqual(code, 2, out)
        self.assertIn("[platform] loses typescript", out)

    def test_a_platform_value_that_is_not_a_string_is_refused(self):
        for extra in ['rust = ["1.x"]', '[platform.rust]\nmajor = "1"']:
            with self.subTest(extra=extra):
                text = pointer("v2") + ("\n[platform]\n" + extra if not extra.startswith("[") else "\n" + extra)
                code, out = self.breaking(text).run()
                self.assertEqual(code, 2, out)
                self.assertIn("this standard allows", out)

    def test_a_symlinked_tehas_directory_is_refused(self):
        r = self.breaking(None)
        r.write("real/coding-standard", "v1\n")
        os.symlink("real", os.path.join(r.root, ".tehas"))
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn(".tehas/coding-standard: a symlink, or under one (.tehas)", out)

    def test_a_symlinked_tehas_directory_at_the_base_is_refused(self):
        r = base_repo(standard=None)
        r.write("real/coding-standard", "v2\n")
        os.symlink("real", os.path.join(r.root, ".tehas"))
        r.git("add", ".tehas")
        r.commit()
        os.remove(os.path.join(r.root, ".tehas"))
        r.write("tehas.toml", pointer("v1"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn(":.tehas: a symlink", out)

    def test_an_empty_file_is_refused(self):
        r = self.breaking(None)
        r.write("tehas.toml", "")
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("no [standard] table", out)

    def test_a_version_that_is_not_a_string_is_refused(self):
        code, out = self.breaking(f'[standard]\nurl = "{URL}"\nversion = 2').run()
        self.assertEqual(code, 2)
        self.assertIn("the version must be a string", out)

    def test_a_minor_needs_a_later_script(self):
        # v2.1 and v3.1 are this script's to enforce; a minor of v4 is not
        code, out = self.breaking("v4.1").run()
        self.assertEqual(code, 2)
        self.assertIn("standard v4.1 is newer than this script", out)

    def test_a_file_that_is_not_utf8_is_refused(self):
        r = self.breaking(None)
        os.makedirs(os.path.join(r.root, ".tehas"), exist_ok=True)
        with open(os.path.join(r.root, "tehas.toml"), "wb") as f:
            f.write(f'[standard]\nurl = "{URL}"\n'.encode() + b'version = "\xff"\n')
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("not UTF-8", out)

    def test_bad_toml_is_refused(self):
        code, out = self.breaking("[standard\nversion = v2").run()
        self.assertEqual(code, 2)
        self.assertIn("not valid TOML", out)

    def test_the_old_name_is_read_for_v1(self):
        r = self.breaking(None)
        r.write(".tehas/coding-standard", "v1\n")
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("Skipped: this repository's standard is v1", out)

    def test_the_old_name_with_v2_asks_for_the_move(self):
        r = self.breaking(None)
        r.write(".tehas/coding-standard", "v2\n")
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn(f'.tehas/coding-standard says v2; move it to tehas.toml as [standard] url = "{URL}", version = "v2"', out)

    def test_both_files_at_once_are_refused(self):
        r = self.breaking("v2")
        r.write(".tehas/coding-standard", "v1\n")
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("are both here; keep tehas.toml alone", out)

    def test_an_empty_old_file_is_refused(self):
        r = self.breaking(None)
        r.write(".tehas/coding-standard", "# nothing\n")
        code, out = r.run()
        self.assertEqual(code, 2)
        self.assertIn("empty", out)


class Config(unittest.TestCase):
    def test_every_problem_at_once_and_exit_2(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        r.write("architecture.toml", 'version = 1\nextra = 1\n[[check]]\nid = "a"\nrule = "R11"\nmode = "spans"\npattern = "("\n')
        code, out = r.run()
        self.assertEqual(code, 2)
        for want in ("unknown key 'extra'", "what is missing", "files is missing", "max is missing",
                     "rule must be one of R1 to R10", "mode spans needs start", "pattern:"):
            self.assertIn(want, out)

    def test_the_wrong_version_is_refused(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        r.write("architecture.toml", "version = 2\n")
        code, out = r.run()
        self.assertEqual(code, 2)
        self.assertIn("version must be 1", out)

    def test_start_and_end_belong_to_spans(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        r.write("architecture.toml", config().replace('mode = "spans"\n', ""))
        code, out = r.run()
        self.assertEqual(code, 2)
        self.assertIn("start and end are for mode spans", out)


class Globs(unittest.TestCase):
    def test_double_star_crosses_directories_and_star_does_not(self):
        g = architecture.glob_re("src/**/*.rs")
        self.assertTrue(g.match("src/a.rs"))
        self.assertTrue(g.match("src/web/api.rs"))
        self.assertFalse(g.match("src/a.rsx"))
        self.assertFalse(architecture.glob_re("src/*.rs").match("src/web/api.rs"))


def hits(entry, files):
    """count() on in-memory files: {path: text}."""
    base = {"id": "x", "rule": "R4", "what": "x", "files": ["**"], "max": 0}
    return [(p, n) for p, n, _ in architecture.count({**base, **entry}, sorted(files), files.get)]


class Standards(unittest.TestCase):
    """The standard patterns catch what the 2026-11-24 dry-run grade of
    of one repository found its own patterns let through."""

    def test_untyped_fields_behind_newtypes_aliases_and_narrow_pub(self):
        src = "\n".join([
            "pub struct AsCame(Value);",              # 1 a newtype, its field private
            "pub(crate) struct Doc(pub Value);",      # 2
            "pub type Raw = serde_json::Value;",       # 3 an alias
            "type Map = BTreeMap<String, Value>;",     # 4
            "pub struct S {",
            "    pub(crate) basis: Value,",            # 6 pub(crate)
            "    pub(super) pin: Option<Value>,",      # 7
            "    pub doc: Verbatim,",                  # a typed field
            "    private: Value,",                     # private to the module
            "}",
            "pub enum Place {",
            "    AsCame(Value),",                      # 12 a tuple variant
            "    Typed(Ticket),",
            "}",
            "let v = Value::Null;",                    # a path into Value
            "// pub x: Value,",                        # a comment
        ])
        self.assertEqual(hits({"standard": "rust-untyped-field"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (1, 2, 3, 4, 6, 7, 12)])

    def test_untyped_signatures_whatever_their_qualifiers(self):
        src = "\n".join([
            "pub(crate) async fn a(v: &Value) {}",     # 1
            "pub(super) const fn b() -> u8 { 0 }",
            "unsafe fn c(",                            # 3 across lines
            "    v: Option<Value>,",
            ") -> u8 {",
            "fn d() { Value::Null; }",                 # a body is not a signature
            "    fn e(&self) -> Value;",               # 7 a trait method
        ])
        self.assertEqual(hits({"standard": "rust-untyped-signature"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (1, 3, 7)])

    def test_public_items_count_re_exports(self):
        src = "pub use crate::web::Site;\npub(crate) use x::*;\npub fn f() {}\npub(crate) mod m;\nuse y::Z;\nfn g() {}\n"
        self.assertEqual(hits({"standard": "rust-public-item"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (1, 2, 3, 4)])

    def test_rust_inward_is_an_allowlist_through_super_groups_and_lines(self):
        files = {"crates/o/src/decide/x.rs": "\n".join([
            "use super::state::Stage;",               # decide::state: allowed
            "use super::super::web::Site;",           # 2 web, through super::super
            "use crate::{plain::Plain, web};",        # 3 grouped
            "use crate::{",                           # 4 across lines
            "    plain::Line,",
            "    store::Store,",
            "};",
            "use std::fs;",                           # another crate
            "fn f() { crate::decide::y::g(); crate::live::push(); }",  # 9
            "use crate::plain::secret::Key;",        # 10 never
            "// use crate::web;",
        ])}
        entry = {"standard": "rust-inward", "only": ["decide", "plain"], "never": ["plain::secret"]}
        self.assertEqual(hits(entry, files), [("crates/o/src/decide/x.rs", n) for n in (2, 3, 4, 9, 10)])

    def test_rust_inward_reads_super_from_an_inline_module(self):
        files = {"src/decide.rs": "\n".join([
            "pub fn f() {}",
            "mod inner { }",
            "#[cfg(test)]",
            "mod tests {",
            "    use super::f;",                       # decide::f: allowed
            "    use super::super::web;",              # 6 web
            "    fn g() { let s = \"}\"; }",
            "}",
            "use super::web::Site;",                  # 9 web, from decide
        ])}
        entry = {"standard": "rust-inward", "only": ["decide"]}
        self.assertEqual(hits(entry, files), [("src/decide.rs", 6), ("src/decide.rs", 9)])

    def test_rust_inward_catches_a_port_that_reaches_its_adapter(self):
        files = {"crates/o/src/supplier.rs": "mod http;\npub mod read;\npub use http::HttpSupplier;\nuse crate::answers::Ticket;\n"}
        entry = {"standard": "rust-inward", "only": ["answers", "supplier"], "never": ["supplier::http", "supplier::read"]}
        self.assertEqual(hits(entry, files), [("crates/o/src/supplier.rs", n) for n in (1, 2, 3)])

    def test_js_inward_is_an_allowlist_of_files(self):
        files = {"a/x.model.js": "\n".join([
            'import { t } from "./app-text.js";',
            'import {',
            '  board,',
            '} from "./app-board.js";',            # 4
            'const k = await import("./kit/k.js");',  # 5
            'import "./app-route.js";',
            'import { h } from "preact";',            # a package
        ])}
        entry = {"standard": "js-inward", "only": ["a/app-text.js", "a/app-route.js", "a/*.model.js"]}
        self.assertEqual(hits(entry, files), [("a/x.model.js", 4), ("a/x.model.js", 5)])

    def test_cargo_deps_is_an_allowlist_by_package(self):
        files = {"c/Cargo.toml": "\n".join([
            "[package]",
            'name = "core"',
            "[dependencies]",
            'serde = "1"',
            'net = { path = "../net" }',               # 5
            'web2 = { package = "web", path = "../web" }',  # 6 by its package
            "[target.'cfg(unix)'.dependencies]",
            'libc = "0.2"',                            # 8
            "[dev-dependencies]",
            'testing = { path = "../testing" }',
        ])}
        entry = {"standard": "cargo-deps", "only": ["serde", "web2"]}
        self.assertEqual(hits(entry, files), [("c/Cargo.toml", n) for n in (5, 6, 8)])

    def test_a_standard_cannot_be_narrowed_or_mixed(self):
        for extra, said in (
            ({"pattern": "x", "standard": "rust-public-item"}, "exactly one of pattern and standard"),
            ({}, "exactly one of pattern and standard"),
            ({"standard": "rust-public-item", "mode": "spans", "start": "a", "end": "b"}, "mode is fixed by the standard"),
            ({"standard": "rust-inward"}, "needs only"),
            ({"standard": "rust-public-item", "only": ["a"]}, "only is for the standards"),
            ({"pattern": "x", "never": ["a"]}, "only and never need a standard"),
            ({"standard": "rust-nothing"}, "standard must be one of"),
        ):
            c = {"id": "c", "rule": "R4", "what": "w", "files": ["**"], "max": 0, **extra}
            with self.assertRaises(architecture.ConfigError) as e:
                architecture.parse(_toml(c), "t")
            self.assertIn(said, str(e.exception), extra)

    def test_changing_only_is_a_rescope_that_needs_a_new_why(self):
        r = Repo()
        r.write("tehas.toml", pointer("v2"))
        toml = 'version = 1\n[[check]]\nid = "in"\nrule = "R8"\nwhat = "inward"\nstandard = "rust-inward"\nonly = [{only}]\nfiles = ["src/decide/**"]\nmax = 0\nwhy = "the core"\n'
        r.write("architecture.toml", toml.format(only='"decide"'))
        r.write("src/decide/a.rs", "use crate::decide::b;\n")
        r.commit()
        r.write("architecture.toml", toml.format(only='"decide", "web"'))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 1)
        self.assertIn("in (R8): only changed from the base without a new why", out)


class StandardsReviewed(unittest.TestCase):
    """What the independent review of the draft found (2026-11-24)."""

    def test_a_use_tree_with_a_comment_or_raw_ident_ends(self):
        files = {"src/core.rs": "use crate::{\n  core::a, // note\n  web::b, /* x */\n};\nuse crate::r#web::c;\n"}
        self.assertEqual(hits({"standard": "rust-inward", "only": ["core"]}, files), [("src/core.rs", 1), ("src/core.rs", 5)])

    def test_a_glob_of_the_root_is_the_root(self):
        files = {"src/core.rs": "use crate::*;\nuse super::*;\nfn f() { crate::core::g(); }\n"}
        self.assertEqual(hits({"standard": "rust-inward", "only": ["core"]}, files), [("src/core.rs", 1), ("src/core.rs", 2)])
        self.assertEqual(hits({"standard": "rust-inward", "only": ["core", "crate"]}, files), [])

    def test_braces_in_comments_and_strings_do_not_move_modules(self):
        files = {"src/core/x.rs": 'mod t {\n    let a = 1; // {\n    let b = "{\n    {";\n    /* { */\n}\nfn f() { super::y::g(); }\n'}
        self.assertEqual(hits({"standard": "rust-inward", "only": ["core::x"]}, files), [("src/core/x.rs", 7)])

    def test_the_crate_reached_by_its_own_name(self):
        files = {"crates/my-lib/src/main.rs": "use my_lib::web::x;\nuse std::fs;\n",
                 "crates/my-lib/tests/it.rs": "use my_lib::core::y;\nmod common;\nuse common::z;\n"}
        self.assertEqual(hits({"standard": "rust-inward", "only": ["core", "common"]}, files),
                         [("crates/my-lib/src/main.rs", 1)])

    def test_enum_variants_wrapped_aliases_and_one_line_structs(self):
        src = "\n".join([
            "pub enum E {",
            "    Foo { v: Value },",                     # 2 a struct variant
            "    Bar {",                                 # 3
            "        w: Value,",
            "    },",
            "    Baz(HashMap<String, Value>), // x",     # 6
            "    Qux(",                                  # 7
            "        Value,",
            "    ),",
            "    Typed(u8),",
            "}",
            "type J =",                                  # 12
            "    Value;",
            "pub struct S { pub v: Value }",            # 14
            "struct P { v: Value }",                    # private
            "pub x: u8, // not a Value",
        ])
        self.assertEqual(hits({"standard": "rust-untyped-field"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (2, 3, 6, 7, 12, 14)])

    def test_signatures_past_const_generics_and_inside_one_line_impls(self):
        src = "fn f(x: S<{1}>, v: Value) {}\nimpl X { fn g(v: Value) {} }\nfn h(a: [u8; 3], v: Value) {}\n"
        self.assertEqual(hits({"standard": "rust-untyped-signature"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (1, 2, 3)])

    def test_public_items_with_attributes_macros_and_extern_crates(self):
        src = '#[cfg(x)] pub fn f() {}\n#[macro_export]\nmacro_rules! m { () => {} }\npub extern crate serde;\n// pub fn g() {}\nlet s = "pub fn h";\n'
        self.assertEqual(hits({"standard": "rust-public-item"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (1, 2, 4)])

    def test_js_require_templates_dots_and_split_lines(self):
        files = {"a/b/m.js": "\n".join([
            'const x = require("../ui/b.js");',     # 1
            'const y = await import(`../ui/c.js`);', # 2
            'import d from "..";',                  # 3
            'export * from',                        # 4
            '  "./e.js";',
            '/* import z from "./z.js" */',
            '// import w from "./w.js";',
            'import ok from "./ok.js";',
        ])}
        self.assertEqual(hits({"standard": "js-inward", "only": ["a/b/ok.js"]}, files),
                         [("a/b/m.js", n) for n in (1, 2, 3, 4)])

    def test_odd_configs_are_refused_not_crashes(self):
        c = {"id": "c", "rule": "R4", "what": "w", "files": ["**"], "max": 0, "standard": ["x"]}
        with self.assertRaises(architecture.ConfigError):
            architecture.parse(_toml(c), "t")
        files = {"c/Cargo.toml": 'target = 3\ndependencies = "x"\n'}
        self.assertEqual(hits({"standard": "cargo-deps", "only": ["serde"]}, files), [])


class StandardsReviewedAgain(unittest.TestCase):
    """What the second review of the draft found (2026-11-24)."""

    def test_js_slash_star_in_a_string_hides_no_import(self):
        files = {"web/a.js": 'const g = "src/**/*.js";\nimport x from "../ui/b.js";\nconst u = "http://x/*";\nimport y from "../ui/c.js";\n/* c */\n/** doc */\n'}
        self.assertEqual(hits({"standard": "js-inward", "only": ["web/**"]}, files), [("web/a.js", 2), ("web/a.js", 4)])

    def test_js_a_directory_and_a_computed_specifier(self):
        files = {"web/core/a.js": 'import i from "./";\nimport j from ".";\nconst m = await import(`../ui/${n}.js`);\n'}
        self.assertEqual(hits({"standard": "js-inward", "only": ["web/core/**"]}, files), [("web/core/a.js", 3)])

    def test_nested_crates_take_their_own_root(self):
        self.assertEqual(architecture.rust_crate("examples/demo/src/main.rs"), ("demo", []))
        self.assertEqual(architecture.rust_crate("tests/fixtures/p/src/lib.rs"), ("p", []))
        self.assertEqual(architecture.rust_crate("crates/foo/tests/it/main.rs"), ("foo", []))
        self.assertEqual(architecture.rust_crate("crates/foo/tests/it/common.rs"), ("foo", ["common"]))
        self.assertEqual(architecture.rust_crate("crates/foo/src/a/mod.rs"), ("foo", ["a"]))

    def test_the_crate_by_its_package_name_and_dollar_crate(self):
        files = {"crates/foo/Cargo.toml": '[package]\nname = "tehas-foo"\n',
                 "crates/foo/tests/it.rs": "use tehas_foo::web::a;\n",
                 "crates/foo/src/core.rs": "macro_rules! m { () => { $crate::web::g() } }\nfn f() { use crate::{web::b}; }\n"}
        entry = {"standard": "rust-inward", "only": ["core"], "files": ["**/*.rs"]}
        self.assertEqual(hits(entry, files), [("crates/foo/src/core.rs", 1), ("crates/foo/src/core.rs", 2), ("crates/foo/tests/it.rs", 1)])

    def test_fields_wrapped_generic_and_late_braced(self):
        src = "\n".join([
            "pub struct A {",
            "    pub v: HashMap<",                       # 2 wrapped
            "        String,",
            "        Value,",
            "    >,",
            "}",
            "pub struct S { pub a: u8, b: Value }",     # private b: not counted
            "pub struct T<X: Into<Vec<u8>>>(Value);",   # 8 nested generics
            "pub type J<X = Vec<u8>> = Value;",         # 9
            "pub enum E<X>",
            "where X: Clone",
            "{",
            "    W(Value),",                             # 13
            "}",
        ])
        self.assertEqual(hits({"standard": "rust-untyped-field"}, {"src/a.rs": src}),
                         [("src/a.rs", n) for n in (2, 8, 9, 13)])

    def test_every_fn_on_a_line_and_macro_export_with_args(self):
        sig = "trait T { fn f(&self) -> u8; fn g(&self, v: Value); }\n"
        self.assertEqual(hits({"standard": "rust-untyped-signature"}, {"src/a.rs": sig}), [("src/a.rs", 1)])
        sig2 = "trait T { fn f(&self) -> u8; }\n"
        self.assertEqual(hits({"standard": "rust-untyped-signature"}, {"src/a.rs": sig2}), [])
        pubs = "#[macro_export(local_inner_macros)]\nmacro_rules! m { () => {} }\n"
        self.assertEqual(hits({"standard": "rust-public-item"}, {"src/a.rs": pubs}), [("src/a.rs", 1)])


class FollowUps(unittest.TestCase):
    """The review nits after revision 5 of the pointer patch, 1 to 9."""

    def repo_at(self, files, commit=True):
        """A repository at v2 whose base holds `files` ({path: text or bytes})
        beside its architecture.toml and sources."""
        r = base_repo(standard=None)
        for path, text in files.items():
            full = os.path.join(r.root, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as f:
                f.write(text if isinstance(text, bytes) else text.encode())
            r.git("add", path)
        if commit:
            r.commit()
        return r

    def head(self, r, files):
        for name in ("tehas.toml", ".tehas/coding-standard"):
            if os.path.lexists(os.path.join(r.root, name)):
                r.git("rm", "-qf", name)
        for path, text in files.items():
            r.write(path, text)

    def test_1_each_pointer_is_parsed_once(self):
        r = self.repo_at({"tehas.toml": pointer("v2") + '\n[platform]\nrust = "1.x"\n'})
        with mock.patch.object(architecture, "parse_toml", wraps=architecture.parse_toml) as p:
            code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertEqual(p.call_count, 1)
        with mock.patch.object(architecture, "parse_toml", wraps=architecture.parse_toml) as p:
            code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertEqual([c.args[1] for c in p.call_args_list], ["tehas.toml", "main:tehas.toml"])

    def test_2_a_base_with_both_files_takes_the_higher(self):
        r = self.repo_at({"tehas.toml": pointer("v1"), ".tehas/coding-standard": "v2\n"})
        self.head(r, {"tehas.toml": pointer("v1")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("the standard goes down from v2 at main to v1", out)
        r = self.repo_at({"tehas.toml": pointer("v2"), ".tehas/coding-standard": "v1\n"})
        self.head(r, {"tehas.toml": pointer("v2")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def test_3_a_non_table_platform_at_the_base_is_compared(self):
        base = 'platform = "rust"\n' + pointer("v2")
        r = self.repo_at({"tehas.toml": base})
        self.head(r, {"tehas.toml": pointer("v2")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("main:tehas.toml: [platform] is there (not a table) and this head has none", out)
        self.head(r, {"tehas.toml": pointer("v2") + '\n[platform]\nrust = "1.x"\n'})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def subdirectory(self, base_top=None):
        """A repository whose part lives in sub/: its own tehas.toml and
        architecture.toml there, and maybe another tehas.toml at the top."""
        r = Repo()
        if base_top:
            r.write("tehas.toml", pointer(base_top))
        r.write("sub/tehas.toml", pointer("v2"))
        r.write("sub/architecture.toml", config())
        r.write("sub/src/adapter.rs", 'fn get() { call("/api/a") }\n')
        r.write("sub/src/web.rs", 'fn page(v: Value) { call("/api/c") }\n')
        r.write("sub/src/core.rs", "pub fn decide() {}\n")
        r.commit()
        return r

    def run_sub(self, r, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = architecture.main(["--root", os.path.join(r.root, "sub"), "--summary", os.devnull, *args])
        return code, out.getvalue() + err.getvalue()

    def test_4_the_base_is_read_relative_to_root(self):
        r = self.subdirectory(base_top="v1")
        code, out = self.run_sub(r, "--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 | 1 | 1 | 1 | holds |", out)
        r.write("sub/tehas.toml", pointer("v1"))
        code, out = self.run_sub(r, "--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("the standard goes down from v2 at main to v1", out)

    def test_4_a_raised_max_under_root_is_seen_against_the_base(self):
        r = self.subdirectory()
        r.write("sub/architecture.toml", config(routes=2))
        r.write("sub/src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = self.run_sub(r, "--base", "main")
        self.assertEqual(code, 1, out)
        self.assertIn("max raised from 1 to 2 without a new why", out)

    def test_4_a_symlink_under_root_at_the_base_is_named(self):
        r = Repo()
        r.write("sub/real.toml", pointer("v2"))
        os.symlink("real.toml", os.path.join(r.root, "sub/tehas.toml"))
        r.git("add", "sub/tehas.toml")
        r.commit()
        os.remove(os.path.join(r.root, "sub/tehas.toml"))
        r.write("sub/tehas.toml", pointer("v2"))
        code, out = self.run_sub(r, "--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("main:tehas.toml: not a regular file (mode 120000)", out)

    def test_5_the_pointer_constants_sit_together(self):
        with open(architecture.__file__, encoding="utf-8") as f:
            text = f.read()
        block = text[text.index("STANDARD_FILE = "):text.index("ENFORCED = ")]
        for name in ("OLD_STANDARD_FILE", "STANDARD_KEYS", "STANDARD_URL", "PLATFORM_ALLOWED", "STANDARDS"):
            self.assertIn(f"\n{name} = ", block)

    def test_the_first_line_after_the_docstring_names_the_version(self):
        with open(architecture.__file__, encoding="utf-8") as f:
            text = f.read()
        after = text.split('"""', 2)[2]
        self.assertEqual(after.split("\n")[1], f"# tehas-standard {architecture.SCRIPT}")
        self.assertEqual(after.split("\n")[1], "# tehas-standard v3")

    def test_6_the_skip_hint_can_be_followed_as_written(self):
        r = base_repo(standard=None)
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run()
        self.assertEqual(code, 0, out)
        table = out.split("```toml\n", 1)[1].split("```", 1)[0]
        self.assertIn(f'url = "{URL}"', table)
        r.write("tehas.toml", table)
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)

    def test_7_a_malformed_base_file_can_be_repaired(self):
        for broken in ("[standard\nversion = v2\n", b"[standard]\nversion = \"\xff\"\n", "[standard]\nversion = \"v2\"\n",
                       f'[standard]\nurl = "{URL}"\nversion = "strict"\n', "# nothing\n"):
            with self.subTest(broken=broken):
                r = self.repo_at({"tehas.toml": broken})
                self.head(r, {"tehas.toml": pointer("v2")})
                code, out = r.run("--base", "main")
                self.assertEqual(code, 0, out)
                self.assertIn("The base's standard cannot be read (main:tehas.toml:", out)
                parses = not isinstance(broken, bytes) and not broken.startswith("[standard\n")
                self.assertIn("its [platform] is compared" if parses
                              else "the base's [platform] is not compared", out)

    def test_7_a_repair_keeps_the_base_toolchains(self):
        bad = f'[standard]\nurl = "{URL}"\nversion = "strict"\n\n[platform]\nrust = "1.x"\n'
        r = self.repo_at({"tehas.toml": bad})
        self.head(r, {"tehas.toml": pointer("v2")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("[platform] loses rust against main", out)
        self.head(r, {"tehas.toml": pointer("v2") + '\n[platform]\nrust = "1.x"\n'})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("its [platform] is compared", out)

    def test_7_a_malformed_base_file_still_needs_the_highest_standard(self):
        for head in ({"tehas.toml": pointer("v1")}, {}):
            with self.subTest(head=head):
                r = self.repo_at({"tehas.toml": "[standard\n"})
                self.head(r, head)
                code, out = r.run("--base", "main")
                self.assertEqual(code, 2, out)
                self.assertIn("with the base's standard unreadable, this head must name v2", out)

    def test_7_an_unknown_value_in_the_base_old_file_can_be_repaired(self):
        r = self.repo_at({".tehas/coding-standard": "strict\n"})
        self.head(r, {"tehas.toml": pointer("v2")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("main:.tehas/coding-standard: 'strict' is not a standard", out)
        self.head(r, {"tehas.toml": pointer("v1")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)

    def test_7_a_later_standard_at_the_base_is_no_repair(self):
        r = self.repo_at({"tehas.toml": pointer("v4")})
        self.head(r, {"tehas.toml": pointer("v2")})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("main:tehas.toml: standard v4 is newer than this script", out)

    def test_7_a_malformed_head_file_is_still_refused(self):
        r = self.repo_at({"tehas.toml": pointer("v2")})
        self.head(r, {"tehas.toml": "[standard\n"})
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("tehas.toml: not valid TOML", out)

    def test_8_a_push_run_compares_with_nothing(self):
        # Decided: without --base nothing is compared, not even the parent.
        # A workflow that wants the guard on a push passes --base itself.
        r = self.repo_at({"tehas.toml": pointer("v2")})
        r.write("other", "x\n")
        r.commit()
        r.git("rm", "-q", "tehas.toml")
        r.commit()
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("is not set (no tehas.toml)", out)
        code, out = r.run("--base", "HEAD~1")
        self.assertEqual(code, 2, out)
        self.assertIn("goes down from v2 at HEAD~1 to none", out)

    def test_9_the_base_and_the_head_read_alike(self):
        # One pointer() for both trees: the same text gives the same answer.
        for text in (pointer("v2"), pointer("v1") + '\n[platform]\nrust = "1.x"\n'):
            with self.subTest(text=text):
                r = self.repo_at({"tehas.toml": text})
                self.assertEqual(architecture.pointer(architecture.WorkTree(r.root)),
                                 architecture.pointer(architecture.Commit(r.root, "main"), history=True))

    def test_a_byte_that_is_not_utf8_hides_nothing(self):
        r = base_repo()
        with open(os.path.join(r.root, "src/bin.rs"), "wb") as f:
            f.write(b'// caf\xe9\nfn z() { call("/api/z") }\n')
        r.git("add", "src/bin.rs")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)
        self.assertIn("src/bin.rs:2:", out)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads any file")
    def test_a_tracked_file_that_cannot_be_read_stops_the_run(self):
        r = base_repo()
        path = os.path.join(r.root, "src/web.rs")
        os.chmod(path, 0)
        try:
            code, out = r.run()
        finally:
            os.chmod(path, 0o644)
        self.assertEqual(code, 2, out)
        self.assertIn("src/web.rs: tracked, but cannot be read", out)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root reads any file")
    def test_a_tracked_file_under_a_directory_that_cannot_be_read_stops_the_run(self):
        r = base_repo()
        src = os.path.join(r.root, "src")
        os.chmod(src, 0)
        try:
            code, out = r.run()
        finally:
            os.chmod(src, 0o755)
        self.assertEqual(code, 2, out)
        self.assertIn("tracked, but cannot be read", out)

    def test_a_bad_byte_on_the_counted_line_prints(self):
        r = base_repo()
        with open(os.path.join(r.root, "src/bin.rs"), "wb") as f:
            f.write(b'fn z() { call("/api/z") } // \xff\n')
        r.git("add", "src/bin.rs")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("src/bin.rs:1:", out)
        self.assertIn("\ufffd", out)

    def test_a_long_rust_file_is_read_in_linear_time(self):
        # Four times the text takes about four times as long, not sixteen;
        # a ratio, so a busy runner slows both sides alike.
        import time
        line = 'let s = r#"x"#; let c = \'a\'; let t = "y";\n'

        def took(n):
            start = time.perf_counter()
            lines = architecture.rust_code(line * n)
            self.assertEqual(len(lines), n + 1)
            return time.perf_counter() - start
        took(500)
        small, large = min(took(4000) for _ in range(3)), min(took(16000) for _ in range(3))
        self.assertLess(large, small * 9 + 0.05)


RS_ESCAPE = """
[[check]]
id = "rs-escape"
rule = "R12"
what = "no allow"
pattern = '#\\[allow\\('
files = ["src/**/*.rs"]
max = 0
"""


def check(cid, rule, pattern, files, max=0, why="", allowed=()):
    """One [[check]] as TOML text."""
    out = f'\n[[check]]\nid = "{cid}"\nrule = "{rule}"\nwhat = "{cid}"\npattern = \'{pattern}\'\n'
    out += f"files = {list(files)!r}\n".replace("'", '"')
    if allowed:
        out += f"allowed = {list(allowed)!r}\n".replace("'", '"')
    out += f"max = {max}\n" + (f'why = "{why}"\n' if why else "")
    return out


def agents(version):
    return f"# Agents\n\nThis repository follows tehas-standard {version} (`tehas.toml`):\n{URL}/tree/{version}/{version}\n"


def v3_repo(standard="v3", checks=RS_ESCAPE, agents_version=None, **kw):
    """base_repo at `standard`, with what v3 asks of a Rust repository:
    rs-escape and AGENTS.md naming the version."""
    r = base_repo(standard=standard, **kw)
    r.write("architecture.toml", config(**kw) + checks)
    r.write("AGENTS.md", agents(agents_version or standard))
    return r


WEB_CHECKS = RS_ESCAPE + "".join(check(cid, rule, "NEVER", ["**/*.js"]) for cid, rule in (
    ("kit-solid-import", "R11"), ("kit-copy", "R11"), ("kit-own-fetch", "R11"), ("kit-raw-html", "R11"),
    ("vendor-unlisted", "R11"), ("ts-strict", "R12"), ("ts-escape", "R12"), ("model-pure", "R13")))


class Versions(unittest.TestCase):
    """The v3 script knows v1, v2 and v3 and their minors, and enforces
    from v2 on, in order (architecture-script.md items 1, 2, 9)."""

    def test_v3_is_enforced_not_skipped(self):
        r = v3_repo()
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 |  | 1 | 1 | holds |", out)
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)
        self.assertNotIn("Skipped", out)

    def test_v3_1_is_enforced_with_the_checks_of_v3(self):
        r = v3_repo("v3.1")
        code, out = r.run()
        self.assertEqual(code, 0, out)
        r.write("architecture.toml", config())
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("rs-escape (R12): required at v3.1, since it holds Rust", out)

    def test_v2_1_is_enforced_as_v2(self):
        r = base_repo(standard="v2.1")
        code, out = r.run()
        self.assertEqual(code, 0, out)
        r.write("src/core.rs", 'fn x() { call("/api/d") }\n')
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 2 places, 1 allowed", out)

    def test_v4_is_refused_by_name(self):
        for version in ("v4", "v4.1", "v10"):
            with self.subTest(version=version):
                code, out = v3_repo(version).run()
                self.assertEqual(code, 2, out)
                self.assertIn(f"this script is tehas-standard v3, take the script of {version} for {version}", out)

    def test_shapes_that_are_no_version_are_refused(self):
        for version in ("v1.1", "v2.0", "v2.01", "v3.", "V3", "v3.1.2"):
            with self.subTest(version=version):
                code, out = v3_repo(version).run()
                self.assertEqual(code, 2, out)
                self.assertIn(f"{version!r} is not a standard", out)

    def test_minors_rank_by_number(self):
        r = base_repo(standard="v2.10")
        r.commit()
        r.write("tehas.toml", pointer("v2.9"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("the standard goes down from v2.10 at main to v2.9", out)
        r.write("tehas.toml", pointer("v2.11"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)

    def test_with_a_base_at_v3_writing_v2_fails(self):
        r = v3_repo()
        r.commit()
        r.write("tehas.toml", pointer("v2"))
        r.write("AGENTS.md", agents("v2"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("the standard goes down from v3 at main to v2", out)

    def test_with_a_base_at_v3_deleting_the_file_fails(self):
        r = v3_repo()
        r.commit()
        r.git("rm", "-q", "tehas.toml")
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("goes down from v3 at main to none", out)

    def test_with_a_base_at_v3_1_writing_v3_fails(self):
        r = v3_repo("v3.1")
        r.commit()
        r.write("tehas.toml", pointer("v3"))
        r.write("AGENTS.md", agents("v3"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("goes down from v3.1 at main to v3", out)

    def test_v3_in_the_old_file_asks_for_the_move(self):
        r = v3_repo(standard=None)
        r.write(".tehas/coding-standard", "v3\n")
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn(f'.tehas/coding-standard says v3; move it to tehas.toml as [standard] url = "{URL}", version = "v3"', out)

    def test_an_unreadable_base_that_spells_v3_needs_v3_at_the_head(self):
        r = base_repo(standard=None)
        r.write("tehas.toml", '[standard]\nversion = "v3"\n')     # no url: unreadable
        r.commit()
        r.write("tehas.toml", pointer("v2"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 2, out)
        self.assertIn("this head must name v3 or later, the highest version the base's pointer spells out", out)
        r.write("tehas.toml", pointer("v3"))
        r.write("architecture.toml", config() + RS_ESCAPE)
        r.write("AGENTS.md", agents("v3"))
        code, out = r.run("--base", "main")
        self.assertEqual(code, 0, out)
        self.assertIn("This head names v3, at or above v3", out)


class Rules(unittest.TestCase):
    """A check's rule is one of its version's rules (item 3)."""

    def test_r11_to_r14_are_accepted_at_v3(self):
        for rule in ("R11", "R12", "R13", "R14"):
            with self.subTest(rule=rule):
                r = v3_repo(checks=RS_ESCAPE + check("extra", rule, "NEVER", ["src/**/*.rs"]))
                code, out = r.run()
                self.assertEqual(code, 0, out)
                self.assertIn(f"| `extra` | {rule} |", out)

    def test_r15_is_refused_by_name_at_v3(self):
        r = v3_repo(checks=RS_ESCAPE + check("extra", "R15", "NEVER", ["src/**/*.rs"]))
        code, out = r.run()
        self.assertEqual(code, 2, out)
        self.assertIn("check extra: rule must be one of R1 to R14; R15 is not a rule of v3", out)

    def test_r11_is_refused_by_name_at_v2(self):
        for version in ("v2", "v2.1"):
            with self.subTest(version=version):
                r = base_repo(standard=version)
                r.write("architecture.toml", config() + check("extra", "R11", "NEVER", ["src/**/*.rs"]))
                code, out = r.run()
                self.assertEqual(code, 2, out)
                self.assertIn(f"check extra: rule must be one of R1 to R10; R11 is not a rule of {version}", out)

    def test_a_rule_that_is_no_rule_is_refused(self):
        for rule in ("R0", "R01", "r1", "R"):
            with self.subTest(rule=rule):
                r = v3_repo(checks=RS_ESCAPE + check("extra", rule, "NEVER", ["src/**/*.rs"]))
                code, out = r.run()
                self.assertEqual(code, 2, out)
                self.assertIn("check extra: rule must be one of R1 to R14", out)


class Required(unittest.TestCase):
    """At v3 the checks of R11 to R14 must be there where they apply."""

    def test_a_missing_check_fails_and_is_named(self):
        r = v3_repo(checks="")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("rs-escape (R12): required at v3, since it holds Rust, and architecture.toml has no such check", out)

    def test_only_what_applies_is_required(self):
        code, out = v3_repo().run()
        self.assertEqual(code, 0, out)
        for cid in ("kit-solid-import", "ts-strict", "py-escape", "sh-escape", "model-pure", "plugin-provider"):
            self.assertNotIn(cid, out)

    def test_pages_require_the_kit_checks(self):
        r = v3_repo()
        r.write("web/page.js", "export const a = 1;\n")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        for cid in ("kit-solid-import", "kit-copy", "kit-own-fetch", "kit-raw-html", "vendor-unlisted",
                    "ts-strict", "ts-escape", "model-pure"):
            self.assertIn(f"{cid} (R1", out)
        r.write("architecture.toml", config() + WEB_CHECKS)
        code, out = r.run()
        self.assertEqual(code, 0, out)

    def test_vendored_files_say_nothing_of_the_languages_here(self):
        r = v3_repo()
        r.write("vendor/lib/x.js", "export const a = 1;\n")
        r.write("web/vendor/run.sh", "echo\n")
        r.write("node_modules/y/z.py", "x = 1\n")
        code, out = r.run()
        self.assertEqual(code, 0, out)

    def test_a_required_check_may_hold_a_max_with_a_why(self):
        r = v3_repo(checks=check("rs-escape", "R12", "allow", ["src/**/*.rs"], max=1, why="one left, step 5"))
        r.write("src/core.rs", "#[allow(dead_code)]\nfn x() {}\n")
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `rs-escape` | R12 |  | 1 | 1 | holds |", out)

    def test_a_required_check_under_another_rule_fails(self):
        r = v3_repo(checks=check("rs-escape", "R4", "NEVER", ["src/**/*.rs"]))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn('rs-escape (R4): this check is R12\'s at v3; write rule = "R12".', out)

    def test_a_report_does_not_stand_for_a_check(self):
        r = v3_repo(checks='\n[[report]]\nid = "rs-escape"\nrule = "R12"\nwhat = "x"\npattern = "allow"\nfiles = ["src/**"]\n')
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("rs-escape (R12): required at v3", out)

    def test_force_below_v2_runs_v2s_checks_only(self):
        r = base_repo(standard="v1")
        code, out = r.run("--force")
        self.assertEqual(code, 0, out)
        self.assertNotIn("required at", out)
        r.write("tehas.toml", pointer("v3"))
        r.write("AGENTS.md", agents("v3"))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("rs-escape (R12): required at v3", out)


class Plugin(unittest.TestCase):
    """In a plugin repository, R11 to R14 read src/ (item 4)."""

    def plugin(self, checks):
        r = Repo()
        r.write("tehas.toml", pointer("v3"))
        r.write("AGENTS.md", agents("v3"))
        r.write("tehas-plugin.json", '{"plugin": 2}\n')
        r.write("architecture.toml", "version = 1\n" + checks)
        r.write("src/view/board.tsx", 'import { createSignal } from "solid-js";\n')
        r.write("src/driver.ts", 'import { createSignal } from "solid-js";\n')
        r.write("dist/view/board.js", 'import { createSignal } from "solid-js";\n')
        r.write("dist/driver.js", 'import { createSignal } from "solid-js";\n')
        return r

    def all_checks(self, solid_max=1):
        out = check("kit-solid-import", "R11", "from .solid", ["**/*.ts", "**/*.tsx", "**/*.js"],
                    max=solid_max, why="the driver, until step 2" if solid_max else "", allowed=["src/view/**"])
        for cid, rule in (("kit-copy", "R11"), ("kit-own-fetch", "R11"), ("kit-raw-html", "R11"),
                          ("vendor-unlisted", "R11"), ("ts-strict", "R12"), ("ts-escape", "R12"),
                          ("model-pure", "R13"), ("plugin-provider", "R14")):
            out += check(cid, rule, "NEVER", ["src/**"])
        return out

    def test_dist_is_not_counted_a_view_is_allowed_a_driver_is_counted(self):
        r = self.plugin(self.all_checks(solid_max=1))
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `kit-solid-import` | R11 |  | 1 | 1 | holds |", out)
        r.write("architecture.toml", "version = 1\n" + self.all_checks(solid_max=0))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("kit-solid-import (R11): 1 places, 0 allowed", out)
        self.assertIn("src/driver.ts:1:", out)
        self.assertNotIn("dist/", out)

    def test_a_plugin_needs_plugin_provider(self):
        r = self.plugin(self.all_checks().replace('id = "plugin-provider"', 'id = "other"'))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("plugin-provider (R14): required at v3, since it is a plugin", out)

    def test_other_rules_still_read_the_whole_plugin(self):
        r = self.plugin(self.all_checks() + check("dist-word", "R1", "createSignal", ["dist/**"], max=2, why="the build"))
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `dist-word` | R1 |  | 2 | 2 | holds |", out)

    def test_an_r11_check_on_dist_alone_has_no_scope(self):
        r = self.plugin(self.all_checks() + check("kit-dist", "R11", "solid", ["dist/**"]))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("kit-dist (R11): its files match no tracked file it may count", out)


class Agents(unittest.TestCase):
    """At v3, AGENTS.md names the version tehas.toml names (item 7)."""

    def test_the_same_version_passes(self):
        code, out = v3_repo().run()
        self.assertEqual(code, 0, out)

    def test_another_version_fails(self):
        code, out = v3_repo(agents_version="v2").run()
        self.assertEqual(code, 1, out)
        self.assertIn("AGENTS.md: names tehas-standard v2, and tehas.toml says v3; name the same version in both.", out)

    def test_a_minor_is_named_exactly(self):
        code, out = v3_repo("v3.1", agents_version="v3").run()
        self.assertEqual(code, 1, out)
        self.assertIn("names tehas-standard v3, and tehas.toml says v3.1", out)
        code, out = v3_repo("v3.1").run()
        self.assertEqual(code, 0, out)

    def test_no_file_or_no_name_fails(self):
        r = v3_repo()
        r.git("rm", "-qf", "AGENTS.md")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("AGENTS.md: missing", out)
        r.write("AGENTS.md", "# Agents\n")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("AGENTS.md: names no tehas-standard version", out)

    def test_it_is_read_from_v3_on_only(self):
        r = base_repo()
        r.write("AGENTS.md", agents("v3"))
        code, out = r.run()
        self.assertEqual(code, 0, out)
        r = v3_repo(agents_version="v2")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("AGENTS.md: names tehas-standard v2", out)


class Pins(unittest.TestCase):
    """At v3, each exact pin is within its [platform] major (item 6)."""

    PLATFORM = '\n[platform]\nrust = "1.x"\ntypescript = "7.x"\n'

    def repo(self, pins, platform=PLATFORM, standard="v3"):
        r = v3_repo(standard, checks=RS_ESCAPE if standard != "v2" else "")
        r.write("tehas.toml", pointer(standard) + platform)
        for path, text in pins.items():
            r.write(path, text)
        return r

    def test_pins_within_the_major_pass(self):
        r = self.repo({"rust-toolchain.toml": '[toolchain]\nchannel = "1.100.0"\n',
                       "host/versions.env": "RUST_VERSION=1.100.0\nTSC_VERSION=7.0.2\n",
                       ".github/workflows/ci.yml": "env:\n  TSC_VERSION: 7.0.2\n  RUST_VERSION: '1.99'\n",
                       "package.json": '{\n  "devDependencies": {\n    "typescript": "7.0.2"\n  }\n}\n'})
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertNotIn("no exact pin", out)

    def test_a_pin_outside_the_major_fails_and_is_named(self):
        cases = {"rust-toolchain.toml": ('[toolchain]\nchannel = "2.0.0"\n', 'rust-toolchain.toml:2: pins rust 2.0.0, outside [platform] rust = "1.x"'),
                 "versions.env": ("TSC_VERSION=6.0.3\n", 'versions.env:1: pins typescript 6.0.3, outside [platform] typescript = "7.x"'),
                 ".github/workflows/ci.yml": ("steps:\n  - run: npx -p typescript@5.9.2 tsc\n", "ci.yml:2: pins typescript 5.9.2"),
                 "package.json": ('{"devDependencies": {\n"typescript": "6.0.0"}}\n', "package.json:2: pins typescript 6.0.0")}
        for path, (text, want) in cases.items():
            with self.subTest(path=path):
                code, out = self.repo({path: text}).run()
                self.assertEqual(code, 1, out)
                self.assertIn(want, out)

    def test_the_pins_are_compared_from_v3_on_only(self):
        pin = {"rust-toolchain.toml": '[toolchain]\nchannel = "2.0.0"\n'}
        code, out = self.repo(pin, standard="v2").run()
        self.assertEqual(code, 0, out)
        self.assertNotIn("rust-toolchain", out)
        code, out = self.repo(pin, standard="v3").run()
        self.assertEqual(code, 1, out)
        self.assertIn("pins rust 2.0.0", out)

    def test_a_pin_of_a_toolchain_platform_does_not_name_fails(self):
        r = self.repo({"rust-toolchain.toml": '[toolchain]\nchannel = "1.100.0"\n'}, platform="")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("rust-toolchain.toml:2: pins rust 1.100.0, and [platform] names no rust", out)

    def test_no_pin_and_a_floating_channel_are_noted(self):
        r = self.repo({"rust-toolchain.toml": '[toolchain]\nchannel = "stable"\n'})
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("rust-toolchain.toml:2: rust 'stable' is not an exact version", out)
        self.assertIn("[platform] rust: no exact pin found", out)
        self.assertIn("[platform] typescript: no exact pin found", out)

    def test_a_pin_deeper_than_one_directory_is_not_read(self):
        r = self.repo({"test/fixtures/old/versions.env": "TSC_VERSION=5.0.0\n", "vendor/x/versions.env": "RUST_VERSION=0.9.0\n"})
        code, out = r.run()
        self.assertEqual(code, 0, out)


class Scope(unittest.TestCase):
    """A check whose files match nothing counts nothing (#29 item 2)."""

    def test_at_v2_it_is_a_warning(self):
        r = base_repo()
        r.write("architecture.toml", config() + check("ghost", "R1", "x", ["lib/**/*.rs"]))
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("Warning: ghost (R1): its files match no tracked file it may count", out)
        self.assertIn("From v3 this fails.", out)

    def test_at_v3_it_fails(self):
        r = v3_repo(checks=RS_ESCAPE + check("ghost", "R1", "x", ["lib/**/*.rs"]))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("ghost (R1): its files match no tracked file it may count", out)
        self.assertNotIn("Warning", out)

    def test_every_file_allowed_is_no_scope_either(self):
        r = v3_repo(checks=RS_ESCAPE + check("ghost", "R1", "x", ["src/*.rs"], allowed=["src/**"]))
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("ghost (R1): its files match no tracked file", out)


class Reading(unittest.TestCase):
    """How a tracked file is read (#29 items 1, 3, 6 and 7)."""

    def test_a_symlink_inside_the_repository_is_counted_where_it_lives(self):
        r = base_repo()
        os.symlink("web.rs", os.path.join(r.root, "src/also.rs"))
        r.git("add", "src/also.rs")
        code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertIn("| `routes` | R1 |  | 1 | 1 | holds |", out)

    def test_a_symlink_out_of_the_repository_is_not_read(self):
        r = base_repo()
        with tempfile.TemporaryDirectory() as outside:
            with open(os.path.join(outside, "x.rs"), "w") as f:
                f.write('fn x() { call("/api/q") }\n')
            os.symlink(os.path.join(outside, "x.rs"), os.path.join(r.root, "src/out.rs"))
            r.git("add", "src/out.rs")
            code, out = r.run()
        self.assertEqual(code, 0, out)
        self.assertNotIn("out.rs", out)

    def test_a_symlink_loop_is_no_file(self):
        r = base_repo()
        os.symlink("loop.rs", os.path.join(r.root, "src/loop.rs"))
        r.git("add", "src/loop.rs")
        code, out = r.run()
        self.assertEqual(code, 0, out)

    def test_a_file_under_a_symlinked_directory_is_not_read(self):
        r = base_repo()
        r.commit()
        os.makedirs(os.path.join(r.root, "elsewhere"))
        with open(os.path.join(r.root, "elsewhere/core.rs"), "w") as f:
            f.write('fn x() { call("/api/d") }\n')
        os.rename(os.path.join(r.root, "src"), os.path.join(r.root, "real"))
        os.symlink("real", os.path.join(r.root, "src"))
        reader = architecture.reader(r.root)
        self.assertIsNone(reader("src/web.rs"))
        self.assertIsNotNone(reader("real/web.rs"))

    def test_utf16_with_a_bom_is_read(self):
        r = base_repo()
        for name, bom, codec in (("le.rs", b"\xff\xfe", "utf-16-le"), ("be.rs", b"\xfe\xff", "utf-16-be")):
            with open(os.path.join(r.root, "src", name), "wb") as f:
                f.write(bom + 'fn z() { call("/api/z") }\n'.encode(codec))
            r.git("add", f"src/{name}")
        code, out = r.run()
        self.assertEqual(code, 1, out)
        self.assertIn("routes (R1): 3 places, 1 allowed", out)
        self.assertIn('src/le.rs:1: fn z() { call("/api/z") }', out)

    def test_the_imports_are_in_order(self):
        with open(architecture.__file__, encoding="utf-8") as f:
            lines = f.read().split('"""', 2)[2].split("\n")
        imports = [l for l in lines if l.startswith("import ")]
        self.assertEqual(imports, sorted(imports))


class Published(unittest.TestCase):
    def test_the_published_hash_is_this_scripts_and_a_changed_copy_fails_it(self):
        import hashlib
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "architecture.py"), "rb") as f:
            data = f.read()
        with open(os.path.join(here, "architecture.py.sha256"), encoding="utf-8") as f:
            published = f.read().split()[0]
        self.assertEqual(hashlib.sha256(data).hexdigest(), published)
        self.assertIn(b"\n# tehas-standard v3\n", data)
        changed = data.replace(b"# tehas-standard v3\n", b"# tehas-standard v3 \n", 1)
        self.assertNotEqual(hashlib.sha256(changed).hexdigest(), published)


def _toml(c):
    def v(x):
        if isinstance(x, list):
            return "[" + ", ".join(v(i) for i in x) + "]"
        if isinstance(x, bool):
            return "true" if x else "false"
        if isinstance(x, int):
            return str(x)
        return "'" + x + "'"
    return "version = 1\n[[check]]\n" + "".join(f"{k} = {v(x)}\n" for k, x in c.items())


if __name__ == "__main__":
    unittest.main()
