# Launch story, copy tests and campaign tracks

Read by you in Step 4 (the story and tracks in the plan, the L-day rule, and the §7
after-launch rows), by the Step 5 writers and by the Step 6 reviewer.

The story, the copy test, the X checklist and the tracks draw on "The secret behind viral
product launches" by Kyle Jeong with Tereza Tizkova
(x.com/kylejeong/status/2119925224334586085, 2026-11-09; practitioner advice, not
platform rules). The disclosure rule in §5 comes from the US FTC. The lead times in §4
are this skill's planning defaults, not figures from the post. Ideas marked
*(practitioner)* in §1 and §7 come from Oleksii Sidorov's X carousel "48 SEO & GEO tricks
from a YC founder" (x.com/acecreamu/status/2125234701912985928): one founder's advice. The
Google pages §7 quotes override it.

## 1. The launch story

One story, curated from the business and reused in every post, the video, the landing
page and talks. It has five elements:

| Element         | What it says                                                  | Usual source                                  |
| --------------- | ------------------------------------------------------------- | --------------------------------------------- |
| hero            | the customer, and what they get done with the product         | Profile `ideal_customer`, `what_it_does`      |
| villain         | the problem with how the world works today                    | Profile `problem`                             |
| contrarian take | what the founder believes that most of the market does not    | founder input                                 |
| lovers          | who will love the product, and the reason                     | Profile `audience`, or founder input          |
| haters          | who will dislike it, and the trait they will reject           | founder input                                 |

- Each element is a Product Profile fact with its source, or a founder input in the
  founder's own words. Never invent an element.
- The plan's `## Launch story` section lists each element with its source, or
  `founder input needed`. The founder supplies a missing element through the gate's
  Change answer or in "Founder inputs needed"; until then it has no copy-bank field.
- The copy-bank writer writes each known element once, as `copy.story.<element>`
  (`copy.story.hero`, `.villain`, `.contrarian`, `.lovers`, `.haters`; max=200, a house
  limit). Put `Source: <Profile row>` or `Source: founder input` on the line after the
  closing fence, never inside the block.
- Every post, pitch, video brief and talk outline restates the story. Reddit sections
  restate it in new sentences (launch-kit.md, reviewer check 7).
- **Story owner:** one person keeps the story the same everywhere and approves changes
  to it. With the story-owner track on, the plan records the owner's role (founder, head
  of marketing), never a name; with it off, `Story owner: none (track off)`.
- A plan with no `## Launch story` or `## Campaign tracks` section: treat every track as
  off, and write `copy.story.*` fields only for elements a Profile row sources.
- **Founder interview (optional)** *(practitioner)*: the founder answers the copy-bank
  story prompts in a recorded 20–30 minute session and gives you the transcript, in the
  request or as a file path. You read it in Step 4; the answers you use reach the writers
  only as sourced rows in `launch-plan.md` (`## Launch story`, Product Profile). The
  explorer reads it only when it comes with the request (`product-profile.md`, source 1).
  - A quoted answer is a founder input in the founder's own words. Its source is
    `user: "<quote>" (interview transcript)`, the form `product-profile.md` already
    accepts, for a story element or a fact. Quote only what the founder said; never fill
    a gap from it by inference.
  - Own-voice long form (a build article, a LinkedIn article, a post on the founder's
    own site) is drafted from the quoted answers. The founder edits it before it goes
    out, and it is published first on the founder's own site: copies on Hashnode, dev.to
    or Medium set their canonical URL to that original, and a LinkedIn article links to
    it (`launch-kit.md`, *Long-form article (owned first)*).
  - Founder-voice rules still apply. A platform whose rules ban generated or AI-edited
    text (hacker-news, r/programming, awesome lists, a subreddit that bans LLM-written
    posts) never gets text drafted from the transcript: its brief may point to which
    answers to draw on, and the founder writes the words.
  - Contacts and the transcript itself stay out of the kit (§6).
- **Cross-posts:** with or without a transcript, when the request mentions a long-form
  article or a cross-post, the plan's `## Assumptions and unknowns` states the
  owned-first rule: the original goes on the founder's own site and every copy sets its
  canonical URL to it, or links to it.

## 2. The copy test

Every line of marketing copy passes three questions: taglines, descriptions, posts,
pitches, invites and outreach. The test skips list and fact fields (`copy.name`,
`copy.tags`, `copy.competitors`, `copy.pricing`, `copy.disclosure`). A line that fails
gets rewritten from Profile facts, or cut.

1. **Visualizable:** a reader can picture a person, an object or an action. "Invoices
   that chase late payments for you" passes; "Streamline your billing" fails.
2. **Falsifiable:** a reader can check the line, and it would be false if the product
   did not do what it says. A Profile fact with a source stands behind it. This applies
   to factual claims; the story's belief elements (contrarian take, lovers, haters) are
   judged on questions 1 and 3 only.
3. **Only-we-can-say:** a competitor could not paste it onto their own page unchanged. It
   names this product's mechanism, number or story.

Founder-voice briefs hold no wording, so the test applies to their facts list only.

## 3. X launch-post checklist

The X launch post (`x.md`, max=280) covers four items, from Profile facts only:

1. **Proof of work:** what exists and runs today (a demo, a release, a feature the
   founder can show).
2. **A clear problem with how the world works:** the villain.
3. **The contrarian take:** from the story.
4. **One big number:** a Profile number with its source.

A missing number or contrarian take never gets invented and never becomes a placeholder.
Write the post without it, and list the gap under "Founder inputs needed". When 280
characters cannot hold all four, the launch post carries the problem and the number, and
the optional thread carries the rest; the post and thread together meet the checklist.

## 4. Campaign tracks (opt-in)

The plan lists these tracks in its `## Campaign tracks` table, all off by default. A
track is on when the user asks for it in the request, or turns it on or off through the
gate's existing "Change the plan" answer. There is no extra gate question. Lead times are
defaults the founder can change.

| Track | Lead time (default) | What the plan and kit add | Rules |
| --- | --- | --- | --- |
| video | 42 days | an `assets.md` row with a brief: a script outline built from the story, length, and the sizes the chosen platforms need | Studio criteria: a reel of launch videos for comparable products, a fixed written quote and delivery date, revisions included, and every size the kit needs. Budget and lead time are founder inputs; any figure from the post is practitioner advice, not a fact. The skill never hires or pays. |
| friends and launch-day invite | 14 days | `copy.invite` (max=300): a hold for the launch hour, sent ahead; then `copy.outreach`, sent at launch time | Message friends when the launch is live. Ask for a reply or a quote of what they think, over likes, and ask anyone who posts to say in the post how they know the founder ("friend of the founder", §5). Never ask for votes (rule 6). |
| supporter list | 21 days | a checklist row: build the list in the founder's own private tool | Counts and roles only in the kit (§6). |
| day-0 co-launch partners | 28 days | a pitch to each partner role, from `copy.pitch-100w` | Partners are integrations or tools in the Profile, or ones the founder names. A partner's post discloses the relationship (§5). |
| earned media | 28 days | pitches from `copy.pitch-100w`, for writers and hosts the founder already knows | Real relationships only. Never buy coverage; a paid placement is paid amplification. |
| in-person event | 42 days | a checklist: date, venue, a demo script from the story | The skill never books or pays. |
| paid amplification | 7 days | the option in `## Budget`, and the disclosure line for each paid post | Founder-run and off by default; the default $0 budget keeps it off. The skill never buys, runs or targets ads (rule 1); it writes only the copy and its disclosure. |
| story owner | 0 days | the owner's role in the plan | With the track on, name the role before Step 5. Off: `none (track off)`. |

**L-day rule:** with at least one track on, L-day is the first Tuesday on or after the
later of today + 21 days and today + the longest opted-in lead time. A user-set L-day
earlier than that is never moved silently: flag the conflict and propose the later date
at the gate.

For each track that is on, add a `## Timeline` row at L minus its lead time with the track's
first action; checklist rows take their date from that row.

## 5. Disclosure rule

Source: US FTC, "Disclosures 101 for Social Media Influencers"
(https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers).

- **When:** any post by someone with a material connection to the product: money, free or
  discounted products or perks, or a personal, family or employment relationship. That
  covers paid amplification, gifted accounts, co-launch partners, employees, investors,
  and friends and family who post about the launch.
- **How:** the post itself carries the disclosure, in plain words and in the post's
  language, where a reader cannot miss it. Not only on a profile page, not after a
  "more" cut, not inside a cluster of hashtags. A video says it in the video. Clear
  wording: "Ad", "Sponsored", "I work at <product>", "<product> gave me a free account",
  "friend of the founder".
  Vague wording fails: "sp", "spon", "collab", or "thanks" on its own.
- A platform's disclosure tool alone is not enough. Use it as well as the in-post line.
- Writers put the disclosure line, from `copy.disclosure`, into each draft they write:
  only the founder's own posts and paid posts. Never write a post for someone else (a
  friend, partner, employee or investor) to publish as their own. When the kit asks
  others to post (`copy.invite`, `copy.outreach`, a co-launch partner pitch), it gives
  them the facts, the link and the disclosure line, asks them to write the post
  themselves and to put that line in it.
- **Never propose** fake or sock-puppet accounts, bots, engagement pods (groups that
  trade likes, replies or votes), or undisclosed paid posts. Refuse such a request,
  quote this rule, and offer the disclosed alternative (the friends track).

## 6. Supporter privacy

- Never write names, handles, emails, phone numbers or other personal data of the
  founder's contacts into `launch-kit/`.
- The supporter list stays in the founder's own private tool (a spreadsheet, a CRM).
  The kit holds counts or roles only: "12 customers, 3 investors, 2 partner teams".
- Outreach and invite drafts carry no recipient name. The founder adds it when sending.
- A founder interview transcript (§1) is never copied into `launch-kit/`: the kit holds
  only the quoted answers it uses. Before quoting, remove the names and personal data of
  anyone the founder mentions (customers, colleagues, investors); keep their role only.

## 7. After launch: signal checks and AI-cited pages

Founder-run, by hand, after L-day. It needs no opt-in and no lead time, so it never moves
L-day and adds no row before L-day: §5 of `plan-and-reports.md` puts it at L+7 and L+30,
and the README's `## After launch` section holds the steps and a blank log. The kit gives
no figures, and the skill never runs any step itself.

### Signal check (L+7 and L+30)

1. **Branded search:** in the founder's own Search Console (Performance → Search
   results), filter Query to those containing the product name, and compare impressions
   and clicks for the days since L-day (7 at L+7, 28 at L+30) with the same number of
   days just before L-day.
   Record each figure with its date range. No Search Console for the site: "not
   available: verify the site in Search Console".
2. **Generative AI performance report:** where Search Console shows it for the site,
   note its figures for the launch pages, each column exactly as labelled; otherwise
   "not available". Google's guide: "To measure how your content is performing in
   generative AI features on Google Search and Discover, use the Generative AI
   performance report in Search Console."
   (https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
3. **AI answers** *(practitioner)*: the founder asks 2–3 AI assistants they use, in their
   own session, "what's the best tool for <category>?", with the category in a
   customer's words. They note whether the product is named, which tools are named, and
   which pages are cited.

Each result is one log row: `| Date | Check | Source | Result |`. Never script Google
queries, scrape rankings, or send automated questions to an assistant. Google's spam
policies (*Machine-generated traffic*): "This includes scraping results for rank-checking
purposes or other types of automated access to Google Search conducted without express
permission." (https://developers.google.com/search/docs/essentials/spam-policies) The
founder can hand the exports and the AI-answer log to `/seo-ai-optimizer`, whose
`search-performance` and `ai-citations` checks read them.

### AI-cited pages: legitimate actions only

Each page step 3 found cited for the category gets one action, by its kind:

| Cited page | Action |
| --- | --- |
| Review site (G2, Capterra, TrustRadius) | The founder's own profile there, under that site's review rules (`platforms-directories.md`): reviews come from real users, never conditional on a positive one. |
| Listicle or article | A short factual note the founder writes to its author: what the product does, for whom and how it differs, from Profile facts, disclosing any material connection (§5). The kit lists the facts and never drafts the note. No payment, product or perk for inclusion: paying for a place in the list is never an action here, and ads stay in the paid amplification track (§4, §5). |
| Reddit or forum thread | The Reddit rules (`platforms-core.md` reddit, the `reddit.md` Participation plan): help in the thread where its rules allow, and disclose whenever the product comes up. Never post to get the product named. |
| A page that answers the question better than the founder's site | A better page on the founder's own site: hand it to `/seo-ai-optimizer`. |

Never seed, write, buy or trade reviews or mentions, and never ask friends to post them.
Google's guide: "However, seeking inauthentic "mentions" across the web isn't as helpful as
it might seem." (https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
Refuse such a request, quote this rule, and offer the action in the table instead.
