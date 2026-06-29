# Report Template

Produce the report in this exact order and shape. Keep it scannable — the user wants
"what's satisfied" and "what to do next, in priority order", not an essay.

Write the report to a file when working in a repo (`viral-evaluation.md` at the repo root,
or next to the landing page source). Also print the verdict block + top fixes inline so the
user sees the headline result without opening the file.

---

## 1. Verdict block (print inline + top of file)

```
Virality Score: <NN>/100 — <Tier>
Product: <name or one-line description>
Evaluated: <landing page source> · <codebase path>

PASS: <n>/32   PARTIAL: <n>/32   FAIL: <n>/32
```

## 2. Scorecard (all 32, grouped, with one-line evidence)

One line per principle. Format:

```
<verdict>  #<n> <short name> ········ <evidence / what was found>   [⚠ if low-confidence]
```

- `verdict` is `PASS` / `PART` / `FAIL` (pad to align).
- Group under the rubric's A–G headings so related findings sit together.
- Evidence is concrete and specific to THIS product — quote the actual headline, name the
  actual tier, cite the file. Never generic ("copy could be better").
- Append `⚠` and a 3–6 word "needs human eyes" note to every `judgment`/`visual` verdict.

## 3. Top fixes — prioritized, ordered (the main deliverable)

A numbered list, highest leverage first. This is what the user asked for: "what needs to be
done, in order, priority, to make it more viral." Order by **impact × ease**, with the
virality levers that move the most (hero, paywall, headline, proof, single CTA) first.

Each fix:

```
<N>. <Imperative action> — fixes #<principles it resolves>
     Now:    <what the product does today, quoted>
     Change: <the specific change to make>
     Why:    <the principle's logic, one line>
```

Rules for this list:
- **Only include FAIL and PARTIAL** principles. PASSes don't generate fixes.
- **Merge related principles** into one fix when they share a root cause (e.g. #3 numbers +
  #26 weak words + #24 outcome → one "rewrite the hero copy" fix).
- **Be concrete enough to act on without re-reading the rubric.** Give the actual new headline
  candidate, the actual tier to cut, the actual CTA label to use — not "improve the headline".
- Cap at the ~7–10 fixes that matter. Note any remaining low-impact misses in one trailing line.

## 4. What's already working (brief)

A short bulleted list of the PASS principles, so the user sees the strengths to preserve and
doesn't undo them while fixing the rest. One line each, no fixes.

## 5. Caveats

- List every low-confidence verdict and exactly what a human should eyeball
  (OG image punch, founder presence, emotional pull, novelty, real pricing vs competitors).
- Note any principle you couldn't evaluate and why (e.g. landing page URL unreachable, pricing
  lives in a backend you couldn't see).
- If the user gave strategic context that deliberately breaks a principle, restate it here so
  the score is read in context.

---

### Example top-fix entry (for calibration)

```
1. Rewrite the hero to sell the outcome, not the feature — fixes #20, #24, #3, #18
   Now:    "An AI-powered platform for automated code review"
   Change: "Catch the bug before your user does — review every PR in 30 seconds"
   Why:    80% never scroll past the hero; sell a human desire (less pain) with a number.
```
