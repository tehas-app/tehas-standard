# Changelog

## v3 (draft)

- Adapter routes cover GraphQL as persisted operations (name and document
  hash, mutations only in write methods, the target filled in by the
  host); plugin code runs as its own operating system user, apart from
  the core (plugin standard §2a, §14).
- Adapter plugins: the vetted entry carries a route table (methods, path
  templates and credential kind per port method), each origin says whether
  the credential may go to it, and a host release may ship a default
  vetted-list entry for our own adapter (plugin standard §2a, §14).
- An adapter plugin may be one WebAssembly component built from Rust,
  implementing the host's adapter world, its imports exactly that world's
  and its I/O only `http.request` (plugin standard §2a, §8). Ordinary
  plugins keep core modules only.
- The API changes tool, `tools/api_changes.py` (contracts C3): the delta
  between two commits' `api/`, for the CI job summary and the release
  notes; in a minor it marks removals and changes, in a patch everything.
- Adapter plugins (plugin standard §2a): `kind: "adapter"`, our own only,
  called by the core and never acting on their own, outside the plugins
  switch, carrying out the core's writes; their one way out is
  `http.request` to listed origins, the credential held by the host
  (§6, §14; coding standard R14). A plugin is on no host release. Views
  may be static HTML; a driver imports no `node:` module; the starter is
  `tehas plugin new`; our own plugin repositories keep `tehas.toml` at
  the root.
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
  (`issue:advisory` and `feed:advisories` come with guard's pull request;
  `issue:advisory` waits for the owner's OK there.)
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
