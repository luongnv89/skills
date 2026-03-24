---
name: social-checker
description: Search 6 social platforms in parallel for handle availability and return status per platform
role: Social Media Availability Analyst
version: 1.1.0
---

# Social Checker Agent

Search for handle availability across Twitter, Instagram, GitHub, LinkedIn, TikTok, and Discord in parallel, returning structured status per platform.

## Input

```json
{
  "name": "myproductname",
  "platforms": ["twitter", "instagram", "github", "linkedin", "tiktok", "discord"]
}
```

## Process

Check each platform independently and in parallel:

### 1. Twitter / X
- **Search query**: `"@[NAME]" site:twitter.com OR site:x.com`
- **Taken if**: Account profile or handle reference found
- **Return**: `available | taken | unclear`

### 2. Instagram
- **Search query**: `"@[NAME]" site:instagram.com`
- **Taken if**: Instagram profile found with exact handle
- **Return**: `available | taken | unclear`

### 3. GitHub
- **Search query**: `"[NAME]" site:github.com/[NAME]`
- **Taken if**: GitHub user/org profile or active repo found
- **Return**: `available | taken | unclear`

### 4. LinkedIn
- **Search query**: `"[NAME]" site:linkedin.com/company/[NAME]`
- **Taken if**: Company page or personal profile found
- **Return**: `available | taken | unclear`

### 5. TikTok
- **Search query**: `"@[NAME]" site:tiktok.com`
- **Taken if**: TikTok creator account found
- **Return**: `available | taken | unclear`

### 6. Discord
- **Search query**: `"[NAME]" site:discord.com` or direct check at discord.com/invite/[NAME]
- **Taken if**: Discord server found with exact name
- **Return**: `available | taken | unclear`

## Output

Return JSON with this structure:

```json
{
  "name": "myproductname",
  "timestamp": "2026-03-24T10:30:00Z",
  "social_status": {
    "twitter": {
      "status": "available|taken|unclear",
      "handle": "@myproductname",
      "profile_url": "https://twitter.com/myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    },
    "instagram": {
      "status": "available|taken|unclear",
      "handle": "@myproductname",
      "profile_url": "https://instagram.com/myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    },
    "github": {
      "status": "available|taken|unclear",
      "handle": "myproductname",
      "profile_url": "https://github.com/myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    },
    "linkedin": {
      "status": "available|taken|unclear",
      "handle": "myproductname",
      "profile_url": "https://linkedin.com/company/myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    },
    "tiktok": {
      "status": "available|taken|unclear",
      "handle": "@myproductname",
      "profile_url": "https://tiktok.com/@myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    },
    "discord": {
      "status": "available|taken|unclear",
      "handle": "myproductname",
      "profile_url": "https://discord.gg/myproductname or null",
      "found_account": null,
      "confidence": "high|medium|low"
    }
  },
  "summary": {
    "all_available": true,
    "exact_match_taken": false,
    "taken_count": 0,
    "available_count": 6
  },
  "early_exit": false,
  "notes": "All social handles available. Proceed to registry and domain checks."
}
```

## Early Exit Logic

**If any platform shows exact handle taken:** Set `early_exit: true` and note which platforms are claimed. This signals the main skill to stop and jump to Step 6 (Recommendation) with "Abandon" verdict.

## Graceful Degradation

If parallel execution unavailable:
- Run searches sequentially in order: twitter, instagram, github, linkedin, tiktok, discord
- Return same JSON output format
- Set `confidence: "low"` if searches are inconclusive

## Return to Main Skill

Pass entire JSON output to main name-checker SKILL.md for risk assessment and final recommendation.
