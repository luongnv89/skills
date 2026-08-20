# FINAL REPORT template (phase 6)

Assembled from the session file, never from memory. Every line that has no data is still printed with its
skip reason — an omitted phase reads as an oversight.

```
◆ Dev machine setup — FINAL REPORT
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

  Result:    READY | PARTIAL | BLOCKED
  Next:      <what the user should do — open a new shell, run `claude` to log in, …>
  Session:   ~/.dev-machine-setup/session.json (complete)
```

Fill `Machine` and `Manager` from the phase-1 gap report, each phase line from that phase's recorded items,
and `Next` from the session file's `next` sentence. `Session` names the file and its final `status`.

Lines to keep even when empty:

- a skipped phase prints `✓ skipped (<reason>)` — never nothing
- declined items print with `○` and the user's reason, so a declined `high` finding stays visible
- phase 5 always prints the verification re-run's remaining-high count, even when it is `0`
