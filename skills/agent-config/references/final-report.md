# Final Report

Print this report at the end of every run, after the last step report. A run that stops early, for example at Repo Sync or a declined draft, still ends with it.

## Four parts, in this order

1. `Result:` with one status at the start of the line, then what changed or was found:
   - `COMPLETE` — write: every file was written and every Step 4 verify check passed. Audit: every checklist item was reported and `git status` is unchanged.
   - `PARTIAL — <reason>` — write: a file was written, but a Step 4 check still fails after one fix, or a command was left out because no manifest or CI defines it. Audit: a file in the audit set could not be read, so its items are unverified.
   - `BLOCKED — <reason>` — nothing was written: the user declined the draft or diff, a Repo Sync stop condition is unresolved, or the target path cannot be resolved.
2. `Evidence:` only the checks that actually ran, each with its observed result: the shadow-check output, `wc -l` per file, the `## Token Efficiency` count, the wrapper's first line, and the files written. An audit names the checklist file and its pass, fail, and N/A counts.
3. `Uncertainty:` what was not verified. A write run always lists that the client load was not observed, with the confirm command from Step 4 (`/memory` in Claude Code, the `codex` summary prompt). Label inferences, such as a command read from CI but never run, as inferences.
4. `Decision:` the action still waiting on the user, such as approving the diff, answering a missing command, or moving a CLAUDE file this skill never edits. Otherwise write "No approval needed."

The audit's overall verdict (`PASS`, `PARTIAL`, or `FAIL`) is a verdict on the audited files. It stays in the audit step report; the `Result:` status above describes the run.

## Example

```
Result: COMPLETE — wrote AGENTS.md (agents-only branch)

Evidence:
- Shadow check: no CLAUDE file at or above the repo root
- wc -l AGENTS.md: 48 (under 200)
- grep -c '^## Token Efficiency' AGENTS.md: 1
- Commands read from package.json and .github/workflows/ci.yml

Uncertainty:
- The client load was not observed; run /memory in Claude Code to confirm AGENTS.md is listed
- The single-test command is an inference from the vitest config; it was not run

Decision: No approval needed.
```

A run where the user declined the diff ends like this:

```
Result: BLOCKED — diff not approved, nothing written

Evidence:
- Shadow check: CLAUDE.md in the repo root, no @AGENTS.md import (migrate branch)
- Draft diff shown for AGENTS.md and CLAUDE.md

Uncertainty:
- Step 4 checks not run, because no file was written

Decision: Approve the diff, or name the lines to change, to write the files.
```

## Reader checks

Grade the report against these checks:

- The opening line states the result and its status, so the reader finds the outcome without reading the step reports.
- Verified facts name the check that observed them. Unverified items and inferences appear under `Uncertainty`, not as facts.
- Each claim matches its evidence: a file that was written is not reported as loaded, and a drafted diff is not reported as applied.
- `Decision:` names the pending user action, or states "No approval needed."

Without reviewer feedback, human understanding of the report stays unconfirmed. An agent's own reading does not confirm it.
