# Source Checks (Steps 1-4)

Per-source queries and status rules for the four checks in `SKILL.md` → *Analysis Protocol*. This file is their single home: `agents/source-checker.md` reads the section for its `check`, and without subagents Steps 1-4 run inline from it.

**Tools.** Any working HTTP tool (WebFetch, an MCP fetch tool, or `curl` in a shell) can fetch the direct endpoints below, and any web-search tool can run the queries. Each source lists its direct endpoint first: use it, and run the search query only when the source has none or its endpoint cannot be reached, and say so in the evidence. Put only the normalized slug of the name (`references/edge-cases.md`: letters `a-z`, digits and `-`, starting and ending with a letter or digit) into a URL or a shell command, never the raw input. A `[TLD]` or a WHOIS server name goes into a URL or command only as a plain label or hostname (letters, digits, `-` and `.`, starting with a letter or digit), and an RDAP base only as an `https://` URL read from the IANA bootstrap file.

Record each result as one of the statuses below, together with the source that produced it (the query or URL) and the time it was checked. A source that cannot be reached is `Unknown`, never clear.

## Step 1: Social Media Check

Check each platform through its direct endpoint when it has one, else through its search query:

| Platform | Direct endpoint | Search query |
|----------|-----------------|--------------|
| X/Twitter | none | `"@[NAME]" site:twitter.com OR site:x.com` |
| Instagram | none | `"@[NAME]" site:instagram.com` |
| GitHub | `https://api.github.com/users/[NAME]` (users and organizations): 200 is `taken (exact)`, 404 is `available`, a 403 or 429 rate limit is `unknown` | `"[NAME]" site:github.com/[NAME]` |
| LinkedIn | none | `"[NAME]" site:linkedin.com/company/[NAME]` |
| TikTok | none | `"@[NAME]" site:tiktok.com` |
| Discord | `https://discord.com/api/v10/invites/[NAME]`: 200 with a server is `taken (exact)`, 404 means the invite name is unused (`available`), a 403 or 429 is `unknown` | `"[NAME]" site:discord.com` |

Statuses: `available`, `taken (exact)`, `similar (non-exact)`, `unknown`.

- `taken (exact)`: a profile whose handle equals the name exactly.
- `similar (non-exact)`: a close variant of the name.
- `unknown`: the search was inconclusive or the platform could not be reached.

If any platform returns `taken (exact)`, apply the Early-Exit Rule: return `NEGATIVE: Exact social handle taken (@platform)` and stop the remaining source checks.

## Step 2: Package Registry Check

Package registries are first-come-first-served namespaces. Unlike GitHub, which allows duplicate project names, a registry enforces unique names: once someone claims a name on PyPI or npm, nobody else can publish under it. If the name is taken on a registry the user plans to publish to, the user needs a different name or a naming variant (prefix or suffix).

Fetch each registry's endpoint with any HTTP tool:

| Registry | Check URL | Taken if... |
|----------|-----------|-------------|
| **npm** | `https://registry.npmjs.org/[NAME]` | Returns JSON with package data (not a 404) |
| **PyPI** | `https://pypi.org/pypi/[NAME]/json` | Returns JSON with package data (not a 404) |
| **Homebrew** | `https://formulae.brew.sh/api/formula/[NAME].json` | Returns JSON (not a 404) |
| **apt** | `https://packages.debian.org/search?keywords=[NAME]&searchon=names&exact=1&suite=all&section=all`, and the same query on `packages.ubuntu.com` | Either page lists `Exact hits`; `Sorry, your search gave no results` on both is not found, and a no-results answer from only one is Unknown |

When the Debian and Ubuntu pages cannot be reached, fall back to the search `"[NAME]" site:packages.debian.org OR site:packages.ubuntu.com` and say so in the evidence. A listing found there is Taken; a search with no listing leaves apt Unknown.

Report each registry as:

- **Available**: the registry source returned 404 or not found. Record the source evidence and its scope.
- **Taken**: the package exists. Record the owner, the description, and the last publish date; for Homebrew, the repository or tap; for apt, the maintainer and version. A recently claimed but empty package can indicate namespace squatting. So can a stale one: last published more than 2 years ago, with no description or a placeholder name, or an owner who looks inactive. Note it in the evidence, and say the user can contact the maintainer about a takeover or pick a different name.
- **Similar**: no exact match, but close variants exist (for example `name-js`, `py-name`).
- **Unknown**: the registry did not answer, or answered with an error other than 404.

If the name is taken on a target registry, flag it at the top of the registry line and suggest variants such as `name-cli`, `name-py`, `name-lib`, or an npm org scope like `@org/name`. If the target registries are not stated and cannot be read from `prd.md`, record the target intent as unknown. Do not treat every registry as clear.

## Step 3: Domain Check

Check `.com` first, then `.io` and `.app`. Add `.co`, `.eu`, `.fr` or another TLD only when `prd.md` or the user names it (`SKILL.md` → *Step 3: Domain Check*).

Ask the TLD's registry first, by RDAP or WHOIS. A search or a registrar's availability page is only a fallback. For each `[NAME].[TLD]`:

1. **RDAP.** Read the TLD's RDAP base URL from the IANA bootstrap file `https://data.iana.org/rdap/dns.json` and fetch `<base>domain/[NAME].[TLD]`. A 404 from that registry server means not found. A 200 means registered: record the registrar (the `entities` entry with role `registrar`) and the expiry date (the `events` entry with action `expiration`). When the bootstrap file lists no RDAP server for the TLD, go to WHOIS. Never count a 404 from a redirector such as `rdap.org` for a TLD with no RDAP server: it answers 404 for registered domains too.
2. **WHOIS.** Ask IANA for the TLD's WHOIS server (`whois -h whois.iana.org [TLD]`, the `whois:` line), then query that server: `whois -h <server> [NAME].[TLD]`. Its not-found reply (for example `Domain not found.` or `No match`) means not found; a record that names a registrar means registered. Any other reply (a rate-limit notice, a reply that is neither) is a failure. A reserved or blocked notice in an RDAP or WHOIS reply makes the domain Unknown, never Available; a premium-price notice keeps it Available and goes into the evidence.
3. **One method failed.** No answer, a host that does not resolve, a timeout, a 403, 429 or 5xx, or an empty reply is a failure, not an answer. Try the other method before giving up on the TLD. A failed WHOIS never ends the check while RDAP is untried, and a failed RDAP never ends it while WHOIS is untried.
4. **Status.** A registry not-found reply is Available; cite the RDAP URL or the WHOIS command and its reply as the evidence. For a registered domain, fetch `https://[NAME].[TLD]` to tell Active from Parked; a `site:[NAME].[TLD]` search result alone decides neither. For an active site, record its industry and whether it overlaps the user's product. For a parked or for-sale page, record the sale contact. A registered domain is Parked only when its page shows parking or a sale offer. A fetch that times out, is blocked, returns a 403, 429 or 5xx, or fails to resolve, or a page that shows neither a site nor parking, leaves Active or Parked undecided: record the domain as Unknown and name the fetch in the evidence.
5. **Fallback, still Unknown.** When neither RDAP nor WHOIS answers, run `"[NAME].[TLD]" domain availability` and look the domain up in a registrar's availability search (for example GoDaddy or Namecheap). Record what they show in the evidence, but the status stays Unknown; name the RDAP or WHOIS lookup that would verify it. Only a site that answers at `https://[NAME].[TLD]` can still show the domain is registered (Active or Parked); nothing short of the registry shows it is Available.

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
