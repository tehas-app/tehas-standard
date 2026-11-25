# Coding standard v3

Part of tehas-standard v3. A repository follows it when its
`tehas.toml` says `[standard] version = "v3"` (see [v3/repository.md](repository.md)).

v3 is v2 plus four rules for code that runs in a browser or in a plugin
(R11 to R14), with the plugin rules written for the plugin standard of
this version ([v3/plugins.md](plugins.md), manifest `"plugin": 2`). It names:

| With coding standard v3 | Valid version |
| --- | --- |
| Architecture standard | [v3/architecture.md](architecture.md) |
| External contracts | [v3/contracts.md](contracts.md) |
| Plugin standard | [v3/plugins.md](plugins.md), manifest `"plugin": 2` |
| Repository conventions | [v3/repository.md](repository.md) |
| Architecture patterns | [v3/patterns.md](patterns.md): the published patterns the rules rest on |
| The architecture script | [v3/architecture-script.md](architecture-script.md) |

So a reader who finds `v3` in a repository knows every rule its code
follows from the directory `v3/` alone.

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
- The other parts of this tag: [v3/architecture.md](architecture.md), [v3/contracts.md](contracts.md), [v3/plugins.md](plugins.md), [v3/repository.md](repository.md), [v3/patterns.md](patterns.md).
- The host's front-end standard for the kit (tehas `host/docs/frontend.md`) at the host release a repository pins.

## 1. Aim and scope

**Aim.** A resilient architecture, not a code style:

- a supplier changes, one module changes;
- a supplier fails, the program carries on and reports it once;
- a crash loses nothing;
- a contract changes without a flag day.

**Scope.** Every repository of the tehas system that holds a program,
plugins included. Skills, prose and settings repositories are out of
scope.

**Not in scope.** Naming, formatting, function length, comment style and
the rest of a repository's style stay as its `AGENTS.md` says. The
standard sets where knowledge lives and how the parts meet, not how a line
reads.

## 2. Terms

| Term | Meaning |
| --- | --- |
| a piece of knowledge | One design decision that could change on its own: a supplier's request and answer shapes, a file format, a directory layout, the words of a set of states, a route table, a wire format, a rule of the business |
| its owner | The one module that knows a piece of knowledge. Everyone else asks it |
| a module | A unit with an interface: a crate, a Rust module, a JavaScript or WebAssembly module. Never a plugin |
| deep, shallow | Deep: the interface is small against what it hides. Shallow: the interface is nearly as large as the body |
| a seam | Where two modules or two programs meet |
| a port | An interface named in our terms for what a program needs from outside |
| an adapter | The one implementation of a port for one outside system. It alone knows that system's shapes. It may be delivered as an adapter plugin, `kind: "adapter"` ([v3/plugins.md](plugins.md) §2a) |
| a fake | An implementation of a port for tests, written against the port, never against the outside system's wire |
| the core | The pure decisions: no network, clock or files |
| the shell | The code that reads, calls the core, and writes |
| a contract | What a release promises outside the repository: a CLI, a file format, an HTTP route, a schema, a public item |
| a page | Code a program serves to a browser from its own origin |
| a plugin | An addition to a host, written by anyone, pinned by commit, run with the grants a person or the vetted list gave it ([v3/plugins.md](plugins.md)) |
| `src/`, `dist/` | In a plugin: the source people read, and the deployable code the host vets and runs |

MUST marks a rule a conformant repository meets. SHOULD marks the default,
departed from with a reason written in the repository's
`docs/architecture.md`.

## 3. The rules of v2, kept

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

## 4. The rules v3 adds

R11 to R14 bind the code a repository ships to a browser or runs as a
plugin. A repository with neither (a Rust service with no pages) is at
`v3` as soon as it meets R1 to R10 and the v3 repository conventions.

**Where the checks look.** A page is checked where it is served from,
since a page's files load as they are written. A plugin is checked in
`src/`, since `dist/` is what the builder's tools made from it; `dist/`
is the host's to vet, under [v3/plugins.md](plugins.md) §7.

### R11. The host's kit, nothing else

MUST. A page or a plugin view that does more than show static HTML is
built on the tehas kit:

- islands from the kit's `island()`; each kind as `<name>.js`, a pure
  `<name>.model.js` and the only drawing file `<name>.render.js`;
- drawing with the kit's Solid 2, data through `feed.js` or `stream.js`,
  changes through `press.js`, shared state through `state.js`;
- styles on `kit.css` and the `tehas-` custom properties.

A plugin view loads the kit from the host, never a copy. A plugin view
may be written as Solid JSX in `src/`; its compiled output imports only
the names the kit exports (`solid-js`, `@solidjs/web`), mapped to the
kit by the host.

Third-party code is allowed only as a **verified vendor library**: a
published release, kept unchanged in `dist/vendor/<lib>/` (a plugin) or
`vendor/<lib>/` (a page), named in the manifest or the repository's
vendor list with its version, upstream source and a sha256 for each file.
A changed file counts as the repository's own code. No other UI or
general-purpose runtime library: not React, not a second Solid, not
Effect, not lodash or RxJS. A page or view that needs something the kit
lacks asks the host for it (a plugin surface request).

*Checked* (`architecture.toml`, each `max` 0 unless a `why` says
otherwise):

- `kit-solid-import`: an import of `solid-js`, `@solidjs/web` or any
  `solid*.js` outside render files (pages) or outside `src/` view files
  (plugins);
- `kit-copy`: a file named `solid*.js` or a kit file outside the kit's
  own home;
- `kit-own-fetch`: `fetch(` in island and render files (data goes through
  the kit);
- `kit-raw-html`: `innerHTML`, `outerHTML`, `insertAdjacentHTML` or
  `document.write` outside the kit (a ratchet where it is above 0, with a
  `why`);
- `vendor-unlisted`: a file under a vendor folder that the vendor list
  does not name with its hash.

*Patterns* ([patterns.md](patterns.md) §9): islands architecture; origin isolation.

### R12. Typed sources

MUST. Every module a person writes is type-checked by the one pinned
checker for its language, in strict mode, in a CI job named `types`.

| Language | Where | Checker | Escape hatch counted |
| --- | --- | --- | --- |
| JavaScript and TypeScript | pages: `.js`/`.mjs` with JSDoc, no compile step; plugins: `.ts`, `.tsx`, `.js`, `.jsx` in `src/` | TypeScript's native `tsc` 7.x (`[platform] typescript = "7.x"`), pinned exactly by the repository, `--strict` (`--checkJs` for `.js`), against the host's generated types (`tehas.d.ts`) and the kit's (`solid.d.ts`, and `kit.d.ts` once the kit ships it); a plugin that types `.tsx` adds `@solidjs/web` at the kit's version as a type-only dev dependency | `@ts-ignore`, `@ts-nocheck`, `any`, `{*}` |
| Rust | programs; the source of a plugin's WebAssembly module in `src/`, or of an adapter plugin built as one component | `cargo clippy -- -D warnings`, on Rust 1.x (`[platform] rust = "1.x"`) | `#[allow(` |
| Python | tools and scripts (not a tehas plugin language) | `mypy --strict` on Python 3.11 or later | `# type: ignore`, `Any` |
| Shell | scripts that hold no logic a test needs | `shellcheck` | `# shellcheck disable` |

Another language enters the table by a minor version of this standard,
before its first use. The source of a plugin's WebAssembly module may be
in any language its toolchain supports; a language outside the table is
allowed for a third-party plugin and refused for our own.

**Strict, and when.** New code is strict from its first commit. A
repository with code already is checked at once, and its strict error
count is a ratchet (`ts-strict`, and its twins for other languages) that
only falls. It writes `v3` when the count is 0.

*Checked:* the `types` job; `ts-strict`; `ts-escape` (and `rs-escape`,
`py-escape`, `sh-escape` where the language is there), max 0 in new code
and a ratchet in old.

*Patterns* ([patterns.md](patterns.md) §3, §5): make illegal states unrepresentable; ratchet.

### R13. Pure models, tested

MUST. R3 holds for JavaScript too.

- An island's `<name>.model.js` is `(data, props, nowMs) -> model`. It
  reads no DOM, Solid, network, clock or storage.
- A plugin's driver keeps its decisions in pure modules and its effects
  at the edge: the calls to the host API (`tehas.fs`, `tehas.git`,
  `tehas.model`, `tehas.wasm`, and `tehas.http` for an adapter plugin),
  made in one shell module that `run(ctx)` drives.
- Each model and each pure driver module has tests. A plugin's tests are
  built into `dist/test/` and run in the host's engine with fake host
  functions (`tehas plugin test`); a page's run with `node --test`.

*Checked:* `model-pure`, max 0: `document`, `window`, `fetch`,
`Date.now`, `new Date()`, `localStorage`, `solid` or a `tehas.` call in
`*.model.js` and in the files `architecture.toml` names as a plugin's
core; CI runs the tests.

*Patterns* ([patterns.md](patterns.md) §2): functional core, imperative shell.

### R14. A plugin uses the host's surfaces

MUST, for plugins. Where the host offers a feature, a plugin uses it and
does not make its own:

- the model only through `tehas.model.chat`, never a provider's client,
  address or key;
- files, state and code only through the host API (`fs.*`, `git.*`);
  there is no other I/O inside the engine, except an adapter plugin's
  `http.request` to its listed origins, the credential held by the host;
- heavy pure compute in a WebAssembly module of its own (`wasm.load`),
  never a second engine; a hot path two plugins share is asked of the
  host as a host function;
- the view on the kit (R11), its buttons as the kit's presses to the
  host's actions;
- events by their names in the plugin standard (§10 there), as
  `hook:<when>:<event>`; a gate's answer as the object the run returns, in
  the host's gate-answer schema, never a file;
- its manifest, `ctx` and outputs checked against the host's `api/`
  schemas in its own tests, and the host's `dist/` checks (`tehas plugin
  check`) run in its own CI before a commit is pinned.

*Checked:* `plugin-provider`, max 0: a model provider's host name or key
variable in `src/`; a `plugin` CI job that builds `dist/`, runs the host's
checks on it and fails on a difference between the committed `dist/` and
a fresh build.

That last check is the builder's, not the host's: the host never builds
or compares `src/` with `dist/`, so the plugin's own CI keeps them in step
([v3/plugins.md](plugins.md) §3).

*Patterns* ([patterns.md](patterns.md) §7, §8): microkernel; capabilities and least authority.

## 5. Where v3 is enforced

| Place | What it holds |
| --- | --- |
| The repository's architecture test | R1 to R14's mechanical checks, from `architecture.toml`, by the canonical `scripts/architecture.py` |
| The repository's CI | the `architecture`, `types` and, for plugins, `plugin` jobs |
| The host, at vetting | the plugin standard's `dist/` rules (§7 there): it refuses unsafe code, never code for its style |
| The vetted list | a plugin of ours is listed `vetted` only at `v3` with its architecture test green at the vetted commit |
| The starter | `tehas plugin new`, which scaffolds and checks `src/` and `dist/`, from a template repository at `v3`: `tehas.toml`, `architecture.toml`, the script at this tag's hash, one view island on the kit, a pure model with a test, the `types` and `plugin` jobs, `src/` and a built `dist/` |
| Review | the review questions of [v3/repository.md](repository.md) §5, R11 to R14 included |

## 6. Isolation is the frame, not the component

A plugin's view is isolated by the browser: it is served from an origin of
its own, framed by the host's page, under a policy the host writes. R11's
islands are custom elements for structure, not isolation: a shadow root is
no security boundary. Plugin code never runs in the host's own page. A
plugin that wants to change how the host's page looks asks for a surface;
it does not ship a component into that page.

## 7. Changes from v2

| v2 | v3 |
| --- | --- |
| No rule for front ends | R11: the host's kit and verified vendor libraries |
| No type rule | R12: one pinned strict checker per language, with a ratchet |
| R3 for Rust only, in practice | R13: R3 for JavaScript models and plugin drivers |
| No plugin rule | R14 and the plugin standard (`"plugin": 2`) |
| `.tehas/coding-standard`: `v1` or `v2`, one line | `tehas.toml`, `[standard] version`: adds `"v3"` and minors as `"v3.1"`; one owner per table ([v3/repository.md](repository.md) §1) |
