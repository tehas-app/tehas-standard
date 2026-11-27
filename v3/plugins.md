# Plugin standard v3

Part of tehas-standard v3. The rules every plugin and every plugin host
meet. A manifest that follows this standard says `"plugin": 2`; a host
refuses a manifest number it does not know. tehas's own plugin
specification (2.0.0, "the operator") is the first host's implementation
of it; what is only that host's is in §12.

*Informative:* plugins are additional capability for the core, mostly UI
and integration glue, not an application platform.

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
| a cycle plugin | A plugin of `kind: "cycle"`: code the host loads into the agent of a cycle, so the agent gains a feature, under §2b |
| an ordinary plugin | Any plugin that is not an adapter plugin or a cycle plugin |

## 2. The guarantees

A host gives every ordinary plugin, and every person on the host, these.
An adapter plugin keeps them except where §2a says otherwise, a cycle
plugin except where §2b says otherwise.

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
   A plugin writes only its own `/out`, and `/state` with `keep` (§6). An
   adapter plugin carries out the core's writes, and only those (§2a).
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

*Checked:* a host's tests show each guarantee on a running host: plugins
off fetch nothing, an unapproved commit does not run, a malformed setting
stops the load, a refused plugin is skipped, an ungranted call is refused,
a gate with no answer holds. Its spec names the test of each.

*Patterns* ([patterns.md](patterns.md) §3, §4, §7, §8): fail closed, timeouts and bulkheads, microkernel,
capabilities and least authority, vet the artifact you run.

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

*Checked:* the host refuses `kind: "adapter"` from a plugin that is not
blessed; its request gate refuses a request outside the routes of the port
call in flight, and its tests show both. The component's imports are listed
from the binary at vetting.

*Patterns* ([patterns.md](patterns.md) §2, §8): ports and adapters, anti-corruption layer, capabilities
and least authority.

## 2b. Cycle plugins

A cycle plugin adds a feature to the agent that works a cycle: a check on
each file the agent writes, say, or a feature the agent's own release does
not have yet. The host loads it into that agent, inside the cycle, and
nowhere else.

- **Blessed only.** A cycle plugin exists only in a blessed plugin (§11).
  Code inside the agent's process cannot be fenced by grants, so it is
  trusted like the host's own. A host refuses any other plugin of
  `kind: "cycle"`.
- **Inside the cycle, by the admin's choice.** Guarantee 5 binds ordinary
  plugins: a cycle plugin runs inside a cycle. A cycle is given a cycle
  plugin only when an admin turned it on for that host, or when the host
  runs a release's default entry for it (below); never because some other
  plugin is on.
- **Under the plugins switch.** Guarantee 1 holds: with plugins off, no
  cycle plugin is fetched or loaded, and a cycle runs as it would without
  them.
- **Contained by the cycle.** Guarantee 11 holds: the host's own processes
  never load it. It runs in the cycle's sandbox, as the cycle's user, under
  the cycle's limits, network rules and credential, and gets nothing the
  cycle does not already have. Its failure is that cycle's.
- **No host API, no grants.** It does not run in the operator and imports
  nothing of the host's worlds (§6). It asks only `cycle:<role>`, once for
  each role of the agent it is loaded into (§5); the roles are the host's,
  listed in its spec. It has no view, schedule, hook, tool, gate or model
  budget of its own.
- **Writes only as the cycle does.** Guarantee 8 binds ordinary plugins:
  a cycle plugin acts through the agent, so what it changes is the cycle's
  work, under every rule the cycle's work is under, the cycle's review and
  gate included.
- **Approval stays a person's** (guarantee 9) holds: a cycle plugin never
  approves or merges, and gives the agent no way to.
- **Never in a role that reviews.** A host never loads a cycle plugin into
  a role that reviews or judges the cycle's work, whatever its manifest
  asks: a plugin inside the agent can bend the agent's output, and the
  review is what checks that output. A host's spec names which of its
  roles review, and refuses `cycle:<role>` for them.
- **Named in the cycle's record.** The record of every cycle names each
  cycle plugin it loaded, by repository and commit, and each one it
  skipped, with why.
- **The host's settings win over the product's.** A product's own
  configuration for a cycle plugin cannot turn on, for that plugin, what
  the host has off: installs, project-local binaries and network access
  keep the host's setting for a cycle plugin whatever the product's file
  asks. The host's spec names these switches (§12).
- **Fetched before, never during.** The host puts the pinned `dist/agent/`
  in the cycle's sandbox, read only, before the cycle starts. Nothing of a
  cycle plugin is downloaded while the cycle runs. The tools it calls
  (language servers, linters) come from the host's sandbox, never from the
  plugin's own downloads.
- **Refused or unreachable is skipped, and said.** Guarantee 4 holds: the
  cycle runs without it, and the cycle's record names the plugin and why.
- **A release may ship a default entry.** As for adapter plugins (§2a),
  guarantee 2's "on no host release" binds ordinary plugins: a host release
  may ship a default vetted-list entry for our own cycle plugin, which an
  admin can turn off. Being blessed, it changes only with a release's
  default entry or an admin's pin.
- Pinned and vetted (2), fail closed (3), removable (12) and
  the hardening of §14 that applies to it hold in full.

*Checked:* the host refuses `kind: "cycle"` from a plugin that is not
blessed, and `cycle:<role>` for a role that reviews; its tests show a cycle
with plugins off loads none, a cycle loads only the cycle plugins turned on
for its roles, a cycle with a refused cycle plugin runs without it and
records why, and a product's own config turns on neither installs,
project-local binaries nor network for a cycle plugin the host has off.
Vetting's tests show a package refused on a registry-hash mismatch, on a
provenance that does not verify where one is published, and on an advisory
that flags a pinned package.

*Patterns* ([patterns.md](patterns.md) §7, §8): microkernel, capabilities and least authority,
vet the artifact you run.

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
dist/agent/         a cycle plugin's package, as the agent loads it (§2b)
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

*Checked:* the host's checks of §7 run on `dist/` only; `src/` and `dist/`
in step is the builder's CI job (coding standard R14).

*Patterns* ([patterns.md](patterns.md) §8): vet the artifact you run.

## 4. The manifest

- One JSON file, `tehas-plugin.json`, under a closed schema the host
  publishes in its `api/`: an unknown field is refused. A size cap holds.
- `"plugin": 2`. A host refuses a number it does not know.
- The exact keys are the host's schema's; this list is what every host's
  manifest names.
- It names: the plugin's `name`, `label` and `kind` (`adapter` for an
  adapter plugin, §2a; `cycle` for a cycle plugin, §2b; other kinds are
  the host's); the revision of the
  host's spec it was built against (`spec`), which its tags state; the
  `runtime` (`"starlingmonkey"`, the engine, the only value for an
  ordinary plugin with this version; `"component"` for an adapter plugin
  built as one component, §8; none for a cycle plugin, which names
  instead the `agent` it is loaded into and its entry under `dist/agent/`,
  the values the host's, §12); the `timeout` of a run; what it `asks`;
  its views; the named `actions` a view may press, each with a JSON
  Schema for its arguments; its skill files, under `skills/`; each
  WebAssembly module by name, the driver's apart from the view's, with an
  optional source path and build recipe; each vendor library with its
  version, upstream and per-file hashes; for a plugin that asks `http` or
  `net:`, the `origins` it may reach (§6), each with its `methods`, its
  body policy and whether the credential may go to it;
  the `solid-js` version its compiled view expects; its schedules
  (`every:`, `clock:`); its hook points.
- **Not yet in the manifest:** its licence. Guarantee 13 holds (any
  licence), but no host's schema has the field yet, so a manifest does
  not carry it until one does.
- An endpoint plugin (a model provider) is a manifest only: id, API shape
  (`openai-completions` or `anthropic-messages`) and models. Its address
  comes from the host's or the industry's settings, never from the
  plugin. It has no code, so the rules on `src/`, `dist/`, modules and
  tests (§3, §7, §8 and those items of §13) do not apply to it; the rest
  do.

*Checked:* the host's closed schema in its `api/` refuses a manifest that
does not fit, and an unknown `"plugin"` number.

*Patterns* ([patterns.md](patterns.md) §3): parse, don't validate; schema first; fail closed.

## 5. Capabilities and grants

- A plugin **asks** by name in `asks`; a grant gives a value only on a
  host. Names are `name` or `name:<value>`. A host refuses a name it does
  not know.
- The common names: input grants (`product`, `history`, `files`,
  `cycles`, `issues`, `pages`, `live:<feed>`, `feed:<feed>`,
  `industry:logs`); `keep` (a
  private `/state`); `model:<tokens>` (a token budget per run), with
  `model:images`; `view`, `menu`, `action:<id>`; `every:<interval>` and
  `clock:<when>`; `hook:<when>:<event>`; `tool:<id>`; `record`;
  `issue:draft`; `net:`, a plugin's network on either side, through the
  host only (§6, §14); `viewer:login`, the one piece of a person's data a host
  gives a view: the login of the person who pressed, taken from that
  press's own session, never from the message; a run that holds it can't
  keep it, record it, file issues or call the model; `http`, for an adapter
  plugin only (§2a), refused to any other; `cycle:<role>`, for a cycle
  plugin only (§2b), refused to any other; `device:<feature>`, one
  browser device or powerful feature for a view (§14). A host may add its
  own; it lists them in its spec.
- **Grants an admin gives by hand.** Turning a plugin on never gives a grant
  that holds or acts on a person's path:
  - `hook:before:<event>=<policy>` (a gate; a gate grant with no policy is
    refused);
  - `phase:<id>` (policy `pass` or `hold`);
  - `answer:<kind>` (one plugin per kind; a person's answer always wins);
  - `device:<feature>` (the browser still asks the person, §14);
  - `cycle:<role>` (a release's default entry for our own cycle plugin
    excepted, §2b).

  A review lists them apart, as "needs your grant".
- **Our own plugins:** turning one on gives the grants of its vetted entry,
  less those above. A later commit that asks for more waits for the admin;
  the host keeps running the last commit that fits.
- **Third-party plugins:** the admin gives each grant.

*Checked:* the host refuses a name it does not know; its tests show that
turning a plugin on gives none of the grants an admin gives by hand, and
that a commit asking for more keeps the last commit that fits running.

*Patterns* ([patterns.md](patterns.md) §8): capabilities and least authority.

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
  | `http.request(req)` | `http`: an adapter plugin only (§2a); or `net:`, an ordinary plugin's driver; to its destinations (below) |
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

*Checked:* the host's side and `tehas.d.ts` are generated from the WIT in
its `api/`, and its surface list for the WIT package only grows within a
major (contracts C3, C4). The request gate's tests show a request outside a
plugin's destinations refused, from either side.

*Patterns* ([patterns.md](patterns.md) §3, §5, §8): schema first, parallel change, capabilities and
least authority, sandboxing in WebAssembly.

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
- **Size caps** for `dist/view/`, `dist/view/wasm/`, `dist/vendor/`,
  `dist/wasm/` and `dist/agent/`, set by the host.
- **A cycle plugin's package.** `dist/agent/` is loaded by the agent, not
  the engine, so parse and imports are the agent's. Each third-party
  package in it is named in the manifest's `vendor` and verified, not
  read, by version, upstream and per-file hashes, native binaries
  included; the rest is the plugin's own code and readable. Vetting checks
  each package further, package by package, so a person's approval of a
  version bump covers the version change and these checks cover the
  files: the bytes match the registry's own integrity hash for that exact
  published version (npm: the registry's `sha512` for the tarball); the
  package's signed build provenance is verified where the package
  publishes one; and the lockfile the tree was installed from passes an
  advisory scan for the packages it pins. It has no
  install step: what the agent loads is what was vetted.
- **Tests** in `dist/test/` pass in the engine, against fake host
  functions.

*Checked:* by the host's check of `dist/` (tehas: `tehas plugin check`),
which runs at vetting and before every deploy, and in the builder's CI.

*Patterns* ([patterns.md](patterns.md) §6, §8): vet the artifact you run, test at the interface, with
fakes.

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

*Checked:* a module's imports, exports, features and name section are read
from the binary at every deploy; the rebuild from source runs at vetting.

*Patterns* ([patterns.md](patterns.md) §8): sandboxing in WebAssembly, vet the artifact you run.

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

*Checked:* the host checks each compiled import against the kit's export
list and the manifest's `solid-js` version against its kit; the frame's
policy is written by the host, from hashes.

*Patterns* ([patterns.md](patterns.md) §9): islands architecture, origin isolation.

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

*Checked:* the host's event list is a surface list that only grows; a test
of it shows no event under `plugin-` or `annex-` (contracts §2).

*Patterns* ([patterns.md](patterns.md) §3, §7): event notification and hooks, tolerant reader, pull
first.

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
  only those may hold adapters or cycle plugins. Blessed code is trusted like the host's
  own, the truth of its answers included. It changes only at a host
  release (its default entry) or by an admin's pin, never by a newer
  signed entry on its own, and its repository requires an approving
  review of every change by the reviewing account (below): the signing job
  checks that the merge of the commit it signs had an approving review by
  exactly that account, on the head whose tree it signs, and signs nothing
  without one.
- **The reviewing account.** Each host names one reviewing account: a
  person's own account of the repository owner's, to which no agent ever
  holds a credential, held with a hardware key and never signed in where
  agents run. The host keeps its account name and the code host's
  immutable account id in a gate file of its repository. An approving
  review counts for a blessing, for a release's default-entry file, and
  for the other gate files only when it comes from that account; an
  approval by any other account does not count, whatever its account type,
  because a person's agents may sign in as that person.
- **What a blessing names.** A blessing is the owner's own act, never
  delegated, and it is kept where changing it needs a person's review (a
  gate file of the host's repository). It names:
  - the repository by its code host's stable id, not only its name, so a
    renamed repository keeps its blessing and a new repository that takes
    an old name gets none;
  - the kind it may be (`adapter`, `cycle`), and the most it may ask. A
    blessed commit whose manifest asks beyond that, or names another kind,
    is refused, not held for an admin.
- **The default-entry file is a gate file.** A release ships its default
  entries for blessed plugins in a file of the host's repository. A
  default entry lets a blessed commit run on every host of that release,
  so it blesses a commit as the blessing itself does, and the file needs
  the same review as the blessing: a gate file, with the reviewing
  account's code-owner approval.
- **Only commits of the protected branch.** A blessed commit is reachable
  from the repository's protected default branch and is in the signed list
  as blessed. A host refuses a pin to any other commit of a blessed
  repository, one reached through a fork or a branch included, rather than
  trusting it.
- **The reviewed tree is the merged tree.** The signing job compares the
  tree of the commit it signs with the tree of the head the person
  approved, and signs nothing when they differ: a squash, a rebase or a
  batch merge that brought in anything unreviewed. A commit pushed to the
  branch without a reviewed pull request is never signed as blessed. A
  batch merge is signed only when every pull request in it was approved on
  its final head.
- **An expired list skips blessed entries too.** A host that holds an
  expired or unsigned list keeps no blessed entry running on its own: an
  adapter plugin's port fails as §2a says, a cycle plugin is skipped and
  the cycle records it.
- **The audit and the signing are apart.** The audit jobs that run
  plugin code have no signing identity, no secrets and no network. The
  one job that signs runs no plugin code.
- **The host protects its own default branch.** All of the above rests on
  the host's own repository, so its protection is rules, not habit: the
  default branch has an active branch ruleset that requires a pull request
  before any merge, blocks deletion and force-push, and names no bypass
  actor; the gate files (the blessing, the default-entry file, the signing
  identities, the reviewing account, the audit pipeline, the release
  workflow and the checker of these very rules) need the reviewing
  account's code-owner approval; and a check of these settings runs in the
  host's CI, on every pull request and on a schedule, and fails closed:
  protection found off, a bypass actor found, or a gate file without its
  code owner fails the build rather than passes unnoticed.
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

*Checked:* the audit pipeline's record for each entry, its SLSA provenance,
and the host's refusal of a lower serial, an expired list or an unsigned
one, shown by its tests. Its tests also show a blessed repository's commit
refused when it is not on the protected branch, when its manifest asks
beyond its blessing, and when the repository is not the blessed id; the
signing job's tests show a tree mismatch and an unreviewed push left
unsigned, and an approval by an account other than the reviewing account
left unsigned. The settings check's own tests show it failing on a disabled
ruleset, on a bypass actor, and on a gate file whose code-owner rule is
off.

*Patterns* ([patterns.md](patterns.md) §8): vet the artifact you run, defence in depth.

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
- the agents it loads cycle plugins into, their roles for `cycle:<role>`,
  how it puts `dist/agent/` in a cycle's sandbox, and the settings whose
  host value wins over a product's for a cycle plugin (§2b);
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
- [ ] Our own: `tehas.toml` at the root, at `"v3"` or later,
      architecture test green. A third-party plugin SHOULD keep the same
      file.
- [ ] An adapter plugin: on the vetted list, `kind: "adapter"`, asks
      `http` and nothing a view, schedule, hook, tool or gate needs; built
      as JavaScript or as one component whose imports are exactly the
      adapter world.
- [ ] A cycle plugin: on the vetted list, blessed for `kind: "cycle"`,
      asks only `cycle:<role>` and never for a role that reviews;
      `dist/agent/` holds the whole package, every third-party package in
      it verified, and downloads nothing when it runs.

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
- **A cycle plugin is confined as the cycle is.** It runs in the cycle's
  sandbox and never in a process of the host's; the host's confinement of
  a cycle (its user, its network rules, its credential) is its boundary.
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
  A host gives a view `net:` only once its own spec says how a view's
  network runs and how it was checked in the browsers it supports; until
  then it gives no view `net:`.
  A view gets no credential, with one kind of exception, for our own
  signed plugins only: an origin the vetted entry marks for a view
  credential gets a read-only credential
  narrowed to the one target, for reads only. Unlike an adapter's
  persisted operations (§2a), a view's GraphQL read may be a query the
  view writes: one query operation per request, never a mutation, under a
  depth and a cost cap the host sets, and a budget per load;
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

*Checked:* each item is a host test, on the operator and in the browsers
the host supports; the host's spec lists how it confines each process and
which test shows each item.

*Patterns* ([patterns.md](patterns.md) §4, §8, §9): defence in depth, sandboxing in WebAssembly,
timeouts and bulkheads, origin isolation.

## Open for the owner

- **Plugin events carried by the host.** A manifest field declaring a
  plugin's events and schemas, the host checking and carrying them,
  `hook:after:<event>` on another plugin's event, pages and limits. The
  subjects are reserved now (§10); the mechanism is a later minor.
- Whether `kind` is one shared list in this standard or each host's own,
  so whether one plugin can serve two hosts with one manifest name.
  `adapter` (§2a) and `cycle` (§2b) are the standard's; the other kinds
  are still open.
- Whether "signed in, always" (guarantee 7) stays a guarantee of the
  standard. It is drafted as one.
- **The WASI version.** The engine imports WASI 0.2 interfaces (random,
  clocks, poll), while wasi.dev lists WASI 0.3 as current and 0.2 as
  superseded (checked 2026-11-25). The standard names WASI only for a
  module's imports (§8: preview 1 for a driver's core module; random and
  the clocks for an adapter component). Which version the engine imports
  is the host's spec, and moving it is the host's change.
- Whether a second plugin host meets this standard in v3 or in a later
  version.
- **Advisory grants.** `issue:advisory`, an admin's grant to file one
  issue per package and advisory with public facts only (package, advisory
  id and link, installed and fixed versions; a daily cap), and the input
  grant `feed:advisories` it reads. Not in v3; a later minor adds them
  once the owner decides.
