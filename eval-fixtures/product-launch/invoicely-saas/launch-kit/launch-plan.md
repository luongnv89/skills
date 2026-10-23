# Launch plan: Invoicely
Status: approved 2026-10-21
Generated: 2026-10-21 · L-day: 2026-11-17 (user-set) · Budget: $0, free paths only · sync: skipped (not a git worktree)
Opted-in actions: none

## Product Profile
| Field | Value | Source |
| --- | --- | --- |
| name | Invoicely | site/index.html `<title>` |
| one_liner | "Get paid faster: invoices that chase themselves." | site/index.html h1 |
| problem | "Freelancers lose hours every month chasing late payments." | site/index.html hero paragraph |
| what_it_does | Sends invoices, reminds clients on a schedule the freelancer picks, stops reminders when the client pays by card | site/index.html hero paragraph |
| ideal_customer | freelancers | site/index.html hero paragraph |
| product_type | web app (SaaS) | package.json (next) |
| ai | no | package.json dependencies (no AI SDK) |
| audience | freelancers and solo consultants | site/index.html |
| model | B2B (freelancers as small businesses) | (inferred: sells to self-employed businesses) |
| license | proprietary | package.json "private": true |
| code_public | no | no repository link on the site |
| self_hostable | no | no Dockerfile |
| pricing | Free: 3 invoices a month; Pro: $9/month, unlimited | site/index.html Pricing; app/pricing.ts:3-4 |
| availability | usable now after sign-up (free plan) | site/index.html "Start free" |
| stage | launched | package.json version 1.2.0 |
| launch_history | none found | no Product Hunt or HN links |
| domain | own domain (invoicely.example) | site/index.html og:image URL |
| https | yes | og:image uses https |
| languages | en | `<html lang="en">` |
| platforms | web | package.json |
| key_features | automatic reminders that stop when the client pays; Stripe card payments; recurring invoices; PDF export | site/index.html Features |
| differentiators | "Invoicely does one job: getting a freelancer paid. No accounting suite to learn." | site/index.html |
| competitors | FreshBooks, Wave | site/index.html "Why not FreshBooks or Wave?" |
| proof | "Used by 1,200 freelancers."; "I got paid 9 days faster on average." — Maya R., designer | site/index.html |
| founders | Sam Ortiz | site/index.html footer |
| hiring | unknown | none stated |
| channels | X @invoicelyapp | site/index.html footer |
| news_angle | none | none |
| category_flags | no | invoicing product |
| confetti_moment | unknown | none stated |

## Launch blockers
| Check | Result | Evidence |
| --- | --- | --- |
| usable now, no waitlist or invite gate | pass | "Start free" link; free plan in app/pricing.ts:3 |
| try path without sign-up or email | fail | sign-up needed for the free plan |
| own domain over HTTPS | pass | https://invoicely.example |
| no noindex | pass | no robots meta in site/index.html |
| og and twitter tags | pass | og:title, og:description, og:image, twitter:card present |
| content in raw HTML | pass | static site/index.html |
| privacy and terms linked | pass | footer links /privacy and /terms |
| links work | unknown | the example domain cannot be fetched |

## Assets found
| Asset | Path or URL | Size |
| --- | --- | --- |
| Square logo or icon | missing | none in the repository |
| OG image | https://invoicely.example/og.png | not fetched |
| Screenshots | missing | none found |
| Demo video or GIF | missing | none found |

## Fix before launch
None. The free plan is usable after sign-up; HN readers prefer a try-without-sign-up path, so the HN brief tells the founder to say up front that a free account is needed.

## Plan
| Tier | Platform | Why (score: fit/reach/cost/timing = total) | Path and cost | Go-live (platform time and UTC) | Mode |
| --- | --- | --- | --- | --- | --- |
| Core | product-hunt | 3/3/2/1 = 9 | free | 2026-11-17 12:01 AM PT (08:01 UTC) | paste-ready |
| Core | hacker-news | 3/3/2/1 = 9 | free | 2026-11-18, any time the founder can stay in the thread | founder-voice |
| Directory drip | saashub | 3/2/2/1 = 8 | free; verify with a domain email | submit 2026-11-20 | paste-ready |
| Own channels | x | 3/2/2/1 = 8 | free | 2026-11-17 after Product Hunt is live | paste-ready |
| Own channels | linkedin | 3/1/2/1 = 7 | free | 2026-11-17 after Product Hunt is live | paste-ready |

## Skipped
| Platform | Reason |
| --- | --- |
| theresanaiforthat, futurepedia, toolify, future-tools | Not AI-powered |
| devhunt | Not a developer tool |
| sourceforge | Not open source |
| wellfound | Hiring unknown; product promotion is banned there |
| crazy-about-ai, 500-tools | Not taking launches |
| other launch boards and directories | user removed them at the approval gate to keep the first launch small |

## Timeline
| Date | Action | Platform |
| --- | --- | --- |
| 2026-10-27 | Create a personal Product Hunt account (7-day wait before posting) | product-hunt |
| 2026-11-03 | Schedule the Product Hunt launch for 2026-11-17 | product-hunt |
| 2026-11-17 | Product Hunt goes live 12:01 AM PT; post on X and LinkedIn once live | product-hunt, x, linkedin |
| 2026-11-18 | Show HN, written in your own words | hacker-news |
| 2026-11-20 | Submit to SaaSHub with competitors listed; verify with a domain email | saashub |
| 2026-11-24 | Recap post with real numbers only | x |

## Budget
Free path total: $0. Paid options proposed: none. Total if all are accepted: $0.

## Materials Step 5 will write
README.md, copy-bank.md, assets.md, platforms/product-hunt.md, platforms/hacker-news.md, platforms/saashub.md, platforms/x.md, platforms/linkedin.md

## Actions that need a second yes
- /logo-designer: no square logo found (not opted in)

## Assumptions and unknowns
- hiring is unknown, so wellfound is skipped.
- No logo file was found in the repository; the og:image URL exists but its size was not checked.

## Live check
| Platform | Result | Checked URL | Changes from catalog |
| --- | --- | --- | --- |
| product-hunt | same | https://www.producthunt.com/launch | none |
| hacker-news | same | https://news.ycombinator.com/showhn.html | none |
| saashub | same | https://www.saashub.com/services/submit | none |
