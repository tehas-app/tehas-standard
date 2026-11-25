# External contracts v2

Part of tehas-standard v2. The rules every external API of the tehas system
follows, and the catalogue of those APIs: between the factory, the
industry and an annex. v2 has no plugin standard, so it has no plugin host API.

**External** means used by another program or by a person outside the
repository that owns it: a command and its exit statuses, a `--json`
object, a setting, an HTTP route, an event, a file another program reads,
a schema. **Internal** is everything else
(a crate's items, a unit's verbs, a store's tables, a private socket
between two programs of one repository). Internal APIs are not in this
standard and are never promised: the owner may change them in any release.

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
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) (Core and Validation), for every object schema.


## 1. The rules

**C1. One owner, one document.** Each external API has one owning
repository and one document of its own, written for its readers, apart
from the code and from any plan: `docs/contract.md` for what is public, and
for each API a reference page (`docs/api.md`, `docs/mcp.md`, a spec under
`docs/specs/`). A reader needs nothing but that document and the schemas
to use the API. The document says who its readers are.

**C2. Schemas in `api/`.** Every object that crosses an external seam has a
JSON Schema in the owner's
`api/`, with at least one sample per shape (`<name>.sample.json`,
`<name>.bare.json`, `<name>.full.json`, an edge case as
`<name>.<case>.json`). The schema and samples are tested against the code
that writes them. A reader takes the schema from the owner at a pinned
release; it never re-declares the shape by hand (architecture rule A2).
Types for a language are generated from the schema, never written
beside it. Each schema is JSON Schema 2020-12 and declares
`"$schema": "https://json-schema.org/draft/2020-12/schema"`.

*Patterns* ([patterns.md](patterns.md) §3, §6): schema first; contract tests from recorded samples.

**C3. One surface list.** The owner keeps the list of its public names in
one generated file, `api/surface-<major>.<minor>.txt`: one name per line,
its kind first, sorted. Its gate fails when a listed name disappears from
the code, when the file is not what the generator writes, or when a
retired name comes back (a retired-names list kept beside it). A name not on the list is
internal or building, and may change in any release. Command lists
(`api/commands.txt`) and event lists (`api/events.txt`) are kept the same
way.

**C4. Within a major, only additions.** Within a major release a public
name is only added, never renamed, removed or given a new meaning: a
command, flag, exit status, setting, value, route, field, label, event
name or host function. A change waits for the next major, by expand then
contract (R9). A major lists what it changed once, in the contract's
"Changed in <major>", each change with its readers and what they do.

*Patterns* ([patterns.md](patterns.md) §5): parallel change.

**C5. Readers are tolerant, writers are strict.** A reader ignores a field
it does not know, and treats an enum value, a state or an event name it
does not know as unknown, not as an error. A writer writes only what its
schema allows; an object that fails its schema is refused at the edge and
shown as unreadable (R4). 

*Patterns* ([patterns.md](patterns.md) §3): tolerant reader.

**C6. Building is outside the contract.** A feature still being built is
marked `building=<feature>` on its names. Its settings, commands, routes
and fields join the list only in the release that ships it.

**C7. Fail closed, with named statuses.** Malformed settings stop the
program with exit status 78; each public command's exit statuses are
listed in the contract. A program that answers for another (a gate, a
grant, a sign-in) treats no answer as no: it holds, never allows.

*Patterns* ([patterns.md](patterns.md) §3): fail closed.

**C8. Identity is the caller's, said once.** A program acting for a person
says who in one named argument (`--by <login>`) or one signed-in session;
the owner checks it against its own allowed list. No API takes a token in
an argument, a URL or a log.

**C9. Fit is tested end to end.** The released versions of the parts that
meet at a seam are run together before a release is tagged, and the
manifest of versions that fit is kept (architecture rule A5).

*Patterns* ([patterns.md](patterns.md) §6): end-to-end fit check.

## 2. The seams

Each row is an external API. Its document and schemas are the owner's; this
table says what crosses, which way, and where the reader looks.

| Seam | Owner | Readers | What crosses | Document | Schemas |
| --- | --- | --- | --- | --- | --- |
| **The factory API** | the factory (tehas) | the industry, annexes, people, scripts | commands, flags and exit statuses; `--json` objects (`status`, `history`, `question`, `start`, `answer`, `limit`, `drain`, `order`, ...); `tehas api --json`, the index of the rest | tehas `host/docs/contract.md`, `host/docs/api.md` | tehas `api/*.schema.json`, `api/commands.txt`, `api/surface-<v>.txt` |
| **Factory settings** | the factory | the industry (which writes them), people | the settings and their values, by the knob rule | tehas `host/docs/contract.md` | tehas `api/settings-rules.json` |
| **Factory events** | the factory | the industry, annexes | the event names and each event's object, pull first (each is also a fact the factory API prints) | tehas `docs/specs/<date>-events.md` | tehas `api/event.schema.json`, `api/event-<name>.schema.json`, `api/events.txt` |
| **The factory's MCP server** | the factory | agents, the work cycle | tools, their arguments and answers | tehas `host/docs/mcp-server.md` | the tool list it prints |
| **The host bridge** | the factory (its side) | the industry, which answers it | `/host/bridge.json` on the factory's origin: data the dashboard draws natively | tehas `host/docs/api.md`, the host bridge | tehas `api/host-bridge.schema.json` |
| **The industry API** | the industry | its operator, annexes, the factories' pages, end-to-end tests | its commands and `--json` objects, its routes, its settings, the events it raises from its polls | the industry's `docs/contract.md`, `docs/mcp.md` | the industry's `api/*.schema.json`, `api/surface-<v>.txt` |
| **The model gateway** | the industry | factories, annex plants | a model call in a supported shape (`openai-completions`, `anthropic-messages`) with the caller's budget; an endpoint's address from the industry's settings | the industry's gateway document | the shapes are the suppliers' published APIs; budgets in the industry's settings schema |
| **An annex's wire** | the annex | its plugin, the industry that runs its plant | the types between the plant and its plugin, and the plant's routes the industry fronts | the annex's `docs/contract.md` | the annex's `api/` |
| **The kit** | the factory | pages of every part | the kit's files and exports at `kit <n>`, its `.d.ts` | tehas `host/docs/frontend.md` | `solid.d.ts` (and `kit.d.ts` once the kit ships it), the kit's `MANIFEST` |

Rules for each seam:

- **The factory knows no industry.** The factory's APIs never name the
  industry. The industry reaches a factory only through the factory API,
  its settings, its events and the host bridge.
- **Event subjects are owned.** An event name is
  `<subject>.<what-happened>`. The factory's subjects are its own
  (`cycle`, `question`, `ticket`, `change`, `factory`). The subject
  `plugin-<name>` belongs to the plugin `<name>`, and `annex-<name>` to
  the annex `<name>`. A factory or an industry MUST NOT raise an event
  whose subject starts `plugin-` or `annex-`, and its event list MUST NOT
  hold one. A plugin or annex MUST raise its own events only under its own
  subject, never under a factory's or another's. Checked by a test of the
  factory's event list.
- **An annex reaches factories only through the industry** and the
  factory API.
- **A third party writes against these documents alone.** A program outside the tehas system needs nothing internal to use an
  external API.

## 3. A new external API

Before a new external API ships, its owner has:

1. the document (C1), its readers named;
2. the schemas and samples, tested against the writer (C2);
3. the names on the surface list, or marked building (C3, C6);
4. the exit statuses or failure answers, failing closed (C7);
5. its row in the table above, through a minor version of this standard;
6. an end-to-end check with one reader (C9).

## 4. Checklist for an extension standard

An extension standard (an adapter API, the events)
is tagged into tehas-standard only when it has:

- its terms, apart from any one host's;
- its guarantees, as a numbered list a reader can rely on;
- its contracts as rows of §2, each meeting C1 to C9;
- what a host keeps in its own spec, named;
- a conformance checklist for the thing that extends (an adapter). v2 has no plugin standard; it comes with v3;
- the decisions it rests on, cited.
