# Repository conventions v3

Part of tehas-standard v3. What every repository that follows v3 keeps, so
an agent or a person picking up any repository finds the same things in
the same places.

## Conformance language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in BCP 14
[RFC 2119] [RFC 8174] when, and only when, they appear in all capitals, as
shown here.

A plain statement of what a conformant repository, plugin or host does
("the host refuses", "a plugin never writes") is a requirement, read as
MUST or MUST NOT. A section marked *informative* explains and adds no
requirement.

## Normative references

- BCP 14: [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), the key words.
- [MADR 4.0](https://adr.github.io/madr), for decision records.
- [SLSA v1.1](https://slsa.dev/spec/v1.1/), Build track, for release workflows a host trusts (§8).
- Informative: [arc42](https://arc42.org/overview) and the [C4 model](https://c4model.com/), for `docs/architecture.md`; [Diátaxis](https://diataxis.fr/), for `docs/`.

## 1. The pointer: `tehas.toml`

One TOML file at the repository root says how the repository is kept, for
the tehas system. Its `[standard]` table names the standard by its full URL
and the version the repository follows:

```toml
# How this repository is kept. Each table has one owner.
[standard]
url = "https://github.com/tehas-app/tehas-standard"
version = "v3"
```

| `version` | Means |
| --- | --- |
| no file, or `"v1"` | the code as it is, with no formal definition. The architecture test is skipped and passes, saying so |
| `"v2"` | tehas-standard v2: coding standard v2, the architecture standard and the external contracts |
| `"v3"` | `v3/coding.md` and the files it names: the architecture, contract and plugin standards v3 and these conventions |
| `"v3.1"`, `"v3.2"`, ... | `v3.1/coding.md` (and so on) and the files it names |
| anything else | refused by name: a repository can't claim a standard nothing checks |

`url` names the standard; a script checks only its own, and another
standard brings its own script. `.tehas/` stays for a project's own items
(what a factory reads, such as `needs.toml` and `definition/`). The value
of `version` names one version exactly: `"v3"` means `v3/coding.md` and
nothing later. A file that exists MUST have a `[standard]` table: an empty
file, a near miss (`[Standard]`, `[standards]`, a top-level `version`) or a
file with other tables only is refused, so a typo can't switch the checks
off; so is a symlink. A repository that names no standard has no file.

### 1.1 One owner for each table

The file grows one table per subject, never one key per whim. Each table
has one owner, the program that reads it:

- the owner is strict about its own table: an unknown key there is refused,
  so a newer file is never half read;
- every other reader leaves the table alone;
- a table and its keys enter by a minor of this standard, which names the
  owner. `[standard]` is the architecture script's.

`[platform]` names what the repository needs from its platform. From v2 it
holds the toolchains it builds with, at the majors this version allows, and
the architecture script owns it:

```toml
[platform]
rust = "1.x"
typescript = "7.x"
```

A repository lists only the toolchains it uses and pins the exact version
where it always has (`rust-toolchain.toml`, its versions file, CI); the
script checks that each pin is within the major. The infrastructure the
program needs to run (operating system, init system, container runtimes,
CPU architectures, resources) joins the table by a later minor, with the
infrastructure tooling as its reader.

Tables that may come, each once its owner exists: `[plugin]` (that the repository is a plugin, and its
manifest number), `[kit]` (the kit version a repository pins), `[release]`
(the surface step's settings, contracts C3). What a factory needs to build
and preview a product stays in `.tehas/needs.toml`, the factory's own file.

### 1.2 The old pointer

Before v2 the pointer was the one line of `.tehas/coding-standard`. It is read
only when it says `v1`. A repository that writes `"v2"` or later deletes it in
the same commit that writes `tehas.toml`, and never keeps both.

A repository takes a minor by writing it, in a pull request of its own.
The value only goes up: a pull request that writes a lower version than
its base has fails the `architecture` job. A minor is a small step, so that pull request is small; a major is a
larger one, planned from the diff of the two version directories (see
[../VERSIONS.md](../VERSIONS.md)).

## 2. The files each repository keeps

| File | What |
| --- | --- |
| `tehas.toml` | §1 |
| `AGENTS.md` | first, the standard and its exact version ("This repository follows tehas-standard v3 (`tehas.toml`)" and a link to `v3/` at its tag), so an agent reads it before anything else; then an architecture section: the rules in short and every departure the repository takes. The architecture script checks that the version named matches `[standard] version`. Style stays the repository's own |
| `docs/architecture.md` | the repository's architecture description (§2.1): the knowledge map (each piece of knowledge, its owner, where else it is known, with counts); the ports with their adapters and fakes; the departures with their reasons; the table of grades, appended, never rewritten |
| `docs/adr/` | decision records, one per decision, `NNNN-<slug>.md`, in the MADR 4.0 template |
| `docs/architecture-review.md` | the review questions (§5), copied from this standard's tag |
| `docs/architecture-rubric.md` | the grading rubric (§6), copied from this standard's tag |
| `architecture.toml` | the repository's checks for the architecture test |
| `scripts/architecture.py` | the canonical script, byte for byte as this standard's tag ships it ([v3/architecture-script.md](architecture-script.md)) |
| `docs/contract.md` | for a repository with an external API: what is public, internal and building, the exit statuses, "Changed in <major>" ([v3/contracts.md](contracts.md) C1) |
| `api/` | the schemas, samples, `openapi.yaml`, `asyncapi.yaml` and surface list of its external API ([v3/contracts.md](contracts.md) C2, C3) |
| `docs/plans/`, `docs/specs/` | plans and specs, dated (`YYYY-MM-DD-<slug>.md`), each with a status line |

### 2.1 The architecture description

`docs/architecture.md` follows the arc42 template's sections, in arc42's
order and numbering, with the knowledge map, ports and grades in their
places:

| arc42 section | What it holds here |
| --- | --- |
| 1 Introduction and goals | what the part is for, its stakeholders and the quality goals |
| 3 Context and scope | the part's external APIs and the parts on their other side ([v3/contracts.md](contracts.md) §2) |
| 5 Building block view | the knowledge map, the ports with their adapters and fakes |
| 8 Crosscutting concepts | the departures, with their reasons |
| 9 Architecture decisions | a list of `docs/adr/`, linked |
| 10 Quality requirements | the table of grades |
| 11 Risks and technical debt | the architecture test's counts above zero, with their `why` |

Sections 1, 3, 5, 8, 9 and 10 are REQUIRED; the others are OPTIONAL and
are left out, not left empty. Diagrams SHOULD follow the C4 model's levels
(context, container, component) and say which level they draw.

### 2.2 Documentation

A repository's `docs/` is sorted by what a reader needs, after Diátaxis:
**reference** (the contract, the API pages, the specs), **how-to** guides
(a task, in steps), **explanation** (why it is so: the architecture
description, the ADRs) and, where the part has new users, **tutorials**. A
page is one of the four and says which in its first lines. The standard's
own files are reference.

## 3. CI jobs

Named the same in every repository, run on every pull request, with no
network:

| Job | Runs |
| --- | --- |
| `architecture` | `scripts/architecture.py` with `--base` on a pull request |
| `types` | the pinned checker for each language present (coding standard R12) |
| `plugin` | for a plugin: builds `dist/`, fails on a difference from the committed `dist/`, runs the host's `dist/` checks and the tests in the engine |
| the surface check | for a repository with an external API: the surface list is what the generator writes, nothing listed is gone, nothing retired is back |

## 4. The architecture test

- One check per piece of knowledge with a name a grep can find, its files
  allowed, its `max`, and a `why` when the `max` is above zero.
- Each check is a **ratchet**: it holds today's count and may only fall. A
  count below its `max` fails too, so the pull request that lowers a count
  lowers its `max`.
- With `--base`, a `max` raised over the base's, a check removed, or a
  check whose scope changed needs a new `why`. A departure is always a
  written reason in the diff.
- A repository is conformant when every count is zero or at a floor its
  `docs/architecture.md` explains.

## 5. Review

Every pull request is reviewed against these questions by whoever reviews
it today. A "no" is fixed or answered in the pull request with a reason; a
reason that holds becomes a departure in `docs/architecture.md`. The test
answers what is mechanical; a review never re-checks it by hand.

| Rule | The question |
| --- | --- |
| R1 | Does a piece of knowledge this change touches now live in more than one module? |
| R2 | Does code outside an adapter now name a supplier's path, field, header or command? |
| R3 | Does a decision now read the clock, the network, a file or the environment? |
| R4 | Does untyped data now cross a seam? |
| R5 | Did a module's public surface grow more than what it hides? Is there a new pass-through? |
| R6 | Does a supplier's failure now reach a caller as a raw status? |
| R7 | Does a new test pin a supplier's call shape outside the adapter's own tests? Does a move come with its tests first? |
| R8 | Does the core now depend on the shell or an adapter? |
| R9 | Does a contract term change or go without its parallel step and the release that allows it? |
| R10 | Does the change keep behaviour where it says it does, and is it small enough to review alone? |
| R11 | Does a page or view now draw without the kit, or load a library that is not verified? |
| R12 | Does new code skip the checker, or add an escape hatch? |
| R13 | Does a model or a plugin's core now read the DOM, clock, network or the host API? |
| R14 | Does a plugin now make its own copy of a surface the host offers? |
| C1-C9 | Does an external API change without its document, schema, surface line or "Changed in" entry? |

## 6. Grading

Each rule is graded on four bands, at adoption, before each release, and
when the owner asks:

| Band | Score | Means |
| --- | --- | --- |
| `absent` | 0 | the code breaks the rule widely, and nothing measures it |
| `partial` | 0.25 | the rule holds in some modules only, or its breaks are not all listed |
| `mostly` | 0.75 | the rule holds in most modules, and every break is listed with its count or reason |
| `met` | 1 | the rule holds, or holds to a written floor, and CI checks it where it can |

How far a rule holds and whether its breaks are listed both count: listing
alone does not lift a band, and widespread breaks are `partial` even when
listed.

The grade is the bands, not a sum. Two pass lines:

- **Adopting:** every rule at `partial` or better, the architecture test in
  CI, the knowledge map written.
- **Conformant:** every MUST rule at `met`, R5 at `mostly` or better.

The judged bands are scored by a reviewer who sees only the code at that
commit and the rubric, not the session that wrote it. A person confirms
the grade. Each band names its evidence: a count, a file and line, a test.

**Release gates.** A part's first release and a major are not tagged below
conformant unless the owner says so and the departure is written. A minor
may be tagged at any grade, but no band may fall below the last grade's.

## 7. Releases of a part

- A part's version is its own. It names the tehas-standard version it
  follows in `tehas.toml`, not in its version number, and the
  two never imply each other ([../VERSIONS.md](../VERSIONS.md)).
- A part may move to a new standard version in any of its releases, in a
  pull request of its own with the checks that enforce it, and its release
  notes say so.
- Within a part's major, its external API only adds
  ([contracts.md](contracts.md) C4). A major lists what changed, with its
  readers.
- Tagging runs the surface step of [contracts.md](contracts.md) C3: a new
  minor or major is tagged only with its `api/surface-X.Y.txt` committed and
  current; a patch only when its surface is unchanged. The step lives in the
  release workflow, a gate file.

## 8. Commits and pull requests

- Plain messages that say what changed and why. No tool-generated trailers,
  footers or "generated with" lines.
- One change per pull request, green on its own (R10).
- A gate file (the release workflow, signer lists, the vetting pipeline)
  changes only in a pull request of its own, with the owner's yes.
- A release workflow whose output a host trusts (an engine, a signed list,
  a release asset another part installs) produces SLSA v1.1 Build Level 2
  provenance or better: signed, from a hosted build platform.
- Secrets, tokens, private host names and client names never enter a
  repository, a log or an issue.
