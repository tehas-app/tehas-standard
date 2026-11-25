# Coding standard v2

Part of tehas-standard v2. A repository follows it when its
`.tehas/repository.toml` says `[standard] version = "v2"` (see §4). It names:

| With coding standard v2 | Valid version |
| --- | --- |
| Architecture standard | [v2/architecture.md](architecture.md) |
| Plugin standard | none: v2 has no plugin standard |
| External contracts | [v2/contracts.md](contracts.md) |
| Architecture patterns | [v2/patterns.md](patterns.md): the published patterns the rules rest on |

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
- The other parts of this tag: [v2/architecture.md](architecture.md), [v2/contracts.md](contracts.md), [v2/patterns.md](patterns.md).

## 1. Aim and scope

**Aim.** A resilient architecture, not a code style:

- a supplier changes, one module changes;
- a supplier fails, the program carries on and reports it once;
- a crash loses nothing;
- a contract changes without a flag day.

**Scope.** Every repository of the tehas system that holds a program. Skills, prose and settings repositories are
out of scope.

**Not in scope.** Naming, formatting, function length, comment style and
the rest of a repository's style stay as its `AGENTS.md` says. The
standard sets where knowledge lives and how the parts meet, not how a line
reads.

## 2. Terms

| Term | Meaning |
| --- | --- |
| a piece of knowledge | One design decision that could change on its own: a supplier's request and answer shapes, a file format, a directory layout, the words of a set of states, a route table, a wire format, a rule of the business |
| its owner | The one module that knows a piece of knowledge. Everyone else asks it |
| a module | A unit with an interface: a crate, a Rust module, a JavaScript module |
| deep, shallow | Deep: the interface is small against what it hides. Shallow: the interface is nearly as large as the body |
| a seam | Where two modules or two programs meet |
| a port | An interface named in our terms for what a program needs from outside |
| an adapter | The one implementation of a port for one outside system. It alone knows that system's shapes. Not a plugin: an adapter is defined by the port it answers |
| a fake | An implementation of a port for tests, written against the port, never against the outside system's wire |
| the core | The pure decisions: no network, clock or files |
| the shell | The code that reads, calls the core, and writes |
| a contract | What a release promises outside the repository: a CLI, a file format, an HTTP route, a schema, a public item |

MUST marks a rule a conformant repository meets. SHOULD marks the default,
departed from with a reason written in the repository's
`docs/architecture.md`.

## 3. The rules

**R1. One owner for each piece of knowledge.** MUST. A supplier's paths,
field names and query strings, a file's layout, a set of state words, a
route list: each is written in one module. A change to one piece of
knowledge touches its owner and nothing else.
*Checked:* the outside names (a host name, a path prefix, a label word)
are listed in `architecture.toml` and may appear only in their owner.

*Patterns* ([patterns.md](patterns.md) §1): information hiding, information leakage.

**R2. Outside systems behind ports, in our terms.** MUST. A program names
what it needs (`tickets_of(factory)`, `ask(chat)`), not how a supplier
serves it. The adapter is the only module that knows the supplier. A port
is general enough for two suppliers and no further.
*Checked:* no port method takes a method, a path, a URL or untyped data.

*Patterns* ([patterns.md](patterns.md) §1, §2): ports and adapters, anti-corruption layer, ubiquitous language, somewhat general-purpose interfaces.

**R3. A pure core, effects at the edge.** MUST. Decisions are pure
functions with their own tests. The shell reads, asks the core, then
writes. Where losing work to a crash matters, the shell writes what it
will do before doing it, so a restart picks up.
*Checked:* the core's modules do not depend on the network, clock, file or
process libraries.

*Patterns* ([patterns.md](patterns.md) §2): functional core, imperative shell; write-ahead journal.

**R4. Typed seams, parsed at the edge.** MUST. What crosses a seam is a
type of ours. Outside data is parsed into those types where it enters,
every field the program reads required, unknown fields ignored, and what
fails to parse is refused and shown as unreadable. No untyped value
(`serde_json::Value`, an object of unknown shape, an argv string) travels
past the adapter.
*Checked:* a count of untyped values in the signatures of ports, core
functions and public items outside the adapters, kept until it is zero.

*Patterns* ([patterns.md](patterns.md) §3): parse, don't validate; make illegal states unrepresentable; fail closed.

**R5. Deep modules.** SHOULD. A module's public surface is small against
what it hides. A module that only passes calls on is folded into its
caller or callee. A module grouped by kind of code ("all the helpers") is
regrouped by what it knows.
*Checked:* public items per module are reported; a rise is a question in
review, not a failure.

*Patterns* ([patterns.md](patterns.md) §1): deep modules; decomposition by knowledge, not by time order.

**R6. Failures handled where they can be.** MUST for adapters. An adapter
sets its own time limits, retries what is safe to retry, keeps a
supplier's budget, and answers edge cases as normal results. A failure it
cannot absorb becomes one of a few named outcomes of the port
(`Unreachable`, `SignIn`, `Refused`), reported once, never a raw status
passed up.
*Checked:* a fake of each port that times out, refuses and answers oddly,
and a test that the program carries on with one report.

*Patterns* ([patterns.md](patterns.md) §4): define errors out of existence; pull complexity downward; timeouts, bulkheads, circuit breakers; named failure outcomes.

**R7. Tests at the interface.** MUST. A module is tested through its
public interface and fakes of its ports. Only an adapter's own tests pin a
supplier's call shapes, against recorded samples of its real answers. The
tests come before the moves they protect.
*Checked:* fakes implement the port; only adapter tests name the
supplier's paths.

*Patterns* ([patterns.md](patterns.md) §6): test at the interface, with fakes; contract tests from recorded samples.

**R8. Dependencies point inward.** MUST. The core depends on nothing of
the shell or the adapters. Adapters depend on the port types, never the
other way.
*Checked:* the crate graph, or a check of the import lines.

*Patterns* ([patterns.md](patterns.md) §2): the dependency rule.

**R9. Contracts change by expand, then contract.** MUST. A new term goes
in beside the old one, callers move to it, and the old term goes in the
next major release. Inside a repository a move goes in beside the old
module and the old is removed once nothing calls it.
*Checked:* the repository's contract file lists what is frozen and since
which release.

*Patterns* ([patterns.md](patterns.md) §5): parallel change; branch by abstraction.

**R10. Small, behaviour-keeping steps.** MUST. A move keeps behaviour,
lands as an ordinary pull request, and is green on its own. No big
rewrite.
*Checked:* in review.

*Patterns* ([patterns.md](patterns.md) §5): preparatory refactoring.

## 4. The pointer and the files a repository keeps

`.tehas/repository.toml` names the standard in its `[standard]` table:

```toml
[standard]
version = "v2"
```

`"v1"` (or no file) is the code as it is, with the
architecture test skipped; `"v2"` is this standard, with the test enforced on
every pull request. Any other value is refused by name. The script owns the
`[standard]` table only: an unknown key in it is refused, other tables are
left to their owners. A file with no `[standard]` table is refused, so a
typo can't switch the checks off. Before v2 the pointer was the one line of
`.tehas/coding-standard`; it is read only for `v1`, and a repository never
keeps both files.
An adopted value only goes up: a repository never writes a lower version
than it has adopted.
A minor of v2 is a new directory, `v2.1/`; this file does not change. A repository takes it by writing `v2.1` once its script knows it:
the v2 script knows only `v1` and `v2`, the v3 script knows the minors.

A repository at `v2` keeps `AGENTS.md`'s architecture section,
`docs/architecture.md` (the knowledge map, ports, departures, grades),
`docs/architecture-review.md`, `docs/architecture-rubric.md`,
`architecture.toml` and `scripts/architecture.py`, and runs
the `architecture` job on every pull request.

## 5. The architecture test

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

## 6. Review

Every pull request is reviewed against the questions for R1 to R10.
A "no" is fixed or answered in the pull request with a reason; a reason
that holds becomes a departure in `docs/architecture.md`.

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

## 7. Grading

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
