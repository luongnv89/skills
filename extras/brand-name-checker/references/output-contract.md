# Output Contract

Field rules and worked examples for the compact report in `SKILL.md` → *Output Format*. The template there is authoritative; this file explains how to fill it.

## Field rules

| Line | Rule |
|------|------|
| `RESULT` | First line of each report. Status word, then counts: `N/M checks verified; U unknown, S skipped`. There are 16 checks by default: 6 social, 4 registry, 3 domain (`.com`, `.io`, `.app`), 3 trademark; each extra TLD that `prd.md` or the user names adds one domain check (`SKILL.md` → *Step 3*). |
| `SOCIAL`, `REGISTRY`, `DOMAIN`, `TM` | One status per source, using the vocabulary in `references/source-checks.md` and `SKILL.md` → *Step 3*. `Unknown` and `Skipped (not cleared)` are statuses, never blanks. |
| `EVIDENCE` | For each verified status, the URL or query that produced it and the check time. A status with no evidence is Unknown. |
| `SKIPPED` | Checks omitted by the Early-Exit Rule, or `none`. |
| `UNKNOWN` | Each unverified check, why it failed (timeout, 429, outage, bot check, unconfirmed search, missing target intent), and what would verify it; for a trademark register, its manual check link from `references/source-checks.md` → *Step 4*. `none` when empty. |
| `RISK` | Level, highest matching trigger from the Step 5 matrix, the finding behind it, and the policy rationale. |
| `RECOMMEND` | Verdict, reason, alternatives (checked or labeled unverified), then `next:`. Keep `RISK` and `RECOMMEND` as the last two lines of each report. |

## Status words

- **COMPLETE**: every required check is verified, or skipped by the Early-Exit Rule after an exact handle was confirmed.
- **PARTIAL**: one or more checks are Unknown. The risk is provisional under the unknown policy.
- **BLOCKED**: no name was provided, or no web access works (no HTTP or search tool answers a test request). Return only the `RESULT` line with the reason and the fix (for example, "enable a web fetch or search tool, or shell access for curl, and re-run"). Omit every other line.

## The `next:` clause

Name the decision left to the user: adopt the name, pick a variant, or verify the Unknown checks first. This skill registers nothing and writes no files, so state that no approval is needed for its own actions when the user asks.

## Understanding criteria

Grade actual outputs against these, in addition to the correctness criteria in `SKILL.md` → *Acceptance Criteria*:

| Criterion | Observable check |
|-----------|------------------|
| Main result is findable | The first line of each report is `RESULT:` with COMPLETE, PARTIAL, or BLOCKED. |
| Facts and assumptions are separated | Verified statuses cite a source on `EVIDENCE`; unverified checks appear on `UNKNOWN`; unchecked alternatives are labeled unverified. |
| Claims are traceable | `RISK` names the trigger and the finding that matched it. |
| Next decision is clear | `RECOMMEND` ends with `next:` naming the user's remaining decision. |

Agent review cannot confirm human understanding. When a human reviewer is available, ask whether they could find the result, separate facts from assumptions, trace the risk claim, and name the next decision; record the answers with the eval results. If nobody answers, record human understanding as unconfirmed.

## Worked examples

### COMPLETE, Low, Proceed

Every source verified clear and `.com` parked:

```text
RESULT: COMPLETE - 16/16 checks verified; 0 unknown, 0 skipped
SOCIAL: Clear
REGISTRY: npm (available) | PyPI (available) | Homebrew (available) | apt (available)
DOMAIN: .com (parked) | .io (available) | .app (available)
TM: WIPO (clear) | EUIPO (clear) | INPI (clear)
EVIDENCE: registry.npmjs.org/acme-flow 404; pypi.org/pypi/acme-flow/json 404; rdap.verisign.com/com/v1/domain/acme-flow.com 200 and acme-flow.com shows a for-sale page; pubapi.registry.google/rdap/domain/acme-flow.app 404; whois -h whois.nic.io acme-flow.io: Domain not found.; branddb.wipo.int no live mark in classes 9/35/42; checked 2026-01-15T10:02Z
SKIPPED: none
UNKNOWN: none
RISK: Low - no High or Moderate trigger; every check verified; .com parked, not active
RECOMMEND: Proceed - all sources verified clear; next: decide whether to adopt, then claim npm/PyPI/Homebrew first, register acme-flow.io or negotiate for the parked .com, and secure the handles
```

### PARTIAL, provisional Moderate, Modify

The EUIPO search timed out twice:

```text
RESULT: PARTIAL - 15/16 checks verified; 1 unknown, 0 skipped
SOCIAL: Clear
REGISTRY: npm (available) | PyPI (available) | Homebrew (available) | apt (available)
DOMAIN: .com (available) | .io (available) | .app (available)
TM: WIPO (clear) | EUIPO (Unknown) | INPI (clear)
EVIDENCE: registry.npmjs.org/brightloom 404; rdap.verisign.com/com/v1/domain/brightloom.com 404; whois -h whois.nic.io brightloom.io: Domain not found.; pubapi.registry.google/rdap/domain/brightloom.app 404; checked 2026-01-15T10:20Z
SKIPPED: none
UNKNOWN: EUIPO - search timed out twice; verify at euipo.europa.eu/eSearch for classes 9/35/42
RISK: Moderate - provisional; unknown EUIPO check and no known High finding (unknown policy)
RECOMMEND: Modify - hold adoption until EUIPO is verified; next: run the EUIPO search, then re-check
```

### COMPLETE, High, Abandon (Early-Exit Rule)

```text
RESULT: COMPLETE - 6/16 checks verified; 0 unknown, 10 skipped by the Early-Exit Rule
SOCIAL: NEGATIVE: Exact social handle taken (@github)
REGISTRY: Skipped (not cleared)
DOMAIN: Skipped (not cleared)
TM: Skipped (not cleared)
EVIDENCE: github.com/nimbus resolves to an active organization; checked 2026-01-15T10:31Z
SKIPPED: registries, domains, trademarks; skipped is not cleared
UNKNOWN: none
RISK: High - exact social handle collision on GitHub (Early-Exit Rule)
RECOMMEND: Abandon - nimbus-dev, nimbusly (both unverified); next: pick a candidate and run this check on it
```

## Several names

This layout applies when more than one name was checked, or when the user asked for a quick-screen on one name (`SKILL.md` → *Several names*). Any other run returns the single report alone.

1. `CANDIDATES:` the names in input order, each with its slug when the slug differs, then any name over the 5-name cap as `not checked (over the 5-name cap)`.
2. The `QUICK-SCREEN:` caption and table (*Quick-screen table* below), or `QUICK-SCREEN: none - no alternatives suggested`.
3. For each checked name, in input order, a divider line `--- <name> (i of N) ---` and then that name's compact report. `RESULT` is the first line of each report and counts that name's own checks; `RISK` and `RECOMMEND` are its last two lines.

The table comes before the reports, so every report keeps `RISK` and `RECOMMEND` last and the whole output still ends with the last name's `RISK` and `RECOMMEND` lines. A `BLOCKED` run (no name, or no web access) returns only its one `RESULT` line: no `CANDIDATES` line, no table, no dividers. When `prd.md` exists, its blocks are appended once, after the last report (`references/prd-integration.md`).

## Quick-screen table

**Input.** The alternatives named on the reports' `RECOMMEND` lines (the synthesizer's `variants_if_modify` and `alternatives_if_abandon` when it ran), de-duplicated by slug, leaving out any name checked in full, at most 8 in the order suggested.

**Slug rule.** Normalize each alternative with the slug rule in `references/edge-cases.md` before any fetch, and put only that slug into a URL or a shell command, as `references/source-checks.md` requires for every lookup. An alternative containing `@` or `/`, such as an npm scope `@org/name`, names something other than its slug, so it is not fetched: every endpoint cell in its row is `unknown`.

**Who runs it.** The parent runs these fetches itself; it never spawns source-checker for them, because source-checker's statuses include `available`. Direct endpoints only, no search fallback:

| Column | Endpoint | Cell |
|--------|----------|------|
| GitHub | `https://api.github.com/users/[NAME]` | 200 is `taken`, 404 is `not found` |
| npm | `https://registry.npmjs.org/[NAME]` | 200 with package JSON is `taken`, 404 is `not found` |
| PyPI | `https://pypi.org/pypi/[NAME]/json` | 200 with package JSON is `taken`, 404 is `not found` |
| Homebrew | `https://formulae.brew.sh/api/formula/[NAME].json` | 200 with formula JSON is `taken`, 404 is `not found` |
| .com | `<base>domain/[NAME].com`, with the RDAP base read from `https://data.iana.org/rdap/dns.json` | 200 is `registered`, a 404 from that registry server is `not found` |

Any other answer (a 403 or 429, a timeout, an error page, no working fetch tool) is `unknown`. These cell words replace the Step 1-4 statuses for this table only. `not found` means one endpoint has no record of the slug; it is never written as available, and no alternative gets a `RISK` or `RECOMMEND` line of its own.

**Caption**, always the line right above the table:

```text
QUICK-SCREEN: partial and unverified - 5 of the N checks a full run makes (16 by default, plus each extra TLD named); not run: X/Twitter, Instagram, LinkedIn, TikTok, Discord, apt, .io, .app, any extra TLD, WIPO, EUIPO, INPI
```

Columns: `| Alternative (slug) | Suggested for | GitHub | npm | PyPI | Homebrew | .com | Status |`. The `Status` cell of every row reads `unverified - not cleared`, whatever the endpoint cells say: a quick-screen never clears a name, and adopting an alternative takes a full run on it.

### Worked example: two names

`sfm` hits an exact GitHub handle, so the Early-Exit Rule ends its checks; `hosthale` still runs every check:

```text
CANDIDATES: sfm, hosthale
QUICK-SCREEN: partial and unverified - 5 of the 16 checks a full run makes; not run: X/Twitter, Instagram, LinkedIn, TikTok, Discord, apt, .io, .app, WIPO, EUIPO, INPI
| Alternative (slug) | Suggested for | GitHub | npm | PyPI | Homebrew | .com | Status |
|--------------------|---------------|--------|-----|------|----------|------|--------|
| sfmctl (sfmctl) | sfm | not found | not found | not found | not found | registered | unverified - not cleared |
| HostHale CLI (hosthale-cli) | hosthale | not found | not found | unknown | not found | not found | unverified - not cleared |
--- sfm (1 of 2) ---
RESULT: COMPLETE - 6/16 checks verified; 0 unknown, 10 skipped by the Early-Exit Rule
SOCIAL: NEGATIVE: Exact social handle taken (@github)
REGISTRY: Skipped (not cleared)
DOMAIN: Skipped (not cleared)
TM: Skipped (not cleared)
EVIDENCE: api.github.com/users/sfm 200, an active account; checked 2026-11-23T17:02Z
SKIPPED: registries, domains, trademarks; skipped is not cleared
UNKNOWN: none
RISK: High - exact social handle collision on GitHub (Early-Exit Rule)
RECOMMEND: Abandon - sfmctl (quick-screened, unverified); next: run a full check on sfmctl or pick another candidate
--- hosthale (2 of 2) ---
RESULT: PARTIAL - 15/16 checks verified; 1 unknown, 0 skipped
SOCIAL: Clear
REGISTRY: npm (available) | PyPI (available) | Homebrew (available) | apt (available)
DOMAIN: .com (available) | .io (available) | .app (available)
TM: WIPO (clear) | EUIPO (Unknown) | INPI (clear)
EVIDENCE: api.github.com/users/hosthale 404; registry.npmjs.org/hosthale 404; pypi.org/pypi/hosthale/json 404; rdap.verisign.com/com/v1/domain/hosthale.com 404; checked 2026-11-23T17:05Z
SKIPPED: none
UNKNOWN: EUIPO - search timed out twice; verify at euipo.europa.eu/eSearch for classes 9/35/42
RISK: Moderate - provisional; unknown EUIPO check and no known High finding (unknown policy)
RECOMMEND: Modify - hold adoption until EUIPO is verified; fallback HostHale CLI (quick-screened, unverified); next: run the EUIPO search, then decide on hosthale or run a full check on hosthale-cli
```
