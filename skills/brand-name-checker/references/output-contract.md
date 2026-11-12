# Output Contract

Field rules and worked examples for the compact report in `SKILL.md` → *Output Format*. The template there is authoritative; this file explains how to fill it.

## Field rules

| Line | Rule |
|------|------|
| `RESULT` | First line. Status word, then counts: `N/M checks verified; U unknown, S skipped`. There are 16 checks: 6 social, 4 registry, 3 domain, 3 trademark. |
| `SOCIAL`, `REGISTRY`, `DOMAIN`, `TM` | One status per source, using the vocabulary in `references/source-checks.md` and `SKILL.md` → *Step 3*. `Unknown` and `Skipped (not cleared)` are statuses, never blanks. |
| `EVIDENCE` | For each verified status, the URL or query that produced it and the check time. A status with no evidence is Unknown. |
| `SKIPPED` | Checks omitted by the Early-Exit Rule, or `none`. |
| `UNKNOWN` | Each unverified check, why it failed (timeout, 429, outage, missing target intent), and what would verify it. `none` when empty. |
| `RISK` | Level, highest matching trigger from the Step 5 matrix, the finding behind it, and the policy rationale. |
| `RECOMMEND` | Verdict, reason, alternatives (checked or labeled unverified), then `next:`. Keep `RISK` and `RECOMMEND` as the last two lines. |

## Status words

- **COMPLETE**: every required check is verified, or skipped by the Early-Exit Rule after an exact handle was confirmed.
- **PARTIAL**: one or more checks are Unknown. The risk is provisional under the unknown policy.
- **BLOCKED**: no name was provided, or the web tools are unavailable. Return only the `RESULT` line with the reason and the fix (for example, "enable WebSearch and re-run"). Omit every other line.

## The `next:` clause

Name the decision left to the user: adopt the name, pick a variant, or verify the Unknown checks first. This skill registers nothing and writes no files, so state that no approval is needed for its own actions when the user asks.

## Understanding criteria

Grade actual outputs against these, in addition to the correctness criteria in `SKILL.md` → *Acceptance Criteria*:

| Criterion | Observable check |
|-----------|------------------|
| Main result is findable | The first line is `RESULT:` with COMPLETE, PARTIAL, or BLOCKED. |
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
EVIDENCE: registry.npmjs.org/acme-flow 404; pypi.org/pypi/acme-flow/json 404; branddb.wipo.int no live mark in classes 9/35/42; checked 2026-01-15T10:02Z
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
EVIDENCE: registry.npmjs.org/brightloom 404; whois brightloom.com unregistered; checked 2026-01-15T10:20Z
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
