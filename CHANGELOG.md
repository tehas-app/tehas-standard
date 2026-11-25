# Changelog

## v3 (draft)

- Event subjects are owned: `plugin-<name>` and `annex-<name>` belong to
  the plugin and the annex, and no host raises under them (contracts §2,
  plugin standard §10). Carrying plugin events is open.
- Coding standard v3: R11 (the host's kit, verified vendor libraries), R12
  (one pinned strict checker per language, with a ratchet), R13 (pure
  models and plugin drivers, tested), R14 (a plugin uses the host's
  surfaces).
- The plugin standard, manifest `"plugin": 2`: plugins as `src/` and a
  built `dist/`, vetted by hash and run in a WebAssembly sandbox with one
  host API written in WIT; views on their own origin, one custom element on
  the kit; WebAssembly modules as pure compute; trust through a signed
  vetted list for our own plugins and a person's approval for the rest;
  grants an admin gives by hand for anything on a person's path.
  (`issue:advisory` and `feed:advisories` are queued for the host spec's
  revision 5 and need the owner's OK.)
- External contracts: the plugin host API, the vetted list and plugin
  surface requests join the catalogue.
- Repository conventions move to their own page, with the `types` and
  `plugin` CI jobs and the review questions for R11 to R14 and C1 to C9.
- The architecture script learns `v3` and minors, enforces in order and
  refuses a version it does not know.
- Plugin hardening (plugin standard §14): a narrow repository view,
  host-call deadlines and budgets, output escaped, no precompiled code, a
  versioned WIT package, secrets redacted, the view in a sandboxed frame,
  devices by two keys, browser WebAssembly as boxed third-party code.
- MCP servers in the contracts: the protocol revisions a server speaks,
  each tool's input and output schema in `api/`, tools on the surface list.
- Formats: JSON Schema 2020-12 for objects, OpenAPI 3.1 for routes,
  AsyncAPI 3.0 for events (contracts C2); MADR 4.0 for decision records,
  arc42 sections for `docs/architecture.md`, Diátaxis for `docs/`, SLSA
  v1.1 Build L2 for trusted release workflows (repository conventions).
- BCP 14 key words and normative references in every file.
- Architecture patterns: v2's plus the microkernel, capabilities and least
  authority, WebAssembly sandboxing, islands architecture and origin
  isolation; each rule names the patterns it rests on.
- Each version is a directory of its own, complete, never edited once
  tagged; a minor is a full copy (`v3.1/`).
- `[standard] version` accepts minors (`"v3.1"`).

## v2 (draft)

- Event subjects are owned: `plugin-<name>` and `annex-<name>` belong to
  the plugin and the annex, and no factory or industry raises under them
  (contracts §2).
- Coding standard v2: R1 to R10, the knowledge map, the architecture test as
  ratchets, review questions and grading on four bands.
- The architecture standard: A1 to A6, rules across repositories.
- External contracts: C1 to C9 and the catalogue of the system's seams.
- No plugin standard.
- `[platform]`: Rust 1.x and TypeScript 7.x.
- `AGENTS.md` names the standard and its exact version first.
- The pointer is `tehas.toml` at the repository root, table `[standard]`,
  keys `url` (the standard's full URL) and `version`;
  each table of the file has one owner. Before v2 it was the one line of
  `.tehas/coding-standard`, read only for `v1`.
- JSON Schema 2020-12 for every schema; BCP 14 key words.
- Architecture patterns: the published patterns R1 to R10, A1 to A5 and C1
  to C9 rest on, each rule naming its own.

## v1

- The code as it was, with no formal definition.
