# Phase 3: Policy Compliance Check

Validate every piece of proposed metadata against Apple App Store and Google Play Store policies before presenting the plan.

## 3.1 Prohibited Keyword Scan

Check all proposed metadata fields (title, subtitle, keywords, short description, full description) for prohibited terms.

**Apple App Store — Banned in title, subtitle, and keywords:**
- Pricing terms: "free", "sale", "discount", "limited time"
- Superlative claims: "best", "#1", "top-rated", "must-have", "top app"
- Reserved terms: "For Kids", "For Children" (unless Kids Category), "Editor's Choice"
- Platform references: "Android", "Google Play", "Play Store"
- Call-to-action: "download now", "install now", "try now"

**Google Play — Banned in title, short description, developer name, and icon:**
- Performance claims: "top", "best", "#1", "number one", "popular"
- Pricing terms: "free", "no ads", "ad free"
- Promotional terms: "new", "hot", "first", "bonus", "discount", "sale", "million downloads"
- Ranking claims: "App of the Year", "Best Google Play App of [year]"
- Call-to-action: "download now", "install now", "play now", "try now", "update now"

## 3.2 Trademark and Competitor Check

Scan all proposed metadata for:
- **Competitor brand names** — Must be removed from title, subtitle, keywords, descriptions
- **Trademarked terms** — Any trademarked term the user doesn't own or have a license for must be flagged
- **Celebrity names** — Unless explicitly authorized
- **Apple/Google trademarks** — Cannot suggest endorsement

## 3.3 Formatting Compliance

- [ ] No emojis or special characters in title/subtitle (both stores)
- [ ] No ALL CAPS in title/subtitle unless registered brand name
- [ ] No repeated special characters
- [ ] Title within character limits (30 chars both stores)
- [ ] No unattributed user testimonials or fake reviews in metadata
- [ ] No graphic elements in icon suggesting store rankings (Google Play)

## 3.4 Content Accuracy Check

- [ ] No unverifiable claims ("fastest", "most popular", "award-winning" without evidence)
- [ ] Description accurately reflects app features
- [ ] Screenshots show the actual app in use
- [ ] In-app purchases and subscriptions clearly disclosed
- [ ] No misleading descriptions of app functionality

## 3.5 Compliance Report Template

```markdown
## Store Policy Compliance Report

### Prohibited Keyword Check
| Proposed Term | Field | Store | Status | Issue | Fix |

### Trademark Check
| Term | Field | Risk Level | Action |

### Formatting Check
- [x] or [ ] for each formatting rule

### Content Accuracy Check
- [x] or [ ] for each accuracy rule

### Overall Status: PASS / NEEDS REVISION
```

If any violations are found, **revise the plan to fix all issues before presenting to the user**.

## Present for Approval

After the compliance check passes, present both the ASO plan and the compliance report:

> "Here's the ASO plan based on my analysis. All proposed metadata has been validated — no prohibited keywords, trademark violations, or policy issues found.
>
> Please review each section. Let me know:
> 1. Which recommendations you approve
> 2. Which you'd like to modify
> 3. Any you want to skip
> 4. Any additional ideas to include"

**Do not proceed to Phase 4 until the user explicitly approves the plan.** Each revision must pass the compliance check again.
