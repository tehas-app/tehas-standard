# External contracts v3

Part of tehas-standard v3. The rules every external API of the tehas system
follows, and the catalogue of those APIs: between the factory, the
industry, an annex and a plugin.

**External** means used by another program or by a person outside the
repository that owns it: a command and its exit statuses, a `--json`
object, a setting, an HTTP route, an event, a file another program reads,
a schema, a host function a plugin calls. **Internal** is everything else
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
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html), for the releases of a part's external API (not for tehas-standard's own versions).
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12) (Core and Validation), for every object schema.
- [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.1), for every external HTTP route.
- [AsyncAPI 3.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0), for every external event API.
- The [Model Context Protocol specification](https://modelcontextprotocol.io/specification), at the revisions a server names, for every external MCP server.
- The [Component Model](https://component-model.bytecodealliance.org/) and its WIT, for a plugin host API.
- Informative: [CloudEvents 1.0.2](https://github.com/cloudevents/spec), see § Open.

## 1. The rules

**C1. One owner, one document.** Each external API has one owning
repository and one document of its own, written for its readers, apart
from the code and from any plan: `docs/contract.md` for what is public, and
for each API a reference page (`docs/api.md`, `docs/mcp.md`, a spec under
`docs/specs/`). A reader needs nothing but that document and the schemas
to use the API. The document says who its readers are.

**C2. Schemas in `api/`, in standard formats.** Every object that crosses an external seam has a
JSON Schema (or, for the plugin host API, a WIT world) in the owner's
`api/`, with at least one sample per shape (`<name>.sample.json`,
`<name>.bare.json`, `<name>.full.json`, an edge case as
`<name>.<case>.json`). The schema and samples are tested against the code
that writes them. A reader takes the schema from the owner at a pinned
release; it never re-declares the shape by hand (architecture rule A2).
Types for a language are generated from the schema or the WIT, never
written beside it. The formats:

*Patterns* ([patterns.md](patterns.md) §3, §6): schema first; contract tests from recorded samples.

| What crosses | Described by |
| --- | --- |
| an object (a `--json` answer, a setting file, an event's payload, a manifest) | JSON Schema 2020-12; each file declares `"$schema": "https://json-schema.org/draft/2020-12/schema"` |
| an HTTP route (the industry API's routes, an annex plant's routes, the host bridge) | an OpenAPI 3.1 document, `api/openapi.yaml`, whose schemas reference the files of `api/`, never copy them |
| an event API (the factory's events, the events the industry raises) | an AsyncAPI 3.0 document, `api/asyncapi.yaml`, referencing the event schemas |
| an MCP server (its tools, resources and prompts) | the Model Context Protocol specification revisions it speaks, named in its document; each tool's input and output schema as JSON Schema 2020-12 in `api/`, the same schemas the server answers `tools/list` with, tested against the server |
| a plugin host API | a WIT world |
| a command line | the command list (`api/commands.txt`) and the contract's exit statuses |

**C3. One surface list for each minor release, kept.** The owner records
its public names for each minor release of the part in a generated file of
its own, `api/surface-<major>.<minor>.txt` (`api/surface-2.1.txt`): one
name per line, its kind first, sorted. Every kind of public name is in it:
commands, flags, exit statuses, settings and values, routes, fields, labels,
event names, host functions, MCP tools with their arguments and result
fields. A name not on the list is internal or
building, and may change in any release.

- **Kept, never edited.** The file of a released minor never changes. The
  next minor starts a new file from it; older files stay beside it, so the
  surface of every release can be read without git.
- **The part's own versions are semantic.** A part's external API follows
  Semantic Versioning 2.0.0, unlike tehas-standard's own numbers: a patch
  adds no public name, a minor only adds, only a major may remove. So the
  delta between two minors of one major is additions only, and the
  release notes' "Added in <minor>" list is that delta.
- **The gate** fails when:
  - the current minor's file is not what the generator writes from the
    code;
  - a name of the previous minor's file of the same major is missing from
    the current one;
  - a patch release changes the current minor's file;
  - a name left out of a new major's first file is not in the retired-names
    list and in "Changed in <major>";
  - a retired name comes back.

- **Tagging forces the update.** The part's release workflow runs a
  surface step before it tags, and refuses the tag when it fails:
  - a new minor or major (`vX.Y.0`): `api/surface-X.Y.txt` MUST exist,
    be what the generator writes at the tagged commit, and, for a minor,
    hold every name of the previous minor's file. The step writes the file
    and asks for its commit when it is missing, so a new version's surface
    is always recorded before its tag;
  - a patch (`vX.Y.Z`, Z above 0): the generator's output MUST equal
    `api/surface-X.Y.txt`. A patch fixes bugs and changes no surface, so
    this step normally passes with nothing to do; a difference means the
    release is a minor, not a patch.

Command lists (`api/commands.txt`) and event lists (`api/events.txt`), where
a part keeps them apart, follow the same rule. The OpenAPI and AsyncAPI
documents (C2) carry the part's version in `info.version`.

**C4. Within a major, only additions.** A part numbers its releases by
Semantic Versioning 2.0.0. Within a major release a public name is only
added, never renamed, removed or given a new meaning: a
command, flag, exit status, setting, value, route, field, label, event
name or host function. A change waits for the next major, by expand then
contract (R9). A major lists what it changed once, in the contract's
"Changed in <major>", each change with its readers and what they do.

*Patterns* ([patterns.md](patterns.md) §5): parallel change.

**C5. Readers are tolerant, writers are strict.** A reader ignores a field
it does not know, and treats an enum value, a state or an event name it
does not know as unknown, not as an error. A writer writes only what its
schema allows; an object that fails its schema is refused at the edge and
shown as unreadable (R4). Two exceptions fail closed: an unknown field in a manifest or a grant is
refused, so a newer file never runs half read; and an unknown value or
field in a gate's answer holds the act, never allows it.

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
| **Factory events** | the factory | the industry, plugins, annexes | the event names and each event's object, pull first (each is also a fact the factory API prints) | tehas `docs/specs/<date>-events.md` | tehas `api/event.schema.json`, `api/event-<name>.schema.json`, `api/events.txt` |
| **The factory's MCP server** | the factory | agents, the work cycle | tools, their arguments and answers | tehas `host/docs/mcp-server.md` (protocol revisions `2026-07-28` and `2025-11-25`) | each tool's input and output schema in tehas's `api/` (not yet written; the schemas live in the code today) |
| **The host bridge** | the factory (its side) | the industry, which answers it | `/host/bridge.json` on the factory's origin: data the dashboard draws natively | tehas `host/docs/api.md`, the host bridge | tehas `api/host-bridge.schema.json` |
| **The industry API** | the industry | its operator, annexes, the factories' pages, end-to-end tests | its commands and `--json` objects, its routes, its settings, the events it raises from its polls | the industry's `docs/contract.md`, `docs/mcp.md` | the industry's `api/*.schema.json`, `api/surface-<v>.txt` |
| **The model gateway** | the industry | factories, annex plants | a model call in a supported shape (`openai-completions`, `anthropic-messages`) with the caller's budget; an endpoint's address from the industry's settings | the industry's gateway document | the shapes are the suppliers' published APIs; budgets in the industry's settings schema |
| **An annex's wire** | the annex | its plugin, the industry that runs its plant | the types between the plant and its plugin, and the plant's routes the industry fronts | the annex's `docs/contract.md` | the annex's `api/` |
| **The plugin host API** | the plugin host (the factory today) | plugins | the manifest, the grants, the host functions, `ctx`, a run's outputs, a gate's answer, the view's frame contract | [v3/plugins.md](plugins.md); the host's plugin spec | the host's `api/` WIT world `tehas:plugin`, `plugin-manifest`, `plugin-context`, `gate-answer`, `plugin-review` schemas. Specified, not built (2026-11-25) |
| **The vetted list** | the plugins' list | hosts | entries (repo, commit, `dist/` hash, grants, state), its serial, expiry and signature | [v3/plugins.md](plugins.md) §11 | the list's own schema (not yet written) |
| **The kit** | the factory | pages of every part, plugin views | the kit's files and exports at `kit <n>`, its `.d.ts` | tehas `host/docs/frontend.md` | `solid.d.ts` (and `kit.d.ts` once the kit ships it), the kit's `MANIFEST` |
| **A plugin surface request** | the host | plugin builders | an issue form asking the host for a surface a plugin lacks | the host's `plugin-surface` issue template (not yet added) | none |

Rules for each seam:

- **The factory knows no industry.** The factory's APIs never name the
  industry. The industry reaches a factory only through the factory API,
  its settings, its events and the host bridge.
- **An annex reaches factories only through the industry** and the
  factory API. It shows in a factory or the industry only as a plugin,
  under the plugin standard.
- **A plugin reaches its host only through the plugin host API.** Nothing
  else exists inside the engine.
- **A third party writes against these documents alone.** A plugin or a
  program outside the tehas system needs nothing internal to use an
  external API.

## 3. A new external API

Before a new external API ships, its owner has:

1. the document (C1), its readers named;
2. the schemas and samples, tested against the writer, and its route or
   event entries in `api/openapi.yaml` or `api/asyncapi.yaml` (C2);
3. the names on the current minor's surface list, or marked building
   (C3, C6);
4. the exit statuses or failure answers, failing closed (C7);
5. its row in the table above, through a minor version of this standard;
6. an end-to-end check with one reader (C9).

## 4. Checklist for an extension standard

An extension standard (the plugin standard, an adapter API, the events)
is tagged into tehas-standard only when it has:

- its terms, apart from any one host's;
- its guarantees, as a numbered list a reader can rely on;
- its contracts as rows of §2, each meeting C1 to C9;
- what a host keeps in its own spec, named;
- a conformance checklist for the thing that extends (a plugin, an
  adapter);
- the decisions it rests on, cited.

## Open

*Informative.*

- **Earlier surface lists.** Parts that renamed their list at a major
  (`surface-1.0.txt` became `surface-2.0.txt`) recover the earlier files
  from their release tags when they move to v3, as far as the tags allow.
- **MCP tool schemas.** tehas's MCP server keeps its tools' schemas in its
  code, and its surface list has no tool lines (2026-11-25). It writes them
  into `api/` and its surface list when it moves to v3. An industry or
  annex plant that serves MCP does the same; a part that is only an MCP
  client has nothing to record.
- **The two description documents are new.** No part has an
  `api/openapi.yaml` or `api/asyncapi.yaml` yet (2026-11-25). Each part writes them when it moves to v3, from the schemas it already
  has.
- **CloudEvents.** The tehas events envelope is the host's own, frozen for
  2.x. A mapping to the CloudEvents 1.0.2 attributes (`id`, `source`,
  `type`, `specversion`, `time`, `data`) MAY be added in a minor as an
  optional binding. Making CloudEvents the envelope is a major, a question
  for v4.
