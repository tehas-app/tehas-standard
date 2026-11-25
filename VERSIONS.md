# Versions

tehas-standard is tagged as a whole: `v1`, `v2`, `v2.1`, `v2.2`, `v3`, and
so on. A tag holds the coding standard of that version and the
architecture, contract and plugin standards, the patterns they rest on
and the repository conventions valid with it. The standards are not versioned apart.

The numbers are not semantic versions. (A part's own releases are: its
external API follows Semantic Versioning, and it records its surface for
each minor release, [v3/contracts.md](v3/contracts.md) C3.)

- **A major** (`v3`) is a larger move: a new standard (v3's plugin
  standard), a new kind of check, a rework that touches much of a
  repository.
- **A minor** (`v3.1`) is a small step: it may add a rule, take one out,
  sharpen a check or fix wording. Which steps count as small is the
  owner's call.

Either can add or remove. Every version, major or minor, is a step
forward from the one before, and a repository takes each step on purpose
by raising its pointer. For example:

| Version | Rules it holds | What changed |
| --- | --- | --- |
| `v1.1` | A, B | adds B |
| `v1.2` | A, B, C, D | adds C and D |
| `v1.3` | A, C, D | removes B |

`v1.1/` and `v1.2/` keep B as they were. A repository at `v1.2` is still
held to B; it stops being held to B when it writes `v1.3`. It never gets rid of B by going back to `v1` or by editing `v1.2/`.

**Even an undo is an upgrade.** A rule found to be a mistake, or bad, is
taken out by a new version, and the changelog says why. The new version
may hold exactly what an earlier one held: if `v1.4` undoes `v1.3`, it
holds A, B, C and D again, like `v1.2`, and it is still `v1.4`, with a
directory of its own. Repositories move up to it; none moves back to
`v1.2`.

## Every version is a directory of its own

Each version is one directory: `v2/`, `v3/`, and for a minor `v3.1/`. It
holds every standard of that version, complete: `v3/coding.md`,
`v3/architecture.md`, `v3/contracts.md`, `v3/plugins.md`,
`v3/repository.md`, `v3/patterns.md`, `v3/architecture-script.md`. A
directory is never edited once its version is tagged. A correction is a new
version in a new directory; git history is not how a version is found.

- **A minor is a full copy.** `v3.1/` copies all of `v3/` and changes what
  it corrects, so a reader at `v3.1` needs no other directory.
- **`coding.md` is the version's root.** It names the other files valid with
  it, so the pointer `v3.1` leads to `v3.1/coding.md`, and that file to
  everything else.
- **Moving between versions is a diff of two directories.** A repository
  moving from `v2` to `v3` reads `diff -r v2 v3`, and each file's "Changes
  from" section, and plans its refactoring from that. Both stay side by
  side for as long as any repository is at the older one.

[CHANGELOG.md](CHANGELOG.md) says what each tag changed.

## Standards and software versions are independent

The versions of tehas-standard and the versions of the parts that follow
it never imply each other. This holds for every standard a version holds:
coding, architecture, contracts, plugins, patterns and the repository
conventions.

- A part names the tehas-standard version it follows in
  `.tehas/repository.toml`, never in its own version number.
- A part may move to a new standard version in any of its releases, major,
  minor or patch, and is expected to: a minor of the standard is a small
  pull request, a major is planned from the diff of two directories. The
  part's release notes say when it moved.
- Where a standard's major asks for a change the part's own contract allows
  only in its next major (removing a public name), the part moves when its
  contract allows, and its `docs/architecture.md` records the departure
  until then.
- A plugin host names the standard version whose plugin standard it meets;
  its plugins follow the manifest number that goes with it.
- **Adopted versions only go up.** A part never writes a lower version in
  `.tehas/repository.toml` than the one it has adopted: no downgrade, not
  for a release branch, not to get past a failing check. A check it can't
  meet yet is held at a ratchet with a written `why`, not escaped by going
  down.
- **Removals only go forward too.** A rule, a check, a pattern, a
  guarantee or a row of the contracts catalogue leaves a standard only in a
  new version, major or minor; every earlier directory keeps it as it was.
  On the part's side the same holds: a check leaves `architecture.toml`
  only because the standard version the part moves up to dropped it, and
  deleting `.tehas/repository.toml` is a downgrade, refused like one.
- A new standard version never changes what an old directory says, so a
  part that stays on `v2` keeps meeting `v2`.

## The versions

| Version | Coding standard | Architecture standard | Plugin standard | Contracts | Patterns | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `v1` | the code as it was, no definition | none | none | none | none | the default for a repository with no pointer |
| `v2` | [v2/coding.md](v2/coding.md): R1 to R10, the architecture test, review and grading | [v2/architecture.md](v2/architecture.md): A1 to A6 | none: plugins are off in every release that follows v2 | [v2/contracts.md](v2/contracts.md): C1 to C9 | [v2/patterns.md](v2/patterns.md) | draft; the tehas system's first three parts are adopting it |
| `v3` | [v3/coding.md](v3/coding.md): v2 plus R11 to R14 | [v3/architecture.md](v3/architecture.md): A1 to A6 | [v3/plugins.md](v3/plugins.md): manifest `"plugin": 2` | [v3/contracts.md](v3/contracts.md): C1 to C9 and the catalogue | [v3/patterns.md](v3/patterns.md): v2's plus plugins and front ends | draft |

**Which host meets which version.** A plugin host names the tehas-standard
version whose plugin standard it meets, and the manifest number that goes
with it. A host runs one manifest number at a time; when it moves to a new
one, its own contract says in which of its releases.
