# Tools

- `api_changes.py`: the API changes between two commits of a part
  (contracts C3).
- `architecture.py`: the architecture script of tehas-standard v3, which
  also runs v2 (coding standard §4 and §5, and
  [v3/architecture-script.md](../v3/architecture-script.md)), with its
  tests in `architecture_test.py`. It knows no
  repository: what it checks is the repository's own `architecture.toml`.

## Taking the architecture script

A repository copies `architecture.py` byte for byte to
`scripts/architecture.py` **from the tag of the version it follows**, and
never edits its copy. At `v2` that is the `v2` tag's file (sha256
`485a7e639236c5236e542ff7fb2c9b9d815fcb7646745cbdb5c89f180cd0452b`); the
file on `main` is the v3 script, taken only when the repository moves to
`v3`. The copy's sha256 must be the one in that tag's
`architecture.py.sha256`:

```
git -C tehas-standard show v2:tools/architecture.py > <repository>/scripts/architecture.py
cd <repository>/scripts && sha256sum architecture.py
```

The two hashes must be equal. The tests may be copied the same way to
`scripts/architecture_test.py`. A change to the script is a pull request
here, with a new hash; repositories take it by copying the file again.

The script's own run is its CI job: `python3 -I scripts/architecture.py`,
with `--base <the pull request's base>` on a pull request. A run without
`--base` compares with nothing, so a workflow that wants the downgrade
guard on a push passes the push's previous commit as `--base`.
