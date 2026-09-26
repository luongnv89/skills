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

### Installed-helper capability gate

Dependency Preflight records `herdr_agent_dir` as the absolute installed
`herdr-agent` directory. Carry that value into this phase; do not derive it
from the repository checkout or invent a repo-relative fallback. Check the
installed helper and its supported selective option before splitting or
starting a worker:

```bash
here=""
if [ -n "${herdr_agent_dir:-}" ] && [ -d "$herdr_agent_dir/scripts" ]; then
  here="$(cd -- "$herdr_agent_dir/scripts" 2>/dev/null && pwd -P)"
fi
[ -n "$here" ] || {
  echo "Error: installed herdr-agent directory is unavailable; refusing to launch a worker" >&2
  exit 1
}
helper="$here/launch_profile.py"
[ -f "$helper" ] || {
  echo "Error: installed herdr-agent launch_profile.py is missing; refusing to launch a worker" >&2
  exit 1
}
helper_usage="$(python3 "$helper" --help 2>&1)" || {
  echo "Error: installed herdr-agent launch_profile.py --help failed; refusing to launch a worker" >&2
  exit 1
}
if ! grep -Fq -- "--without" <<<"$helper_usage" ||
   ! grep -Fq -- "bypass" <<<"$helper_usage"; then
  echo "Error: installed launch_profile.py does not support --without bypass; refusing to launch a worker" >&2
  exit 1
fi
```

A missing helper or unsupported `--without bypass` is a hard stop, not a
fallback to a repository copy, `--without flags`, a native skip-permissions
switch, or an unverified launcher.

### Probe and target evidence

Resolve and verify the profile with the **exact** kind, model, thinking level,
native arguments, destination pane, requested cwd/environment, and worker
configuration intended for the worker's `--start` call. Keep the same launch
inputs for both calls; if any input changes, discard the old result and resolve
again. For example, the profile probe and start share the same
`worker_profile_args` and `worker_native_args` Bash arrays. Populate these from
the actual worker launch request: helper kind/model/thinking options in the
former, native arguments in the latter (an empty array when none). Do not
substitute or omit supplied values.

```bash
profile_args=(
  --root-pane "$root_pane"
  --main-model "$main_model" --main-thinking "$main_thinking"
  "${worker_profile_args[@]}" --without bypass
)
profile_json="$(python3 "$helper" \
  "${profile_args[@]}" -- "${worker_native_args[@]}")" || {
  echo "Error: worker launch profile failed; refusing to launch" >&2
  exit 1
}
if ! printf '%s\n' "$profile_json" | python3 -c '
import json
import sys
try:
    profile = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
required = (
    "kind", "inherited", "model", "thinking", "flags", "flags_source",
    "without", "explicit", "bypass", "dropped", "warnings", "argc",
)
if not isinstance(profile, dict) or any(key not in profile for key in required):
    raise SystemExit(1)
if not isinstance(profile["kind"], str) or profile["kind"] not in {"claude", "pi", "codex"}:
    raise SystemExit(1)
if not isinstance(profile["inherited"], bool):
    raise SystemExit(1)
if not isinstance(profile["flags_source"], str) or profile["flags_source"] == "not mapped":
    raise SystemExit(1)
if not all(
    isinstance(profile[key], dict)
    and isinstance(profile[key].get("value"), str)
    and isinstance(profile[key].get("source"), str)
    for key in ("model", "thinking")
):
    raise SystemExit(1)
if not isinstance(profile["without"], list) or any(not isinstance(item, str) for item in profile["without"]):
    raise SystemExit(1)
if "bypass" not in profile["without"] or "flags" in profile["without"]:
    raise SystemExit(1)
if profile["bypass"] != [] or not isinstance(profile["explicit"], list):
    raise SystemExit(1)
if any(not isinstance(item, str) for item in profile["explicit"]):
    raise SystemExit(1)
if not all(isinstance(profile[key], list) for key in ("flags", "dropped", "warnings")):
    raise SystemExit(1)
if not isinstance(profile["argc"], int) or profile["argc"] < 0:
    raise SystemExit(1)
'; then
  echo "Error: worker launch profile JSON is malformed, unmapped, or not selectively filtered; refusing to launch" >&2
  exit 1
fi
```

The parser validates only the helper contract: it does not treat names only
`flags`/`explicit` or an empty inherited-only `profile.bypass` as proof that
native, configuration, or environment bypass is absent. The following evidence
boundary is mandatory before the start command:

- `herdr agent get "$root_pane"` identifies the main kind, and
  `herdr pane process-info --pane "$root_pane"` supplies the root foreground
  argv. Inspect the actual token/value pairs in memory and redact values in any
  report; inherited inline settings cannot be replaced by a JSON field name.
- Inspect every actual worker argument and every local file it names, including
  `--settings`, `--mcp-config`, `--config`, and inline JSON/config values. Keep
  only redacted provenance (for example, a path plus metadata/digest), never
  print credential-bearing content, and stop if an effective configuration
  source cannot be identified or read.
- `herdr pane split --cwd ... --env ...` creates the destination pane, while
  `herdr agent start ... --pane "$worker_pane"` launches there, not in the
  caller. The split request is launch input, not proof of the destination's
  effective cwd/environment. The helper JSON has no destination config or
  environment readback. Do not use caller `pwd`, caller environment, guessed
  paths, or an empty `profile.bypass` as target evidence.
- Use only actual local target-pane evidence from a supported Herdr response for
  destination cwd/environment. No supported `launch_profile.py` field or
  documented command supplies that readback; do not invent `herdr pane env`,
  `herdr agent config`, or an equivalent. If effective target environment or
  configuration, including inherited inline settings values, cannot be
  established from real local inspection/evidence, report the source and stop
  before `herdr agent start`:

```text
Error: worker target cwd/environment/configuration cannot be established from supported local evidence; refusing to start
```

Retain selective filtering for every launch: require `without` to contain
`bypass` but not blanket `flags`, require empty inherited `profile.bypass`, and
reject skip-permissions switches, `--permission-mode bypassPermissions`, Pi
`--approve`, Codex dangerous full-access/never-approval settings, and
explicit native/configuration/environment bypasses; every such bypass is
prohibited. Preserve restrictive inherited setup flags. Unknown or unverifiable
profile data fails closed,
including on retries and replacements, without a native/unverified fallback.

The probe is not an immutable start snapshot. Immediately before starting,
repeat `herdr agent get "$root_pane"`,
`herdr pane process-info --pane "$root_pane"`, the local configuration/source
inspection, and any supported destination-pane evidence. Re-run the helper with
the same `profile_args`, `worker_native_args`, destination pane, and recorded
launch provenance. Compare only stable, redacted source identities (root kind
and argv fingerprint, configuration path/metadata or inline-value digest, and
target pane/evidence source); never print the values. If any source changes,
discard the old profile and re-probe. If stable provenance cannot be
established, stop rather than start on stale or caller-side evidence.

Only after all checks above PASS, start with the same verified inputs:

```bash
python3 "$helper" "${profile_args[@]}" \
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

For normal worker transport, delegate to the current `herdr-agent` skill's
**Phase 4 — Prompt Safely** and **Phase 5 — Read and Verify**. Those phases are
the transport source of truth; do not reproduce an older pane protocol here.

### Detected-agent path (normal)

For every probe, resolve, review, fix, or parse re-prompt:

1. Resolve the exact target and require the installed `preflight_send.py` to
   pass immediately before dispatching the task. A working, blocked, or
   unverifiable target stops dispatch; only exit 5 permits the fallback below.
2. For a detected agent, submit and wait in one server request:
   `herdr agent prompt "$target" "$task" --wait --timeout 180000`.
3. On success, read only the relevant reply delta with
   `herdr agent read "$target" --source recent-unwrapped --lines 80`.

The normal detected-agent path does not capture a pre-send transcript baseline,
mint a completion marker, call `pane run`, or invoke `wait_for_idle.py`. A
prompt plus `--wait` is one server-side request, so do not blindly resend after
an uncertain result.

Preserve the source error mapping exactly: `agent_blocked` (BLOCKED) means
nothing was sent and a human must resolve the dialog; `agent_prompt_stalled`
(STALLED) means the prompt was submitted but no activity followed; `timeout`
(TIMEOUT) means no settled state arrived within the budget. Inspect and report
these outcomes; never treat them as replies or blindly resend.
Blocked/trust dialog: surface it; never send another task or type into the dialog.

### Explicit no-agent fallback

If preflight exits 5 (no detected agent, `agent_not_found` from agent lookup),
use the current `herdr-agent` Phase 4–5 pane-surface fallback in that installed
skill's `references/delivery-and-waiting.md` only after verifying that no detected
agent exists. In that explicitly verified fallback, follow the source's documented
`pane run` + `wait_for_idle.py` contract; it is not the normal transport.

Autonomous-mode switches are keystrokes verified by bounded reads, not task
sends. Keep them separate from the task prompt, and repeat the boot gate after
every FRESHEN.

## Max rounds and handoff

At `max_rounds` with FINDINGS: outcome `MAX_ROUNDS`, preserve findings verbatim, leave PR open, run SWEEP, and hand off USER-MERGE. Do not imply the PR is clean.

SWEEP is mode-aware: ISSUE may own implementer/reviewer and issue-resolver worktrees; PR owns reviewer plus optional FIXER and its isolated worktree. A CLEAN-first PR run has no FIXER artifacts. See `references/cleanup.md`.
