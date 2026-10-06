# FINAL REPORT template (phase 6)

Assembled from the session file, never from memory. Every line that has no data is still printed with its
skip reason: an omitted phase reads as an oversight.

Format: plain text in the chat. Do not write a report file unless the user asks for one; if they do, write the
same block to the path they name.

```
◆ Dev machine setup — FINAL REPORT
  Result:    READY | PARTIAL — <reason> | BLOCKED — <reason>
  Machine:   <os> / <arch> / <distro or build>   Mode: setup | tune
  Manager:   <package manager>

  Phase 1 · Gap report
    ✓ present N · missing B baseline, A agents · findings H high / M med / L low
  Phase 2 · Debloat
    ✓ skipped (not fresh Windows) | listed N, removed K (names: …)
  Phase 3 · Baseline gaps
    ✓ nothing missing | installed: uv 0.11 · node v22.14  (deferred: …)
  Phase 4 · Agent CLI gaps
    ✓ nothing missing | installed: pi 0.84 · opencode 1.18  (declined: …)
  Phase 5 · Optimize
    ✓ fixed:    npm-global-bin-not-on-path (high) · path-duplicates (low)
    ○ declined: intel-homebrew-on-apple-silicon (medium) — user deferred migration
    verified by re-running detect_env.py: 0 high remaining

  Evidence:     <checks that ran and what they returned>
  Uncertainty:  <untested or unconfirmed items> | none
  Decision:     No approval needed. | <the approval still pending>
    Remaining action: <open a new shell, run `claude` to log in, …>
  Session:   ~/.dev-machine-setup/session.json (complete)
```

Fill `Machine` and `Manager` from the phase-1 gap report, and each phase line from that phase's recorded
items. `Session` names the file and its final `status`.

Lines to keep even when empty:

- a skipped phase prints `✓ skipped (<reason>)`, never nothing
- declined items print with `○` and the user's reason, so a declined `high` finding stays visible
- phase 5 always prints the verification re-run's remaining-high count, even when it is `0`

## The four contract lines

1. **`Result:`** comes first. The status word, then for PARTIAL or BLOCKED a one-line reason naming the
   item or phase that caused it.
2. **`Evidence:`** lists only checks that ran, each with its observed result:
   - the phase 5 `detect_env.py` re-run, and whether it ran in a fresh login shell or the same shell
   - the version check for each item installed in phases 3 and 4
   - the backup path of each rc file edited
   - for debloat, the inventory command that no longer lists each removed package

   Never list a check that did not run.
3. **`Uncertainty:`** names what is unknown or untested, apart from the verified facts:
   - each item recorded *fixed — needs new shell* that no fresh shell has confirmed
   - each agent CLI installed but not yet logged in (auth is the user's first interactive run)
   - `gap report built from detect.md fallbacks` when `detect_env.py` did not run in phase 1
   - `commands adapted for <distro>` when the distro is outside the apt/dnf/pacman tables
   - `deep checks not run` when `brew outdated` / `winget upgrade` / `npm outdated -g` were not opted into
   - each `you run this` block whose outcome the user did not report back

   Write `none` only when every item above is empty.
4. **`Decision:`** names the approval still pending, or says `No approval needed.` At phase 6 every item is
   normally decided, so a pending approval is rare: one exists only when the user answered "later" to a
   mutating fix. Put each remaining user action on its own `Remaining action:` line, taken from the session
   file's `next` sentence: open a new shell, log in to each new CLI, run an approved `you run this` block.

## Status rules

Apply the first rule that matches. SKILL.md § Final Report carries the same three rules.

| Order | Status | When |
|-------|--------|------|
| 1 | `BLOCKED — <reason>` | No gap report could be built, or a blocking finding stayed unfixed so no requested install could run. |
| 2 | `PARTIAL — <reason>` | A step failed and was not fixed; a `high` finding was declined, was deferred, or remains in `findings` after the re-run without being recorded *fixed — needs new shell*; in `setup` a `missing.baseline` item was declined or deferred; or the phase 5 re-run could not run. |
| 3 | `READY` | None of the above. |

READY is the complete status: the machine is ready to develop on. It does not mean every finding was fixed;
`Phase 5` and `Uncertainty:` say what was left.

How each run outcome maps:

| Outcome | Status |
|---------|--------|
| `detect_env.py` fails and the `detect.md` fallbacks give no OS or tool list | `BLOCKED` |
| `no-package-manager` fired and installing one was declined or failed, so nothing requested can install | `BLOCKED` |
| `no-sudo` fired, a requested item needs a system install, and no user-level path exists for any of them | `BLOCKED` |
| `no-sudo` fired but some requested items installed at user level | `PARTIAL` (the blocked items are deferred) |
| An install or fix command exits non-zero and is not fixed after re-presenting it | `PARTIAL` |
| A `high` finding is declined, deferred, or still in `findings` after the re-run and not recorded *fixed — needs new shell* | `PARTIAL` |
| `setup`: the user declines or defers a `missing.baseline` item (including NixOS, recorded deferred) | `PARTIAL` |
| A download fails for lack of network and the item is recorded `deferred — no network` | `PARTIAL` (setup baseline item) or `READY` (agent CLI or low/medium finding) |
| The phase 5 `detect_env.py` re-run cannot run | `PARTIAL` |
| `python3` absent in phase 1, gap report built from `detect.md` fallbacks, Python installed in phase 3 and the re-run passed | `READY` (list the fallback under `Uncertainty:`) |
| A fix is recorded *fixed — needs new shell* (rc line confirmed, same-shell re-run still lists it) and no fresh shell confirmed it | `READY` (list it under `Uncertainty:`) |
| The user declines an agent CLI, or a low/medium finding | `READY` |
| The user declines a mutating step that later phases do not depend on | `READY`, or `PARTIAL` when it is a `high` finding or a `setup` baseline item |
| `tune` run, or a re-run on an already-good machine, with nothing to install or fix | `READY` |
| The user pauses ("stop here") | No FINAL REPORT. Print the pause output in `session.md` § Pausing, which opens `Result: PARTIAL — paused before phase N` |

A user declining a change never produces `BLOCKED` by itself. A phase Step Completion Report of `FAIL` gives
`BLOCKED` only when it matches rule 1; otherwise it gives `PARTIAL`.

## Example: a partial tune run

```
◆ Dev machine setup — FINAL REPORT
  Result:    PARTIAL — high finding npm-global-bin-not-on-path declined
  Machine:   linux / x86_64 / Ubuntu 24.04   Mode: tune
  Manager:   apt
  ...
  Evidence:     detect_env.py re-run in a fresh login shell: 1 high remaining (npm-global-bin-not-on-path, declined)
                path-duplicates gone from findings; ~/.zshrc backed up to ~/.zshrc.bak.20260820094533
  Uncertainty:  deep checks not run
  Decision:     No approval needed.
    Remaining action: re-trigger the skill if you want npm-global-bin-not-on-path fixed
  Session:   ~/.dev-machine-setup/session.json (complete)
```

## Reader checks

Judge the final report against these four checks, alongside the Acceptance Criteria in SKILL.md:

- **Main result is findable.** The first line under the header states the status and, when not READY, why.
- **Facts and assumptions are separated.** Every `Evidence:` line names a check that ran and its result;
  untested behavior appears only under `Uncertainty:`.
- **Claims are traceable.** Each fixed finding traces to the phase 5 re-run, each install to its version
  check; a *needs new shell* item is never reported as confirmed.
- **Next decision is clear.** `Decision:` names the pending approval, or says `No approval needed.`, and each
  remaining user action has its own line.

When a human reviews the report, ask whether they could find the result, separate facts from assumptions,
trace each claim, and name the next decision. Without a response, human understanding is unconfirmed; agent
inspection cannot confirm it.
