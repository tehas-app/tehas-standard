# Architecture patterns v2

Part of tehas-standard v2. The named, published patterns the rules of this
version rest on: what each pattern means in the tehas system, where it
comes from, and which rules apply it. A reader who knows a pattern by its
name finds here how this standard uses it; a reader who does not finds
where to read it.

## Conformance language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in BCP 14
[RFC 2119] [RFC 8174] when, and only when, they appear in all capitals, as
shown here.

This file adds no requirement of its own. Each pattern is required as far
as the rules that name it require it: a pattern behind a MUST rule is
required, one behind a SHOULD rule is the default. The sources are given
for the reader; the wording here is ours, not quoted.

## Normative references

- BCP 14: [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), the key words.
- The rules that apply the patterns: [coding.md](coding.md) (R1 to R10), [architecture.md](architecture.md) (A1 to A6), [contracts.md](contracts.md) (C1 to C9).

## 1. Modules and knowledge

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Information hiding** | David Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules" (1972) | Each design decision that may change (a supplier's shapes, a file layout, a set of state words) is hidden in one module, its owner | R1, A1 |
| **Deep modules** | John Ousterhout, *A Philosophy of Software Design* | A module's interface is small against what it hides. Shallow modules and pass-through methods are folded into their neighbours | R5 |
| **Decomposition by knowledge, not by time order** | Ousterhout, as above | Modules are grouped by what they know, never by kind of code ("all the helpers") or by the order steps run | R5 |
| **Information leakage** | Ousterhout, as above | The same knowledge in two modules is the defect R1 counts and the architecture test holds at a ratchet | R1 |
| **Somewhat general-purpose interfaces** | Ousterhout, as above, held back by **speculative generality** (Martin Fowler and Kent Beck, *Refactoring*) | A port is general enough for two suppliers and no further | R2 |
| **Design it twice** | Ousterhout, as above | A port's first design is drafted twice and read by fresh reviewers before one is chosen | review |

## 2. Boundaries and dependencies

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Ports and adapters** (hexagonal architecture) | Alistair Cockburn (2005) | A program names what it needs from outside as a port in its own terms; one adapter per outside system answers it | R2, R6, R7 |
| **The dependency rule** | the rule of ports and adapters | The core depends on nothing of the shell or the adapters; adapters depend on the port types | R8 |
| **Anti-corruption layer** | Eric Evans, *Domain-Driven Design* (2003) | An adapter translates a supplier's model into ours, so a supplier's words never reach the core | R2, A3 |
| **Ubiquitous language** | Evans, as above | Ports, events and contracts use the system's own words (`ticket`, `change`, `cycle`), not a supplier's (`issue`, `pull_request`) | A3, R2 |
| **Functional core, imperative shell** | Gary Bernhardt, "Boundaries" (2012) | Decisions are pure functions with their own tests; the shell reads, asks the core, then writes | R3 |
| **Write-ahead journal** | common practice in databases and stores | Where a crash must lose nothing, the shell writes what it will do before doing it, so a restart picks up | R3 |

## 3. Data at the edges

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Parse, don't validate** | Alexis King (2019) | Outside data is parsed into our types where it enters; past the adapter nothing untyped travels | R4 |
| **Make illegal states unrepresentable** | Yaron Minsky | Types are shaped so a wrong state can't be built, where the language allows | R4 |
| **Fail closed** | security practice | Malformed input, settings or answers are refused, never guessed at; no answer from a gate is no | R4, C7 |
| **Tolerant reader** | Martin Fowler (2011), after Postel's robustness principle | A reader ignores a field it does not know and treats an unknown value as unknown. Writers stay strict | C5 |
| **Schema first** | JSON Schema, OpenAPI, AsyncAPI, WIT practice | The contract is a schema in its owner's `api/`; code and types are checked or generated against it | C2, A2 |

## 4. Failure

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Define errors out of existence** | Ousterhout, as above | An adapter answers a supplier's edge cases as normal results (a label already gone counts as removed) | R6 |
| **Pull complexity downward** | Ousterhout, as above | The adapter keeps time limits, retries and budgets so its callers don't | R6 |
| **Timeouts, bulkheads, circuit breakers** | Michael Nygard, *Release It!* | Every outside call has a time limit; one failing supplier can't starve the rest; repeated failures pause the caller | R6 |
| **Named failure outcomes** | the ports' design | A failure an adapter can't absorb reaches its caller as one of a few named outcomes (`Unreachable`, `SignIn`, `Refused`), reported once | R6 |

## 5. Change over time

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Parallel change** (expand, then contract) | Danilo Sato, on martinfowler.com (2014) | A new term goes in beside the old, readers move, the old term goes in the next major | R9, A4, C4 |
| **Branch by abstraction** | Paul Hammant (2007) | Inside a repository, a new module goes in beside the old behind one interface, and the old is removed once nothing calls it | R9 |
| **Strangler fig** | Martin Fowler (2004) | Features move out of the factory and the industry one at a time, each move removing its old code from the core in the same release | A small cores |
| **Preparatory refactoring** | Kent Beck, in Fowler's *Refactoring*: "make the change easy, then make the easy change" | A move earns its place by making a named change easier, lands as an ordinary pull request and keeps behaviour | R10 |
| **Ratchet** | common CI practice | Each architecture check holds today's count and may only fall; a raised count needs a written reason | coding standard §5 |

## 6. Tests

| Pattern | Source | Here | Rules |
| --- | --- | --- | --- |
| **Test at the interface, with fakes** | common practice; Fowler, *Refactoring* (tests before moves) | Modules are tested through their public interface and fakes of their ports | R7 |
| **Contract tests from recorded samples** | consumer-driven contracts, Ian Robinson (2006) | Only an adapter's own tests pin a supplier's call shapes, against recorded real answers; schemas are tested against the code that writes them | R7, C2 |
| **End-to-end fit check** | common release practice | The released versions of the parts run together before a tag, and the versions that fit are recorded | A5, C9 |

## Changes

The first version of this file.
