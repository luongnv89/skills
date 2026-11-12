# Launch story, copy tests and campaign tracks

Read by you in Step 4 (the story and tracks in the plan, and the L-day rule), by the
Step 5 writers and by the Step 6 reviewer.

The story, the copy test, the X checklist and the tracks draw on "The secret behind viral
product launches" by Kyle Jeong with Tereza Tizkova
(x.com/kylejeong/status/2119925224334586085, 2026-11-09; practitioner advice, not
platform rules). The disclosure rule in §5 comes from the US FTC. The lead times in §4
are this skill's planning defaults, not figures from the post.

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
  to it. The plan records the owner's role (founder, head of marketing), never a name.

## 2. The copy test

Every line of paste-ready copy passes three questions. A line that fails gets rewritten
from Profile facts, or cut.

1. **Visualizable:** a reader can picture a person, an object or an action. "Invoices
   that chase late payments for you" passes; "Streamline your billing" fails.
2. **Falsifiable:** a reader could check the line and find it false. A Profile fact with
   a source stands behind it.
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
| friends and launch-day invite | 14 days | `copy.invite` (max=300): a hold for the launch hour, sent ahead; then `copy.outreach`, sent at launch time | Message friends when the launch is live. Ask for a reply or a quote of what they think, over likes. Never ask for votes (rule 6). |
| supporter list | 21 days | a checklist row: build the list in the founder's own private tool | Counts and roles only in the kit (§6). |
| day-0 co-launch partners | 28 days | a pitch to each partner role, from `copy.pitch-100w` | Partners are integrations or tools in the Profile, or ones the founder names. A partner's post discloses the relationship (§5). |
| earned media | 28 days | pitches from `copy.pitch-100w`, for writers and hosts the founder already knows | Real relationships only. Never buy coverage; a paid placement is paid amplification. |
| in-person event | 42 days | a checklist: date, venue, a demo script from the story | The skill never books or pays. |
| paid amplification | 7 days | the option in `## Budget`, and the disclosure line for each paid post | Founder-run and off by default; the default $0 budget keeps it off. The skill never buys, runs or targets ads (rule 1); it writes only the copy and its disclosure. |
| story owner | 0 days | the owner's role in the plan | Set before Step 5. |

**L-day rule:** with at least one track on, L-day is the first Tuesday on or after the
later of today + 21 days and today + the longest opted-in lead time. A user-set L-day
earlier than that is never moved silently: flag the conflict and propose the later date
at the gate.

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
  wording: "Ad", "Sponsored", "I work at <product>", "<product> gave me a free account".
  Vague wording fails: "sp", "spon", "collab", or "thanks" on its own.
- A platform's disclosure tool alone is not enough. Use it as well as the in-post line.
- Writers put the disclosure line into each such draft, from `copy.disclosure`.
- **Never propose** fake or sock-puppet accounts, bots, engagement pods (groups that
  trade likes, replies or votes), or undisclosed paid posts. Refuse such a request,
  quote this rule, and offer the disclosed alternative (the friends track).

## 6. Supporter privacy

- Never write names, handles, emails, phone numbers or other personal data of the
  founder's contacts into `launch-kit/`.
- The supporter list stays in the founder's own private tool (a spreadsheet, a CRM).
  The kit holds counts or roles only: "12 customers, 3 investors, 2 partner teams".
- Outreach and invite drafts carry no recipient name. The founder adds it when sending.
