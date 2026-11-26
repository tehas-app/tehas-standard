# Plugin standard v3

Part of tehas-standard v3. The rules every plugin and every plugin host
meet. A manifest that follows this standard says `"plugin": 2`; a host
refuses a manifest number it does not know. tehas's own plugin
specification (2.0.0, "the operator") is the first host's implementation
of it; what is only that host's is in §12.

Plugins are additional capability for the core, mostly UI and integration
glue, not an application platform.

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
- The WebAssembly Core Specification and the [Component Model](https://component-model.bytecodealliance.org/) with WIT, for the host API and modules.
- ECMAScript 2023, for drivers and views.
- [JSON Schema 2020-12](https://json-schema.org/draft/2020-12), for the manifest and every object a run exchanges.
- [SLSA v1.1](https://slsa.dev/spec/v1.1/), Build track, for the provenance of what a host trusts (§11).
- [v3/coding.md](coding.md) and [v3/contracts.md](contracts.md) of this tag.

## 1. Terms

| Term | Meaning |
| --- | --- |
| a plugin | An addition to a host: a git repository, pinned by commit, whose `dist/` the host vets and runs with the grants it was given. What a builder writes |
| a host | The program that pins, vets and runs plugins and serves their views. The factory is the host today |
| the operator | The host's service that runs plugins, each run in a fresh WebAssembly instance |
| a builder | Whoever writes and builds a plugin |
| an admin | The person who manages a host's plugins: pins, approves, grants, turns on |
| a grant | One capability a plugin may use on one host, given for one commit |
| a tool | A function a plugin offers to the chats (`tool:<id>`), which a model calls. Never a name for a plugin |
| a module | An ES module (a file of `dist/`) or a WebAssembly module (`dist/wasm/<name>.wasm`). Never a name for a plugin |
| our own plugins | Plugins on the host's signed vetted list, annexes' plugins included |
| a blessed plugin | One of our own that the owner blesses: trusted like the host's own code, the truth of its answers included (§11) |
| a third-party plugin | Any other plugin |
| an adapter | The one implementation of a port for one outside system (coding standard R2). Delivered as a plugin, it is an adapter plugin (§2a) |
| an adapter plugin | A plugin of `kind: "adapter"`: an adapter the core calls on its own path, under §2a |
| an ordinary plugin | Any plugin that is not an adapter plugin |

## 2. The guarantees

A host gives every ordinary plugin, and every person on the host, these.
An adapter plugin keeps them except where §2a says otherwise.

1. **Off unless asked.** With plugins off, nothing is fetched, vetted or
   run, and nothing of plugins shows.
2. **Pinned and vetted.** A plugin is a git URL and a full commit, on its
   own schedule: a plugin is on no host release. The host
   runs exactly the `dist/` bytes that were approved, by their hash. A new
   commit runs only once it is approved; the last approved commit keeps
   running meanwhile.
3. **Fail closed.** A malformed plugin setting stops the settings load. A
   manifest or `dist/` that breaks a rule makes that plugin refused, and
   nothing of it runs.
4. **A refused or unreachable plugin is skipped, not fatal.** The host
   carries on with the rest and says why.
5. **Outside the work.** A plugin never runs inside a cycle, and a cycle is
   given nothing new because a plugin is on.
6. **Nothing without a grant.** Each grant opens one group of host
   functions; a call no grant covers is refused before any work is done.
7. **Signed in, always.** Every address of a plugin is behind the host's
   sign-in. A view loads nothing from another site itself: it reaches
   one only through the host, under `net:`, over its port (§14). (How a host
   signs a person in is its own.)
8. **Writes only through the host.** A plugin never writes to the product,
   the code host or the host's store; the host writes what a run returns.
   The one exception planned is `issue:advisory` (§5), an admin's
   grant, waiting for the owner's OK, which is decided in guard's pull
   request.
9. **Approval stays a person's.** A plugin never approves or merges the
   host's work and never removes a person's approval; there is no merge
   grant.
10. **No answer means hold.** A gate or phase that gets no answer, because
   the run failed or the operator is down, holds the act, whatever its
   policy. A person can always lift a hold.
11. **Contained.** A run's failure is that run's. The host's own code never
    runs plugin code, and a plugin can't crash or starve the host.
12. **Removable.** A plugin taken out loses its view, state and schedule at
    the next update. Its run history stays.
13. **Any licence**, closed source included.

Guarantees 1 to 8, 12 and 13 carry tehas's 1.x plugin guarantees into
this version, as plugin spec 2.0.0 reshapes them. 9 is tehas's hard rule 5, which plugin spec 2.0.0 keeps. 10
and 11 are plugin spec 2.0.0's (its decisions 30 and 32).

## 2a. Adapter plugins

An adapter plugin is how the core reaches an outside system (a code host,
say) when that adapter ships as a plugin and not inside the host. It is
the core's own code, delivered apart.

- **Blessed only.** An adapter plugin exists only in a blessed plugin
  (§11). A host refuses any other plugin of `kind: "adapter"`.
- **Called, never acting.** It runs on the host's path only when the core
  calls it through the port, and does only what that call asks. It has no
  schedule, hook, view, tool or gate of its own, and never decides to
  write.
- **Not under the plugins switch.** Turning plugins off (guarantee 1)
  leaves adapter plugins running, so the host still reaches its outside
  systems. Guarantee 1 binds ordinary plugins.
- **Inside the work, as the core's hands.** Guarantee 5 binds ordinary
  plugins: an adapter plugin runs inside a cycle when the core calls it.
  Guarantee 8 binds ordinary plugins: an adapter plugin carries out the
  core's writes to its outside system, and only those.
- **Approval stays a person's** (guarantee 9) holds for adapter plugins
  too. A merge is the core's rule, behind a person's gate, and no plugin,
  adapter or not, has a merge grant.
- **Its one way out** is `http.request` (§6), to the origins its manifest
  and its vetted entry both list. The host holds the credential; it never
  enters the engine. Each origin says whether the credential may go to it
  (`credential: true` or `false`); the host never sends it to one that
  says `false`, nor on a redirect to one.
- **Destinations: exact in the manifest, narrowed on the host.** See §6.
- **Its routes are vetted.** An adapter plugin's vetted entry carries a
  route table: for each port method, its routes and the credential kind
  allowed. A route is an HTTP method and a path template, or a persisted
  GraphQL operation: its name and the sha256 of its exact document. The
  host refuses a request that is not in the routes of the port call in
  flight.
  - For GraphQL the adapter sends an operation's name and its variables,
    never a document; the host sends the vetted document. A mutation is
    only in a write method's routes.
  - The target the port call names (a repository, say) is filled in by the
    host, never by the adapter.
  - The credential the host attaches SHOULD be narrowed to what the port
    call needs, where the outside system allows it (its permissions and
    the one target).
- **A release may ship a default entry.** Guarantee 2's "on no host
  release" binds ordinary plugins. A host release may ship a default
  vetted-list entry for our own adapter plugin, so a host that has chosen
  no adapter runs that entry. It is an entry like any other: signed, a
  full commit, the `dist/` hash, its origins and routes. It is not a pin
  in the release's code. Being blessed, it changes only with a release's
  default entry or an admin's pin, never because a newer signed entry
  appears.
- **Its own world.** An adapter plugin implements the host's adapter world
  (tehas: `tehas:adapter`), made from the host's port types: the ports as
  exports; `http.request`, `log` and the host state the ports need as
  imports. It has no files, git, model, sockets, environment or arguments.
- **JavaScript or one component.** An adapter plugin is either JavaScript in
  the engine, like any plugin, or one WebAssembly component built from
  Rust that implements the adapter world itself (§8).
- **Refused or unreachable is the port's failure.** Guarantee 4 binds
  ordinary plugins: an adapter plugin that is refused or down fails the
  core's call as an adapter does (coding standard R6), never skipped in
  silence.
- Pinned and vetted (2), fail closed (3), contained (11) and the
  hardening of §14 hold in full.

## 3. Layout, and who builds

```
tehas-plugin.json   the manifest; its paths point into dist/
src/                source: .ts, .tsx, .jsx, .js, tests, each module's source
dist/driver/        deployable driver JS; main.js exports run(ctx)
dist/view/          deployable view JS, HTML and CSS
dist/view/wasm/     WebAssembly modules the view runs in the browser
dist/vendor/<lib>/  verified third-party libraries
dist/wasm/          WebAssembly modules the driver runs
dist/test/          built tests
skills/             skill files
```

- **Builds are the builder's.** The builder picks the tools and commits
  `dist/` at the pinned commit. The host ships no build command and
  transforms nothing.
- **The host deploys `dist/` and nothing else.** It never compares `dist/`
  with `src/`; the builder's CI keeps them in step (coding standard R14).
- **`src/` is for people.** It holds the source of the plugin's own
  JavaScript. A WebAssembly module's source and build recipe may be named
  there too; our own plugins must name them, so their modules rebuild to
  the same bytes (§8).
- **Types** come from the host: `tehas.d.ts`, generated from the host API
  (§6), and the kit's `kit.d.ts` and `solid.d.ts`.

## 4. The manifest

- One JSON file, `tehas-plugin.json`, under a closed schema the host
  publishes in its `api/`: an unknown field is refused. A size cap holds.
- `"plugin": 2`. A host refuses a number it does not know.
- The exact keys are the host's schema's; this list is what every host's
  manifest names.
- It names: the plugin's `name`, `label`, `kind` (`adapter` for an adapter
  plugin, §2a; other kinds are the host's) and `license`; the
  `runtime` (`"starlingmonkey"`, the engine, the only value for an
  ordinary plugin with this version; `"component"` for an adapter plugin
  built as one component, §8); the `timeout` of a run; what it `asks`; its views; the named `actions` a
  view may press, each with a JSON Schema for its arguments; each
  WebAssembly module by name, the driver's apart from the view's, with an
  optional source path and build recipe; each vendor library with its version, upstream and per-file
  hashes; for an adapter plugin, the `origins` it may reach, each with
  whether the credential may go to it; the `solid-js` version its compiled view expects; its schedules
  (`every:`, `clock:`); its hook points.
- An endpoint plugin (a model provider) is a manifest only: id, API shape
  (`openai-completions` or `anthropic-messages`) and models. Its address
  comes from the host's or the industry's settings, never from the
  plugin.

## 5. Capabilities and grants

- A plugin **asks** by name in `asks`; a grant gives a value only on a
  host. Names are `name` or `name:<value>`. A host refuses a name it does
  not know.
- The common names: input grants (`product`, `history`, `files`,
  `cycles`, `issues`, `pages`, `live:<feed>`, `feed:<feed>`,
  `industry:logs`; `feed:advisories`, which comes with guard's pull request); `keep` (a
  private `/state`); `model:<tokens>` (a token budget per run), with
  `model:images`; `view`, `menu`, `action:<id>`; `every:<interval>` and
  `clock:<when>`; `hook:<when>:<event>`; `tool:<id>`; `record`;
  `issue:draft`; `net:`, a plugin's network on either side, through the
  host only (§6, §14); `viewer:login`, the one piece of a person's data a host
  gives a view: the login of the person who pressed, taken from that
  press's own session, never from the message; a run that holds it can't
  keep it, record it, file issues or call the model; `http`, for an adapter
  plugin only (§2a), refused to any other. A host may add its own; it lists them in its spec.
- **Grants an admin gives by hand.** Turning a plugin on never gives a grant
  that holds or acts on a person's path:
  - `hook:before:<event>=<policy>` (a gate; a gate grant with no policy is
    refused);
  - `phase:<id>` (policy `pass` or `hold`);
  - `answer:<kind>` (one plugin per kind; a person's answer always wins);
  - `issue:advisory`, waiting for the owner's OK, decided in guard's pull
    request
    (files one issue with public facts only: package,
    advisory id and link, installed and fixed versions; one open issue per
    package and advisory, a daily cap).

  A review lists them apart, as "needs your grant".
- **Our own plugins:** turning one on gives the grants of its vetted entry,
  less those above. A later commit that asks for more waits for the admin;
  the host keeps running the last commit that fits.
- **Third-party plugins:** the admin gives each grant.

## 6. The host API

- **One interface, written once in WIT** as the world `tehas:plugin`, in the
  host's `api/`; an adapter plugin's is the host's adapter world (§2a),
  written the same way. The host's side and `tehas.d.ts` are generated from it, so
  the types a builder sees can't drift from what the host provides. No
  `u64`: sizes, counts and times are `u32` or `f64`.
- **The functions** and the grant each needs:

  | Function | Grant |
  | --- | --- |
  | `fs.read`, `fs.list`, `fs.stat` | any input grant |
  | `fs.write`, `fs.remove` | `/out` always; `/state` with `keep` |
  | `git.head`, `git.diff`, `git.show`, `git.tree`, `git.blob`, `git.isAncestor`, `git.defaultBranch`, `git.status`, `git.log`, `git.files` | `product` or `history` |
  | `model.chat(req)` | `model:<tokens>` (images: `model:images`) |
  | `run.module(path, argv, env)` | always |
  | `wasm.load(name)` | a module the manifest lists |
  | `http.request(req)` | `http`: an adapter plugin only (§2a); or `net:`, an ordinary plugin's driver; to its destinations (§6) |
  | `log(...)` | always |

  The engine's own web APIs (`crypto.subtle.digest`,
  `crypto.getRandomValues`, `TextEncoder`, `URL`) need no grant. Apart
  from `http.request` (an adapter's, or a driver's under `net:`), there is
  no network, socket, environment or host file access.
- **Destinations.** A manifest's origins are exact: a scheme and a host
  (and a port only where the host allows one), no pattern, each with its
  `methods` and its body policy (`none` or `bounded`; the bound is the
  host's, and a host may write it in the manifest as its own extension). The manifest only
  asks: an origin is granted by the signed vetted entry (our own) or by
  the person (third party), and vetting signs what it grants. A person
  may set a plugin's destinations in the host's configuration, in one
  format for every kind:
  - there, and only there, a pattern may be used (a host MAY support
    none until it has `net:`): a leftmost `*.` label
    alone, never `*`, never a public suffix (`*.com`, `*.co.uk`), never in
    the scheme or the port;
  - for an adapter plugin, the host's configuration only narrows what
    the manifest and the vetted entry allow;
  - for other code a host lets reach the network (an ordinary plugin under
    `net:`, an annex), the configuration may
    also widen, as an explicit choice the host records and shows in its
    status;
  - widening never adds a credential: an origin the configuration adds
    gets none.
- **One list, one gate, both sides.** A plugin has one list of
  destinations for its server side (`http.request`, a driver under
  `net:`) and its view alike; narrowing closes an origin for both. One
  request gate in the host vets every request from every side, with the
  same rules and one record format. Only the credential kinds differ by
  side.
- **The parent.** The reserved origin id `parent` is the app the plugin
  runs in. It needs no manifest entry, a manifest may not declare it, and
  the host's configuration cannot narrow it away. It reaches only the
  routes the hosting app publishes for plugins, never with the person's
  session cookie. Reach is not authority: each published route names the
  grant it needs, and a request runs at the lesser of the person's
  standing and the plugin's grants. A view never writes to it by a
  request; a write goes only through a persisted `action` with the
  person's confirm (§14).
- **`http.request`** is the host's call, not the plugin's: the host adds
  the credential, which the plugin never sees, sends the request to an
  allowed origin (or through the host's configured upstream), and returns
  the status, the headers it allows and the body. A redirect off the
  allowed origins is refused.
- **Paths** keep the mount names (`/work`, `/out`, `/state`, `/product`,
  ...). No links, no `..`; a path outside a granted root is refused.
- **`run(ctx)`** is the entry; `ctx` carries the run's context, under the
  host's `plugin-context` schema.
- **A gate's answer is a shape, not a file:** the run returns an object of
  the host's `gate-answer` schema (`{"api": 1, "answer": "allow" |
  "refuse", "why"}`). A return that doesn't fit is no answer, so the gate
  holds.
- **Language.** ES2023 modules; no timers beyond `await`. Whether `run`
  may return a promise is the host's to say in its spec, by its engine: a
  host that cannot settle one refuses a run that returns a promise, with a
  named error, and never takes a half-run result. A plugin meant for every
  host returns its result directly. A plugin that needs to wait asks for `every:` or `clock:`
  (`clock:mon-fri@06:00`).
- New host functions come through a plugin surface request and are added
  only (contracts C4).

## 7. What `dist/` must be

A host checks `dist/` before it runs or serves anything, and refuses a
plugin that fails:

- **Parse.** JS is ES modules the engine parses.
- **Imports.** A driver imports only its own `dist/` files and the host
  API (`tehas`), never a `node:` module or a package. A view imports only its own `dist/view/` files, the host's kit and
  its verified vendor libraries. No outside URLs, no source maps.
- **Readable.** In the plugin's own code: no line over 1,000 characters, no
  packed or mangled code, no `eval` or `new Function`.
- **Vendor libraries verified, not read.** In `dist/vendor/<lib>/`, named in
  the manifest; their bytes must equal the upstream release. A match is
  exempt from the readable and `eval` rules; a mismatch is refused; a
  patched file counts as the plugin's own.
- **Grant fit.** Every host function `dist/` calls is covered by the
  manifest's asks.
- **WebAssembly** follows §8.
- **Size caps** for `dist/view/`, `dist/view/wasm/`, `dist/vendor/` and
  `dist/wasm/`, set by the host.
- **Tests** in `dist/test/` pass in the engine, against fake host
  functions.

## 8. WebAssembly modules

- Built by the builder, with any toolchain, and committed as built. The
  host never compiles one.
- **Pure compute.** A driver's module imports nothing, or only `env.abort`
  or a null WASI preview 1 (no files, no sockets; output to `log`; random
  and a monotonic clock from the host; everything else `ENOSYS`). It gets
  no grants: its whole effect is what it returns. Each is its own
  instance, sharing no memory.
- **Audit, in three layers:** the binary at every deploy (its name section
  kept; imports, exports, memory and data listed; a stripped module
  refused); a rebuild from its source in `src/` with its pinned recipe,
  during vetting and never on a host ("rebuilt from source: matches" or
  "binary only"); and its behaviour through the plugin's tests.
- **Calling.** `wasm.load("<name>")` returns the module's exports. Numbers
  pass straight through; bytes are copied by the host through the module's
  exported `memory` and `alloc(len)`, with a `(ptr, len)` argument and a
  result packed as `ptr << 32 | len`.
- **Features.** wasmtime's defaults (SIMD, bulk memory, multi-value,
  reference types) are allowed. Threads, shared memory and memory64 are
  refused. Core modules only; the component model comes later, with the
  one exception below.
- **An adapter plugin may be one component.** Our own adapter plugin MAY be
  a single WebAssembly component, built from Rust, in `dist/wasm/` and
  named in its manifest, in place of a driver in the engine. The adapter
  world (§2a) is its seam:
  - its imports are exactly the adapter world's, listed from the binary
    (`wasm-tools component wit` or the same), and any other import, a WASI
    interface beyond random and the clocks included, is refused at
    vetting;
  - its host I/O goes only through `http.request`, under §6 and §14;
  - the audit above holds for every core module inside it, and it must
    match its rebuild from source;
  - threads, shared memory and memory64 are refused as above;
  - inside, coding standard R3 and R13 hold: decisions in pure modules,
    the `http.request` calls in one shell module.

  An ordinary plugin keeps core modules only.
- **Our own plugins must match** their rebuild. For a third-party plugin
  the approver decides whether "binary only" is acceptable.
- **When.** A hot loop of one plugin. Heavy work on data that starts in the
  browser (images, media, files a person picks) runs in the view's own
  module, in a worker. A hot path several plugins share is asked of the
  host.

## 9. Views

- **The origin is the boundary.** A view is served by the host on an origin
  of its own, behind the sign-in, under a policy the host writes from
  hashes. Plugin code never runs in the host's own pages.
- **The host's wrapper.** In the host's page, a host-owned custom element
  (`<tehas-plugin-view>`) frames the view and owns its size, its loading,
  failed and off states, the theme tokens (through a narrow `postMessage`
  contract) and its removal.
- **Inside its origin,** a view is static HTML, or its entry defines
  exactly one custom element, drawn with Solid 2 from the host's kit, in
  the light DOM. The element may be written as HTML and JS on the kit or
  as JSX.
- **JSX** is allowed in `src/`; the builder compiles it with Solid 2's
  compiler, DOM mode, ESM. Compiled output imports only names the kit
  exports; the host maps them to the kit's Solid and checks every such
  import against the kit's export list. Hydratable output is refused.
- **The Solid version.** The manifest names the `solid-js` version its
  compiled output expects; the host refuses one its kit does not carry.
  A builder who types `.tsx` adds `@solidjs/web` at the kit's version as a
  type-only dev dependency.
- **Heavy view work** runs in a WebAssembly module in a dedicated worker
  started from a `blob:` URL, under the frame's policy (§14), declared in
  the manifest, under §8's audit. The view's policy allows
  `'wasm-unsafe-eval'` only for a view that declares modules. A view
  module's imports are met by the plugin's own glue JS, and worker code
  does not import the kit. A vendored `.wasm` is verified by its upstream
  hash in place of a name section.

## 10. Events

- **Names in the ports' words.** The host's event list is in its `api/`
  (`events.txt`). Today: `cycle.started`, `cycle.parked`,
  `question.asked`, `cycle.ended`, `change.offered`,
  `factory.limit-changed`, `ticket.acted`, `ticket.closed`,
  `change.merged`. Names are only added.
- **Two sides of a point.** `hook:after:<event>` is a notify: nothing
  waits. `hook:before:<event>=<policy>` is a gate: the act waits for every
  gate listener's answer (tehas's events spec), and no answer holds. A host's own spec says from which of its releases it raises gates.
- **Each event's object** is under the host's `event-<name>` schema; a
  reader skips an event or field it does not know.
- **A plugin's own events** take the subject `plugin-<name>`, its own
  manifest name; an annex's take `annex-<name>`
  ([contracts.md](contracts.md) §2). A host MUST NOT raise an event under
  either. On a page they are `plugin-<name>:<event>`, never `tehas:`. How a
  plugin declares its events and their schemas, and how a host carries
  them to other plugins and pages, is not yet specified (see Open).

## 11. Trust

- **Our own plugins: automatic, audited.** Each commit to a listed plugin's
  protected main branch passes an automatic audit (every §7 and §8 check,
  the rebuild of each module, the tests, one real run against a fixture
  host). A passing commit is written to the vetted list, which is signed;
  no person approves it.
- **The vetted list.** Each entry names the repository, commit, `dist/`
  hash, manifest hash, vendor and module hashes, the most grants it may
  have, and its `state`: `building`, `vetted`, `refused` or `revoked`. The
  list carries an increasing `serial` and an `expires` date; a host
  refuses a lower serial, and an expired or unsigned list turns
  auto-approval off. A host trusts the list only through its signature.
- **Blessed plugins.** The owner may bless some of our own plugins, and
  only those may hold adapters. Blessed code is trusted like the host's
  own, the truth of its answers included. It changes only at a host
  release (its default entry) or by an admin's pin, never by a newer
  signed entry on its own, and its repository requires a person's review
  of every change: the signing job checks that the merge of the commit it
  signs had a person's approving review, and signs nothing without one.
- **The audit and the signing are apart.** The audit jobs that run
  plugin code have no signing identity, no secrets and no network. The
  one job that signs runs no plugin code.
- **Provenance.** The audit pipeline's signed list and the host's engine
  release each carry SLSA v1.1 Build Level 2 provenance or better.
- **Revocation.** A revoked commit is turned off at the next update, with
  its state kept and the admin alerted.
- **Third-party plugins** never get list trust. An admin approves the exact
  `dist/` (by commit, hash and their own account) after a review that
  shows the grants, all of `dist/` or its diff since the last approval,
  the vendor and module results, and a link to `src/`. Adding one is the
  admin's act and the admin's risk.
- A coding standard rule binds our own plugins only: a plugin is listed
  `vetted` only at `[standard] version` `"v3"` or later, with its
  architecture test green at the vetted commit.

## 12. What a host keeps in its own spec

Not in this standard; each host specifies its own and names the
tehas-standard version it meets:

- the engine and its build (tehas: StarlingMonkey through componentize-js,
  on wasmtime), its caches, how the operator is run and sandboxed;
- the default limits (memory, time, sizes, quotas, failures before a
  pause, model tokens per day) and their settings;
- its settings and commands for plugins, their exit statuses;
- how it signs a person in, its gate and its view policy in detail;
- the vetted list's signing (tehas: Sigstore keyless, the allowed identity
  in `api/plugins-signers`), its audit pipeline, the fetch of private
  repositories;
- its own extra grants and kinds.

## 13. A conformant plugin

- [ ] `tehas-plugin.json` says `"plugin": 2` and passes the host's schema.
- [ ] `src/` holds the source of all its own code; `dist/` is built from it
      and committed.
- [ ] `dist/` passes the host's checks (`tehas plugin check`) in its CI.
- [ ] Every host function it calls is covered by its asks; it asks for no
      more than it uses.
- [ ] Its views are static HTML or one custom element on the kit; its
      vendor libraries are verified.
- [ ] Its WebAssembly modules keep their name sections (a vendored one: its
      upstream hash) and, for our own, rebuild to the same bytes.
- [ ] Its tests run in the engine with fake host functions.
- [ ] It reaches models only through `model.chat`.
- [ ] Our own: `tehas.toml` at the root, at `"v3"`, architecture test
      green. Until v3 is tagged, `"v2"` is the bridge. A third-party
      plugin SHOULD keep the same file.
- [ ] An adapter plugin: on the vetted list, `kind: "adapter"`, asks
      `http` and nothing a view, schedule, hook, tool or gate needs; built
      as JavaScript or as one component whose imports are exactly the
      adapter world.

## 14. Hardening

A host treats every plugin as untrusted code, on the server and in the
browser: no static check proves a plugin harmless, so the host controls
every capability it hands out and checks it at run time.

**On the host (the operator):**

- **Plugin code runs apart from the core.** The trust boundary is plugin
  code against the core. The processes that run plugins (tehas: the
  operator, and the adapter host for adapters) each run as an operating
  system user of their own, never the core's user, and reach the core
  only through its sockets.
- **Confined by the operating system, too.** A process that runs plugins
  and needs no network gets none, by a kernel rule, not only by the
  engine's interface; the one that serves `http.request` may send only to
  the TLS port, and the host lists in its spec how it confines each.

- **A narrow repository view.** An input grant gives a prepared view, never
  the clone: tracked files at the commit only; `.env` and `.env.*`, private
  keys, credential and token files and `.git/` left out by default (a
  repository may add paths, never remove these); symlinks resolved while
  the view is prepared, one that leaves the view or reaches an excluded path
  left out; `fs.*` and `git.*` behind the same view.
- **A deadline on every host call.** Epoch and fuel interrupt WebAssembly,
  not a blocked host function, so each host function has its own deadline,
  enforced by the host.
- **Budgets per run** on host calls and bytes read, beside memory, time,
  fuel, output and model tokens. A spent budget fails the call.
- **Output is untrusted data.** Everything a run returns is bounded and
  escaped before anyone sees it: terminal control sequences stripped,
  Markdown and HTML escaped, links only as text or to the plugin's own view.
- **No precompiled code from a plugin.** The host compiles every module
  itself. `dist/` holding precompiled or native code is refused; the host's
  compiled cache is its own, and each entry's hash is checked before it is
  loaded.
- **A versioned interface.** The host API's WIT package carries a version
  (`tehas:plugin@2.0.0`) whose major matches the manifest's `"plugin"`; its
  functions are on the host's surface list, so they only grow within a
  major.
- **No secrets out.** What a run returns is scanned for secret patterns and
  redacted before it is published.
- **`http.request` is fenced.** Only an adapter plugin's, or a driver's under
  `net:`, only to an origin granted to it (§6), only on a route of the port
  call in flight (a GraphQL request only as a persisted operation, by
  name and document hash), the credential only to an origin marked for
  it, within the destinations the host's configuration leaves (§6); the credential is the
  host's and never enters the engine; each call has the host-call deadline,
  and a run has a request budget, a page limit, and caps on body size and
  time; every request is recorded (origin, method, path, status, size,
  time), never its credential.
- **Names and keys are the host's.** A plugin never resolves a name or
  picks a certificate: it hands the host a request, and the host vets it
  and makes it. With an upstream set, all of it goes through the
  upstream: the host resolves no supplier name and connects only to the
  pinned upstream, whose public key (SPKI) is pinned. With no upstream, it
  goes direct, and how the host resolves is its own; it connects to
  the address it checked, and refuses loopback, private, link-local,
  multicast and cloud metadata addresses, first and on every redirect.
  TLS is verified against a root bundle the host pins, never the system
  trust store, which is what makes a spoofed name harmless.
- **The connection itself.** TLS 1.3, or 1.2 with AEAD suites only; no
  0-RTT early data, so a replayed write cannot repeat. The SNI and the
  certificate are checked against the approved name. Proxy settings from
  the environment are ignored. Every outbound request leaves through an
  egress process of the host, run as a user of its own, where the request
  gate runs; a host may keep one for the server side and one for views. A
  process that runs plugin code, or only relays a view's requests, never
  connects out itself.
- **The upstream.** The host and its upstream authenticate each other by
  mutual TLS alone: a client certificate per host, bound to its key, and
  the upstream trusted by its pinned key set and its name, with no public
  CA chain needed. No key in a header stands in for it.
  - **A call that acts as a person** goes through the upstream with the
    person's own short-lived credential, which the host attaches; the
    upstream forwards it untouched and never puts its own in its place.
    A sign-in's code exchange is a route of the upstream, which holds the
    client secret.
  - **The upstream is no open proxy.** It enforces, itself, the vetted
    entry's origins for each credential class, and refuses anything
    else.
- **Bodies are capped as read.** An answer's size cap counts the bytes
  after decompression, and only `gzip` or `identity` encodings are
  accepted.

**In the browser (the view):**

- **The frame is a sandbox.** The host's element frames the view in an
  `<iframe sandbox="allow-scripts">` without `allow-same-origin`: an opaque
  origin with no cookies, no storage and no session; no popups, forms, top
  navigation, downloads or modals; a CSP of `default-src 'none'` with
  scripts and styles by hash and `connect-src 'none'`, always. Its one
  channel is
  `postMessage` with the host element, which sends the granted data and
  checks every press and result against the plugin's grants before acting.
  Every message is typed and versioned and checked against the host's
  schema in its `api/`; one that fails is dropped. A press names one of
  the manifest's `actions`, carries a single-use nonce the host issued
  (with its last message to that load; a view never makes one) and
  arguments under that action's schema, and its answer goes only to the frame load that
  pressed, never into the output other viewers see.
  - **A frame is known by its port, never its origin** (a sandboxed frame's
    origin is `null`). The host element transfers a fresh `MessageChannel`
    port on each load and listens only on it; a new load revokes the old
    port and its nonces, and the view's kit takes messages only on its
    port. So no frame can speak for another.
  - **Caps** on a message's bytes and on messages per load, and one press
    in flight per load.
  - **A press that acts as the person** (it files under the person's name
    or uses the person's credential) needs a confirm drawn in the host
    element's own page, outside the frame, naming the action's manifest
    label. A nonce proves a message is fresh, not that a person clicked.
- **A view's network is only through the host, over its port.** The
  frame never connects anywhere. With `net:`, the kit carries the view's
  requests over the load's port to the host element, which is the host's
  own code in the host's page; it hands them to the request gate, which
  makes them. There is no proxy address in the frame's policy, no load
  token and no CORS answer. The kit maps a URL to an origin id (a
  relative one to `parent`) and an unmapped URL is refused. No `Cookie`
  or `Authorization` comes from the view, and no `Set-Cookie` goes back.
  A host specifies a view's network in its own spec once its browser
  checks (H8 to H10) are done; until then it gives no view `net:`.
  A view gets no credential, with one kind of exception, for our own
  signed plugins only: an origin the vetted entry marks for a view
  credential gets a read-only credential
  narrowed to the one target, for free-form reads only (one read
  operation per request, a depth and a cost cap, a budget per load);
  writes from a view go only through persisted `actions` with the
  person's confirm.
- **Devices take two keys.** Every device and powerful feature is denied by
  `Permissions-Policy`, unless the manifest asks `device:<feature>` and an
  admin grants it; then the host element delegates exactly that feature,
  the browser asks the person, and the element shows a lasting sign naming
  the plugin while the device is in use.
- **WebAssembly in the browser is boxed third-party code.** A view module is
  pure compute: its imports are memory and a short list of glue helpers; an
  import that binds a web API is refused at vetting. It runs only in a
  dedicated worker that the frame starts from a `blob:` URL (an
  opaque-origin frame can start no other), so the worker runs under the
  frame's own policy. Classic or module is the host's choice, by what
  the browsers start in a sandboxed frame (a `blob:` module worker fails
  there in at least one engine today). Either way it runs under that
  policy, `connect-src 'none'` included, with
  `'wasm-unsafe-eval'` only for a view that declares modules: no DOM, no
  network, the module's bytes and its results in and out through
  `postMessage`. A vendored codec is
  verified by its upstream hash and meets the same rules.
- **A result reaches the host only through the host element**, under a
  grant, checked for type and size. A plugin never uploads anything itself.

## Open for the owner

- **Plugin events carried by the host.** A manifest field declaring a
  plugin's events and schemas, the host checking and carrying them,
  `hook:after:<event>` on another plugin's event, pages and limits. The
  subjects are reserved now (§10); the mechanism is a later minor.
- Whether `kind` is one shared list in this standard or each host's own,
  so whether one plugin can serve two hosts with one manifest name.
  `adapter` is the standard's (§2a); the other kinds are still open.
- Whether "signed in, always" (guarantee 7) stays a guarantee of the
  standard. It is drafted as one, the session's recommendation.
- **The WASI version.** The engine imports WASI 0.2 interfaces (random,
  clocks, poll), while wasi.dev lists WASI 0.3 as current and 0.2 as
  superseded (checked 2026-11-25). The standard names no WASI version; the
  host's spec says which it imports, and moving it is the host's change.
- Whether a second plugin host meets this standard in v3 or in a later
  version.
