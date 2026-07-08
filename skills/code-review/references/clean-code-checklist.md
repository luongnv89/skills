# Clean Code Checklist

Audit catalog distilled from the **bbv Clean Code Cheat Sheet V2.2** (Urs Enzler), pages 1–2.
Each item is a check: scan for the violation, classify severity, cite `file:line`, propose the fix direction.

> **Why clean code matters** — Clean code keeps the cost of change roughly constant over a project's life. Shortcuts add technical debt that compounds: unclean code is a major debt driver, and dirty code also breeds bad processes and broken windows. In clean code, bugs cannot hide.

---

## 1. Smells (high-level)

| Smell | What to look for |
| --- | --- |
| **Rigidity** | A small change forces a cascade of other changes. |
| **Fragility** | One change breaks the software in many unrelated places. |
| **Immobility** | Code can't be reused elsewhere because of tangled dependencies. |
| **Viscosity of design** | The easy thing to do is the wrong thing; doing it right takes more effort. |
| **Viscosity of environment** | Build/test/deploy is so slow that people take shortcuts. |
| **Needless complexity** | Elements that aren't currently useful; over-design. |
| **Needless repetition** | Same logic duplicated; a change must be made in many places. |
| **Opacity** | Code is hard to understand; changes risk defects because intent is unclear. |

**Severity hint:** Rigidity, Fragility, Immobility, Opacity → usually Major/Critical. Needless complexity/repetition → Major.

---

## 2. Class Design — SOLID + cohesion

- **SRP (Single Responsibility)** — a class has one, and only one, reason to change. *Multiple responsibilities → Critical/Major (God class).*
- **OCP (Open/Closed)** — extend behavior without modifying existing code.
- **LSP (Liskov Substitution)** — subtypes must be substitutable for their base types.
- **DIP (Dependency Inversion)** — depend on abstractions, not concretions.
- **ISP (Interface Segregation)** — many small client-specific interfaces over one fat one.
- **Classes should be small** — small classes are easier to grasp; aim ~100 lines. A class that's hard to name in one sentence likely does too much.

## 3. Package Cohesion (which classes belong together)

- **REP (Release-Reuse Equivalency)** — the unit of reuse is the unit of release.
- **CCP (Common Closure)** — classes that change together are packaged together.
- **CRP (Common Reuse)** — classes used together are packaged together.

## 4. Package Coupling (relationships between packages)

- **ADP (Acyclic Dependencies)** — no cycles in the package dependency graph. *Cycle → Major.*
- **SDP (Stable Dependencies)** — depend in the direction of stability.
- **SAP (Stable Abstractions)** — a stable package should be abstract.

---

## 5. Design

- **Keep configurable data at high levels** — constants/config belong in a high level, exposed via argument to low-level functions; don't bury them deep.
- **Don't be arbitrary** — communicate reasons through structure; make structure empowerable for change.
- **Be precise** — when you decide, decide precisely; know why, and handle exceptions.
- **Structure over convention** — enforce design decisions with structure, but prefer naming conventions over structures that force compliance when they're heavier.
- **Prefer polymorphism to if/else or switch** — one switch per type of selection at most. *Repeated type-switching → Major (replace with polymorphism).*
- **Symmetry / analogy** — favor symmetric designs (e.g. load/save) and familiar analogies.
- **Separate multi-threading** — keep concurrency code out of the rest; separate it into its own classes.
- **Misplaced responsibility** — something is in the wrong place. *Major.*
- **Code at wrong level of abstraction** — e.g. a `PercentFull` property on a generic stack. *Major.*

### General

- **Follow standard conventions** — coding/architecture/design (check with tools).
- **KISS** — simpler is better; reduce complexity.
- **Boy Scout Rule** — leave code cleaner than you found it.
- **Root cause analysis** — fix the cause, not the symptom.
- **No multiple languages in one source file** (HTML+JS+SQL mixed inline). *Minor/Major.*

### Environment

- **Build requires one step.** **Tests require one step.**
- **Use source control.** **Continuous Integration** keeps integrity.
- **Don't override safeties** — no suppressing warnings/errors/exceptions blindly. *Major.*

### Dependency Injection

- **Decouple construction from runtime** — separate object construction from use to simplify runtime behavior.

---

## 6. Dependencies

- **Make logical dependencies physical** — if A depends on B, that dependency should be explicit, not assumed.
- **No Singletons / Service Locator** — they hide dependencies; prefer DI. *Major.*
- **Base classes should not depend on derivatives.**
- **Too much information** — minimize what a class exposes; reduce coupling.
- **Feature Envy** — a method more interested in another class's data than its own. *Major (Coupler).*
- **Artificial coupling** — things that don't depend on each other shouldn't be bound together.
- **Hidden temporal coupling** — if call order matters, make it impossible to call out of order.
- **Transitive navigation (Law of Demeter)** — write shy code; a module knows only its direct collaborators. *Message chains → Major.*

---

## 7. Naming

- **Descriptive / unambiguous names** — name reflects what it is or does.
- **Names at the right level of abstraction** — reflect the class/method's abstraction level.
- **Name interfaces after functionality** they abstract (e.g. `IStream`); name implementations after how they fulfill it (e.g. `MemoryStream`).
- **Name methods after what they do**, not how.
- **Long names for long scopes**, short names for short scopes (fields > params > locals > loop counters).
- **Names describe side effects** — don't hide them.
- **Use standard nomenclature** where one exists; don't invent your own language.
- **No encodings in names** — no Hungarian prefixes, no type/scope tags.

*Unclear/misleading names → Minor–Major depending on scope.*

---

## 8. Understandability

- **Consistency** — same concept, same name/pattern everywhere. *Inconsistency → Minor/Major.*
- **Use explanatory variables** — name intermediate steps.
- **Encapsulate boundary conditions** — put off-by-one logic in one place (`nextLevel = level + 1`).
- **Prefer dedicated value objects to primitives** (`AbsolutePath` over `string`). *Primitive obsession → Major.*
- **Poorly written comment** — a redundant/ill-formed/wrong comment is worse than none. *Minor.*
- **Obscured intent** — dense code that loses expressiveness. *Major.*
- **Obvious behavior unimplemented** — violates Principle of Least Astonishment. *Major.*
- **Hidden logical dependency** — a method silently relies on another being called first. *Major.*

---

## 9. Methods

- **Methods should do one thing** — loops, exception handling → extract into sub-methods. *Long Method (>~20 lines doing many things) → Major.*
- **Descend one level of abstraction** — statements in a method sit one level below the method's name.
- **Few arguments** — fewer is better; >3 params is a smell. Maybe move data into a dedicated object. *Long Parameter List → Major.*
- **No out/ref arguments** — return a new value or have the object change its own state. *Major.*
- **No selector / flag arguments** — split a `Foo(bool)` into separate methods. *Major.*
- **No inappropriate static** — a static that should be an instance method. *Minor/Major.*

---

## 10. Source Code Structure

- **Vertical separation** — declare variables/methods close to their use; locals just above first use.
- **Nesting** — nested code should handle the less-probable / more-specific case; keep happy path un-nested. *Deep nesting (>3) → Major.*
- **Structure into namespaces by feature** — group by feature, not by layer; cross-cutting features (logging) may be core features.

---

## 11. Conditionals

- **Encapsulate conditionals** — `if (ShouldBeDeleted(timer))` over `if (timer.HasExpired && !timer.IsRecurrent)`.
- **Positive conditionals** — positive reads easier than negative.

---

## 12. Useless Stuff (Dispensables)

- **Dead comment / commented-out code** — delete it; version control remembers. *Minor.*
- **Clutter** — code that does nothing and adds no value. *Minor.*
- **Inappropriate information** — comments holding info that belongs in another system (tickets, source control). *Minor.*

---

## 13. Maintainability Killers

- **Duplication** — eliminate it (DRY). *Major; cross-file → Major/Critical.*
- **Magic numbers / strings** — replace with named constants when meaning isn't derivable. *Minor/Major.*
- **Enums (persistent or behavioral)** — use reference codes instead of enums if persisted; use polymorphism instead of enums that carry behavior. *Major.*

---

## 14. Exception Handling

- **Catch specific exceptions** — catch only what you can react to meaningfully.
- **Catch where you can react meaningfully** — otherwise let it propagate.
- **Use exceptions, not return codes / null** — throw when the method can't do its job; don't return error codes or null. *Major.*
- **Fail fast** — throw as early as possible after detecting the problem, to pinpoint location.
- **Don't use exceptions for control flow** — bad performance, hard to follow. *Major.*
- **Don't swallow exceptions** — only swallow when the exceptional case is fully resolved inside the catch; otherwise the system is left inconsistent. *Critical.*

---

## 15. From Legacy Code to Clean Code (refactoring approach)

When the audit covers legacy code, the remediation tasks should follow this safety-first path:

1. **Always keep a running system** — change in small steps, running to running.
2. **Identify features**, prioritize by future value (likelihood + risk of change).
3. **Introduce boundary interfaces for testability** (fakes/mocks/stubs).
4. **Write feature acceptance tests** — a safety net before refactoring.
5. **Identify components** in a feature; prioritize by future value.
6. **Refactor interfaces between components** so each can be tested in isolation.
7. **Write component acceptance tests.**
8. **For each component decide**: refactor, re-engineer, or keep — based on defect history and expected future change.

### Refactoring patterns to recommend

- **Reconcile differences → unify similar code** — make two similar pieces identical stepwise, then merge.
- **Isolate change** — isolate the code to refactor, refactor, then undo isolation.
- **Migrate data** — move to a new representation via temporary duplication.
- **Temporary parallel implementation** — build the new version alongside, switch callers one by one, remove the old.
- **Demilitarized zone for components** — push unwanted dependencies outside an internal boundary, then refactor the interface.

---

## How to learn / sustain clean code (recommend in Notes when relevant)

Pair programming, commit/code reviews against clean-code guidelines, and coding dojos (kata) are the cheat sheet's recommended practices for keeping a team's code clean over time.

**Bibliography:** *Clean Code: A Handbook of Agile Software Craftsmanship* — Robert C. Martin.
