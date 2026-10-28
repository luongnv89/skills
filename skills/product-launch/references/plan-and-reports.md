# Platform index, fit rubric, scheduling, plan and reports

Only the main agent reads this file: §1–§5 in Step 2 (fit table) and Step 4 (timeline),
§6–§11 in Steps 4, 5c and 8 and on the Resume branch. §1–§5 hold everything Steps 2 and 4
need, so the main agent never opens a family file. It holds one row per catalog platform:
the 50 launch sites plus the founder's own channels. Detail for each platform is in the
family file named in the `File` column, and only workers read those files. Facts were
verified on 2026-10-22. Step 3 re-checks the volatile cells (free path, paid from, free
wait, status) for shortlisted platforms only.

## 1. Gate every platform

There are two kinds of gate. Gate fields are Product Profile field names.

- An **exclusion gate** fails only when the profile shows the excluded value. A field
  marked `unknown` passes, and goes into the plan as an assumption.
- A **requirement gate** fails unless the profile shows the required value. A field marked
  `unknown` fails, with the reason "unknown: <field>", so the user can correct it at the
  gate.
- A value marked `(inferred: …)` counts like a stated value. List it under assumptions.

Record each failed gate in the fit table.

| Exclusion gate     | Fails when                                                                   | Platforms                                                                                       |
| ------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Not usable now     | `availability` is waitlist, invite-only or not launched ("usable after sign-up" passes) | hacker-news, uneed, saashub, future-tools, saascity, pitchwall, capterra. product-hunt is scored but flagged "not featured while waitlisted". |
| Free subdomain     | `domain` is a free subdomain (vercel.app, netlify.app, herokuapp.com, github.io) | betalist, saashub, saascity                                                               |
| No English version | `languages` lacks English                                                    | saashub, sideprojectors, startup-fame                                                           |
| B2C or pre-release | `model` is B2C, or `stage` is pre-launch or beta                             | g2                                                                                              |
| Launched a while ago | `stage` is launched with a date more than 4 weeks ago                      | betalist                                                                                        |
| Promotion product  | `category_flags` is yes                                                      | r/SaaS                                                                                          |
| Not taking launches | the index status                                                            | crazy-about-ai, 500-tools. tiny-startups is planned as paid only.                               |

| Requirement gate | Passes when                                                                  | Platforms                                              |
| ---------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------ |
| AI-powered       | `ai` is yes                                                                  | theresanaiforthat, futurepedia, toolify, future-tools  |
| Developer tool   | `audience` includes developers, or `product_type` is CLI, library, API or MCP server | devhunt                                       |
| B2B              | `model` is B2B or both                                                       | g2, trustradius                                        |
| Open source      | `license` is an OSS license **and** `code_public` is a public repository URL | sourceforge (hosting)                                  |
| Public code      | `code_public` is a public repository URL                                     | github                                                 |
| Hiring           | `hiring` is yes                                                              | wellfound                                              |
| Confetti moment  | `confetti_moment` is yes                                                     | confetti-saas                                          |
| News angle       | `news_angle` is not "none"                                                   | slashdot                                               |
| Email audience   | `channels` lists a waitlist or newsletter                                    | email-list                                             |

**geeknews** has no gate. The plan marks it "needs a Korean speaker to review", and the
user decides at the approval gate.

### Subreddits (reddit gets one fit-table row, listing the subreddits that pass)

Pick at most 3 subreddits that pass, highest audience fit first. Their full rules are in
`platforms-core.md`, which only the writers read.

| Subreddit             | Passes when                                                                                  | Allowed day                            |
| --------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------- |
| r/SideProject         | always                                                                                       | any day                                |
| r/startups            | always, but only in the stickied threads                                                     | quarterly "Share your startup" thread, Feedback Friday |
| r/SaaS                | `product_type` is SaaS and `category_flags` is no                                            | any day, if the post is helpful        |
| r/indiehackers        | always                                                                                       | once per product, "SHOW IH" flair      |
| r/webdev              | a web app or dev tool that is free (no commercial promotion)                                 | Saturday only                          |
| r/selfhosted          | `self_hostable` is yes                                                                       | weekly megathread if under 3 months old |
| r/opensource          | the open-source requirement passes                                                           | any day, "Promotional" flair           |
| r/coolgithubprojects  | `code_public` is a public GitHub URL                                                         | any day                                |
| r/InternetIsBeautiful | a free single-purpose website: not paid or freemium, no sign-up wall, `ai` no, not an extension, download or game, own domain | any day                |
| r/alphaandbetausers   | `stage` is alpha or beta, and the product is usable now                                      | any day                                |
| r/MacApps             | `platforms` includes macOS                                                                   | monthly "App Pile" megathread, unless the founder qualifies for Trust or Transparency |
| r/iOSProgramming      | `platforms` includes iOS                                                                     | Saturday, once per app per year        |
| r/chrome_extensions   | `product_type` is a browser extension                                                        | any day                                |
| r/LocalLLaMA          | `ai` is yes and the model runs locally                                                       | any day, at most 1/10 self-promotion   |
| r/artificial          | `ai` is yes (rules unverified)                                                               | any day, after reading the rules       |
| r/programming         | a technical write-up exists (founder-voice, its own file)                                     | any day                                |
| r/androidapps, r/devops, r/EntrepreneurRideAlong | never (self-promotion banned, or rules unverified)                   | none                                   |

## 2. Score each eligible platform from 0 to 10

| Component     | Points | Rule                                                                                                                                                        |
| ------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Audience fit  | 0–4    | Compare the platform's `Fits` with the profile's `audience` and `ideal_customer`. 4: the platform names that audience. 3: the audience is a large share (developers and tech early adopters on product-hunt or hacker-news). 2: general makers and early adopters (most launch boards). 1: weak overlap. 0: none. |
| Reach         | 0–3    | The `Reach` column: A=3, B=2, C=1. For own channels, 2 when `channels` lists one, else 1.                                                                    |
| Cost          | 0–2    | 2: free with no conditions. 1: free with a badge, backlink or engagement task, or paid at ≤$40 and within budget. 0: paid only above $40, or outside budget. |
| Timing        | 0–1    | 1: it can go live between L-day and L+30, by its free wait or by a paid option within budget (§5). 0: it cannot.                                             |

Write all four components into the fit table, so the user can audit any score. Break
ties by higher audience fit, then lower cost, then catalog order.

## 3. Tier the shortlist

Take the rows top to bottom. The first row that matches a platform sets its tier.

| Tier            | Rule                                                                                     | Cap  |
| --------------- | ---------------------------------------------------------------------------------------- | ---- |
| Core            | product-hunt, hacker-news or reddit, with score ≥6                                        | 3    |
| Launch week     | kind "launch board", score ≥6                                                             | 8    |
| Community       | kind community, content or code host (not Core), score ≥5                                 | 4    |
| Directory drip  | kind directory, review site or AI directory, score ≥5                                     | 10   |
| Profiles        | crunchbase when the product has a company; wellfound when its gate passes                 | none |
| Own channels    | x and linkedin always; email-list when its gate passes                                    | none |
| Skip            | everything else, with a reason: a failed gate, "score N below the tier threshold", or "over cap: lower score than <id>" | none |

The user can move any skipped platform back in at the approval gate.

## 4. Index

`File`: core = `platforms-core.md`, boards = `platforms-launch-boards.md`, dirs =
`platforms-directories.md`. `Link`: badge-dofollow means dofollow only while their badge
is live. Mode `voice` means founder-voice. `Conf`: H, M or L.

| id                  | Platform               | File   | Kind          | Fits                                    | Free path                               | Paid from        | Free wait            | Cadence                    | Link              | Reach | Mode   | Conf |
| ------------------- | ---------------------- | ------ | ------------- | --------------------------------------- | --------------------------------------- | ---------------- | -------------------- | -------------------------- | ----------------- | ----- | ------ | ---- |
| product-hunt        | Product Hunt           | core   | launch board  | new tech products usable now            | yes (account ≥1 week old)               | none (ads only)  | schedule ≤30 days    | daily 12:01 AM PT          | unknown           | A     | paste  | H    |
| hacker-news         | Hacker News (Show HN)  | core   | community     | things people can try; dev, OSS         | yes                                     | none             | none                 | continuous                 | nofollow at first | A     | voice  | H    |
| reddit              | Reddit                 | core   | community     | per subreddit table                     | yes (subreddit gates)                   | ads only         | karma/age per subreddit | per subreddit days      | nofollow (unverified) | A | paste* | M    |
| geeknews            | GeekNews               | core   | community     | Korean devs and founders; usable things | yes (account ≥1 week old)               | none             | 1 week (account)     | continuous                 | nofollow          | B     | paste (ko) | H |
| indie-hackers       | Indie Hackers          | core   | community     | indie and bootstrapped products         | yes                                     | none             | none                 | daily Build Board          | nofollow          | B     | paste  | M    |
| slashdot            | Slashdot               | core   | community     | newsworthy tech stories                 | yes (editorial)                         | none             | editorial            | editorial                  | dofollow (story)  | B     | paste  | M    |
| hashnode            | Hashnode               | core   | content       | technical launch articles               | yes                                     | $5/mo (domain)   | none                 | hot feed                   | unknown           | C     | paste  | M    |
| github              | GitHub                 | core   | code host     | OSS, CLIs, libraries, dev tools         | yes                                     | none             | none                 | Trending                   | nofollow          | A     | paste* | H    |
| x                   | X (own)                | core   | own channel   | the founder's followers                 | yes                                     | none             | none                 | your timing                | n/a               | own   | paste  | n/a  |
| linkedin            | LinkedIn (own)         | core   | own channel   | B2B and professional network            | yes                                     | none             | none                 | your timing                | n/a               | own   | paste  | n/a  |
| email-list          | Email list (own)       | core   | own channel   | your waitlist or newsletter             | yes                                     | none             | none                 | L-day                      | n/a               | own   | paste  | n/a  |
| what-launched-today | What Launched Today    | boards | launch board  | any tech product                        | yes                                     | €27              | ~3 months            | daily 00:00 UTC            | dofollow          | C     | paste  | H    |
| betalist            | BetaList               | boards | launch board  | pre-launch or just-launched startups    | no (refunded if rejected)               | after sign-in    | by plan              | editorial                  | dofollow (paid)   | B     | paste  | M    |
| uneed               | Uneed                  | boards | launch board  | SaaS, dev, AI, apps, extensions         | yes (score ≥10 to stay)                 | $14.99           | ≥30 days             | daily 12:00 AM PST         | dofollow if score ≥20 | B | paste  | H    |
| peerlist            | Peerlist Launchpad     | boards | launch board  | coding/design projects, digital products | yes (verified profile)                 | none             | none (weekly)        | weekly, Monday             | top 5 only        | B     | paste  | M    |
| devhunt             | DevHunt                | boards | launch board  | developer tools only                    | listing only                            | $19              | n/a                  | weekly Tue 00:00 UTC       | dofollow (paid)   | B     | paste  | H    |
| launching-next      | Launching Next         | boards | launch board  | startups, side projects                 | yes (editorial)                         | $99              | unstated             | editorial                  | mixed             | C     | paste  | M    |
| microlaunch         | Microlaunch            | boards | launch board  | startups, software                      | queue (unpublished)                     | $39              | unpublished          | monthly                    | dofollow          | C     | paste  | M    |
| betterlaunch        | BetterLaunch           | boards | launch board  | live software                           | yes                                     | $9 (skip)        | ≥45 days (−14 by voting 3) | weekly Mon 00:00 UTC | badge-dofollow    | C     | paste  | H    |
| foundrlist          | FoundrList             | boards | launch board  | products you own                        | badge, or 3 upvotes + 1 comment         | $29              | ~4 weeks             | weekly Mon 12:01 AM PT     | dofollow (paid)   | C     | paste  | H    |
| peerpush            | PeerPush               | boards | launch board  | web, mobile, API, CLI, MCP              | queue, or 400 points                    | $39              | unpublished          | continuous                 | dofollow          | C     | paste  | H    |
| startupbase         | StartupBase            | boards | launch board  | products with a working site            | badge (4–5 weeks) or none (10+ weeks)   | $39              | 4–10+ weeks          | daily 12:00 AM PDT         | dofollow (paid)   | C     | paste  | H    |
| aura-plus-plus      | Aura++                 | boards | launch board  | real working software                   | yes (5 slots a day)                     | $29              | review 24–48 h       | daily 08:00 UTC            | top 3 + badge     | C     | paste  | H    |
| shipybara           | Shipybara              | boards | launch board  | tech products                           | yes (18 slots a week)                   | $50              | slot capacity        | weekly Mon 00:00 UTC       | top 3 or badge    | C     | paste  | M    |
| saascity            | SaaSCity               | boards | launch board  | SaaS, AI, dev tools                     | badge (15 slots a week)                 | $19.99           | weeks to ~336 days   | weekly Mon 00:00 UTC       | badge-dofollow    | C     | paste  | H    |
| pitchwall           | Pitchwall              | boards | launch board  | AI, SaaS, OSS, tech with a demo         | yes                                     | $49              | ≥30 days             | daily                      | dofollow          | C     | paste  | M    |
| scrolllaunch        | ScrollLaunch           | boards | launch board  | SaaS, apps, AI                          | yes (25 slots a week)                   | $39              | week capacity        | weekly ISO week            | badge-dofollow    | C     | paste  | H    |
| discoverlaunches    | DiscoverLaunches       | boards | launch board  | SaaS, AI, dev tools                     | gate (20 slots a week)                  | $9               | week capacity        | weekly ISO week            | badge-dofollow    | C     | paste  | H    |
| rank-in-public      | Rank in Public         | boards | launch board  | SaaS (tournament)                       | yes                                     | $29              | ~6 weeks             | weekly tournaments         | badge-dofollow    | C     | paste  | M    |
| tinylaunch          | TinyLaunch             | boards | launch board  | startups, products                      | yes                                     | $39              | ~4–5 weeks           | weekly Monday              | top 3 + badge     | C     | paste  | H    |
| tiny-startups       | Tiny Startups          | boards | launch board  | indie startups                          | paused (2026-10-22)                     | £69              | n/a                  | weekly Mon–Sun             | dofollow (paid)   | C     | paste  | M    |
| nick-launches       | Nick Launches          | boards | launch board  | indie AI, SaaS, dev tools               | badge                                   | $19              | earliest week with room | weekly Mon–Sun         | badge-dofollow    | C     | paste  | M    |
| alternativeto       | AlternativeTo          | dirs   | directory     | any software, incl. OSS                 | yes                                     | priority fee     | long, no date        | evergreen                  | unknown           | B     | paste  | H    |
| saashub             | SaaSHub                | dirs   | directory     | SaaS, software, OSS                     | yes                                     | $99/mo           | unpublished          | evergreen                  | dofollow if verified | B  | paste  | H    |
| g2                  | G2                     | dirs   | review site   | B2B software (reviews)                  | yes (free profile)                      | $299/mo          | 4–8 business days    | review-driven              | unknown           | A     | paste  | H    |
| capterra            | Capterra (+GetApp)     | dirs   | review site   | packaged business software              | yes (no click-out)                      | PPC              | unpublished          | review-driven              | none (free)       | A     | paste  | M    |
| getapp              | GetApp                 | dirs   | review site   | covered by the capterra profile         | via capterra                            | via capterra     | n/a                  | n/a                        | none (free)       | B     | n/a    | M    |
| trustradius         | TrustRadius            | dirs   | review site   | B2B tech, mid-market and enterprise     | claim profile                           | demo only        | unpublished          | review-driven              | unknown           | B     | paste  | M    |
| sourceforge         | SourceForge            | dirs   | code host     | OSS hosting; business listing           | yes (OSS)                               | by budget        | immediate (OSS)      | evergreen                  | unknown           | C     | paste  | M    |
| sideprojectors      | SideProjectors         | dirs   | directory     | side projects (showcase or sale)        | yes                                     | priority fee     | 24 h–5 days          | evergreen                  | unknown           | C     | paste  | M    |
| startup-fame        | Startup Fame           | dirs   | directory     | startups with an English site, DR >0    | badge                                   | $19/mo           | several days         | evergreen                  | dofollow          | C     | paste  | H    |
| crunchbase          | Crunchbase             | dirs   | profile       | any company (credibility)               | yes                                     | none             | none                 | static                     | unknown           | B     | paste  | M    |
| wellfound           | Wellfound              | dirs   | profile       | hiring only                             | yes (job posts)                         | $200/ad          | n/a                  | n/a                        | unknown           | C     | paste  | M    |
| twelve-tools        | Twelve Tools           | dirs   | directory     | any web tool                            | backlink                                | $36              | ≤72 h review         | 12 a day                   | dofollow          | C     | paste  | H    |
| 500-tools           | 500 Tools              | dirs   | directory     | sold out                                | no                                      | $1→$5/mo         | n/a                  | n/a                        | unknown           | C     | n/a    | M    |
| confetti-saas       | Confetti SaaS          | dirs   | directory     | products with a confetti moment         | badge (DR >0)                           | Fast Track       | unstated             | evergreen                  | dofollow          | C     | paste  | M    |
| rank-anything       | Rank Anything          | dirs   | directory     | user tier lists                         | yes                                     | none             | instant (unverified) | evergreen                  | dofollow (archived) | C   | paste  | L    |
| theresanaiforthat   | There's An AI For That | dirs   | AI directory  | AI tools, MCPs, GPTs                    | no (monthly X thread)                   | $49              | 1–2 days             | permanent listing          | unknown           | A     | paste  | H    |
| futurepedia         | Futurepedia            | dirs   | AI directory  | AI tools                                | no                                      | $497             | 2 business days      | editorial                  | unknown           | B     | paste  | L    |
| toolify             | Toolify                | dirs   | AI directory  | AI tools (multilingual)                 | no                                      | $99              | ≤48 h                | permanent listing          | dofollow          | B     | paste  | M    |
| future-tools        | Future Tools           | dirs   | AI directory  | public AI tools (>75% rejected)         | yes                                     | ads on request   | ≥1 week, no SLA      | editorial                  | unknown           | B     | paste  | H    |
| ai-directories      | AI Directories         | dirs   | AI directory  | AI tools; submission service            | backlink                                | $49              | ≤72 h                | evergreen                  | dofollow          | C     | paste  | H    |
| launch-llama        | Launch Llama tools     | dirs   | AI directory  | AI tools, dev tools, SaaS               | badge + 5 upvotes + rating              | $39              | ~4 weeks             | upvotes; newsletter Tue    | badge-dofollow    | C     | paste  | H    |
| crazy-about-ai      | Crazy About AI         | dirs   | none          | parked domain, always skip              | no                                      | none             | n/a                  | n/a                        | n/a               | n/a   | n/a    | H    |

`paste*` exceptions: r/programming and awesome-list pull requests are founder-voice. Each
gets its own guide file (`reddit-programming.md`, `github-awesome.md`), so every guide has
exactly one mode.

## 5. Schedule (the Step 4 timeline)

1. **L-day:** the user's date. Without one, propose the first Tuesday at least 21 days
   out, and record it as an assumption. Those 21 days cover the 7-day account wait on
   product-hunt and geeknews, Reddit history, and the shorter free queues.
2. **Account setup:** today, for every account with an age, karma or verification gate:
   product-hunt (7 days), geeknews (7 days), peerlist (verified profile and a 100%
   project), and each chosen subreddit's karma gate.
3. **Queue submissions:** submit each free-queue platform today. Its expected go-live is
   today plus its free wait.
   - A weekly board goes on the Monday of launch week when its free wait allows. Otherwise
     book its first open Monday after that, or its paid option when that is within budget.
   - A go-live later than L+30 sets Timing to 0 (§2).
4. **Launch week:** the default, which the user can change. Put at most one
   attention-heavy launch on each day.

   | Day                  | Launch                                                                                         |
   | -------------------- | ---------------------------------------------------------------------------------------------- |
   | L-7 or earlier       | theresanaiforthat, when it is planned. Its PPC bonus requires that the tool appears on no other platform first, so it goes before every other listing. If that is impossible, the plan says the bonus is lost. |
   | Monday of launch week | Weekly boards with Monday cohorts that are booked for launch week.                            |
   | L-day                | product-hunt goes live at 12:01 AM PT. x and linkedin posts, and the email-list send, follow once it is live. |
   | L+1                  | hacker-news (Show HN), on its own day so the founder can stay in the thread.                   |
   | L+2 to L+6           | Reddit, one subreddit a day, on each subreddit's allowed day. Community-tier posts (indie-hackers, geeknews, hashnode). Daily boards on their booked dates. |
   | L+7                  | Recap on x and indie-hackers. The founder writes it from real numbers after launch; the kit gives only an outline. |
   | L+3 to L+30          | Directory drip, 2–3 listings a week.                                                           |
5. **Without product-hunt:** if product-hunt is not in Core, L-day is the hacker-news day,
   or the main board's day.
6. **Times:** write every launch time in its platform's timezone (PT, PST/PDT or UTC) and
   in UTC. Never guess the founder's local timezone.

## 6. launch-plan.md (Step 4)

Write the file in this shape. Replace each `<…>`, and keep the headings: writers and Resume
read them.

```
# Launch plan: <product name>
Status: awaiting-approval | approved <YYYY-MM-DD> | kit-complete <YYYY-MM-DD> | stopped
Generated: <YYYY-MM-DD> · L-day: <YYYY-MM-DD> (<user-set | assumed>) · Budget: <$N | $0, free paths only> · sync: <done | skipped (reason)>
Opted-in actions: <the second-yes actions the user picked, or "none">

## Product Profile
<the explorer's Profile table, unchanged>

## Launch blockers
<the explorer's Blockers table, unchanged>

## Assets found
<the explorer's Assets table, unchanged>

## Fix before launch
<each failed blocker: what to fix, why, and the platforms it unblocks; or "None">

## Plan
| Tier | Platform | Why (score: fit/reach/cost/timing = total) | Path and cost | Go-live (platform time and UTC) | Mode |
<one row per shortlisted platform, ordered by tier, then by go-live. reddit lists its chosen subreddits.>

## Skipped
| Platform | Reason |
<one row per skipped platform: a failed gate, a low score, or over cap>

## Timeline
| Date | Action | Platform |
<every dated action from today to L+30, built with §5>

## Budget
Free path total: $0. Paid options proposed: <each option, its price and what it buys>. Total if all are accepted: $<N>.

## Materials Step 5 will write
<the file list: README.md, copy-bank.md, assets.md, and platforms/<id>.md for each platform>

## Actions that need a second yes
<only what applies: "gh repo edit (metadata)" when the repo is public on GitHub; "/logo-designer: no square logo found"; "/landing-page-generator: no landing page"; "/seo-ai-optimizer: og tags missing"; or "None">

## Assumptions and unknowns
<each assumption, inferred value, and unknown profile field that affected a decision>

## Live check
| Platform | Result | Checked URL | Changes from catalog |
```

## 7. Approval gate (Step 4, in chat)

Print a summary of no more than 40 lines, in this order:

1. The product in one line.
2. The blockers to fix.
3. The plan table: tier, platform, path and go-live.
4. The number of skipped platforms, by reason.
5. The budget.
6. The path of the plan file.
7. The four lines below:

```
Result: PLAN READY — awaiting approval
Evidence: <profile sources read; live check: N same, N changed, N unreachable, with dates>
Uncertainty: <unknown or inferred profile fields that affect the plan; unverified platform facts>
Decision: approve, change or stop the plan<; and pick which second-yes actions to run>
```

Then ask with AskUserQuestion. The answer must be explicit; silence is not approval.

1. **"What should I do with the launch plan?"**
   - Approve: write the launch kit now.
   - Change the plan: add or remove platforms, or change the date or budget.
   - Stop here: keep `launch-plan.md` only.
2. **Only when "Actions that need a second yes" lists something:** "Which of these actions
   should run after the kit is written?" Use multiSelect and list each action. Unchecked
   means not run.

Record the answers in `Status:` and `Opted-in actions:`. An action that is not opted in
never runs. An opted-in action still asks for its own confirmation in Step 7.

Without AskUserQuestion, ask the same questions in plain text, then end the turn.

## 8. Resume table

The Resume branch reads the plan's `Status:` line and acts on it.

| Status              | Action                                                                                                                                                                                         |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `awaiting-approval` | If the request approves the plan, record the approval and go to Step 5. If it changes the plan (date, budget, platforms), take the Change path. Otherwise print the gate summary and ask again. |
| `approved …`        | A change request takes the Change path, then asks for approval again. Otherwise: if `Generated:` is more than 14 days old, re-run Step 3 and show the changes first; then run Step 5.            |
| `kit-complete …`    | Ask what to update. Re-run only the steps it touches, and confirm before replacing any file.                                                                                                   |
| `stopped`           | Treat it as a new run (Full or Named). Ask before replacing the plan.                                                                                                                          |

## 9. README.md (Step 5c)

```
# Launch kit: <product name>
Plan approved <date> · L-day <date> · <N> platforms · Budget $<N>

## Next 3 actions
1. <the earliest-dated unchecked action, with its date>
2. …
3. …

## Checklist
- [ ] <date> · <action> · [<platform>](platforms/<id>.md)
<every timeline row, in date order>

## Founder inputs needed
<every open question the writers returned, with its file>

## Files
| File | What it holds |
```

## 10. Step Completion Reports

After each step, print this block. Write each check as `√` (pass), `×` (fail) or `—`
(note), and tie it to a count, a file or a command.

```
◆ <Step name> (step N of 8)
··································································
  <check>:            √ <evidence>
  <check>:            × <reason>
  ____________________________
  Result:             PASS | FAIL | PARTIAL
```

| Step              | Checks                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| 1 Product Profile | profile rows filled (N/30), sources per row, blockers checked (N/8), assets listed               |
| 2 Fit table       | rows gated (N of 53), scores with all 4 components, tiers within caps, every skip has a reason    |
| 3 Live check      | shortlisted platforms checked (N/M), changes found, fetch failures labeled                       |
| 4 Plan and gate   | sync recorded, launch-plan.md written, approval asked, answers recorded                          |
| 5 Launch kit      | copy-bank written, platform files (N/M), README and assets written                               |
| 6 Kit check       | check_kit.py exit 0, reviewer blocking issues (0), review fresh or self-review (labeled)         |
| 7 Actions         | each opted-in action: run and verified, declined, failed, or none opted in                       |
| 8 Final report    | Result line first; Evidence, Uncertainty and Decision present                                    |

## 11. Final report (Step 8)

Print this block last, after the Step 8 Step Completion Report. The Result line comes
first.

```
Result: COMPLETE | PLAN READY — stopped | PARTIAL — <reason> | BLOCKED — <reason>
Evidence: <what was verified: profile sources, live-check results with dates, check_kit.py output, gh repo view output>
Uncertainty: <unverified platform facts (catalog date), unknown profile fields, Reddit rules to re-read, Korean copy to review, self-review instead of a fresh reviewer; or "none known within these checks">
Decision: <the approval needed, or "No approval needed."> Next for you: <the earliest dated action in README.md>
```

**Status rule:**

- COMPLETE: Steps 5 and 6 passed, and every opted-in action ran. Set `Status: kit-complete <date>`.
- PLAN READY — stopped: the user chose Stop at the gate.
- PARTIAL: the kit was written, but a check still failed after its fix rounds, or an
  opted-in action failed.
- BLOCKED: no readable landing page and no codebase; a sync problem the user must resolve;
  or several products and no answer about which one.
