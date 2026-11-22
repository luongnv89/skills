# The Feature Map

The feature map is the verify skill's rubric: the verify skill drives each row and grades it `PASS`, `FAIL` or `UNVERIFIED` against the row's expected result. It is written to `.claude/skills/<name>/feature-map.md`, next to the verify skill, and copied byte for byte to `.agents/skills/<name>/`.

## Format

```markdown
# Feature map: <app name>

Rubric for `.claude/skills/<name>/SKILL.md`. Keep this file identical to its copy in `.agents/skills/<name>/`.
Base: <commit SHA it was derived from> · App type: <web app | API or service | CLI>

| ID | Feature | How to reach | Action | Expected result | Mutates | Source |
|---|---|---|---|---|---|---|
| F1 | App boots | `npm run dev` | wait for ready signal | GET /health → 200 within 30s | no | package.json:7, src/server.ts:41 |
| F2 | Sign-in page | `/login` | open the page | heading "Sign in" and an email field (`input[name=email]`) | no | src/pages/login.tsx:12 |
| F3 | Search shortcut | any page, `Ctrl+K` | press the shortcut | the command palette opens with focus in its input | no | src/hooks/useHotkeys.ts:20 |
| F4 | Add a todo | `POST /api/todos {"title":"verify"}` | call | 201 and a JSON body with `"title":"verify"` | yes: todos table (test DB, compose.test.yaml:3) | src/routes/todos.ts:18 |
```

## Columns

- **ID:** `F1`, `F2`, … in the order the verify skill runs them. IDs never get reused: a removed feature leaves a gap.
- **Feature:** what a user would call it, one short phrase.
- **How to reach:**
  - Web app: the URL path, and the selector, link text or keyboard shortcut that reaches the control. Prefer stable selectors the repo already uses (`data-testid`, `name`, `aria-label`, visible text) over generated class names.
  - API: the method and path, with the request body or query when needed (`POST /api/todos {"title":"a"}`).
  - CLI: the command and arguments, with input files from the repo's fixtures or README examples.
- **Action:** what the verify skill does there: open, click, type, submit, call, run.
- **Expected result:** one observable fact the verify skill can check without judgement: an HTTP status, text on the page or in the response, a JSON field and its value, an exit code and an output pattern, a file created. "Works" or "looks right" is not a result.
- **Mutates:** `no`, or `yes:` and what it changes, with the local or test setup it runs against. A mutating row never runs against a real or shared database or service: with no local or test setup in the repo, it is `UNVERIFIED (no test setup)`.
- **Source:** the `path:line` the row comes from: a route, a handler, a help string, a test assertion, a README example. Several sources are separated by commas.

## Where features come from

| App | Sources |
|---|---|
| Web app | The router (file-based `pages/` or `app/`, a routes file), navigation links, forms, keyboard shortcut handlers, existing end-to-end tests |
| API or service | Route registrations, an OpenAPI or GraphQL schema, handler code, API docs, existing integration tests |
| CLI | Subcommands and flags from the parser and `--help`, README usage blocks, fixtures under `tests/` or `examples/` |

Always include, first:

1. **Boot:** the app starts and its ready signal fires.
2. **Main path:** the feature the README leads with.

Then one row per remaining user-visible feature, and one error path per app: a 404 page or unknown route, an API request that should be rejected, a CLI unknown command or invalid flag.

## Expected results without a source

When the repo does not say what a feature should produce, the row's expected result is `expected: ask the user`. The plan lists these rows. Until the user gives the result, the verify skill records the observation and grades the row `UNVERIFIED`, never `PASS`.

Never take the current output as the expected result just because the app produced it: that grades the app against itself.

## Rows that cannot run here

- **Needs credentials or a paid service:** the action names the environment variables (from `.env.example` or config). Without them set, the row is `UNVERIFIED (needs <VAR>)`.
- **Needs a driver this machine lacks** (a browser for a click, a simulator): `UNVERIFIED (no driver)`.
- **Destructive or external** (sends email, charges a card, deletes data outside a test database): leave it out of the verify skill and list it under the map as `not driven: <reason>`.

## Size and speed

The verify skill runs before every commit, so it must be fast. Keep one check per feature, reuse one boot for every row, and leave exhaustive input coverage to the test suite. When the map passes 30 rows, ask the user which features matter most, and keep the others in a second section that the verify skill runs only when asked (`full`).

## Changing the map

The map changes when features change, through the same approval as the first plan. A row that fails is never edited to match what the app did; that is a decision for the user (see `SKILL.md` → *Rules* 6).
