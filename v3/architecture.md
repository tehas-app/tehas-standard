# Architecture standard v3

Part of tehas-standard v3. The coding standard's rules hold inside one
repository. These six rules carry the same ideas across repositories:
across the factory, the industry, the annexes and the plugins.

## Terms

This standard uses the terms of ISO/IEC/IEEE 42010:2022. The **entity of
interest** is the tehas system, or one of its parts. Its **stakeholders**
are the people and programs that build, run or use it; their
**concerns** are what each needs to know. An **architecture description**
expresses the architecture: in each repository it is
`docs/architecture.md`, with its knowledge map. A **view** shows the entity
for some concerns, under the rules of a **viewpoint**. In those terms
tehas-standard is an architecture description framework: the coding
standard sets the viewpoint for one repository, this standard the
viewpoint across repositories, and the contracts standard the viewpoint
of the seams. tehas-standard does not claim conformance to 42010.

## The rules

**A1. One owner for each piece of knowledge, across the system.** As R1
does inside a repository. A ticket's states, an event's name, a manifest's
fields, a model call's shape: each is decided in one repository, and every
other repository reads it from there. Two parts that need the same rule
ask its owner; neither keeps a copy.

*Patterns* ([patterns.md](patterns.md) §1): information hiding.

**A2. Every contract between programs is a schema in its owner's `api/`.**
Read by the others at a pinned release, never re-declared. Types in
another language are generated from it. The rules for contracts, and the
catalogue of the system's external APIs, are in
[v3/contracts.md](contracts.md).

*Patterns* ([patterns.md](patterns.md) §3): schema first.

**A3. Event names in the ports' words, not a supplier's.** An event says
what happened in our terms (`cycle.started`, `change.offered`,
`ticket.closed`), not how a supplier said it (no `pull_request.opened`).
An event has two sides: the `after` side notifies (nothing waits), the
`before` side of a few points is a gate (the act waits for an answer). A
listener names a point as `hook:<when>:<event>`; a gate holds when no
answer comes. Event APIs are described in AsyncAPI 3.0 ([v3/contracts.md](contracts.md) C2).

*Patterns* ([patterns.md](patterns.md) §2, §7): ubiquitous language; event notification and hooks.

**A4. A contract changes by parallel change, never on a flag day.** The
new term ships beside the old in a minor release, readers move, the old
term goes in the next major ([v3/contracts.md](contracts.md) C4). No release
of one part may require a simultaneous release of another.

*Patterns* ([patterns.md](patterns.md) §5): parallel change.

**A5. An end-to-end check that the released versions still fit.** The
released versions of the parts are run together before a release is
tagged, and the manifest of versions that work together is kept. A part's
release that breaks a seam is not tagged.

*Patterns* ([patterns.md](patterns.md) §6): end-to-end fit check.

**A6. A checklist each extension standard meets before it is tagged.**
Plugins, adapters and events each have their terms, guarantees, contracts,
host-side split and conformance checklist written before they enter a
tehas-standard tag ([v3/contracts.md](contracts.md) §4).

*Patterns* ([patterns.md](patterns.md) §7): microkernel.

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
- [v3/contracts.md](contracts.md) and [v3/patterns.md](patterns.md) of this tag.
- Informative: ISO/IEC/IEEE 42010:2022, *Software, systems and enterprise: architecture description*, for its terms (§ Terms).

## What follows from them

- **Small cores.** The factory and the industry keep their core features;
  additions come as plugins or annexes, each through a documented external
  API. Code used by one plugin lives with that plugin; a service two
  plugins share stays in the host, and reaches them as a grant input read
  with `fs.read` or, where it must compute, as a host function.
- **The factory runs alone.** It never needs an industry, and its APIs
  never name one. An industry adds what many factories share.
- **An annex** (a plant and its plugin, ours) reaches factories only
  through the industry and the factory API, and shows only as a plugin.
- **A plugin** reaches its host only through the plugin host API
  ([v3/plugins.md](plugins.md)).
- **Suppliers sit behind ports.** The code host, the ticket tracker, the
  model server: each is a port with an adapter (R2), so a second supplier
  touches only adapter code.

## What stays out of this standard

The concrete map of one deployment of the tehas system (which part owns
which knowledge today, which private part reads which seam) is kept by its
owner, not here. Each program keeps the manual of its own implementation
and names the tehas-standard version it follows in
`.tehas/standard`.
