# Loop Protocol — /issue-work-loop

This file is authoritative for mode-specific state, GitHub evidence, push safety, and parse rules. Load it only after selecting **ISSUE** or **PR** mode.

## Mode state machines

```text
ISSUE
PREFLIGHT → SPAWN_IMPL → RESOLVE → SPAWN_REV → LOOP
LOOP: REVIEWER_GATE → REFRESH_HEAD → REVIEW
      CLEAN → SWEEP
      FINDINGS + rounds left → IMPLEMENTER_GATE → FIX → VERIFY_SAME_PR_NEW_SHA → LOOP
      FINDINGS + no rounds left → SWEEP(MAX_ROUNDS)

PR
PREFLIGHT → SPAWN_REV → LOOP
LOOP: REVIEWER_GATE → REFRESH_HEAD → REVIEW
      CLEAN → SWEEP                         # no FIXER
      FINDINGS + rounds left → PUSH_SAFETY
          unsafe/unknown → SWEEP(FAILED_HANDOFF)  # no FIXER, no push
          safe → LAZY_SPAWN_FIXER → FIXER_GATE → FIX_IN_ISOLATED_WORKTREE
                 → VERIFY_SAME_PR_NEW_SHA → LOOP
      FINDINGS + no rounds left → SWEEP(MAX_ROUNDS)
```

Terminal outcomes: `CLEAN | MAX_ROUNDS | FAILED | ALREADY_RESOLVED`. ISSUE preserves `ALREADY_RESOLVED`; PR does not invent that outcome for a closed or missing PR.

## Input resolution

- Bare positive number: ISSUE.
- `--pr M` or `pr M`: PR.
- Natural language explicitly asking to review **and fix** an existing PR until clean: PR.
- Review-only/no-fix request: do not trigger this workflow.
- Both issue `N` and PR `M`: inspect PR links. If `N` is absent, stop with `Issue/PR mismatch`; if present, run PR mode and retain all linked issues.

## ISSUE preflight and linked open PRs

Confirm the issue is OPEN, then find open PRs linked by GitHub closing references or closing keywords in PR title/body. Search candidates broadly, but only retain evidence-backed links.

| Count | Action |
|---|---|
| 0 | Continue ISSUE mode and spawn implementer |
| 1 | Ask exactly once whether to switch to PR mode on that PR. Accept → PR preflight/reviewer-first flow. Decline → abort. Never create a second PR |
| 2+ | Stop with ambiguous-PR error before spawning any worker |

## PR identity query and fallback

Try the rich query first:

```bash
gh pr view {M} --json \
number,url,title,body,state,headRefName,headRefOid,headRepository,headRepositoryOwner,isCrossRepository,maintainerCanModify,closingIssuesReferences
```

Require `number`, `url`, `state`, `headRefName`, and a head SHA. State must be exactly `OPEN`.

GitHub CLI versions expose different optional fields. If the rich query fails because a field is unavailable:

1. Print the optional-field fallback warning.
2. Retry core identity:

   ```bash
   gh pr view {M} --json number,url,title,body,state,headRefName,headRefOid
   ```

3. If `headRefOid` is unavailable, retry with `commits` and derive the newest commit OID:

   ```bash
   gh pr view {M} --json number,url,title,body,state,headRefName,commits
   ```

4. Query supported optional fields individually, or use authenticated `gh api graphql`/REST for equivalent facts. Record unavailable `headRepositoryOwner`, `headRepository`, `isCrossRepository`, or `maintainerCanModify` as `unknown`.
5. Unknown identity/head is fatal. Unknown push-safety facts are not fatal to review, but they make PR-mode fixing unsafe until independently proven.

Record immutable run keys before worker spawn:

```text
pr_number, pr_url, pr_title, head_ref, head_sha,
head_repository, head_repository_owner,
is_cross_repository, maintainer_can_modify
```

## Linked-issue evidence in PR mode

Linked issue is optional. Build a de-duplicated, numerically sorted set from:

1. GitHub `closingIssuesReferences` (or equivalent API closing-reference data).
2. Case-insensitive closing-keyword evidence in PR title/body:

   ```regex
   \b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#(\d+)\b
   ```

Do not count arbitrary `#N` mentions without closing evidence. Do not infer a canonical issue from branch names, commit text, or prose. Keep all linked numbers:

```text
issue_context: none
issue_context: #42
issue_context: #42,#77
```

If an issue was explicitly supplied with the PR, it must appear in this set. Additional linked issues remain in context.

## ISSUE PR creation and validation

The initial implementer runs `/issue-resolver N --auto`. Prefer structured `pr_number` and `pr_url`, then validate:

```bash
gh pr view {M} --json number,url,state,title,body,headRefName,headRefOid,closingIssuesReferences
```

If the report omits a PR number, search open PRs and apply the same GitHub/closing-keyword link evidence. Prefer a reported branch match only among evidence-backed candidates. Zero matches is FAILED; multiple matches is ambiguous. Record `head_ref` and `head_sha` from GitHub, not only worker output.

### Already resolved (ISSUE only)

If the implementer authoritatively returns `already_resolved`:

| Linked open PR count | Action |
|---|---|
| 0 | `ALREADY_RESOLVED`; no reviewer or writer |
| 1 | Ask the same existing-PR confirmation. Accept → switch to the full PR reviewer→lazy-FIXER mode; decline → abort |
| 2+ | Stop ambiguous |

A missing PR is a failure only when the implementer status is not `already_resolved`.

## ROUND counter and current-head gate

- `round = 1` for the first review after an open PR is known.
- Initial ISSUE resolve is ROUND 0 and does not count.
- A ROUND counts when REVIEW completes. Its fix, if any, belongs to that ROUND.
- Default `max_rounds = 5`; minimum 1.

Immediately before every REVIEW, refresh:

```bash
gh pr view {M} --json number,state,headRefName,headRefOid
```

Require OPEN, the same PR number, and expected head branch. Send the refreshed SHA to the reviewer. Reviewer must return `reviewed_head_sha: <sha>` equal to that value. If the head changes before/during review, discard stale results and restart that ROUND against the new SHA without consuming an extra ROUND.

## CLEAN and FINDINGS (strict)

CLEAN requires all three:

1. `VERDICT: CLEAN`
2. Zero numbered findings/notes/partials
3. `reviewed_head_sha` equals the refreshed current PR SHA

Normalize contradictions conservatively:

- CLEAN plus any item → FINDINGS
- Both verdict lines → FINDINGS
- Soft pass with notes → FINDINGS
- Missing verdict → one verdict-only re-prompt; still missing → fail ROUND
- FINDINGS with no list → one list re-prompt; still empty → fail with a synthetic finding explaining the missing details

Normalize findings as:

```text
{i}. [severity:fix|note] [dimension] description (path or area)
```

Words such as crash/security/wrong/fail/broken default to `fix`; otherwise missing severity defaults to `note`. Notes remain actionable.

## PR push-safety gate

Run only after PR-mode FINDINGS and before spawning FIXER. Review is always allowed; fixing is not.

A PASS requires all of the following to be known and true:

1. PR remains OPEN and still has the recorded `headRefName`.
2. Exact source repository and branch are known.
3. Authenticated identity has write access to that source branch.
4. For cross-repository/fork PRs, `maintainerCanModify` is true **and** actual source-repository branch push access is independently established. Either fact alone is insufficient.
5. A non-mutating permission check succeeds, preferably a no-op `git push --dry-run <source-remote> <current-sha>:refs/heads/{headRefName}` from an isolated checkout, or an equivalent authenticated repository-permission query.
6. Branch protection/rules do not require force-push or a different branch/PR.

`false`, permission denied, unsupported verification, missing source repo, or any `unknown` result means STOP before FIXER spawn. Print `Push unavailable or uncertain` with PR URL, current SHA, FINDINGS, and a human handoff. Never "try the push and see" after edits.

## PR FIXER isolation and branch contract

Spawn FIXER lazily only after push-safety PASS, default pane `fix-{M}`. The leading role word in every task is **FIXER**.

Require a dedicated non-primary git worktree. The worktree must:

- live outside the primary checkout;
- fetch the PR source branch from its source repository;
- start at the expected pre-fix `head_sha`;
- check out only the PR `headRefName` (or a local tracking ref that pushes explicitly to it);
- be recorded in `worktree_paths_seen` for SWEEP.

Before editing, compare worktree HEAD and current GitHub `headRefOid` to expected SHA. On mismatch, stop, refresh findings, and re-review. FIXER may modify only this worktree and scope changes to FINDINGS.

Push rules: ordinary non-force push only, explicit source remote and `HEAD:refs/heads/{headRefName}`. Never push to the base repository branch by assumption. Never open/close/merge a PR.

## Fix success and same-PR verification

ISSUE implementer fixes and PR FIXER fixes both require:

- `status: success`
- relevant tests reported (`tests_run: none` is allowed only with no test harness and an explanation)
- no remaining blocker concealed
- new SHA different from pre-fix SHA; if no commit is needed, stop with a handoff instead of claiming a pushed fix

After push, query GitHub—not the worker—as authority:

```bash
gh pr view {M} --json number,url,state,headRefName,headRefOid
```

Require same PR number, OPEN state, same `headRefName`, and a new `headRefOid`. Otherwise stop; do not open another PR or force-push. The next review uses this new SHA.

One automatic retry of the same FINDINGS is allowed only after the applicable writer is FRESHENed for high context; otherwise stop FAILED.

## Context gates

Follow `references/context-gate.md`:

- reviewer: every ROUND start;
- ISSUE implementer: immediately before every fix;
- PR FIXER: immediately before every fix after it exists; first lazy spawn is fresh.

Never gate/spawn a writer before a CLEAN exit or before PR push-safety PASS.

## Selective worker launch-profile gate

This gate runs before **every** Herdr worker launch: the initial ISSUE
implementer/resolver, each reviewer, an ISSUE resolver retry or fix worker, the
PR FIXER, and every retry or FRESHEN replacement. A fresh pane or a restarted
CLI never inherits a previous profile check.

Dependency Preflight records `herdr_agent_dir` as the absolute installed
`herdr-agent` directory. Carry that value into this phase; do not derive it
from the repository checkout or invent a repo-relative fallback. Define the
helper directory and fail before any worker launch if it is missing:

```bash
here=""
if [ -n "${herdr_agent_dir:-}" ] && [ -d "$herdr_agent_dir/scripts" ]; then
  here="$(cd -- "$herdr_agent_dir/scripts" 2>/dev/null && pwd -P)"
fi
[ -n "$here" ] && [ -f "$here/launch_profile.py" ] || {
  echo "Error: installed herdr-agent launch_profile.py is missing; refusing to launch a worker" >&2
  exit 1
}
```

Resolve and verify the profile with the **exact** kind, model, thinking level,
native arguments, cwd, environment, and worker configuration intended for the
worker's `--start` call. Keep the same inputs for both calls; if any input
changes, discard the old result and resolve again. For example, the profile
probe and start share the same `worker_profile_args` and `worker_native_args`
Bash arrays. Populate these from the actual worker launch request: helper
kind/model/thinking options in the former, native arguments in the latter
(an empty array when none). Do not substitute or omit supplied values.

```bash
profile_args=(
  --root-pane "$root_pane"
  --main-model "$main_model" --main-thinking "$main_thinking"
  "${worker_profile_args[@]}" --without bypass
)
profile_json="$(python3 "$here/launch_profile.py" \
  "${profile_args[@]}" -- "${worker_native_args[@]}")" || {
  echo "Error: worker launch profile failed; refusing to launch" >&2
  exit 1
}
```

The helper's `flags` and `explicit` JSON entries are names only; they cannot
prove native permission values or the worker's effective config/settings or
environment. Independently inspect those values in the same worker cwd,
configuration, and environment, and require any supplied kind/model/thinking
value to match the profile's effective value (or verify the expected inherited
source when the override is empty). Reject unmapped or unknown permission
profiles and malformed, missing, or failed profile data. Require `without` to
contain `bypass` but not blanket `flags`, and require empty inherited
`profile.bypass`; that field is an **inherited-only** summary, so
`profile.bypass: []` is **not** proof that explicit native, config, or
environment bypass is absent. Explicit native, config, and environment bypass
is prohibited too. Unknown or unverifiable effective profile data fails closed
before `herdr agent start`, with no native/unverified fallback, including
retry and replacement launches. Reject skip-permissions switches,
`--permission-mode bypassPermissions`, Pi `--approve`, Codex dangerous
full-access/never-approval settings, and equivalent bypasses supplied through
native arguments or configuration. Preserve restrictive inherited setup flags;
never substitute `--without flags` or override restrictive settings to get past
a blocked launch. Report the blocked worker and the unverifiable source, without
printing credential-bearing values.

Only after all checks above PASS, start with the same verified inputs:

```bash
python3 "$here/launch_profile.py" "${profile_args[@]}" \
  --start "$worker_name" --pane "$worker_pane" --timeout 60000 \
  -- "${worker_native_args[@]}" || {
  echo "Error: worker start rejected after profile verification" >&2
  exit 1
}
```

This is caller-side policy only: do not change `herdr-agent` defaults or its
launch-profile contract.

## Autonomous worker boot gate

Every newly launched or FRESHENed reviewer, ISSUE implementer, and PR FIXER must pass this gate before receiving role work:

1. Launch the configured interactive CLI **bare** — only its own verified flags (e.g. `pi` or `pi --thinking high`) — and complete the readiness wait. Do not pass auto-mode startup parameters: even where a harness exposes a mode flag, the post-boot switch below is the verified mechanism this skill relies on.
2. Apply the per-harness switch:

   | Launcher | Startup | Switch after boot | Verify and record |
   |---|---|---|---|
   | `pi` | Bare command; pass no auto-mode parameters | Nothing to activate — autonomous by default | Readiness wait passed; record `autonomous_mode: autonomous_by_default` |
   | `claude` | Plain `claude` | Send the Shift+Tab keystroke (`herdr pane send-keys`, not a text message) until the auto-accept-edits mode is selected | Bounded pane read shows the auto-accept-edits mode indicator; record `autonomous_mode: verified` |
   | `opencode` | Plain `opencode` | Press Tab (or the configured `switch_agent` keybind) to select the full-permission Build agent; settings are the documented alternative | Bounded pane read shows the Build agent selected; record `autonomous_mode: verified` |

3. Never send an auto-mode slash command. Never use `--dangerously-skip-permissions` or `--allow-dangerously-skip-permissions`; the mode switch above is the working mechanism.
4. For any other CLI, autonomy is unknown — fail closed with the autonomous-mode error rather than improvising startup flags.
5. FRESHEN clears the recorded mode state, so the replacement session must pass the gate again.

Do not count mode activation as a ROUND. Do not send the worker task in the same input as the mode switch; a prompt-level request to act autonomously is not verification.

## Herdr send/wait contract

For every probe, resolve, review, fix, or parse re-prompt (autonomous-mode switches are keystrokes verified by bounded pane reads, not message sends):

1. Capture recent-unwrapped baseline.
2. Mint a fresh completion marker.
3. Run `preflight_send.py` immediately before `pane run`.
4. Wait with `wait_for_idle.py` using baseline + marker.
5. Read reply delta only.

Blocked/trust dialog: surface it; never send another task or type into the dialog.

## Max rounds and handoff

At `max_rounds` with FINDINGS: outcome `MAX_ROUNDS`, preserve findings verbatim, leave PR open, run SWEEP, and hand off USER-MERGE. Do not imply the PR is clean.

SWEEP is mode-aware: ISSUE may own implementer/reviewer and issue-resolver worktrees; PR owns reviewer plus optional FIXER and its isolated worktree. A CLEAN-first PR run has no FIXER artifacts. See `references/cleanup.md`.
