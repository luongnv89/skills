# Edge Cases

Read the entry when its situation arises. SKILL.md keeps **Monorepo**, **Existing report files**,
and **User asks to apply fixes** inline — they change how the run is invoked or protect existing
work. Everything else is here.

## Not a git repo

Skip Repo Sync entirely, state it in the report (no commit SHA is recordable, so citations are
`path:line` against the working tree only), and still write both files.

## No manifest at all

Shell scripts, plain HTML, a docs-only repo: `DEP` is **Not Assessed — no manifest**. The plan
drops P2 to a single "no dependency surface" note rather than inventing upgrade tasks. Do not
promote a language runtime version to a dependency finding when nothing declares one.

## No network

Dependency *latest* versions are unobtainable. Record installed versions only and mark currency
**Not Assessed — offline**. Never guess a latest version, and never carry one from memory — a
stale "latest" is worse than an honest gap. Run `scripts/dep_scan.sh` with its offline flag so the
summary states the mode.

## Baseline RED

The audit continues; it never aborts. The plan's Sprint 0 is "restore baseline-green" and every
later task depends on it. Pre is exempt from the baseline-green assertion while the baseline is
RED — its acceptance criteria are install/run notes plus create-or-update of `CLAUDE.md` /
`AGENTS.md`.

## Huge repo (> 2000 source files)

Audit by subsystem in priority order, cap the file set per dimension, and state in Limitations
exactly what was not scanned, by path. Never silently truncate — an unstated cap makes every
"clean" verdict unreliable.

## Dimension filter narrows the run

When the user names only some dimensions, the others are **Not Assessed — out of requested
scope**, and empty P0–P4 phases collapse to a one-line note. Never drop or renumber a phase to
close the gap.
