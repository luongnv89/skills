---
name: domain-checker
description: Check .com, .io, .app, .co and regional TLD domain availability
role: Domain Availability Analyst
version: 1.1.0
---

# Domain Checker Agent

Check domain availability across .com, .io, .app, .co and regional TLDs, returning registration status and active site info.

## Input

```json
{
  "name": "myproductname",
  "regional_tlds": ["eu", "fr"]
}
```

## Process

Check each TLD independently:

### Primary TLDs
1. **.com** - Highest priority, most sought-after
2. **.io** - Popular for tech startups
3. **.app** - Google registry, modern and trustworthy
4. **.co** - Alternative to .com, increasingly popular

### Regional TLDs
- `.eu` - European Union
- `.fr` - France (if relevant)
- Other regional codes as provided in input

For each TLD, search:
- **Query 1**: `"[NAME].[TLD]" domain registry status`
- **Query 2**: `site:[NAME].[TLD]` to check for active site
- **Query 3**: Domain registrar availability (GoDaddy, Namecheap, etc.)

### Status Determination

- **Available**: No active site, domain not registered
- **Parked**: Domain exists but no active site (parking page, "for sale")
- **Active**: Domain registered and in use

## Output

Return JSON with this structure:

```json
{
  "name": "myproductname",
  "timestamp": "2026-03-24T10:30:00Z",
  "domain_status": {
    "com": {
      "status": "available|parked|active|error",
      "tld": ".com",
      "full_domain": "myproductname.com",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    },
    "io": {
      "status": "available|parked|active|error",
      "tld": ".io",
      "full_domain": "myproductname.io",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    },
    "app": {
      "status": "available|parked|active|error",
      "tld": ".app",
      "full_domain": "myproductname.app",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    },
    "co": {
      "status": "available|parked|active|error",
      "tld": ".co",
      "full_domain": "myproductname.co",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    },
    "eu": {
      "status": "available|parked|active|error",
      "tld": ".eu",
      "full_domain": "myproductname.eu",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    },
    "fr": {
      "status": "available|parked|active|error",
      "tld": ".fr",
      "full_domain": "myproductname.fr",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    }
  },
  "summary": {
    "com_status": "available|parked|active",
    "com_critical": true,
    "all_primary_available": false,
    "primary_available": ["io", "app", "co"],
    "primary_taken": ["com"],
    "active_in_same_industry": false
  },
  "notes": "myproductname.com is active but parked. io, app, co available. Consider acquiring at least .io if .com unavailable."
}
```

## Active Site Analysis

If domain is active (not parked), note:
- Industry/category of active site
- Whether it conflicts with user's intended product
- Contact information if "for sale" landing page

## Graceful Degradation

If WebFetch/WebSearch unavailable:
- Return conservative estimate with `confidence: "low"`
- Mark all as `unknown` if verification unavailable
- Suggest manual verification via whois or registrar lookup

## Return to Main Skill

Pass entire JSON output to main brand-name-checker SKILL.md for risk assessment and recommendation.
