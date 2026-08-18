# MODERNIZATION_REPORT.md Template

Written at the target repo root in Phase 3. Sections are ordered so a reader who stops after page one
still has the verdict, the baseline, and the coverage honesty.

````markdown
# Modernization Report — <project name>

**Audited:** <YYYY-MM-DD> · **Commit:** <short sha> · **Branch:** <branch>
**Stack:** <languages / frameworks> · **Size:** <N source files, ~N kLOC>
**Baseline:** GREEN | AMBER | RED — <one-line reason>

## Summary

| Severity | Count |
|---|---|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |

<3–6 sentences: what shape this codebase is in, the two or three things that matter most, and what
the plan does about them. No hedging, no filler.>

**Top 5 by impact:** `F-XXX-NN` — one line each, in the order the plan tackles them.

## Baseline

| Row | Value | Evidence |
|---|---|---|
| Build | pass / fail (Ns) | `<command>` → `<decisive output line>` |
| Tests runnable | yes / no | `<command>` |
| Test pass rate | 41/58 (3 skipped) | `<command>` |
| Coverage | 34% lines / 22% branches — or Not Assessed — <reason> | `<command>` |
| Lint / typecheck | 0 errors, 87 warnings | `<command>` |
| CI | 2 workflows, last run failed — or absent | `.github/workflows/ci.yml` |
| Runtime declared vs installed | node 14 declared / 22.11 installed | `package.json:8`, `node -v` |
| Lockfile | present / missing / stale | `package-lock.json` |
| Last commit | <date>, N commits in 12 months | `git log -1` |

**Verdict:** GREEN | AMBER | RED
**Test command of record:** `<command>` — every P0–P4 plan task's acceptance criteria reference this. Pre ACs do not.

## Dimension coverage

All ten dimensions appear here. Honesty about what was not checked is the point of this table.

`Path` is `own probes` (DEP), `delegated` (a read-only delegate was invoked), or `inline`. For
`CLEAN`, `DEAD`, `TEST`, `CI`, `SEC`, and `DOCS`, **`inline` is the expected path** — their delegates
write files, so the audit never runs them. Do not present that as a limitation.

| Dim | Disposition | Path | Findings |
|---|---|---|---|
| DEP | Audited | own probes (3 of 4 ecosystems) | 14 |
| BUG | Audited | delegated → `code-review` mode `review` | 9 |
| PERF | Not Assessed — out of requested scope | — | 0 |
| CLEAN | Audited | inline | 12 |
| DEAD | Audited | inline | 7 |
| UX | Not Assessed — no UI detected | — | 0 |
| TEST | Audited | inline | 5 |
| CI | Audited | inline | 4 |
| SEC | Audited | inline | 3 |
| DOCS | Audited | inline | 3 |

## Dependency currency

Full `DEP` table in the shape defined by `references/dependency-audit.md`, sorted by severity, then
by wave.

| ID | Package | Ecosystem | Installed | Latest | Gap | Risk | Blast | Wave | Severity | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|

**Runtime and toolchain**

| Component | Declared | Installed | Current stable | Status | Severity |
|---|---|---|---|---|---|

**Upgrade waves**

| Wave | Contents | Lands in |
|---|---|---|
| W1 | security patches — N packages | P1 |
| W2 | patch/minor batch — N packages | P1 |
| W3 | runtime upgrade node 14 → 22 LTS | P2 |
| W4 | react 16 → 19 | P2 |

## Findings

One table per dimension, severity-ranked, using the finding record shape from
`references/dimension-map.md`. Every row cites evidence.

### BUG

| ID | Severity | Evidence | Problem | Fix direction | Effort |
|---|---|---|---|---|---|

### PERF
### CLEAN
### DEAD
### UX
### TEST
### CI
### SEC
### DOCS

*(Omit the heading for any dimension marked Not Assessed — the coverage table already records why.)*

## Cross-cutting patterns

Findings that recur rather than sit at one line — the ones a per-file review misses. Each names the
finding IDs it generalizes.

- **<Pattern>** — <where it recurs, how many sites, why it matters> (`F-XXX-NN`, `F-XXX-NN`, …)

## Artifacts written

Every file this run created. The read-only contract is checked against this list, so it must be
complete.

| File | Why |
|---|---|
| `MODERNIZATION_REPORT.md` | this report |
| `MODERNIZATION_PLAN.md` | the derived plan |
| `CODE_REVIEW.md` | declared artifact — written by `code-review` mode `review` |
| `obj/`, `.dart_tool/` | probe byproducts — created by `dotnet list package` / `flutter pub outdated` |

**Tracked files modified: 0** — `git status --porcelain` and `git diff` match the pre-run snapshot once declared artifacts are set aside. On a clean tree that is also `git diff --stat` empty.

## Limitations

Everything the reader should not over-trust in this report:

- Dimensions marked **Not Assessed**, with the reason.
- Tools that were unavailable and what that hid.
- Files or subsystems excluded from the scan, and the exclusion rule.
- `BUG`, `PERF`, or `UX` run inline because the Skill tool was unavailable — that one *is* reduced
  depth. The six dimensions that are always inline are not; do not list them here.
- Whether network access was available for latest-version and advisory lookups.

## Next step

The plan derived from this report: [`MODERNIZATION_PLAN.md`](./MODERNIZATION_PLAN.md).
````

## Rules for filling it

- **No finding without evidence.** `path:line`, or `path` + symbol, or `repo-wide` for
  absence-of-thing findings only.
- **Counts must reconcile.** The Summary table equals the sum of rows in the Findings tables.
- **Deduplicate across dimensions.** See the rule below — it is the one that keeps the Summary
  counts reconciling.
- **No remediation prose in the report.** `Fix direction` is one line; the actual sequencing,
  ownership, and verification belong in the plan.
- **Never write "no issues found"** for a dimension that produced nothing — either name the checks
  that were run and came back clean, or mark it **Not Assessed**.

## Deduplication rule

When two dimensions report the same `path:line`:

- The dimension appearing **earlier in the delegate table in `SKILL.md`** keeps the finding and its
  ID; the other ID is discarded and never referenced again.
- The finding is listed **once**, in the keeping dimension's table, with an `Also:` column naming the
  other dimension.
- The other dimension's table gets a one-line cross-reference (`See F-BUG-04 — also a SEC issue`)
  that is **excluded from all counts**.

Severity is the **higher** of the two dimensions' assessments — deduplicating must never downgrade a
finding.

This is what keeps the Summary counts equal to the number of counted rows, which Phase 3's
completion criteria check.
