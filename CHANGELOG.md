# Changelog

## Unreleased

### Added
- **`opencode-sandbox` 2.0.0** (was `opencode-docker-dev`): run OpenCode inside a [luongnv89/docker-dev](https://github.com/luongnv89/docker-dev) container. **SSH and GitHub auth are on by default** (`~/.ssh`, `~/.config/gh`, `GH_TOKEN` from `gh auth token`) so the container can commit, push, and open/merge PRs; pass `--no-ssh --no-github` to isolate. The container is **kept by default**. Agents use **`--start-only` then `--exec-in`** so a copy-paste `docker exec -it <name> zsh` attach command reaches the user before OpenCode blocks, then **ask before `docker rm`**. Do not use for opencode.ai cloud routing (`opencode-runner`), Herdr pane management, or running the project's own app.
- **`website-agent-readiness` 1.1.0:** takes a website URL and produces a tracked backlog for making that site usable by AI agents, behind a **human approval gate at every step**. Four phases: scan → triage → plan → issues. The scan is real, not inferred — `POST isitagentready.com/api/scan` returns a 0–5 readiness level across 22 checks in five categories, and a second call with `format: "agent"` returns the scanner's own remediation prose for *every* failing check (the JSON's `nextLevel` covers only the next level). Note that `isitagentready.com/<url>` — the obvious guess — is a 404; there is no page per site. Triage is **deterministic**: one failing check becomes exactly one plan task, phase-assigned by category with the scanner's own `nextLevel` requirements promoted to P0, effort taken from a fixed band table, and priority following from the phase. Two runs on the same scan produce the same plan. The plan is **rendered, not written** — `render_plan.py` emits the exact `MODERNIZATION_PLAN.md` grammar `/plan-to-issues` parses, so filing is a delegation rather than a re-implementation; it is invoked with an **explicit path** because bare `/plan-to-issues` would discover `MODERNIZATION_PLAN.md` first and file a different plan. Every task uses the documented `**Closes**: — (milestone-enabling: M<n>)` form: agent-readiness gaps are not codebase audit findings and `dim:` is a closed enum, so inventing `F-AGENT-001` would fabricate a dimension the tracker cannot filter on. It **plans and files; it never fixes** — the scanner's 24 hosted implementation guides are cited in each task, never fetched or applied, which keeps the boundary against `/seo-ai-optimizer` clean. The scan response is treated as untrusted throughout: it quotes the target site verbatim (`evidence[].bodyPreview` carries its `robots.txt`), so the URL reaches `curl` through an environment variable rather than a shell literal, and every scanner-derived string is collapsed to one line with `|` escaped and leading `#` stripped before it reaches the page. A non-commerce site gets its commerce checks deferred rather than filed; a site with no failing checks exits 3 and writes nothing, because `/plan-to-issues` rejects a file with no task headings.
- **`plan-to-issues` 1.6.0:** carries a finished plan into the tracker. Reads `MODERNIZATION_PLAN.md` (`/codebase-modernizer`) or a `/tasks-generator` `tasks.md`, files **one issue per plan task** through `/issue-creator` batch mode, and makes the **epic body a static plan map** — every child grouped by phase with its goal, milestone exit condition, declared dependencies and the critical-path ordering. The map asserts **no issue status**: no checkbox, progress bar, percentage, milestone verdict or next-actionable list. Live open/closed status and progress come from GitHub **native sub-issues**, which Phase 4 registers for every child (`POST /repos/{o}/{r}/issues/{n}/sub_issues`, which takes the child's database `id`, not its number) — so the epic body is written once per filing run and never needs re-truing when an issue closes. A markdown checkbox cannot do that job: GitHub does not auto-check a task-list box from the referenced issue's state, so every `- [x]` the old dashboard wrote went stale on the next close, which is what made a `sync` necessary after each one. `sync` now runs only when the *set* of issues or the plan changes, and re-rendering between filings is byte-identical. Where sub-issues are unavailable (older GitHub Enterprise) the run degrades with a warning rather than falling back to checkboxes. Labels are derived by rule, not judgement: `phase:`, type, `dim:` per closed finding dimension, `priority:` from the report's severity. It is **plan-faithful** and **idempotent**: a task already filed under the epic is skipped, so a rate-limited run resumes by re-running. An 11-check **Phase 0 preflight** gates the run *before the first mutation*. The epic is bound by a **plan-binding marker** (`<!-- plan-to-issues:plan=<path> -->`) written immediately after creation; the short create/bind window is handled by **recovery** — an unmarked epic is offered for adoption after an explicit confirm. Plan text is treated as untrusted throughout: the renderer collapses newlines in every plan-derived string and escapes `|` in table cells, plan-derived titles are *sourced* from the parsed worklist via `jq` rather than typed into a shell literal, and render-input validation covers every consumed field — container, element and scalar types, with JSON booleans rejected — so malformed input exits 2 with a hint rather than raising or rendering a Python repr into the epic body.

### Fixed
- **`agent-config` 1.4.0 → 1.4.1 (#125):** inject the token-efficiency block once into the source of truth (`AGENTS.md` on the default "both" path), not into the `CLAUDE.md` wrapper. Create/update pass checklist sections 1–3 and 5–7; section 4 (enforceability) is reported on audit and does not fail a create run — constitution Constraints pins are not a create blocker.
- **`code-review` 2.1.0 → 2.1.1 (#131):** the router and the `clean` mode disagreed on when `clean` runs. `SKILL.md` listed "readability" and "audit against standards" as *inference* triggers for it, while `references/clean-mode.md` declares the mode **user-invoked only** and accepts just `mode:clean` plus six explicit "clean code …" phrasings — neither of those two among them — and sends anything ambiguous to `review`. The same request therefore got two different answers depending on which file was read first, and the loose branch was the one that writes `CLEAN_CODE_AUDIT.md` to the repo root. The router now names the phrasings the mode actually accepts and says outright that a bare "readability" ask is ambiguous, so it falls through to the ask-the-user step. Found by the advisory Phase 2b predictability audit, not by a gate: `skills/code-review` **already cleared both hard gates at baseline** — `quick_validate.py` exit 0, `asm eval` 100 (A) with all seven categories at 10 — which is what #131 set out to verify. It correctly carries **no** dependency preflight: it invokes no other skill, so adding one would misstate its runtime dependency surface. One advisory finding is left open by choice (the mode → reference mapping is stated in both the Modes table and the supporting-files list, which carry different information). The last recorded improver pass was against 1.1.4 in July; its three open advisories were all closed by the 2.x rewrite.
- **`website-agent-readiness` 1.1.0 (#113):** a degraded run now says so **in the plan**, not only in triage's terminal output. `render_plan.py` reads `triage.json`'s `joined_by` and emits a header `**Note:**` naming every rendered task left without the scanner's remediation prose, so the caveat travels into the filed issues instead of scrolling past. The note is gated on tasks that are *actually* prose-less, not on `joined_by` alone — a `slug` join whose P0 tasks were refilled from `nextLevel.requirements` degrades nothing and emits nothing. A `position` run renders byte-identically to before. `SKILL.md` and `references/scan-api.md` now describe what the renderer does rather than what it did not.
- **`website-agent-readiness` 1.1.0 (#112):** `scan_site.sh` no longer interpolates `$outdir` into a Python string literal. The response-shape check now takes the path through `OUTDIR=` in the environment with a single-quoted `python3 -c` body, the same pattern lines 29-30 already used for the scanned URL, so no shell variable reaches Python or JSON syntax anywhere in the file. An `outdir` starting with `-` is normalised to `./-...` once at the top, so it cannot be read as an option flag by `mkdir`, `curl -o`, or `head -c`.

### Changed
- **`devops-pipeline` 2.0.3 → 2.2.0 (#133):** shifted the test load onto the local hooks and cut GitHub Actions back to what a laptop cannot do, then retrofitted to the current skill-creator standard. Three defects made the shift-left posture the skill *claims* undeliverable in practice. First, the CI templates were wrong about their own tool: `pre-commit run` executes **commit-stage hooks only**, so every workflow that reached for `pre-commit/action@v3.0.1` — the flagship "Minimal" template among them, under the caption "this single job re-runs everything pre-commit does locally" — silently skipped the full test suite, the coverage threshold and the CLI E2E tests, exactly the checks the skill had just moved to the `pre-push` stage. Every template now calls the CLI directly with both stages. Second, the skill contradicted itself on the shift-left axis: an acceptance criterion forbade running the same check in pre-commit and CI, while the templates re-ran the entire hook set over the whole repository on every push. Resolved by naming the overlap and bounding it — CI keeps exactly one hook invocation, a **bypass guard** scoped to the PR diff via `--from-ref`/`--to-ref`, which exists because `--no-verify` otherwise makes every local gate optional and is the one thing local tooling cannot prove about itself. Third, all 17 config and template snippets emitted the **deprecated stage names**: pre-commit 3.2 renamed `commit` → `pre-commit` and `push` → `pre-push`, and 4.6 warns on the old spellings ahead of removal, so the skill was generating configs onto a deprecation path — verified by running each config through `pre-commit validate-config` before and after. Migrated, with `pre-commit migrate-config` documented for pre-existing files. The guard itself is written to survive its first run, which is a separate hazard from getting the hook stages right: `actions/checkout` clones at **depth 1**, so `--from-ref` would die on a bad object without `fetch-depth: 0`; `github.event.before` is the **all-zeros SHA** on a branch's first push and stale after a force-push, so every guard job is gated on `pull_request`, where bypassed commits actually enter; hooks declared `language: system` shell out to `npm`, `mypy`, `go` or `cargo`, so the guard stays in a job that installs the project toolchain, with `actions/setup-python` added to the four templates that ran `pip install pre-commit` against a runner Python that can refuse under PEP 668. The monorepo template ran the guard once **per language job**, which would have had the Python-only backend job execute the eslint hook — collapsed to one guard job, with `paths-filter` deciding which *build* jobs run rather than which hooks do. The routing rule these all serve is now a single **Check Routing Table** with explicit time budgets (`pre-commit` under 10s on changed files, `pre-push` under 60s, CI billed per minute) declared the source of truth that the workflow steps, the reference files, and any generated config must agree with; the two ways staged tests silently never run — forgetting the second `pre-commit install --hook-type pre-push`, and `--no-verify` — are called out where each bites. On the retrofit: Gate 1 passed at baseline and still does, and it correctly carries **no** dependency preflight (it invokes no other skill). Gate 2 **failed** at baseline on Safety & guardrails = 7 — a fair finding, since the skill writes `.pre-commit-config.yaml` and workflow files into someone else's repository and installs git hooks while saying nothing about how. New **Safety Rails** section: back up to `.bak`, merge rather than overwrite, and confirm against a diff; dry-run through `pre-commit validate-config` plus an *uninstalled* `pre-commit run --all-files`, which surfaces findings without blocking a commit; preserve a foreign git hook via pre-commit's migration mode and never pass `-f`/`--overwrite`; never run `--no-verify` on the user's behalf; never suppress a failure with `SKIP` or a relaxed threshold. `asm eval` 91 (A) → 96 (A), Safety & guardrails 7 → 10, min category 7 → 8, in 2 iterations; `asm eval --fix --dry-run` reported "No fixes needed". 244 → 278 lines, 1948 → 2276 body words (caps 500 / 3000) — nothing was cut, so nothing needed to move to `references/`. **Advisory Phase 2b findings, both acted on:** the "one lane per check" criterion ended on judgement and was given a grep-checkable bar (no hook `id` in a workflow `run:` step outside the bypass guard); and the Resources index omitted `references/cli-e2e.md` although the body linked it twice. The delegability sub-check **passes** — steps 2 and 3 each already name the single `references/` slice a worker would need, so there is no Mode 2 candidate.
- **`test-coverage` 1.3.0 → 1.3.1 (#157):** retrofitted to the current skill-creator standard. Gate 2 was **already green at baseline** — `asm eval` 97 (A) with every category ≥ 8, and `asm eval --fix --dry-run` reporting "No fixes needed" — but Gate 1 was not: `metadata.author` was an **unquoted** plain scalar carrying `<`, `>` and `@`, three characters on the Frontmatter Audit's must-quote list and two of them named independently by this repo's `CLAUDE.md` hard rule #2. `quick_validate.py` exits 0 on it because the value *parses* — YAML treats those characters as ordinary mid-scalar — which is why check 10 is one of the rows the audit marks as needing an agent read; same defect and same fix as `release-manager` in #151, `seo-ai-optimizer` in #153 and `frontend-design` in #138. It correctly carries **no** dependency preflight: a full-directory scan for slash-command invocations and `~/.claude/skills/` reads returns 12 hits that are all file paths (`src/parser.py`), prose slashes (`if/else`, `null/undefined/empty`) or the skill's own fallback branch name `feat/test-coverage` — no skill is invoked, so adding one would misstate its runtime dependency surface. `asm eval`'s one `topSuggestion` (add a labelled `## Example` section) was deliberately not acted on — the two categories it serves already clear the ≥ 8 floor, Phase 3 forbids chasing points a passing category does not need, and the skill already carries a worked `## Expected Output` block. **No content was cut**: the body is 167 lines / 1036 words against the 500 / 3000 caps, so nothing needed to move to `references/` and none exists. `asm eval` holds at 97/A, min category 9. **Advisory Phase 2b findings, left open by choice:** Steps 2 (Identify Test Gaps) and 3 (Write Tests) end on a category list with no per-step checkable bar — the run-level Acceptance Criteria *are* checkable (coverage strictly higher, full suite green, branch not `main`), and closing the gap means inventing a gap count the skill has no basis for; and `## Guidelines` overlaps Step 3's scenario list while the feature-branch rule is stated in both Workflow step 0 and Acceptance Criterion 5, short reinforcement whose removal costs more `context-efficiency` than it returns from a category already at 10. The delegability sub-check **passes** — step 3 consumes step 2's exact gap list and the repo's existing test idiom with no `references/` slice to hand a worker, so there is no Mode 2 candidate.
- **`agent-config` 1.3.1 → 1.4.0 (#125):** folded the official Anthropic and AGENTS.md guidance into the skill, then retrofitted it to the current skill-creator standard. The largest correction is what `AGENTS.md` **is**: the skill previously defined it as a file of subagent definitions, while the open standard (and OpenAI Codex, which reads it) defines it as the cross-agent source of truth — a README *for agents* carrying setup, commands, layout, style deltas, tests, PR rules and security. A skill that got that wrong would write the wrong file, so the disambiguation lives in the body at Step 1 rather than behind an on-demand read, and it now defaults "both" to one `AGENTS.md` plus a thin `CLAUDE.md` that opens with `@AGENTS.md`. Subagent definition files (`.claude/agents/*.md`) are named as `subagent-creator`'s domain and explicitly out of scope; a target that already keeps subagent prompts inside its `AGENTS.md` — this catalog's own file does — is preserved rather than rewritten. A new **Core Principle** section states the rule the rest of the skill now follows: these files are *context, not enforced configuration*, so procedures belong in a skill, must-never-happen belongs in a `PreToolUse` hook plus permissions, and verification belongs in tests or CI. That principle is made **behavioral, not decorative** — the `audit` flow gained a routing-and-enforcement step that names, for every failing line, the layer it should move to, and requires a machine-checkable rule to get its gate *and* lose its prose. The **size budget was reconciled, not stacked**: `references/claude-md-checklist.md` enforced an 80-line ceiling sourced from a community write-up while the official figure is under 200 lines with a 40–150 sweet spot — leaving both would have been exactly the contradiction the guidance warns produces random rule selection, in a skill whose job is catching it. One number governs; the 80-line figure's provenance is noted where it was superseded. Two new references carry the depth: `official-standards.md` (the doc citations — the 4 MiB hard load cap, Codex's 32 KiB combined budget, why `@imports` organize but never shrink context while path-scoped `.claude/rules/*.md` do, and `/init` `/context` `/doctor`) and `knowledge-routing.md` (the layer table, both section-order templates, the writing rules, and the add-a-rule-only-when-the-agent-is-wrong-twice feedback loop). The checklist grew from 5 sections to 7 — **Routing**, **Enforceability** and **Consistency & drift** added, the old *Proper hierarchy* absorbed into Routing — and the anti-pattern list gained the structural failure modes the content list had no room for: contradiction, cross-file duplication, emphasis inflation, `@import` used as a token-saving device, prose standing in for a gate. It correctly carries **no** dependency preflight — it invokes no other skill, and the one skill named in the body is cited as a scope boundary rather than called. **Both hard gates were already green before the adaptation** (`quick_validate.py` exit 0, `asm eval` 100 (A), all seven categories 10), which is what #125 set out to verify; after the fold they hold at `asm eval` 97 (A) with `context-efficiency` at 8 — the one category the added body cost, still clear of the ≥ 8 floor that Phase 3 forbids chasing past. 227 → 245 lines, 1263 → 1841 body words (caps 500 / 3000). **Advisory Phase 2b findings, left open by choice:** the `create` / `update` / `audit` branch is declared in *User Input* but each mode's divergence is not resolved until *Execution Flow*, ten sections later, so every run reads all three; and `Expected Output` restates the Step Completion Report format that its own section already gives.
- **`frontend-design` 1.2.4 → 1.2.5 (#138):** retrofitted to the current skill-creator standard. Gate 2 was **already green at baseline** — `asm eval` 96 (A) with every category ≥ 8, and `asm eval --fix --dry-run` reporting "No fixes needed" — but Gate 1 was not: `metadata.author` was an **unquoted** plain scalar carrying `<`, `>` and `@`, three characters on the Frontmatter Audit's must-quote list and two of them named independently by this repo's `CLAUDE.md` hard rule #2. `quick_validate.py` exits 0 on it because the value *parses* — YAML treats those characters as ordinary mid-scalar — which is why check 10 is one of the rows the audit marks as needing an agent read; same defect and same fix as `release-manager` in #151 and `seo-ai-optimizer` in #153. It correctly carries **no** dependency preflight: a full-directory scan for slash-command invocations and `~/.claude/skills/` reads returns nothing, and the one skill named in the body — `dont-make-me-think` — is cited as the *source* the inlined Krug rules were condensed from, never invoked, so a preflight would misstate the runtime dependency surface. `asm eval`'s one `topSuggestion` (move large sections into `references/`) was deliberately not acted on: it points at the 28-line usability section, whose duplication of `references/usability-guide.md` is by design — those rules must be in context *during* generation, not fetched after — and `context-efficiency` already clears the ≥ 8 floor, which Phase 3 forbids chasing past. One **advisory** Phase 2b finding was acted on: `docs/README.md`'s Resources table listed only `references/usability-guide.md` while SKILL.md links `references/step-reports.md` twice, orphaning a shipped reference from the catalog page. Two are **left open by choice**: the extend-an-existing-codebase branch changes Instructions steps 1-3 but is declared only in Edge Cases, after the agent has been told to commit to a bold aesthetic direction; and the 375/768/1280 px breakpoints with WCAG AA appear in three sections as deliberate reinforcement rather than sediment. The delegability sub-check **passes** — the heavy implementation step needs the previous step's agreed aesthetic direction verbatim, so there is no Mode 2 candidate. Body unchanged at 154 lines / 1615 words (caps 500 / 3000); `asm eval` holds at 96/A, min category 8.
- **`seo-ai-optimizer` 1.2.3 → 1.3.1 (#153):** retrofitted to the current skill-creator standard, and given a **Step 8 agent-readiness handoff**. Gate 2 was **already green at baseline** — `asm eval` 94 (A) with every category ≥ 8 — but Gate 1 was not: `metadata.author` was an **unquoted** plain scalar carrying `<`, `>` and `@`, three characters on the Frontmatter Audit's must-quote list and two of them named independently by this repo's `CLAUDE.md` hard rule #2. `quick_validate.py` exits 0 on it because the value *parses* — YAML treats those characters as ordinary mid-scalar — which is why check 10 is one of the rows the audit marks as needing an agent read; same defect and same fix as `release-manager` in #151. New **Step 8** runs `/website-agent-readiness <live-url>` after validation: Steps 1-7 read the *repository*, while that skill scans the *deployed site* through `isitagentready.com` and so sees server-rendered output, response headers, and whether `robots.txt` / `llms.txt` are actually served rather than merely committed. The boundary between the two is stated in the step, because `website-agent-readiness`'s own description names this skill as a non-trigger for applying llms.txt/SEO fixes — the dependency runs in the opposite direction (fix the code here, then score the deploy there), and its findings re-enter **this** skill at Step 5 as ordinary plan items under the Diff & Confirm protocol rather than being applied inline. The step is **conditional on two preconditions** (a reachable public URL carrying the Step 6 changes, and the user's approval), and a `SKIPPED` result is a pass that must name the unmet one — a library, template, or pre-launch repo finishes at Step 7. Adding a skill invocation is what turns Gate 1's *Dependency preflight* from not-applicable into mandatory, so the skill now carries one naming `website-agent-readiness`, its install command, the installer bootstrap, and a verification step; a miss **skips Step 8** rather than aborting the run, because Steps 1-7 audit the codebase and do not depend on it. The preflight tests the **install path before `asm list`**: this skill ships in the same repo as its dependency, so a repo-installed `website-agent-readiness` is present without the curated registry knowing the bare name — `asm search --json` returns it only as `status: installed`, with no registry entry, so a bare-name `asm install` would not resolve and an `asm list` check alone would nag on every run. Same shape and reason as `dont-make-me-think` in #136. The step's detail — the boundary table, the return path, and the per-outcome verification — went to `references/workflow-detail.md` rather than the body, under the Phase 4 link-out rule. 801 → 1112 body words (cap 3000), 141 → 187 lines (cap 500); `asm eval` holds at 94/A with all seven categories unchanged, min category 8. **Advisory Phase 2b findings, left open by choice:** the framework branch (Next.js / Nuxt / Astro / …) is resolved inside Step 1 rather than by an early selector, and `## Prerequisites` restates the audit-script invocation that Step 1 gives again three sections later — neither blocks a gate, and closing either costs more `context-efficiency` than it returns.
- **`release-manager` 2.6.0 → 2.6.1 (#151):** retrofitted to the current skill-creator standard. Gate 2 was **already green at baseline** — `asm eval` 97 (A) with every category ≥ 8, and `asm eval --fix --dry-run` reporting "No fixes needed" — but Gate 1 was not: `metadata.author` was an **unquoted** plain scalar carrying `<`, `>` and `@`, three characters on the Frontmatter Audit's must-quote list and two of them named independently by this repo's `CLAUDE.md` hard rule #2. `quick_validate.py` exits 0 on it because the value *parses* — YAML treats those characters as ordinary mid-scalar — which is why check 10 is one of the rows the audit marks as needing an agent read; 21 of 39 catalog skills, including every previously-retrofitted one, already quote the same value. It correctly carries **no** dependency preflight: a full-directory scan for slash-command invocations returns only its own `/release-manager`, and the five bundled prompts under `agents/` are not skills, so adding one would misstate its runtime dependency surface. `asm eval`'s one `topSuggestion` (add a labelled `## Example` section) was deliberately not acted on — both categories it serves are already ≥ 8, and Phase 3 forbids chasing points a passing category does not need. One **advisory** Phase 2b finding was acted on: the "an existing release tool is configured, defer to it" branch was announced only in a blockquote inside Step 1, *after* the Overview had laid out 10 unconditional steps, so a run against a `semantic-release` or `.changeset` repo planned all 10 before learning steps 2-10 do not apply; the Overview now states the short-circuit before the step list. One is **left open by choice**: Step 10 (publish to PyPI/npm) is heavy, reads a 139-line `references/publishing.md`, runs inline and names no slice for a worker — its remediation is a **Mode 2 delegation conversion**, which is opt-in and runs outside the Phase 0-7 loop. 1390 → 1415 body words (cap 3000), 243 lines unchanged (cap 500); `asm eval` holds at 97/A, min category 9.
- **`dont-make-me-think` 1.3.2 → 1.4.0 (#136):** retrofitted to the current skill-creator standard. Both hard gates were **already green at baseline** — `quick_validate.py` exit 0, `asm eval` 97 (A) with every category ≥ 8 — but two Gate 1 sub-criteria were not. Adds a **Dependency Preflight**: the skill *invokes* `/browse` for the live-URL input path and named no install command, no installer bootstrap, and no verification step for it. The gate tests the install path (`~/.claude/skills/browse`) **before** `asm list`, because `/browse` ships in gstack (`asm install github:garrytan/gstack:browse -p claude -s global --yes`) and may be present without `asm` knowing about it — an `asm list` check alone would nag on every live-URL review. A missing `/browse` is **fail-soft**: it takes the `/browse` row already in Error Handling rather than stating a second fallback policy. Adds **Repo Sync Before Edits**, which Redesign Mode needed and lacked — it writes to UI source files in a git repo and its own rollback step reverts from git; steps 1-4 stay read-only and skip the sync. `references/screenshot-processing.md` was an **orphan**: it existed, went 91 lines deep, and no line of SKILL.md pointed at it, while the body inlined a shorter duplicate of the same material. The body now carries the invocation and a one-line pointer, and the reference gained the **Warnings** field the body used to name and it did not. 1751 → 2021 body words (cap 3000), 261 → 297 lines (cap 500); `asm eval` holds at 97/A, min category 8. **Advisory Phase 2b findings, left open by choice:** `Working With Live Sites` overlaps the `Live URL` row in Input Handling, `Expected Output` restates the Report Format template's sections, and the acceptance bar "report is skimmable in 30 seconds" is an impression rather than a checkable criterion — none of the three blocks a gate, and each is pre-existing prose the issue did not scope.
- **`codebase-modernizer` 1.2.2 → 1.3.0:** retrofitted to the current skill-creator standard. Adds a **Dependency Preflight** section — the skill *invokes* `code-review` (modes `review`, `perf`) and `dont-make-me-think` (`UX`), and previously named no install command, no installer bootstrap, and no verification step for either; a missing delegate now degrades **fail-soft** to `Not Assessed — skill unavailable` instead of silently producing a `Path: delegated` row backed by nothing. The six *inline* delegates are deliberately excluded from the preflight: they are named in plan tasks and never invoked, so listing them would misstate the runtime dependency surface. The body had also drifted 218 words past the 3000-word cap, so the full Acceptance Criteria checklist moved to `references/acceptance-criteria.md` and the edge-case list to `references/edge-cases.md`, each leaving the bars that are the skill's actual contract inline — the two read-only assertions, and the **Monorepo** case that changes how `dep_scan.sh` is invoked. 3218 → 2936 body words; `asm eval` 90 → 94, min category 6 → 8.
- **Eval suites are runnable, not just declarable (#114):** `scripts/run-skill-evals.py` replays a canonical suite's prompts through `claude -p` and reports, per case, whether the skill triggered. It deliberately does not overclaim — triggering only, with each case's `expectations` printed as `[MANUAL] ... SKIPPED (run by operator)`; the **installed** skill is what is measured, with a warning when its description has drifted from the working tree; and a case declaring `files` is skipped rather than failed, because replaying a prompt that presupposes on-disk state into an empty directory measures the missing fixture. skill-creator's `run_eval.py` is not usable here: it reads `item["query"]` rather than the canonical `prompt`, and it counts a trigger only under the unique name of its own temporary command file — so with the skill also installed under its real name, Claude triggers the real one and every positive case reports a false failure (7 of 10, all spurious).
- **`website-agent-readiness` evals converted to the canonical schema (#114):** the suite was the one file in the catalog that **failed** `scripts/validate-evals.py` — `skill` instead of `skill_name`, string ids, no `expected_output`, and all 10 assertion lists parked under the dead `assertions` key where the runner never reads them. Converted following the `fork-upstream-sync` recipe: integer ids in file order with each original slug kept under `name`, `assertions` → `expectations`, `expected_output` rendered from each case's own expectations, `kind: negative-trigger` on the three cases that declared `should_trigger: false`. The catalog now validates clean (14/14, exit 0).
- **`dev-machine-setup` 0.6.0 → 0.9.0:** now **self-contained** — no `luongnv89/inbash` clone. The shell config ships as `assets/zshrc-config` (a vendored fork; upstream fixes no longer flow in) and the `.sh` wrappers are replaced by the plain brew / apt / dnf / pacman commands and `git clone`s they wrapped.
- **Zsh parity:** `detect_env.py` now reports `starship` as a baseline tool and emits `starship-config-missing` / `starship-config-not-managed`, deploying `assets/starship.toml`. Detection reads a first-line marker so phase 5's re-run can actually observe the fix.
- **`oh-my-zsh-missing` is no longer flatly additive:** deploying the shipped `~/.zshrc` is additive when none exists and **mutating** (backup + its own yes) when one does, so a blanket approval can't silently overwrite a working config.
- **SKILL.md split** for progressive disclosure — approval protocol → `references/approvals.md`, phase bodies → `references/procedure.md`. 354 → 176 lines; `asm eval` 90 → 94, min category 6 → 8.

## v2.0.0 — 2026-08-18

Catalog-wide consolidation and rename: one primary skill per intent, code-faithful docs, and a checkable read-only eval harness. **42** installable `SKILL.md` files (nested suite children included).

### Breaking Changes
- **`docs-generator` → `doc-manager` (#75):** `/docs-generator` and `--skill docs-generator` are removed — use `/doc-manager`. Reoriented from “restructure docs into a hierarchy” to “generate missing or update existing docs so every page matches the code.” Every non-obvious claim is cited to `path:line`; ambiguities are asked and logged to `docs/DECISIONS.md`. Uninstall leftover `docs-generator` copies so they do not compete for triggers.
- **Code-quality cluster merged into `code-review` (#72 / #74):** `code-optimizer`, `clean-code`, and `slop-cleanup` are **removed** as separate skills. **Migration:** `/code-optimizer` → `code-review mode:perf`; `/clean-code` → `code-review mode:clean`; `/slop-cleanup` → `code-review mode:cleanup`. Only `cleanup` writes code, and it never fires by inference.
- **`readme-to-landing-page` → `landing-page-generator` Mode B (#72 / #74):** if you installed `readme-to-landing-page`, install `landing-page-generator` and remove the old skill.
- **`drawio-generator` + `excalidraw-generator` nest under `diagram-generator`:** invocations `/drawio-generator` and `/excalidraw-generator` are unchanged; the install path is nested. Use `/diagram-generator` to pick the engine by output format.

### New Skills
| Skill | Version |
|-------|---------|
| fork-upstream-sync | 1.3.2 |
| herdr-agent-comms | 1.23.0 |
| issue-work-loop | 1.3.1 |
| diagram-generator | 1.1.2 (umbrella routing draw.io + Excalidraw) |
| codebase-modernizer | 1.2.2 |

**codebase-modernizer (1.1.0):** read-only whole-repo audit that produces `MODERNIZATION_REPORT.md` and `MODERNIZATION_PLAN.md` for a codebase gone stale or messy. Phase 0 records a **baseline-green** verdict (build, test pass rate, coverage, CI) that every planned task's acceptance criteria then reference — which is what makes the plan testable rather than aspirational. Ten dimensions: dependency and runtime currency is the skill's own (`scripts/dep_scan.sh` probes 14 ecosystems fail-soft). A delegate is invoked during the audit **only if it writes nothing** — `code-review` modes `review`/`perf` and `dont-make-me-think` run; the six that write (`code-review` modes `clean`/`cleanup`, `test-coverage`, `devops-pipeline`, `security-setup`, `doc-manager`) are scanned inline and instead named as the invocation in the plan task that does the work. Findings cite `path:line` or are marked **Not Assessed** — never guessed. Dependencies are never upgraded in place: they are classified into **upgrade waves** (security patches → patch/minor batch → one major per task with a named migration source, via Context7 when available). The plan uses a fixed P0–P4 skeleton with sprints, milestones, a dependency DAG, and a stated critical path, in `tasks-generator`'s task format. A future gated apply-upgrades mode is the intended v2 extension.

**codebase-modernizer (1.2.0):** every emitted plan now opens with an unconditional **Pre — Agent environment** step before P0 Stabilize (P0–P4 keep their numbers). Pre schedules a runnable agent environment and create-or-improve of `CLAUDE.md` / `AGENTS.md` via `/agent-config create|update` — planned only; the audit still never writes those files.

**codebase-modernizer (1.2.1):** Pre is exempt from the still-green suite AC when the baseline is RED. Pre.3 / `AGENTS.md` is create-or-update against agent-config checklists only; recorded build/test commands live on Pre.1 notes and Pre.2 / `CLAUDE.md`. (#93, #94)

**codebase-modernizer (1.2.2):** the read-only contract is a **delta** against a pre-run snapshot, not an empty `git diff --stat`. A stale already-dirty tree is the intended target; the empty-stat check could never pass there. (#88, #95)

**issue-work-loop (1.1.5):** resolves a single GitHub issue through a Herdr-pane implementer→reviewer loop until the PR review is CLEAN. Implementer runs `/issue-resolver`, reviewer runs `/issue-pr-review --review-only` in a separate pane; every FINDING counts, including notes (no soft-pass). Reviewer is FRESHENed at ROUND start and implementer before each fix when context crosses 50%; `--no-cleanup` skips SWEEP for debug; worker panes and loop worktrees are swept at the end by default; merging is always left to the human.

**herdr-agent-comms:** spawn and message a multi-agent fleet in Herdr panes (split-pane default, tab-per-agent opt-in). (#77)

### Skills Updated
| Skill | Version Change |
|-------|----------------|
| codebase-modernizer | 1.1.0 → 1.2.2 |
| docs-generator → doc-manager | 1.2.5 → 2.0.2 |
| tmux-agent-comms | 1.3.0 → 2.2.0 (observability, app terminal tabs by default, orchestrator context handoff) |
| landing-page-generator | 1.1.4 → 1.2.1 (absorbs README-to-landing as Mode B) |
| code-review | 1.2.0 → 2.1.0 (merge code-optimizer + clean-code + slop-cleanup as modes) |
| drawio-generator | 1.2.2 → 1.2.3 (nested under diagram-generator umbrella) |
| excalidraw-generator | 1.3.2 → 1.3.3 (nested under diagram-generator umbrella) |
| viral-product-evaluator | 1.2.3 → 1.2.4 (update merged-skill cross-reference) |
| dont-make-me-think | 1.2.1 → 1.3.2 (screenshot pre-processing script; #73) |
| agent-config | → 1.3.1 |
| aso-marketing | → 1.2.1 |
| auto-push | → 1.0.3 |
| brand-name-checker | → 1.3.2 |
| cli-builder | → 1.0.5 |
| devops-pipeline | → 2.0.3 |
| frontend-design | → 1.2.4 |
| idea-validator | → 1.5.0 |
| install-script-generator | → 2.2.1 |
| logo-designer | → 1.2.3 |
| ollama-optimizer | → 1.1.1 |
| opencode-runner | → 1.4.1 |
| oss-ready | → 1.2.1 |
| prd-generator | → 1.3.2 |
| release-manager | → 2.6.0 |
| security-setup | → 1.4.0 |
| seo-ai-optimizer | → 1.2.3 |
| subagent-creator | → 1.1.2 |
| tad-generator | → 1.4.0 |
| tasks-generator | → 1.3.1 |
| website-cloner | → 1.2.1 |

**Orchestrator context handoff (herdr-agent-comms 1.23.0, tmux-agent-comms 2.2.0):** the main agent now gates its own context window instead of only its workers'. It self-checks usage at three named points — before a spawn wave, before a broadcast, and after each relayed reply — and at or above a 50% threshold (overridable in conversation) performs a **HANDOFF**: it spawns a successor orchestrator with the skill's own guarded spawn path (`main-g<N>` pane in Herdr, `<folder>-main-g<N>` session in tmux), delivers a compact fleet brief through the normal baseline/marker/preflight cycle, waits for an explicit `HANDOFF ACCEPTED` ack, then goes read-only and announces the successor. Orchestrator is now a **role, not a pane** — the outgoing pane/session is retired, never closed without confirmation — and exactly one orchestrator holds write access at a time. When usage is unreportable, a countable fallback (20 relayed reads or 4 spawn waves) drives the same decision. See `references/context-succession.md` in either skill.

**tmux-agent-comms:** new sessions open in app terminal tabs by default, with detached fallback for background fleets or environments without a tab facility. (#76)

**dont-make-me-think:** `scripts/process_screenshots.py` extracts metadata, palette, layout regions, density, and quality before visual review so the agent consumes structured JSON/markdown instead of generating image-processing code at runtime. (#73)

### Removed Skills (merged into code-review modes)
| Skill | Merged into |
|-------|-------------|
| code-optimizer | `code-review` → `perf` mode |
| clean-code | `code-review` → `clean` mode |
| slop-cleanup | `code-review` → `cleanup` mode |

### Skill Consolidation (#72)
Fewer, clearer entry points — one primary skill per intent.

- **readme-to-landing-page → landing-page-generator (Mode B).** The README-to-landing-page
  capability now lives in `landing-page-generator` as its "README landing page" mode
  (`references/readme-mode.md`). **Migration:** if you installed `readme-to-landing-page`, install
  `landing-page-generator` and remove the old skill — the trigger "turn my README into a landing
  page" now routes there.
- **drawio-generator + excalidraw-generator → diagram-generator umbrella.** Both engines moved to
  `skills/diagram-generator/{drawio,excalidraw}-generator/` behind a new `diagram-generator` router.
  Skill names and the `/drawio-generator` · `/excalidraw-generator` invocations are unchanged; only
  the install path is nested (installers discover both levels). Use `/diagram-generator` to pick the
  engine by output format.
- **Code-quality cluster merged into `code-review` (four modes).** `code-optimizer`, `clean-code`,
  and `slop-cleanup` are **removed** as separate skills; their full workflows become the `perf`,
  `clean`, and `cleanup` modes of `code-review` (default = `review`). One entry point selects the
  mode by intent or an explicit `mode:` parameter. Safety: only `cleanup` writes code, and it never
  fires by inference. **Migration:** `/code-optimizer` → `code-review mode:perf`; `/clean-code` →
  `code-review mode:clean`; `/slop-cleanup` → `code-review mode:cleanup`.

### Tooling
- Add `scripts/validate-evals.py` (stdlib only): walks `skills/*/evals/evals.json` and suite sub-skills, enforcing the canonical `{skill_name, evals:[{id, kind, prompt, expected_output, files, expectations}]}` shape. **FAIL** tier (non-zero exit) covers a wrong top-level shape, a `skill_name` that does not match its directory, missing/duplicate/non-integer ids, missing `prompt` or `expected_output`, assertion lists parked under the dead `assertions`/`expected_behavior` keys, and unknown keys; **WARN** tier (exit 0) surfaces `expectations: []`, a file where no case declares `kind`, and a missing `files`
- Add `scripts/eval-readonly-check.sh` (`snapshot` / `verify` / `restore`): zero-dependency harness that checks a read-only skill's contract as a delta against a pre-run snapshot. The SHA-256 path manifest is what makes it work — `git diff` cannot see untracked files, so a delegate writing a new `.github/workflows/ci.yml` or test file passes an empty `git diff --stat` unnoticed. The declared-artifact allowlist is transcribed from the skill's own contract text with `file:line` citations, and transcript-level assertions are reported as `[MANUAL] ... SKIPPED` rather than dropped

### Changed
- Converge seven drifted `evals.json` files onto the canonical schema, content-preserving: `aso-marketing` (`assertions` → `expectations`); `fork-upstream-sync` (`skill` → `skill_name`, `expected_behavior` → `expectations`, `files: []` added, string ids replaced by integers 1-3 in file order with each original slug preserved under an optional `name` key, and `expected_output` rendered from that case's own expectation list); `herdr-agent-comms`, `landing-page-generator`, `opencode-runner`, `tmux-agent-comms`, `viral-product-evaluator` (explicit `expectations: []`). No `kind` was written into a file that never declared one — it defaults to `happy-path`, so filling it in would guess at cases that may really be negative-trigger. No expectation content was invented; the empty lists are the honest state and the WARN tier keeps them visible

### Bug Fixes
- **codebase-modernizer evals 1, 8, 10, 11 asserted something no run could satisfy** (#88 / #95): each demanded `git diff --stat` be empty at the end of the run, which is false on any genuinely stale repo. Rewritten as a **delta** assertion against a pre-run snapshot (porcelain, full `git diff`, SHA-256 manifest), modulo the declared artifact allowlist.
- **`scripts/eval-readonly-check.sh`:** tracked-file exemption when the index shrinks; directory allowlist no longer exempts tracked files; C-quoted paths, non-git targets, trailing-slash allowlist, flag/`cwd` handling, pipeline `exit 2` for manifest derivation, and `restore` provenance-before-move. (#88)
- `scripts/validate-evals.py` checked only truthiness, so invalid types were reported `[PASS]` (#88). Types are now enforced against schemas.md / grader.md; `aso-marketing` object-valued expectations flattened to strings.
- **issue-work-loop (1.2.1 → 1.3.1)**: Replace the autonomous worker boot gate with a per-harness matrix — pi launches bare and is autonomous by default; Claude Code starts plain and is switched via Shift+Tab; opencode starts plain and is switched to the full-permission Build agent via Tab or settings. Removes the nonexistent auto-mode slash command and invented startup flags. (#83)
- **herdr-agent-comms (1.22.0 → 1.22.2)**: Launcher guidance drops the unverified pi `--skill` flag and replaces vague “verified flags” with concrete direction to launch `claude`/`opencode` bare. (#83)
- **dont-make-me-think:** review fixes for screenshot pre-processing (`text_regions_estimated`, `--json`/`--markdown` flags, NameError/dead code). (#73)
- **doc-manager 2.0.1:** runbook acceptance no longer hard-requires live `--check` exit 0 for operator env/network prereqs; validate script template parses all flags (`--check` + `--run-destructive`).

### Documentation
- Document the canonical `evals.json` shape, `python3 scripts/validate-evals.py`, its FAIL/WARN tiers, the optional `name` key, and the read-only delta harness in CONTRIBUTING.md
- Reconcile root README skill catalog to on-disk `metadata.version` for all installable skills; add `fork-upstream-sync`, `herdr-agent-comms`, Google Antigravity install path, Project docs index, install validation link (#96)
- Reconcile `docs/index.html` GitHub Pages copy to current catalog state: v1.15.0 baseline, Google Antigravity support, and no removed `clean-code` catalog card
- Correct the `docs/index.html` skill count to 42 at every site, state the counting rule (every tracked `SKILL.md` under `skills/`, nested suite sub-skills included) beside the literal, and assert it from `scripts/validate-contribute.sh` (#89, #92)
- Fix CONTRIBUTING setup commands to external skill-creator paths (`~/.claude/skills/skill-creator/scripts/`); align frontmatter example with `metadata.version`
- Add `scripts/validate-install.sh`, `scripts/validate-contribute.sh` (check-only), `docs/DECISIONS.md`, `docs/troubleshooting.md`, `docs/archive/README.md`
- Move former root documentation drafts into `docs/archive/` and explicitly unignore archived copies while keeping future root drafts ignored
- Align `docs/guide-building-agent-skills.md` with catalog conventions (`docs/README.md`, suite nesting, skill-creator CLI paths)

### Other
- **chore(skills)**: trim SKILL.md files under 500-line limit (#67)

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.15.0...v2.0.0

## v1.15.0 — 2026-07-03

### New Skills
| Skill | Version |
|-------|---------|
| security-setup | 1.3.2 |
| website-cloner | 1.1.0 |
| website-analyzer | 1.0.1 |
| website-clone-report | 1.0.0 |
| website-improvement-prd | 1.0.0 |
| website-implementation-plan | 1.0.0 |
| website-builder | 1.0.0 |
| website-clone-final-report | 1.0.0 |
| tmux-agent-comms | 1.3.0 |
| viral-product-evaluator | 1.1.0 |
| clean-code | 1.2.0 |
| subagent-creator | 1.0.1 |
| landing-page-generator | 1.1.3 |

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.4.1 → 2.5.0 |
| opencode-runner | → 1.4.0 |
| idea-validator | 1.3.1+ (OSS competitor research) |
| seo-ai-optimizer | 1.1.2+ (quality floor) |
| agent-config | 1.2.0 → 1.3.0 |
| dont-make-me-think | 1.2.1 (restored; replaces usability-review alias) |

### Repo Structure
- **Catalog GitHub Pages**: Added a public landing page for the Agent Skills catalog with Precision Plug UI/UX; README updated to reflect the full skill inventory. (#61)
- **website-cloner suite**: Six phase skills live under `skills/website-cloner/<name>/` with the umbrella orchestrator at `skills/website-cloner/`; installer discovery walks one extra directory level so umbrellas and children install independently. Layout documented in website-cloner 1.1.0. (#43, #44, #28–#41)
- **dont-make-me-think restored**: Original skill name and directory restored; improved `usability-review` content preserved; duplicate `usability-review` removed. (#47)
- **Skill removals**: Removed `etf-evaluator` (shipped HTML report in #59, then dropped from catalog) and `quick-healthy-recipes` from the catalog.
- **Gitignore**: Ignore local per-vendor AI tool config/scratch folders and local agent skill folders. (#56, a63f320)

### Features
- **security-setup**: Local-first pre-commit security (secrets, dependencies, static analysis), file-aware staged scoping (1.3.0), cross-platform runner, optional Socket Firewall install aliases (1.3.2), and extensive parser/CI/bypass hardening. (#24, #25, #27)
- **website-cloner**: Six-phase orchestrator (analyze → report → PRD → plan → build → final report) with sibling phase skills for cloning and improving sites via Vite/React/shadcn/Tailwind and GitHub Pages. (#28–#41, #45)
- **tmux-agent-comms**: Spawn and message CLI agents in tmux with delivery verification, anti-deadloop bounds, bounded-tail reads, reply deltas, and fleet broadcast. (#48, #52; closes #49–#51)
- **viral-product-evaluator**: Virality Score (/100) and prioritized fixes from 32 viral-product principles over codebase + landing page. (#55)
- **clean-code**: bbv Clean Code Cheat Sheet audit producing `CLEAN_CODE_AUDIT.md` and optional offline HTML report; plan-only, no source edits. (#58)
- **subagent-creator**: Create, evaluate, or improve Claude Code subagent `.md` definitions with rubric, templates, and frontmatter schema aligned to official docs. (#62)
- **landing-page-generator**: Conversion-focused copy (PAS, AIDA, StoryBrand) for heroes, CTAs, and sales pages. (#60)
- **release-manager**: `landing-page-updater` subagent in release fan-out for marketing pages; reviewer checks cross-agent file collisions.
- **opencode-runner**: Restored skill; model picker, pre-run confirm, low-token monitor; A-grade pass via skill-auto-improver.
- **idea-validator**: Requires live open-source competitor research in validation flow.
- **skill-auto-improver**: Four catalog skills brought through both validation gates to meet asm-eval 85/8 floor. (#63, closes #64)

### Bug Fixes
- **install.sh / remote-install.sh**: `copy_skill_files` skips nested directories that contain their own `SKILL.md`, fixing duplicate installs when selecting website-cloner umbrella plus children. (#43)
- **security-setup**: Root-level glob matching for staged path scoping; `--staged-only` exits 2 on empty index; bypass documents `git commit --no-verify` flow; parser and `tool_error` handling fixes (1.3.0 → 1.3.2).
- **seo-ai-optimizer**: Context efficiency and safety fixes to clear quality floor. (#23, #26)

### Documentation
- **agent-config**: CLAUDE.md verification checklist (1.3.0).
- **tmux-agent-comms**: Popular Use Cases in human README. (#54)
- **CLAUDE.md**: Added what-not section for catalog contributors.
- **README**: Full catalog sync and suite-folder convention.

### Other
- **agent-config / catalog**: Added root `CLAUDE.md` and `AGENTS.md` for the skills repo (0cf2ea7).

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.14.0...v1.15.0
## v1.13.0 — 2026-04-28

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.4.0 → 2.4.1 |
| devops-pipeline | 2.0.0 → 2.0.1 |
| idea-validator | 1.3.0 → 1.3.1 |
| readme-to-landing-page | 2.0.0 → 2.1.0 |
| install-script-generator | 2.0.0 → 2.1.0 |
| excalidraw-generator | 1.2.1 → 1.3.0 |
| frontend-design | 1.2.1 → 1.2.2 |
| ollama-optimizer | 1.0.3 → 1.0.4 |
| seo-ai-optimizer | 1.1.1 → 1.1.2 |
| logo-designer | 1.2.0 → 1.2.1 |
| code-review | 1.1.3 → 1.1.4 |
| code-optimizer | 1.3.0 → 1.3.1 |
| docs-generator | 1.2.2 → 1.2.3 |
| cli-builder | 1.0.2 → 1.0.3 |
| auto-push | 1.0.1 → 1.0.2 |
| brand-name-checker | 1.2.1 → 1.3.0 |
|aso-marketing | 1.1.0 → 1.2.0 |
| agent-config | 1.1.0 → 1.2.0 |
| appstore-review-checker | 1.1.0 → 1.2.0 |
| oss-ready | 1.1.0 → 1.2.0 |
| prd-generator | 1.3.0 → 1.3.1 |
| readme-to-landing-page | 2.0.0 → 2.1.0 |
| tad-generator | 1.2.0 → 1.3.0 |
| tasks-generator | 1.2.0 → 1.2.1 |
| usability-review | 1.1.0 → 1.2.0 |
| test-coverage | 1.2.2 → 1.2.3 |
| slop-cleanup | 1.1.0 → 1.1.1 |

### Features
- **quality improvements**: Improve 27 skills past the 85/8 quality floor
- **skill-creator**: Address context budget warning, clarify two entry paths, add xhigh effort value, nest version under metadata, add metadata.author to init template, add mandatory frontmatter audit
- **release-manager**: Expand trigger description and sync catalog version
- **slop-code**: Add codebase cleanup skill with 8 parallel subagents
- **idea-validator**: Add competitive landscape research phase
- **devops-pipeline**: Shift-left testing — maximize pre-commit coverage, lean CI
- **excalidraw-generator**: Use hand-writing font as default, remove all color/theme bias

### Bug Fixes
- **skills**: Quote YAML values with colons and bump patch versions
- **skill-creator**: Add YAML frontmatter safety rule to prevent colon-in-value parse errors
- **skills**: Move README.md to docs/ and add AI-skip notice

### Refactoring
- **skills**: Remove deprecated skills and note-taker from shared skills repo
- **skills**: Add negative-trigger clauses and fix frontmatter

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.12.0...v1.13.0

### Skills Renamed
| Old name | New name | Reason |
|----------|----------|--------|
| dont-make-me-think | usability-review | Action-oriented and searchable; matches description |
| name-checker | brand-name-checker | Disambiguates from generic "name" (variable, file, etc.) |
| slop-code | slop-cleanup | Verb form matches the action (cleanup, not "code that is slop") |
| system-design | tad-generator | Aligns with sibling `prd-generator`/`tasks-generator` chain |

All four skills bumped to a minor version (renaming is a breaking change for invocation but internal behavior is unchanged).

## v1.12.0 — 2026-03-25

### Features
- **subagent architecture**: Add pattern-based subagent specifications for 11 HIGH priority skills
- **skill-creator, release-manager**: Add comprehensive subagent architecture guidance and restructure for multi-agent workflows

### Documentation
- Update adoption plan with documentation completion status
- Fix skill documentation consistency and completeness

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.11.0...v1.12.0

## v1.11.0 — 2026-03-22

### Features
- **skill-creator**: add optional effort level to skill frontmatter
- **readme-to-landing-page**: v2.0.0 with copy-paste friendly code blocks
- **effort levels**: add colored effort badges to all 35 skills in README
- **product planning**: set all planning skills to max effort (idea-validator, name-checker, prd-generator, system-design, tasks-generator)

### Documentation
- Rewrite README as skill catalog with category index and copy-paste install commands

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.10.0...v1.11.0

## v1.10.0 — 2026-03-21

### New Skills
| Skill | Version |
|-------|---------|
| dont-make-me-think | 1.1.0 |

### Features
- **dont-make-me-think**: Usability review and redesign skill based on Steve Krug's "Don't Make Me Think" principles — evaluates UIs through 10 lenses, produces concise visual reports with mermaid scorecard charts, issue maps, flow diagrams, and prioritized fix tables

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| skill-creator | 1.0.1 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.9.0...v1.10.0

## v1.9.0 — 2026-03-20

### New Skills
| Skill | Version |
|-------|---------|
| opencode-runner | 1.2.0 |
| appstore-review-checker | 1.0.0 |

### Features
- **opencode-runner**: Delegate coding tasks to opencode using free cloud models with automatic model selection (minimax > kimi > glm > MiMo > Big Pickle), mandatory process cleanup, and progress monitoring
- **appstore-review-checker**: Audit apps against Apple's App Store Review Guidelines
- **name-checker**: Add package registry checks (npm, PyPI, Homebrew, apt) for comprehensive name availability

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| name-checker | 1.0.1 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.8.0...v1.9.0

## v1.8.0 — 2026-03-20

### Features
- **excalidraw-generator**: adopt dark neon theme and Helvetica font for all diagrams

### New Skills
| Skill | Version |
|-------|---------|
| github-issue-creator | 1.0.0 |

### Documentation
- Add installation instructions (npx + asm) to all 32 skill READMEs
- Fix asm install command format to `github:luongnv89/skills:skills/<name>`

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.1.1 → 1.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.7.0...v1.8.0

## v1.7.0 — 2026-03-18

### Features
- Add **readme-to-landing-page** skill — transform any project README into a persuasive, landing-page-structured markdown using proven copywriting frameworks (PAS, AIDA, StoryBrand) @luongnv89

### Bug Fixes
- **logo-designer**: update default brand palette to dark theme with neon green accent (#0A0A0A, #111111, #262626, #A1A1A1, #FAFAFA, #00FF41) and Inter font
- **README**: add missing readme-to-landing-page skill entry

### Documentation
- Rewrite README as a landing page with PAS copywriting framework

### Other Changes
- Add GitHub issue template for new skill proposals
- Add `.gstack/` and `*-workspace/` to .gitignore

### New Skills
| Skill | Version |
|-------|---------|
| readme-to-landing-page | 1.0.0 |

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| logo-designer | 1.1.0 → 1.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.2...v1.7.0

## v1.6.2 — 2026-03-18

### Bug Fixes
- **skill audit**: comprehensive quality audit and fix across all 30 skills @luongnv89
  - Remove embedded test/validation sections from seo-ai-optimizer and vscode-extension-publisher SKILL.md (91 lines of non-runtime content)
  - Remove dangling script references in idea-validator and note-taker
  - Remove committed `__pycache__/*.pyc` files from skill-creator
  - Fix auto-push README diagram contradicting no-confirmation behavior
  - Trim overly long descriptions on 8 skills (release-manager, excalidraw-generator, drawio-generator, aso-marketing, theme-transformer, note-taker, idea-validator, prd-generator)
  - Extract `references/publishing.md` from release-manager to get body under 500 lines
  - Add missing Go, Rust, and Java language-specific checks to code-optimizer
  - Standardize repo sync block to canonical full form across 6 skills (aso-marketing, release-manager, ollama-optimizer, name-checker, context-hub, code-review)
  - Add explicit read-on-demand cues for reference files (code-review, openspec-task-loop, prd-generator)
  - Fix README resource tables to list specific files (system-design, tasks-generator, code-review, devops-pipeline)
  - Fix name-checker "CRITICAL: STOP" wording to actionable skip instruction
  - Remove decorative padding sections (agent-config Notes, system-design Design Principles)
  - Fix logo-designer conflicting design principles (no gradients vs shadows)
  - Remove motivational non-instructional line from frontend-design
  - Clarify docs-generator commit behavior and branch detection
  - Move drawio-generator "Advantages Over Excalidraw" to README
  - Collapse excalidraw-generator redundant JSON section to pointer
  - Clarify ollama-optimizer output path and benchmark expectations
  - Add missing branch creation step to oss-ready README diagram
  - Add read-on-demand cues for unreferenced files in skill-creator

### Skills Updated (30 files changed, -227 lines net)
| Skill | Change |
|-------|--------|
| agent-config | Remove filler Notes section |
| aso-marketing | Trim description, standardize repo sync |
| auto-push | Fix README diagram |
| cli-builder | (no content change — reviewed, passed) |
| code-optimizer | Add Go/Rust/Java checks, rename Step 0 |
| code-review | Standardize repo sync, read-on-demand cue, fix README |
| context-hub | Standardize repo sync |
| devops-pipeline | Fix README resource table |
| docs-generator | Clarify branch detection and commit behavior |
| drawio-generator | Trim description, remove Advantages section |
| excalidraw-generator | Trim description, collapse redundant section |
| frontend-design | Remove motivational line |
| idea-validator | Trim description, remove missing script ref |
| logo-designer | Fix conflicting design principles |
| name-checker | Standardize repo sync, fix STOP wording |
| note-taker | Trim description, remove missing script ref |
| ollama-optimizer | Standardize repo sync, clarify output/benchmark |
| openspec-task-loop | Add read-on-demand cue |
| oss-ready | Fix README diagram |
| prd-generator | Trim description, add read-on-demand cue |
| release-manager | Trim description, standardize repo sync, extract publishing to references/ |
| seo-ai-optimizer | Remove embedded test cases |
| skill-creator | Remove __pycache__, add reference cues |
| system-design | Remove Design Principles padding, fix README |
| tasks-generator | Fix README resource table |
| theme-transformer | Trim description |
| vscode-extension-publisher | Remove embedded test cases |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.1...v1.6.2

## v1.6.1 — 2026-03-18

### Bug Fixes
- **skill consistency**: audit and fix skill consistency issues across 4 skills @luongnv89
  - excalidraw-generator: add missing metadata.version, fix README mermaid check count (9 → 10)
  - drawio-generator: add missing metadata.version
  - cli-builder: replace non-standard README sections with standard Output
- **SKILL.md frontmatter**: migrate from unsupported `version:` attribute to valid `metadata.version` across all 30 skills @luongnv89
  - Add `license: MIT` and `metadata.creator` to every skill
  - Valid frontmatter attributes now: argument-hint, compatibility, description, disable-model-invocation, license, metadata, name, user-invocable

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.1.0 → 1.1.1 |
| drawio-generator | 1.0.0 → 1.0.1 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.6.0...v1.6.1

## v1.6.0 — 2026-03-18

### Features
- Add **drawio-generator** skill — generate diagrams and visualizations as draw.io (diagrams.net) XML files with a 4-phase workflow (Understand → Propose → Generate → Validate) @luongnv89
  - Supports **25+ diagram types**: flowcharts, C4 models, ER diagrams, swimlanes, architecture, and more
  - **Multi-page support** — multiple C4 levels or related diagrams in a single `.drawio` file
  - **9 automated quality checks**: XML validation, required attributes, unique IDs, edge bindings, overlap detection, container hierarchy, semantic completeness, text readability
  - Native `.drawio` output compatible with diagrams.net, VS Code, Confluence, and Jira
  - Comprehensive reference docs for draw.io XML schema, shapes, styles, and color palettes

### Bug Fixes
- **excalidraw-generator**: fix text rendering — add Check 10 (shape-to-text size fit), require `autoResize: true` and `lineHeight: 1.25`, boundary labels must be standalone text
- **excalidraw-generator**: default output changed to `.excalidraw` (raw JSON) instead of `.excalidraw.md`

### New Skills
| Skill | Version |
|-------|---------|
| drawio-generator | 1.0.0 |

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| excalidraw-generator | 1.0.0 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.5.0...v1.6.0

## v1.5.0 — 2026-03-17

### Features
- Add **excalidraw-generator** skill — generate diagrams, charts, and visualizations as valid Excalidraw JSON with a 4-phase workflow (Understand → Propose → Generate → Validate) @luongnv89
  - Supports **25+ diagram types** across 8 categories: flowcharts, architecture, ER diagrams, mind maps, sequence diagrams, Gantt charts, Kanban boards, SWOT analysis, wireframes, and more
  - **9 automated quality checks** with auto-fix: JSON validation, required fields, unique IDs, two-way text/arrow bindings, overlap detection, semantic completeness, readable text
  - Selectable **color palettes** (Professional, Pastel, Monochrome) and **rendering styles** (Hand-drawn, Clean, Sketchy)
  - Outputs `.excalidraw.md` (Markdown with code block) by default, or raw `.excalidraw` files
  - Comprehensive reference docs for Excalidraw JSON schema and all diagram type layouts

### New Skills
| Skill | Version |
|-------|---------|
| excalidraw-generator | 1.0.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.4.0...v1.5.0

## v1.4.0 — 2026-03-17

### Features
- Add **store policy compliance checking** to aso-marketing skill — validates all proposed metadata against Apple App Store Review Guidelines (2.3.7, 2.3.8, 5.2.1) and Google Play metadata policies before submission @luongnv89
  - New **Phase 3: Policy Compliance Check** — scans for prohibited keywords, trademark/competitor brand violations, formatting issues, and content accuracy
  - Comprehensive **prohibited keyword lists** for both stores (e.g., "free", "best", "#1", "top", "download now")
  - **Trademark protection** — prevents competitor brand names from leaking into proposed metadata
  - Policy compliance integrated into Review (Phase 5), Verify (Phase 6), and Summary Report (Phase 7)
  - New **Store Policy Compliance** section in best practices reference with universal comparison table
  - Updated evals with policy compliance assertions

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| aso-marketing | 1.0.0 → 1.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.3.0...v1.4.0

## v1.3.0 — 2026-03-17

### Features
- Add **aso-marketing** skill — full-lifecycle App Store Optimization for mobile apps covering both Apple App Store and Google Play with keyword strategy, metadata optimization, conversion improvement, and localization @luongnv89
- Add **Skill Management** section to README referencing [agent-skill-manager](https://github.com/luongnv89/agent-skill-manager) (`asm`) for managing skills across all AI coding agents @luongnv89
- Add Marketing phase to the workflow diagram and skill tables @luongnv89

### New Skills
| Skill | Version |
|-------|---------|
| aso-marketing | 1.0.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.2.0...v1.3.0

## v1.2.0 — 2026-03-13

### Features
- Add "Install All" tools option to install.sh and remote-install.sh with shared `.agents/skills/` + symlinks @luongnv89
- Add remote installer and update README with all installation methods @luongnv89
- Add Step 6 (Update Documentation) and Step 10 (Publish to PyPI/npm) to release-manager skill @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.1.0 → 2.2.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.3...v1.2.0

## v1.1.3 — 2026-03-11

### Bug Fixes
- Update release-manager to use CHANGELOG.md instead of RELEASE_NOTES.md @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 2.0.0 → 2.1.0 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.2...v1.1.3

## v1.1.2 — 2026-03-11

### Bug Fixes
- Audit and fix frontmatter, repo-sync, and hardcoded paths across 15 skills (38a74c4) @luongnv89

### Skills Updated
| Skill | Change |
|-------|--------|
| cli-builder | Added `version: 1.0.0`, fixed multi-line description |
| install-script-generator | Fixed multi-line description |
| release-manager | Fixed multi-line description |
| auto-push | Added `version: 1.0.0` |
| context-hub | Added `version: 1.0.0` |
| theme-transformer | Added `version: 1.0.0`, removed unnecessary YAML quoting |
| oss-ready | Added missing H1 title |
| seo-ai-optimizer | Added missing Repo Sync Before Edits section |
| skill-inventory-auditor | Added missing Repo Sync Before Edits section |
| idea-validator | Replaced hardcoded paths/URLs with dynamic resolution |
| prd-generator | Replaced hardcoded paths/URLs with dynamic resolution |
| tasks-generator | Replaced hardcoded paths/URLs with dynamic resolution |
| system-design | Replaced hardcoded GitHub URL with dynamic resolution |
| ollama-optimizer | Removed stale generated output file |
| skill-creator | Standardized README.md to match catalog template |

### README
- Updated version table to match actual SKILL.md versions
- Added missing cli-builder and vscode-extension-publisher entries

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.1...v1.1.2

## v1.1.1 — 2026-03-11

### Bug Fixes
- Require single-line description in skill-creator for correct external parsing (3fde564) @luongnv89

### Skills Updated
| Skill | Change |
|-------|--------|
| skill-creator | Added single-line description validation in SKILL.md guide and quick_validate.py |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.1.0...v1.1.1

## v1.1.0 — 2026-03-11

### Features
- Rename release-notes to **release-manager** with full release automation (2cf22aa) @luongnv89
- Add **skill-inventory-auditor** for finding and removing duplicate skills (d7cb4dd) @luongnv89

### Bug Fixes
- Enforce standard compliance across 6 skills — added repo sync and reference sections (1376208) @luongnv89

### Skills Updated
| Skill | Version Change |
|-------|---------------|
| release-manager | 1.0.0 → 2.0.0 (renamed from release-notes) |
| skill-inventory-auditor | New — 1.0.0 |
| code-review | 1.0.0 → 1.0.1 |
| name-checker | 1.0.0 → 1.0.1 |
| ollama-optimizer | 1.0.0 → 1.0.1 |
| seo-ai-optimizer | 1.0.0 → 1.0.1 |
| skill-creator | 1.0.0 → 1.0.1 |

**Full Changelog**: https://github.com/luongnv89/skills/compare/v1.0.0...v1.1.0

## v1.0.0 — Initial Release

First stable release with 20+ skills for AI agents.
