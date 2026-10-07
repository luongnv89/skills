# Source Checks (Steps 1-4)

Per-source queries and status rules for the four checks in `SKILL.md` → *Analysis Protocol*. The per-source workers in `agents/*.md` carry the same queries plus their JSON output schemas; this file is the inline fallback when subagents are unavailable.

Record each result as one of the statuses below, together with the source that produced it (the query or URL) and the time it was checked. A source that cannot be reached is `Unknown`, never clear.

## Step 1: Social Media Check

Run one WebSearch per platform:

| Platform | Query |
|----------|-------|
| X/Twitter | `"@[NAME]" site:twitter.com OR site:x.com` |
| Instagram | `"@[NAME]" site:instagram.com` |
| GitHub | `"[NAME]" site:github.com/[NAME]` |
| LinkedIn | `"[NAME]" site:linkedin.com/company` |
| TikTok | `"@[NAME]" site:tiktok.com` |
| Discord | `"[NAME]" site:discord.com` |

Statuses: `available`, `taken (exact)`, `similar (non-exact)`, `unknown`.

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
- **Taken**: the package exists. Record the owner, the description, and the last publish date. A recently claimed but empty package can indicate namespace squatting.
- **Similar**: no exact match, but close variants exist (for example `name-js`, `py-name`).
- **Unknown**: the registry did not answer, or answered with an error other than 404.

If the name is taken on a target registry, flag it at the top of the registry line and suggest variants such as `name-cli`, `name-py`, `name-lib`, or an npm org scope like `@org/name`. If the target registries are not stated and cannot be read from `prd.md`, record the target intent as unknown. Do not treat every registry as clear.

## Step 3: Domain Check

Check `.com` first, then `.io`, `.app`, `.co`, and the regional TLDs `.eu` and `.fr`.

Queries: `site:[NAME].com` and `"[NAME].com" domain availability`.

The statuses (Available, Parked, Active, Unknown) are defined in `SKILL.md` → *Step 3: Domain Check*. A search that finds no site proves nothing about registration; record it as Unknown.

## Step 4: Trademark Check

| Database | Query |
|----------|-------|
| WIPO | `"[NAME]" site:branddb.wipo.int` |
| EUIPO | `"[NAME]" site:euipo.europa.eu` |
| INPI (France) | `"[NAME]" site:inpi.fr` |

Limit the conflict review to Nice Classes 9, 35, and 42 (software and technology). For each mark found, record whether it is live or expired, its class, and its owner. Record a database that cannot be queried as Unknown.
