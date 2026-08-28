# The isitagentready.com scan API

Read this when you need the request contract, the check inventory, or the rule that
puts a failing check into a phase.

## There is no page-per-site URL

`https://isitagentready.com/<WEBSITE_URL>` **returns 404.** It is a natural guess and it
does not exist. The scanner is an API:

```
POST https://isitagentready.com/api/scan
Content-Type: application/json

{"url": "https://example.com"}
```

A scan takes roughly 8–20 seconds; `scan_site.sh` allows 120.

## Two response formats, both needed

| Body | Returns | Used for |
|---|---|---|
| `{"url": …}` | **JSON** | `level`, per-check `status`, category grouping, `nextLevel` |
| `{"url": …, "format": "agent"}` | **markdown text** | remediation prose for *every* failing check |

The JSON is authoritative for structure and status. Its `nextLevel.requirements[]`
carries fix prompts for the **next level only** — typically one or two checks — which is
why the second call exists. `format: "agent"` is `text/markdown`, **never valid JSON**;
piping it to `jq` or `json.load` fails.

### JSON shape

```
url, targetUrl, targetRedirectedFrom, scannedAt
level            0–5
levelName        e.g. "Basic Web Presence"
checks.<category>.<check> = { status, message, details?, evidence[], durationMs }
nextLevel        { target, name, requirements[] }
  requirements[] = { check, description, shortPrompt, prompt, specUrls[], skillUrl }
isCommerce       bool
commerceSignals  []
```

`status` is `pass`, `fail`, or `neutral`. **A check object has no `fix` field** — fix
text lives only in `nextLevel.requirements[]` and in the agent-format response.

`targetUrl` may differ from the submitted `url` when the site redirects
(`https://stripe.com` → `https://stripe.com/fr`). The plan is written against
`targetUrl`, because that is what the re-scan will check.

### Agent-format shape

One block per failing check, in the same order the JSON iterates categories:

```markdown
## <fix title>
<one or two sentences of fix prose>
Implementation guide: https://isitagentready.com/.well-known/agent-skills/<slug>/SKILL.md
```

`triage_scan.py` joins these to the failing checks **by position** — same source, same
order, same count. It falls back to matching the guide slug when the counts disagree, and
warns when it does. Some checks (`ap2`) ship no guide URL; the task then cites none.

## The 22 checks

| Category | Checks |
|---|---|
| `discoverability` | `robotsTxt`, `sitemap`, `linkHeaders`, `dnsAid` |
| `contentAccessibility` | `markdownNegotiation` (llms.txt checks appear here when the scanner runs them) |
| `botAccessControl` | `robotsTxtAiRules`, `contentSignals`, `webBotAuth` |
| `discovery` | `apiCatalog`, `oauthDiscovery`, `oauthProtectedResource`, `authMd`, `mcpServerCard`, `a2aAgentCard`, `agentSkills`, `webMcp`, `ard` |
| `commerce` | `x402`, `mpp`, `ucp`, `acp`, `ap2` |

The inventory is the scanner's, not this skill's. **Never hardcode it as a checklist** —
read whatever categories and checks the response contains. `triage_scan.py` iterates the
response, so a check added upstream flows through without a code change; only its effort
band falls back to the `M` default.

## Check key → guide slug

camelCase → kebab-case (`linkHeaders` → `link-headers`, `dnsAid` → `dns-aid`). The
exceptions are why the join is positional rather than computed: `webMcp` → `webmcp`,
`robotsTxtAiRules` → `ai-rules`. Use the `Implementation guide:` URL the response gives
you; do not construct one.

## Category → phase

| Category | Phase | Why |
|---|---|---|
| — | **P0** | whatever `nextLevel.requirements` names, promoted out of its category |
| `discoverability`, `contentAccessibility` | P1 | the foundation every agent hits first |
| `botAccessControl` | P2 | policy, not capability |
| `discovery` | P3 | the deep integration work |
| `commerce` | P4 | only meaningful when the site sells something |

Phases are **not** keyed to the readiness levels. The response exposes `nextLevel` only;
levels 3–5 have no requirement list until the site actually reaches level 2, so a
level-keyed plan would be invented rather than scanned.

Priority follows from the phase, via `/plan-to-issues`'s phase defaults: `P0`/`P1` →
`high`, `P2` → `medium`, `P3`/`P4` → `low`. Choosing the phase *is* choosing the
priority — there is no separate severity to set.

## Failure modes

| Symptom | Cause | Response |
|---|---|---|
| HTTP 404 on `/<url>` | the page-per-site URL does not exist | use `POST /api/scan` |
| HTTP 4xx/5xx from the API | site unreachable *by the scanner* | the site must be publicly reachable — localhost and private IPs cannot be scanned |
| `fixes.md` empty | agent-format call failed | run degrades to `nextLevel` prompts; the plan notes it |
| `joined_by: "slug"` in triage.json | block count ≠ fail count | check the warning for checks with no fix prose |
