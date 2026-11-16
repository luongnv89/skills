---
name: domain-checker
description: Check .com, .io and .app domain availability, plus any TLD the user or prd.md names
role: Domain Availability Analyst
version: 1.1.0
---

# Domain Checker Agent

Check domain availability for .com, .io and .app, plus any TLD in `extra_tlds`, returning registration status and active site info.

## Input

```json
{
  "name": "myproductname",
  "extra_tlds": []
}
```

## Process

Check each TLD independently:

### Primary TLDs
1. **.com** - Highest priority, most sought-after
2. **.io** - Popular for tech startups
3. **.app** - Google registry, modern and trustworthy

### Extra TLDs
- Check `.co`, `.eu`, `.fr` or another TLD only when it is in `extra_tlds`, which the caller fills only when `prd.md` or the user names it
- Each extra TLD adds one entry to `domain_status`, shaped like the entries below

For each TLD, search:
- **Query 1**: `"[NAME].[TLD]" domain registry status`
- **Query 2**: `site:[NAME].[TLD]` to check for active site
- **Query 3**: Domain registrar availability (GoDaddy, Namecheap, etc.)

### Status Determination

- Available: an authoritative availability result confirms the domain is unregistered
- Parked: Domain exists but is for-sale/parking
- Active: In use (flag if same industry)
- Unknown: the source is unavailable or only shows that no active site was found; do not infer availability

## Output

Return JSON with this structure:

```json
{
  "name": "myproductname",
  "timestamp": "2026-03-24T10:30:00Z",
  "domain_status": {
    "com": {
      "status": "available|parked|active|unknown",
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
      "status": "available|parked|active|unknown",
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
      "status": "available|parked|active|unknown",
      "tld": ".app",
      "full_domain": "myproductname.app",
      "site_found": false,
      "site_description": null,
      "site_industry": null,
      "registrar": "registrar name or null",
      "expiry": "2026-04-15 or null",
      "confidence": "high|medium|low"
    }
  },
  "summary": {
    "com_status": "available|parked|active|unknown",
    "com_critical": true,
    "all_primary_available": false,
    "primary_available": ["io", "app"],
    "primary_taken": ["com"],
    "active_in_same_industry": false
  }
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
