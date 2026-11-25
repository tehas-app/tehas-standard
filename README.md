# tehas-standard

The standards of the tehas system, current and past: how code is built in
any repository of the system, how the parts meet, and how a plugin is
written and run.

> **Draft.** Published 2026-11-25. No repository follows it yet and
> nothing is tagged.

## The one pointer

Each repository says which version it follows in one file:

```
.tehas/coding-standard
v3
```

From that line a person or an agent picking up any piece of code finds
every rule it follows: the coding standard of that version names the
architecture, plugin and contract standards valid with it, and the
repository conventions.

## What a version holds

| | v2 | v3 |
| --- | --- | --- |
| [Coding standard](v3/coding.md): rules for code inside one repository | R1 to R10 | R1 to R14: v2 plus pages, types, pure models, plugins |
| [Architecture standard](v3/architecture.md): rules across repositories | A1 to A6 | A1 to A6 |
| [External contracts](v3/contracts.md): the rules for external APIs and the catalogue of the system's seams | C1 to C9 | C1 to C9, the plugin host API added |
| [Architecture patterns](v3/patterns.md): the published patterns the rules rest on (deep modules, ports and adapters, functional core, parse don't validate, parallel change, ...) | §1 to §6 | §1 to §9: v2's plus microkernel, capabilities, islands |
| [Plugin standard](v3/plugins.md): what a plugin and its host meet | none | manifest `"plugin": 2` |
| [Repository conventions](v3/repository.md): the files, CI jobs, review and grading every repository keeps | in v2/coding.md | v3/repository.md |
| [The architecture script](v3/architecture-script.md) | knows v1, v2 | knows v1 to v3 |

[VERSIONS.md](VERSIONS.md) says how versions are numbered (`v2`, `v2.1`,
`v3`: a major is a larger move, a minor a small correction) and what each
holds. [CHANGELOG.md](CHANGELOG.md) says what changed.

## How the rules are written

- Each standard file opens with its scope (its first paragraphs), its
  conformance language
  (BCP 14: MUST, SHOULD, MAY) and its normative references, then its
  terms and its rules, in the manner of ISO/IEC Directives Part 2.
- Each rule states the requirement, then how to check it (*Checked:*), as
  the Standard for Public Code pairs each requirement with a test. A rule
  nothing can check is a review question.
- The files are reference documentation in Diátaxis's sense. Why a rule is
  so lives in its sources' decision records, not here.
- External formats are standards of their own, named, not re-specified:
  JSON Schema 2020-12, OpenAPI 3.1, AsyncAPI 3.0, WIT, MADR 4.0, SLSA v1.1.

## Every version is a directory

Each version is a directory of its own, complete and never edited once its
version is tagged: `v2/` and `v3/` sit side by side, and a minor such as
`v3.1/` is a full copy with its corrections. `v3/coding.md` names the other
files valid with it. Moving a repository between versions is planned from
the diff of two directories. [VERSIONS.md](VERSIONS.md) has the rules.

## Layout

```
README.md           this page
VERSIONS.md         the versions and what each holds
CHANGELOG.md        what each tag changed
v2/                 tehas-standard v2: coding, architecture, contracts, patterns
v3/                 tehas-standard v3: coding, architecture, contracts, plugins,
                    repository conventions, patterns, the architecture script's spec
scripts/check.py    the repository's own check: links, and tagged directories unchanged
AGENTS.md           the rules for changing this repository
LICENSE             CC-BY-4.0, for the text
LICENSES/           Apache-2.0, for the scripts
NOTICE              the copyright and which licence covers what
```

## What is not here

- **Internal APIs.** Only external APIs, used by another program or by a
  person, are in the contracts standard. A repository's internal APIs are
  its own and are never promised.
- **One deployment's map.** Which part owns which knowledge in one
  deployment, and the private parts' details, stay with their owners.
- **A host's implementation.** A plugin host keeps the spec of its own
  runner (engine, limits, settings, signing) and names the version it
  meets.
- **Style.** Naming, formatting and comments stay each repository's own,
  in its `AGENTS.md`.

## Licence

The standards' text is licensed under
[CC-BY-4.0](LICENSE): adopt it, adapt it, with attribution. The scripts are
licensed under [Apache-2.0](LICENSES/Apache-2.0.txt). [NOTICE](NOTICE) says
which covers what.
