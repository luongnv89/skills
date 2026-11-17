# Edge cases

| Input | Behaviour |
|---|---|
| No URL given | Ask once for the URL; without an answer, end the run BLOCKED (see `final-report.md`) |
| `localhost`, a private IP, or a password-walled staging host | The scanner cannot reach it. Say so at gate G1, before the call, not after it fails |
| Several URLs in one request | Confirm which one; this skill scans one site per run |
| A site with zero failing checks | `render_plan.py` exits 3 and writes nothing — `/plan-to-issues` rejects a file with no task headings. Report the score and end the run, reported as a pass |
| `isCommerce: false` | P4 commerce tasks are deferred, not filed |
| Empty `.agent-ready/fixes.md` | The run degrades to the `nextLevel` prompts and the plan header carries a `**Note:**` naming every check left without the scanner's prose |
| A `neutral` check | Informational only; never becomes a task |
| A user who already has a plan | Out of scope — go straight to `/plan-to-issues <path.md>` |
| The dependency preflight misses | Stop before Phase 3; Phases 1–2 are read-only and may still be reported (PARTIAL) |
| The Phase 4 lease acquire fails | Report the written plan and end PARTIAL — filing is blocked, the plan is intact |
| The approved sync fails | Stop and ask before writing; a plan written on a partial sync is worse than none (PARTIAL if Phases 1–2 were reported) |
