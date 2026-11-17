# Source Checks (Steps 1-4)

Per-source queries and status rules for the four checks in `SKILL.md` → *Analysis Protocol*. This file is their single home: `agents/source-checker.md` reads the section for its `check`, and without subagents Steps 1-4 run inline from it.

Record each result as one of the statuses below, together with the source that produced it (the query or URL) and the time it was checked. A source that cannot be reached is `Unknown`, never clear.

## Step 1: Social Media Check

Run one WebSearch per platform:

| Platform | Query |
|----------|-------|
| X/Twitter | `"@[NAME]" site:twitter.com OR site:x.com` |
| Instagram | `"@[NAME]" site:instagram.com` |
| GitHub | `"[NAME]" site:github.com/[NAME]` |
| LinkedIn | `"[NAME]" site:linkedin.com/company/[NAME]` |
| TikTok | `"@[NAME]" site:tiktok.com` |
| Discord | `"[NAME]" site:discord.com`, or open `discord.com/invite/[NAME]` |

Statuses: `available`, `taken (exact)`, `similar (non-exact)`, `unknown`.

- `taken (exact)`: a profile whose handle equals the name exactly.
- `similar (non-exact)`: a close variant of the name.
- `unknown`: the search was inconclusive or the platform could not be reached.

If any platform returns `taken (exact)`, apply the Early-Exit Rule: return `NEGATIVE: Exact social handle taken (@platform)` and stop the remaining source checks.

## Step 2: Package Registry Check

Package registries are first-come-first-served namespaces. Unlike GitHub, which allows duplicate project names, a registry enforces unique names: once someone claims a name on PyPI or npm, nobody else can publish under it. If the name is taken on a registry the user plans to publish to, the user needs a different name or a naming variant (prefix or suffix).

Use WebFetch for each registry:

| Registry | Check URL | Taken if... |
|----------|-----------|-------------|
| **npm** | `https://registry.npmjs.org/[NAME]` | Returns JSON with package data (not a 404) |
| **PyPI** | `https://pypi.org/pypi/[NAME]/json` | Returns JSON with package data (not a 404) |
| **Homebrew** | `https://formulae.brew.sh/api/formula/[NAME].json` | Returns JSON (not a 404) |
| **apt** | Search: `"[NAME]" site:packages.debian.org OR site:packages.ubuntu.com` | Package listing found |

Report each registry as:

- **Available**: the registry source returned 404 or not found. Record the source evidence and its scope.
- **Taken**: the package exists. Record the owner, the description, and the last publish date; for Homebrew, the repository or tap; for apt, the maintainer and version. A recently claimed but empty package can indicate namespace squatting. So can a stale one: last published more than 2 years ago, with no description or a placeholder name, or an owner who looks inactive. Note it in the evidence, and say the user can contact the maintainer about a takeover or pick a different name.
- **Similar**: no exact match, but close variants exist (for example `name-js`, `py-name`).
- **Unknown**: the registry did not answer, or answered with an error other than 404.

If the name is taken on a target registry, flag it at the top of the registry line and suggest variants such as `name-cli`, `name-py`, `name-lib`, or an npm org scope like `@org/name`. If the target registries are not stated and cannot be read from `prd.md`, record the target intent as unknown. Do not treat every registry as clear.

## Step 3: Domain Check

Check `.com` first, then `.io` and `.app`. Add `.co`, `.eu`, `.fr` or another TLD only when `prd.md` or the user names it (`SKILL.md` → *Step 3: Domain Check*).

For each TLD, run `"[NAME].[TLD]" domain registry status`, `"[NAME].[TLD]" domain availability` and `site:[NAME].[TLD]`, and look the domain up in a registrar's availability search (for example GoDaddy or Namecheap). Record the registrar and expiry date when a source shows them. For an active site, record its industry and whether it overlaps the user's product. For a parked or for-sale page, record the sale contact. For an Unknown domain, name a WHOIS or registrar lookup as the way to verify it.

The statuses (Available, Parked, Active, Unknown) are defined in `SKILL.md` → *Step 3: Domain Check*. A search that finds no site proves nothing about registration; record it as Unknown.

## Step 4: Trademark Check

| Database | Direct search | Fallback query |
|----------|---------------|----------------|
| WIPO | `https://branddb.wipo.int` | `"[NAME]" site:branddb.wipo.int` |
| EUIPO | `https://euipo.europa.eu/eSearch` | `"[NAME]" site:euipo.europa.eu` |
| INPI (France) | `https://www.inpi.fr` (French register) | `"[NAME]" site:inpi.fr` |

Search each database directly first. When the direct search cannot be used, run the fallback query and say in the evidence that the status rests on a web search, which is weaker evidence than the register itself.

Limit the conflict review to Nice Classes 9, 35, and 42 (software and technology). For each mark found, record whether it is live or expired, its class, and its owner, so `SKILL.md` Step 5 can tell an active conflict from an expired one.

Statuses: `clear`, `similar`, `conflicts_found`, `unknown`.

- `clear`: the database answered and shows no identical or similar mark in those classes. Marks found only in other classes go in the evidence and leave the status `clear`.
- `similar`: no identical mark, but a close variant is on file in those classes.
- `conflicts_found`: a mark identical to the name is on file in those classes, live or expired; the evidence says which.
- `unknown`: the database could not be queried, or the result was inconclusive.
