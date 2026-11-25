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
| a third-party plugin | Any other plugin |
| an adapter | Not a plugin kind: the one implementation of a port for one outside system (coding standard R2). An adapter may be delivered as a plugin, and then it meets this standard too |

## 2. The guarantees

A host gives every plugin, and every person on the host, these:

1. **Off unless asked.** With plugins off, nothing is fetched, vetted or
   run, and nothing of plugins shows.
2. **Pinned and vetted.** A plugin is a git URL and a full commit. The host
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
   sign-in. A view loads nothing from another site. (How a host signs a
   person in is its own.)
8. **Writes only through the host.** A plugin never writes to the product,
   the code host or the host's store; the host writes what a run returns.
   The one exception planned is `issue:advisory` (§5), an admin's
   grant, queued for the host spec's revision 5 and waiting for the
   owner's OK.
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
- It names: the plugin's `name`, `label`, `kind` and `license`; the
  `runtime` (reserved; `"starlingmonkey"` is the only value with this
  version); the `timeout` of a run; what it `asks`; its view; each
  WebAssembly module by name, with an optional source path and build
  recipe; each vendor library with its version, upstream and per-file
  hashes; the `solid-js` version its compiled view expects; its schedules
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
  `industry:logs`; `feed:advisories` is queued for revision 5); `keep` (a
  private `/state`); `model:<tokens>` (a token budget per run), with
  `model:images`; `view`, `menu`, `action:<id>`; `every:<interval>` and
  `clock:<when>`; `hook:<when>:<event>`; `tool:<id>`; `record`;
  `issue:draft`. A host may add its own; it lists them in its spec.
- **Grants an admin gives by hand.** Turning a plugin on never gives a grant
  that holds or acts on a person's path:
  - `hook:before:<event>=<policy>` (a gate; a gate grant with no policy is
    refused);
  - `phase:<id>` (policy `pass` or `hold`);
  - `answer:<kind>` (one plugin per kind; a person's answer always wins);
  - `issue:advisory`, queued for revision 5 and waiting for the owner's OK
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
  host's `api/`. The host's side and `tehas.d.ts` are generated from it, so
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
  | `log(...)` | always |

  The engine's own web APIs (`crypto.subtle.digest`,
  `crypto.getRandomValues`, `TextEncoder`, `URL`) need no grant. There is
  no network, socket, environment or host file access.
- **Paths** keep the mount names (`/work`, `/out`, `/state`, `/product`,
  ...). No links, no `..`; a path outside a granted root is refused.
- **`run(ctx)`** is the entry; `ctx` carries the run's context, under the
  host's `plugin-context` schema.
- **A gate's answer is a shape, not a file:** the run returns an object of
  the host's `gate-answer` schema (`{"api": 1, "answer": "allow" |
  "refuse", "why"}`). A return that doesn't fit is no answer, so the gate
  holds.
- **Language.** ES2023 modules. Async through promises; no timers beyond
  `await`. A plugin that needs to wait asks for `every:` or `clock:`
  (`clock:mon-fri@06:00`).
- New host functions come through a plugin surface request and are added
  only (contracts C4).

## 7. What `dist/` must be

A host checks `dist/` before it runs or serves anything, and refuses a
plugin that fails:

- **Parse.** JS is ES modules the engine parses.
- **Imports.** A driver imports only its own `dist/` files and the host
  API. A view imports only its own `dist/view/` files, the host's kit and
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
  refused. Core modules only; the component model comes later.
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
- **Inside its origin,** a view's entry defines exactly one custom element,
  drawn with Solid 2 from the host's kit, in the light DOM.
- **JSX** is allowed in `src/`; the builder compiles it with Solid 2's
  compiler, DOM mode, ESM. Compiled output imports only names the kit
  exports; the host maps them to the kit's Solid and checks every such
  import against the kit's export list. Hydratable output is refused.
- **The Solid version.** The manifest names the `solid-js` version its
  compiled output expects; the host refuses one its kit does not carry.
  A builder who types `.tsx` adds `@solidjs/web` at the kit's version as a
  type-only dev dependency.
- **Heavy view work** runs in a WebAssembly module in a module worker,
  declared in the manifest, under §8's audit. The view's policy allows
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
  `vetted` only at `.tehas/coding-standard` `v3` or later, with its
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
- [ ] Its views are one custom element on the kit; its vendor libraries
      are verified.
- [ ] Its WebAssembly modules keep their name sections (a vendored one: its
      upstream hash) and, for our own, rebuild to the same bytes.
- [ ] Its tests run in the engine with fake host functions.
- [ ] It reaches models only through `model.chat`.
- [ ] Our own: `.tehas/coding-standard` at `v3`, architecture test green.

## Open for the owner

- Whether `kind` is one shared list in this standard or each host's own,
  so whether one plugin can serve two hosts with one manifest name.
- Whether "signed in, always" (guarantee 7) stays a guarantee of the
  standard. It is drafted as one, the session's recommendation.
- **The WASI version.** The engine imports WASI 0.2 interfaces (random,
  clocks, poll), while wasi.dev lists WASI 0.3 as current and 0.2 as
  superseded (checked 2026-11-25). The standard names no WASI version; the
  host's spec says which it imports, and moving it is the host's change.
- Whether a second plugin host meets this standard in v3 or in a later
  version.
