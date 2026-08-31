# Epic identity — normalize, find, create, bind

The full mechanics behind SKILL.md's *Phase 3 — Create the epic*. Read this when running Create mode.

An epic is an ordinary issue that parents the others (IDD SPEC §2.1) — not a new artifact type. Its
identity rests on one thing: the **plan-binding marker** `<!-- plan-to-issues:plan=<plan_path> -->`.
Everything here exists to make that marker exact, present, and singular.

**Why this phase is recovery-based, not window-free.** Creating the epic and marking it are two API
calls, and `/issue-creator` owns the body it writes — it places supplied intent text *verbatim, in a
blockquote* inside its own template, so a marker embedded there arrives `> `-prefixed and mid-body,
where it is not a usable body marker. The marker therefore cannot ride in on the create call, and
there is no atomic create-with-marker. Between step 2 and step 4 the epic exists unmarked. That
window cannot be closed, so it is made **recoverable**: step 1's fallback finds the unmarked epic and
adopts it after a confirm. Design for the interruption; do not claim it is impossible.

0. **Normalize `plan_path` first.** Every later comparison is an exact string match, so a plan bound
   once as `MODERNIZATION_PLAN.md` and once as `./MODERNIZATION_PLAN.md` would write two markers and
   then hard-fail its own completion check. Resolve to a single repo-root-relative form and use *that*
   value in step 1's filter, step 4's guard and the probes:

   ```bash
   # A plan is exactly one file — Phase 0's discovery resolves a `tasks/` directory to one before
   # this runs. `git ls-files -- <path>` is a PATHSPEC, so without this guard a directory would
   # expand to one line per file and write a multi-line, broken marker.
   [ -f "$plan" ] || { echo "✗ not a plan file: $plan"; exit 1; }   # discovery resolves tasks/ to one file
   # -c core.quotePath=false: ls-files octal-escapes a non-ASCII name (`"PL\303\204N.md"`) and the
   # shell fallback below does not, so without it the same plan binds two different markers
   # depending on whether it is tracked yet — committing the plan between runs would then miss the
   # marker and file a second epic.
   # `:(literal)` turns pathspec magic off: a plan name holding `*`, `?` or `[` is otherwise a glob,
   # so `p?.md` would bind whatever tracked file it happens to match (`p0.md`) while the untracked
   # branch below binds `p?.md` — the silent disagreement this step exists to prevent.
   plan_path="$(git -c core.quotePath=false ls-files --full-name --error-unmatch -- ":(literal)$plan" 2>/dev/null | head -1)"
   if [ -z "$plan_path" ]; then     # not tracked yet — the usual case for a freshly
     plan_path="$(cd "$(dirname "$plan")" && printf '%s/%s\n' "$(pwd -P)" "$(basename "$plan")")"
   fi                               # generated MODERNIZATION_PLAN.md
   root="$(git rev-parse --show-toplevel)"
   plan_path="${plan_path#"$root"/}"  # relative already on the tracked branch; POSIX, no realpath
   # `$(printf '\n')` strips the newline and would make the pattern match everything — build the
   # newline with a sacrificial character instead.
   nl="$(printf '\nx')"; nl="${nl%x}"
   # `"` and `\` too: quotePath=false still C-quotes a name holding a control character, so those
   # are the two branches' only remaining disagreement — reject them on both rather than let one
   # bind `"bad\nname.md"` and the other `bad<LF>name.md`.
   case "$plan_path" in
     ''|/*|*/|*"$nl"*|*'"'*|*'\'*)
       echo "✗ the plan must resolve to a single file inside the repo, got: $plan"; exit 1;;
   esac
   ```

   The validation is not decoration. Every rejected shape is a *different* marker for the same plan,
   and a marker that differs by one byte files a second epic:

   | Shape | What it would bind | Consequence |
   |---|---|---|
   | empty | `<!-- plan-to-issues:plan= -->` | every plan in the repo shares one marker — the exact collision this step exists to prevent |
   | multi-line (`tasks/` pathspec) | a two-line marker | probe 1 counts 2, hard-failing the run on a correctly-created epic |
   | absolute (a plan outside the repo) | `/home/<user>/checkout/plan.md` | machine-specific: another clone computes a different path, misses the marker, files a second epic — and the local layout leaks into a public issue body |
   | octal-escaped (non-ASCII, tracked) | `"PL\303\204N.md"` | differs from the untracked form, so committing the plan between runs files a second epic |

   The `-f` test rejects a directory and a path that does not exist before either reaches the
   pathspec; `core.quotePath=false` makes the tracked and untracked branches agree byte-for-byte on
   every ordinary name, spaces and non-ASCII included; the `/*` arm keeps `plan_path` inside the
   repo, matching what the error message promises.

   The contract the guard enforces is *not* "every path resolves" — it is **the two branches never
   disagree silently**. A name they could still render differently (one holding a control character,
   a `"`, or a `\`) is rejected on both, so the worst case is a loud stop, never two markers for one
   plan. Such a name is unusable in the line-oriented marker anyway.

   The fallback is shell-only on purpose — BSD/macOS `realpath` has no `--relative-to`, and neither
   `realpath` nor that flag is probed in Phase 0.

1. **Check for an existing epic first** — fetch and filter locally, since GitHub's search tokenizer
   is unreliable on markers. Request every field the filters below need — they cost nothing on the
   same call, and `labels`/`state`/`createdAt` are what the fallback reads:

   ```bash
   gh issue list --state all --limit 200 --json number,title,body,labels,state,createdAt
   ```

   Filter on the **plan-binding marker** for this exact plan path —
   `<!-- plan-to-issues:plan=<plan_path> -->`, matched as a fixed string on its own line. An epic
   carrying it is *this plan's* epic: switch to **idempotent re-run** — reuse it, skip creation, and
   file only the tasks it does not already list. Never create a second epic for the same plan.

   Match on the binding marker, **not** on the `plan-dashboard:start` sentinel: the sentinel carries
   no plan path, so it cannot tell *this* plan's epic from another plan's epic in the same repo.
   (Both are written by step 4, so neither is "the later one".)

   **Fallback — an unmarked epic.** Unmarked means **neither** source-marker kind: no
   `plan-to-issues:plan=` **and** no `plan-to-issues:conversation=`. A run interrupted between
   step 2 and step 4, or a pre-1.5.0 run, leaves an epic with no marker. Skip any issue that
   already carries `conversation=` — adopting it would bind both markers and file this plan
   into the wrong epic. Before concluding that none exists, scan the same fetched list for
   an **open issue that carries neither source marker** and either has the `epic`
   label **or** whose title equals the `Epic: Modernize <project> — …` title this run would create.
   The title clause matters: the `epic` label is applied in step 3, so an interruption between the
   create and the label leaves an epic the label filter alone would miss. Do not require the body to
   name the plan path — an epic interrupted before Phase 5 has an empty dashboard and may never
   mention it. Do not adopt silently; show what is known and **ask once**:

   ```text
   ⚠ #142 "Epic: Modernize acme — Pre + P0–P4"  (epic label, neither source marker)
       created 2026-08-26 14:02 · 0 child issues · no dashboard

     This looks like an interrupted run of this plan. Adopt it? [Y/n]
     (declining creates a new epic; #142 is left untouched)
   ```

   On adoption, run step 4 to bind it, then continue as an idempotent re-run. If several unmarked
   epics match, list them all and ask which — never guess.
2. Otherwise invoke `/issue-creator` in Create mode with the epic intent text built from the plan
   header: project name, baseline verdict, test command of record, the phase table, and the
   milestone exit conditions as the epic's acceptance criteria (they describe the whole-effort
   outcome). Title: `Epic: Modernize <project> — Pre + P0–P4`. Do **not** put the marker in the
   intent text; it would be blockquoted into Reporter Context.
3. Apply the `epic` label and record the number as `<epic>`.
4. **Bind the epic — before filing a single child issue.** Append the plan-binding marker and an
   empty sentinel pair. Each piece is appended only if absent, so re-running this step (or reaching
   it via the adoption path on an epic that already has a sentinel pair) cannot produce a duplicate:

   ```bash
   gh issue view <epic> --json body --jq '.body' > epic-body.md
   grep -qFx "<!-- plan-to-issues:plan=$plan_path -->" epic-body.md \
     || printf '\n<!-- plan-to-issues:plan=%s -->\n' "$plan_path" >> epic-body.md
   grep -q '^<!-- plan-dashboard:start -->$' epic-body.md \
     || printf '<!-- plan-dashboard:start -->\n<!-- plan-dashboard:end -->\n' >> epic-body.md
   gh issue edit <epic> --body-file epic-body.md
   ```

   The guards are what make this idempotent — the prose does not make it so, the `grep -q ||` does.
   Both use `-x` (whole line), matching the completion probes exactly. That is deliberate: with an
   unanchored `-qF`, a marker that exists but is **blockquoted** or indented would satisfy the guard
   while failing probe 1, so the prescribed "re-run step 4" recovery would be a permanent no-op.

**Completion criteria:** `gh issue view <epic> --json number,state,labels` returns an issue whose
`state` is `OPEN` and whose labels contain `epic`; that number is recorded for `--parent` binding;
and the body carries the binding marker **for this plan path** plus exactly one sentinel pair.

`state` has to be *requested*, not assumed: without it the criterion asserts a property the probe
cannot see, and a **closed** epic — the case `references/edge-cases.md` describes as closing the old
epic to force a fresh one — would pass and take the whole backlog with it. `state != "OPEN"` stops
the run.

Each asserted property gets the probe that actually tests it, anchored to line start so a
blockquoted or indented copy fails rather than passing silently:

```bash
body="$(gh issue view <epic> --json body --jq '.body')"
printf '%s\n' "$body" | grep -cFx "<!-- plan-to-issues:plan=$plan_path -->"  # must be 1 — this plan
printf '%s\n' "$body" | grep -c  '^<!-- plan-to-issues:plan='                # must be 1 — no foreign binding
printf '%s\n' "$body" | grep -c  '^<!-- plan-to-issues:conversation='        # must be 0 — not a conversation epic
printf '%s\n' "$body" | grep -cFx '<!-- plan-dashboard:start -->'             # must be 1 — pair opened once
printf '%s\n' "$body" | grep -cFx '<!-- plan-dashboard:end -->'               # must be 1 — pair closed once
```

Probe 1 at 0 means the marker is absent or wrapped (`/issue-creator` reordered the body, or it landed
in a blockquote) — re-run step 4 and re-verify. Probe 2 above 1, or probe 1 at 0 while probe 2 is 1,
means the epic is bound to a **different plan**: **stop**, rather than filing this plan's children
into another plan's epic. The conversation= probe above 0 means the epic is already conversation-
sourced: **stop** — binding `plan=` onto it would mix kinds. Any sentinel count other than 1 means
the body was hand-edited; **stop**.


---

## Conversation-sourced epics (source kind `conversation`)

Everything above governs `source.kind == "file"` and is unchanged. When Phase 0 resolved
conversational intent instead, the same five steps run with these deltas.

**Step 0 — normalize.** There is no path to normalize. The identity value is the **slug of the epic
title the user confirmed** in Phase 1: lowercased, every run of non-alphanumerics collapsed to `-`,
leading and trailing `-` trimmed, truncated to 60 characters. An empty slug after normalization is a
**stop**, exactly as an empty `plan_path` is — it would make one marker match every conversation.

```bash
slug="$(printf '%s' "$epic_title" | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//' | cut -c1-60)"
[ -n "$slug" ] || { echo "✗ empty conversation slug — refusing to bind"; exit 1; }
```

**Step 1 — discovery is advisory, not authoritative.** The marker is
`<!-- plan-to-issues:conversation=<slug> -->`, matched as a fixed string on its own line, the same
way step 1 matches the plan marker. **The difference that matters: a slug is not a stable identity.**
Two unrelated discussions of one subject slug identically, and the same intent rephrased slugs
differently. So a hit is **never silently reused**:

```text
An epic already carries this conversation slug:
  #212  Epic: Harden the ingest path   (opened 3 days ago, 6 children)
Reuse it and file only what it does not list, or create a new epic? [R/n]
```

Default is reuse. `n` creates a second epic with the same slug — permitted, because two backlogs may
legitimately share a title; both then carry the marker and every later run asks. Adoption of an
unmarked epic works exactly as it does on the file path (neither source-marker kind; skip any
issue already carrying `plan=`), and still asks once.

`/plan-to-issues --from-conversation --epic <n>` **skips discovery entirely** and binds to that
number after checking it is open and not already bound to a *different* slug or to a plan path.
This is the supported way to resume a conversation-sourced run. Phase 1 then restores the
worklist from `## Source` (`references/input-resolution.md`) — it does not re-draft. The final
report always prints
`Re-run this backlog with: /plan-to-issues --from-conversation --epic <n>` — the issue number,
not the slug, is the stable handle. `sync <epic#>` only re-renders the map; it creates no issues.

**Step 4 — bind.** Append the conversation marker and, additionally, the `## Source` block holding
the confirmed draft verbatim. Both are guarded the same way as the plan marker, so re-running cannot
duplicate either:

```bash
grep -qFx "<!-- plan-to-issues:conversation=$slug -->" epic-body.md \
  || printf '\n<!-- plan-to-issues:conversation=%s -->\n' "$slug" >> epic-body.md
grep -qFx '## Source' epic-body.md \
  || { printf '\n## Source\n\nConfirmed from conversation:\n\n' >> epic-body.md
       printf '```text\n' >> epic-body.md
       cat confirmed-draft.txt >> epic-body.md
       printf '```\n' >> epic-body.md; }
```

The draft is fenced, so a drafted line cannot inject a heading or a sentinel into the epic body
(`references/security-boundary.md`).

**Step 4 probes.** Same shape, conversation values, plus the mutual-exclusion probe — an epic is
bound to exactly one input kind, never both:

```bash
printf '%s\n' "$body" | grep -cFx "<!-- plan-to-issues:conversation=$slug -->"  # must be 1
printf '%s\n' "$body" | grep -c  '^<!-- plan-to-issues:conversation='           # must be 1
printf '%s\n' "$body" | grep -c  '^<!-- plan-to-issues:plan='                   # must be 0
printf '%s\n' "$body" | grep -cFx '## Source'                                   # must be 1
```

**Never materialize a plan file to obtain a stable identity.** This skill writes to the tracker
only; its acceptance criteria require `git status --porcelain` to match the pre-run snapshot.
