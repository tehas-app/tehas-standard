# Changelog

## v3 (draft)

- Plugin standard, ready to tag: each section says how it is checked
  and names its patterns; `issue:advisory` and `feed:advisories` leave
  v3 for a later minor, and guarantee 8 names the writes a plugin makes
  (its `/out`, its `/state`, an adapter's for the core);
  `device:<feature>` joins the grants, given by an admin; any plugin
  that asks `http` or `net:` lists its origins in the manifest; an
  endpoint plugin is exempt from the code rules; a view's GraphQL reads
  are one query, never a mutation, under the host's caps; a view gets
  `net:` once the host's spec says how it was checked; the `"v2"` bridge
  for our own plugins is gone, since §11 vets only at `"v3"` or later.
- The v3 architecture script (`tools/architecture.py`, `# tehas-standard
  v3`), after `v3/architecture-script.md`: it knows `v1`, `v2`, `v3` and
  every minor of v2 and v3 (`vN.M`, M from 1), enforces from v2 on in
  order, and refuses a later major by name. A check's rule is one of its
  version's (R1 to R14 at v3). From v3 it requires R11 to R14's checks
  where they apply, reads only `src/` for those rules in a plugin
  (`tehas-plugin.json`), checks that `AGENTS.md` names the version, and
  checks each toolchain pin (`rust-toolchain.toml`, a `versions.env`, the
  CI workflows, `package.json`) against `[platform]`. At v2 it gives what
  the v2 script gave.
- The script's reading of tracked files (issue 29): a symlink is not
  followed, a link loop is no file, a file with a UTF-16 byte order mark
  is read as UTF-16, and a check whose files match nothing warns at v2 and
  fails from v3. A base whose pointer cannot be read needs a head at least
  as high as any version that pointer spells out.
- The manifest list (plugin standard §4) names the host spec revision a
  plugin was built against and its skill files; the licence field waits
  until a host's schema has it.
- With an upstream set, every call goes through it, a person's call too,
  with the person's own credential forwarded untouched; the sign-in's code
  exchange is an upstream route; the upstream enforces the vetted origins
  per credential class; the signing job checks a blessed merge's approving
  review (plugin standard §11, §14).
- A view's worker is a `blob:` worker under the frame's policy (classic or
  module, as the browsers allow in a sandboxed frame), since an
  opaque-origin frame can start no other; the size of `bounded` is the
  host's (plugin standard §6, §9, §14).
- Plugin standard, from the host spec's revision 7: a view's network goes
  over its port to the host element and the request gate, the frame
  `connect-src 'none'` always (no proxy, no load token); blessed plugins,
  trusted like the host's code, changed only at a release or an admin's
  pin, the only home of adapters; the upstream authenticated by mutual
  TLS alone, trusted by a pinned key set; `parent` reach is not authority
  (each route names its grant, the lesser of person and plugin, no view
  writes by request); destination
  patterns optional before `net:`; audit jobs without identity, secrets
  or network, apart from the one signing job.
- Plugin network (plugin standard §2, §5, §6, §14): `net:` for either side,
  always through the host; a view's requests over its port to the host,
  no credential save a read-only one for reads;
  one destination list and one request gate for both sides; the manifest
  only asks; `methods` and a body policy per origin; the reserved origin
  `parent`; SNI and certificate on the approved name, no inherited proxy
  settings, every outbound request through an egress process of its own
  user (one for views allowed), view credentials for our own plugins
  only.
- Plugin hardening (§14): plugin processes confined by the operating system
  (no network by kernel rule where none is needed, the request server to
  the TLS port only); TLS 1.3 or 1.2 AEAD, no 0-RTT; mutual TLS to an
  upstream; body caps after decompression, `gzip` or `identity` only.
- Plugin standard: `viewer:login` joins the common grants (the pressing
  person's login from the press's session; a run holding it keeps, records,
  files and asks the model nothing); name resolution and TLS trust are the
  host's: going direct, how it resolves is its own; a pinned root bundle
  makes a spoofed name harmless; the upstream's key is pinned (§5, §14).
- Destinations (plugin standard §6): manifest origins are exact and signed;
  the host's configuration may use a leftmost `*.` label only, narrows an
  adapter, may widen other networked code as a recorded choice, and never
  adds a credential.
- The view frame (plugin standard §14): known by a `MessageChannel` port the
  host transfers per load, never by origin; the host issues every press
  nonce; caps on message size, rate and
  presses in flight; a press that acts as the person needs a confirm in
  the host's own page.
- Plugin standard: the manifest names its `actions` (press arguments under a
  schema); the view channel's messages are typed, versioned and checked,
  a press carries a single-use nonce and its answer goes only to the
  pressing frame; whether a driver may return a promise is the host's to
  say, and one that cannot settle it refuses it by name.
- The v3 script accepts a check's `rule` as any rule of the version found
  (`R1` to `R14` at `v3`), and refuses one the version lacks.
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
  (`issue:advisory` and `feed:advisories` are not in v3; they wait for
  the owner's decision and a later minor.)
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

## v2

Tagged 2026-11-26. `tools/architecture.py` at this tag has sha256
`485a7e639236c5236e542ff7fb2c9b9d815fcb7646745cbdb5c89f180cd0452b`. An
`AGENTS.md` that follows v2 links to
`https://github.com/tehas-app/tehas-standard/tree/v2/v2`.


- The architecture script counts in every tracked file: a byte that is not
  UTF-8 no longer hides the file's matches (it was read as no text). Rust
  is scanned in linear time.
- A tracked file under a directory the script cannot search stops the run
  too (exit 2), never counted as empty.
- A tracked file the script cannot read stops the run (exit 2) instead of
  counting as empty; a repair of an unreadable base pointer still keeps
  the base's [platform] toolchains when its file is TOML.
- The v2 architecture script, `tools/architecture.py`, with its tests and
  its sha256 in `tools/architecture.py.sha256`: one file every repository at
  v2 copies byte for byte to `scripts/architecture.py`. It reads each pointer
  once; a base with both pointer files counts the higher; a base whose
  pointer cannot be read lets the head repair it by naming `v2`; a run
  without `--base` compares with nothing.
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
