# The canonical architecture script, v3

`scripts/architecture.py` is one file, the same in every repository that
follows tehas-standard v2 or later. It knows no language and no repository:
what it checks is the repository's own `architecture.toml`. Python 3.11 or
later and git, no network, no dependencies.

## Its home

The canonical copy lives in tehas-standard at `tools/architecture.py`, with
its tests (`tools/architecture_test.py`). A tag of tehas-standard ships one
copy. A repository copies it byte for byte at the tag it follows, and its
first line after the docstring names that tag:

```
# tehas-standard v3
```

The `architecture` job checks the file's sha256 against the one the tag
publishes (`tools/architecture.py.sha256`), so a local edit can't pass as
the canonical script. A change to the script is a pull request in
tehas-standard and a minor or a major, by the size of the step. Repositories take it by copying the new tag's file.

## What v3 changes

The v2 script knows `STANDARDS = {"v1", "v2"}` with `ENFORCED = "v2"`, and
skips every check when the value found is not `ENFORCED`. A repository at
`v3` would then pass with nothing checked. The v3 script:

1. **Knows the versions up to its tag**, majors and minors: `v1`, `v2`,
   `v2.1`, ..., `v3`, `v3.1`, ... A value it does not know is refused by
   name ("this script is tehas-standard v3; take the script of v4 for v4"),
   never skipped.
2. **Enforces in order.** The checks run at `v2` and every later version.
   `v1`, or no file, is skipped and passes, saying so; `--force` runs the
   checks anyway.
3. **Knows what each version adds.** At `v3` and later it requires R11 to
   R14's checks in `architecture.toml` where they apply: the `kit-*` and
   `vendor-unlisted` checks where the repository has pages or views,
   `ts-strict` and the escape counts for each language present,
   `model-pure`, and `plugin-provider` for a plugin. A check may hold a
   `max` above 0 with a `why`; it may not be missing. A check's `rule` may
   name any rule of the version found: `R1` to `R14` at `v3` (the v2
   script knows only `R1` to `R10`), so a check is filed under its true
   rule; a rule the version does not have is refused by name.
4. **Knows a plugin's layout.** In a repository with `tehas-plugin.json`,
   R11 to R14's checks read `src/`. `dist/` is left to the host's checks and
   the `plugin` job.
5. **Reads `tehas.toml`** at the root, once, its `[standard]` table: `url`
   must be tehas-standard's and `version` one the script knows; an
   unknown key there is refused, other tables are left alone, and a file
   with no `[standard]` table is refused. The old
   one-line `.tehas/coding-standard` is read only where it says `v1`. Both at
   once is refused. Replacing the old file with the new one is not a
   deletion.
6. **Checks `[platform]`**: each key one it knows (`rust`, `typescript`),
   each value a major this version allows (`"1.x"`, `"7.x"`), and each exact
   pin in the repository's own files (`rust-toolchain.toml`, its versions
   file) within that major.
7. **Checks `AGENTS.md`** names the same tehas-standard version as
   `[standard] version`.
8. **Refuses a `--base` that is not a commit** in the repository, and reads
   the base's files by their git mode, so a symlink or directory there is
   named.
9. **Refuses a downgrade.** With `--base`, a `[standard] version` lower than the base's fails, naming both. Removing the file counts as writing `v1`.
10. **Keeps v2's rules for the test itself:** ratchets that fail above and
   below their `max`; with `--base`, a raised `max`, a removed check or a
   changed scope needs a new `why`.

## Its tests

`architecture_test.py` gains, at least:

- `v3` is enforced, not skipped;
- `v3.1` is enforced with the checks `v3.1/coding.md` names;
- `v4`, which the script does not know, is refused by name;
- at `v3` a check with `rule = "R11"` (and `R12` to `R14`) is accepted, `R15`
  is refused by name, and at `v2` `R11` is refused;
- `v3` with a required check missing fails and names the check;
- in a plugin repository, a `kit-solid-import` match in `dist/` is not
  counted, one in a `src/` view file is allowed, and one elsewhere in
  `src/` (a driver) is counted;
- with `--base` at `v3`, writing `v2` fails, and so does deleting the
  file;
- `v2` in the old name `.tehas/coding-standard` is refused and asks for
  the rename; `v1` there passes; keeping both fails;
- a file whose hash is not the tag's fails.

## When it lands

In each repository of the first three parts, byte for byte and in step,
before any of them writes `v3`. The plugin starter and our own plugins copy
the same file at the same hash.
