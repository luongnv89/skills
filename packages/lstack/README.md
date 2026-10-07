# lstack

**lstack 0.4.0** exposes this repository's maintained first-party Agent Skills
as a native Claude Code plugin directly from the canonical root `skills/` tree.
Optional platform-neutral, Claude and Codex ZIP exports remain available. It is
a package, not a new skill or runtime. There are no plugin hooks, MCP servers,
native plugin agents, npm publications or automatic dependency installers.

## Claude Code: direct repository install (primary)

With a current plugin-capable Claude Code CLI:

```bash
claude plugin marketplace add luongnv89/skills
claude plugin install lstack@lstack --scope user
claude plugin list
```

This intentionally changes your user plugin configuration. The root native
metadata must first be committed and pushed for GitHub installation to work;
a local draft is **not live remotely**. Start a new session and inspect `/plugin`
or completion for `/lstack:<skill>`, e.g. `/lstack:code-review` or
`/lstack:drawio-generator`. There is no `/lstack` orchestrator. Prefer qualified
commands when standalone copies coexist; inspect paths before invoking a workflow.

For a single session from a trusted checkout, without persistent installation:

```bash
claude --plugin-dir /absolute/path/to/skills
```

The path is the repository root, not `.claude-plugin/`. Only native metadata
lives in that directory. Default root `skills/` discovery finds 39 immediate
members; the plugin manifest adds **only** the two nested diagram children.
Together they expose 41 skills once, without flattening, copying or moving
source files. Skill-local `agents/` files stay resources, not native agents.

Review upstream changes before explicitly updating a repository-backed install:

```bash
claude plugin marketplace update lstack
claude plugin update lstack@lstack --scope user
```

Restart Claude Code (or use `/reload-plugins` where supported). For session-only
use, update your trusted checkout and restart with its root `--plugin-dir`.
Discovery proves loading, **not** compatibility of every workflow: global paths,
`asm deps`, unqualified sibling calls and external dependencies are unchanged.
See **Prerequisites and capability limits** before use.

### Directory portal and review caveats

If the owner chooses to submit, use repository **luongnv89/skills**, plugin path
**empty** (root), branch **main**. No separate plugin repository or skill tree
is needed. Paid login, connected GitHub account, contact information and
accurate data-handling/legal disclosures are owner responsibilities. This
implementation does not submit, publish, or claim acceptance/approval.

The directory portal reviews the **whole repository tree**, not the builder's
filtered ZIP. The baseline contains 602 tracked entries (604 with these two
metadata files), 12 PNGs and one PDF, the largest about 562 KB, and a tracked
`.claude/skills/skill-creator` symlink. Root `CLAUDE.md` is a regular tracked
AGENTS import wrapper with two rules; it is intentionally preserved, not
plugin-context instructions. Reviewer holds, file-count and format/symlink
policies remain uncertain; builder exclusions do not resolve those risks.
No deletions or source reorganization are authorized by this packaging change.

Members can mutate files/repos, commit/push, install tools and interact with
websites, APIs and GitHub. Depending on the workflow and agent configuration,
prompts, code, URLs, screenshots or supplied documents may reach model providers
and external services. Inspect each member's approval gates, credentials and
dependencies first. The package makes no offline/no-collection claim and supplies
no invented contact, retention or privacy guarantees.

## Contents and scope

[manifest.json](manifest.json) explicitly lists all **41** current tracked skill
definitions: 39 top-level skills plus `drawio-generator` and
`excalidraw-generator`, the two children of `diagram-generator`. Native Claude
loading uses the unchanged nested source layout. In optional ZIP exports every
member becomes a separately discoverable `skills/<name>/SKILL.md` directory;
the exported umbrella excludes the children's subtrees to avoid duplication.

Exported files keep their original bytes and Git executable modes: `SKILL.md`,
references, scripts, agents, assets and human-facing docs. Package version 0.4.0
is independent of both the catalog release and member versions. Generated
`provenance.json` records the full source commit, manifest/builder SHA-256,
original member versions, and source/destination/hash/mode for every member file.
The root MIT `LICENSE`, package README and manifest accompany the payload.

Excluded **from ZIP exports only**: member-root `evals/` and `tests/` (development fixtures), untracked,
ignored, downloaded and installed copies, retired skills, `*-workspace/`, runtime
folders (`.git`, `.gitissue`, `.claude`, `.agents`, `.pi`, `.asm-improver`,
`node_modules`, `dist`, `build`, `__pycache__`, `.venv`, `venv`), editor/OS scratch,
`.env*`, `credentials*`, `secrets*`, SSH key files and credential-like extensions.
The builder rejects included symlinks/submodules, unsafe paths, conflicting
member names and known live-key/private-key patterns. This is a conservative
filter, **not a general secret detector**; inspect inputs before distribution.

## Optional ZIP exports: obtain and build

Requirements: Git and **Python 3.9+**; Python standard library only. No npm,
packaging framework, agent installation or credential is required for building.
Choose and record a trusted repository commit containing the lstack package:

```bash
git clone https://github.com/luongnv89/skills.git
cd skills
# Optionally: git checkout <trusted-commit-containing-lstack>
git rev-parse HEAD
python3 scripts/build-lstack.py --check
python3 scripts/build-lstack.py
```

The default output is `dist/lstack-0.4.0.zip` (ignored by Git). The JSON result
prints the exact commit, skill/file counts, output path and archive SHA-256.
Inputs come **entirely from the selected committed Git tree**, never from local
edits or installed skills. Commit intended packaging/member changes before
building; local edits are not included. The running builder must match that
revision. To rebuild an older package, check out its commit first.

For repeatability checks or a custom new output path:

```bash
python3 scripts/build-lstack.py --revision HEAD --output /tmp/lstack-first.zip
python3 scripts/build-lstack.py --revision HEAD --output /tmp/lstack-second.zip
python3 -c 'from pathlib import Path; assert Path("/tmp/lstack-first.zip").read_bytes() == Path("/tmp/lstack-second.zip").read_bytes()'
```

Outputs must be new `.zip` paths; existing files/symlinks are never overwritten.
Use distinct names for repeat builds. `--check` validates without writing.
Sorted entries, fixed ZIP timestamps and modes, no compression and deterministic
JSON make identical committed inputs/builder produce byte-identical archives,
independent of working-tree mtimes, untracked files or machine paths. Publication
is atomic; errors do not leave a partially completed ZIP.

## Extract and use

Inspect and extract a **trusted, locally built** archive into a new staging
folder, not directly over an existing agent installation:

```bash
python3 -m zipfile -l dist/lstack-0.4.0.zip
python3 -m zipfile -e dist/lstack-0.4.0.zip /tmp/lstack-staging
```

Layout:

```text
lstack-0.4.0/
  README.md
  LICENSE
  manifest.json
  provenance.json
  skills/
    code-review/SKILL.md
    diagram-generator/SKILL.md
    drawio-generator/SKILL.md
    excalidraw-generator/SKILL.md
    ... (41 independent member directories)
```

Read a member's `SKILL.md` and prerequisites before using it. Supply that file
and its relative resources to a skill-capable agent, or manually install the
**whole member directory** at that agent's documented skill location. For the
existing member preflights this is commonly `~/.claude/skills/<name>/` or
`~/.agents/skills/<name>/`. Review any existing copy and back it up before
replacing it; don't nest the entire `lstack-0.4.0` directory as one skill. For
example, after installing `code-review`, ask the agent to review the target
repository using that skill and verify it loaded the intended definition.
There is no `/lstack` entry point or automatic dependency installation.

ZIP extraction does not reliably restore executable permissions on every host.
If a member invokes a script directly, restore its executable bit from the
`mode` field in provenance; invoking Python scripts through `python3` is another
option where the member documents it. No bundled scripts run during build or
extraction.

## Claude Code plugin: build, install and access

For this optional export, first follow **Optional ZIP exports: obtain and build** to clone and select a trusted committed
checkout. Use a current Claude Code CLI with plugin support. Generate the Claude
target and extract it into an unused staging location; keep that location if you
register its marketplace. The following uses ignored `dist/` under the clone:

```bash
python3 scripts/build-lstack.py --target claude --check
python3 scripts/build-lstack.py --target claude
python3 -m zipfile -e dist/lstack-claude-0.4.0.zip dist/claude-staging
marketplace="$(pwd)/dist/claude-staging/lstack-claude-0.4.0"
plugin="$marketplace/plugins/lstack"
claude plugin validate "$plugin"
claude plugin validate "$marketplace"
```

The archive contains actual plugin contents, not a listing pointing at missing
files. The result JSON reports `marketplace_root` and `plugin_root` relative to
the extraction directory. Its layout is:

```text
lstack-claude-0.4.0/
  .claude-plugin/marketplace.json   # lstack, source ./plugins/lstack
  plugins/lstack/
    .claude-plugin/plugin.json     # name lstack, version 0.4.0
    README.md
    LICENSE
    manifest.json
    provenance.json
    skills/<member>/SKILL.md       # all 41 members, including flattened children
```

Only metadata goes inside `.claude-plugin/`; `skills/` is at the **plugin** root.
The marketplace source is relative to the **marketplace** root, starts with
`./`, contains no `..`, and resolves to the existing `plugins/lstack` directory.
Pass that plugin directory, not the ZIP or the marketplace directory, to
`--plugin-dir`. Using an absolute shell path avoids dependence on the target
project's working directory:

```bash
claude --plugin-dir "$plugin"
```

This loads the plugin for **one session**; it does not install it persistently.
For persistent installation, register the generated local marketplace and
install its single plugin (user scope by default; these commands intentionally
change your own Claude plugin configuration, not repository settings):

```bash
claude plugin marketplace add "$marketplace"
claude plugin install lstack@lstack --scope user
claude plugin list
claude plugin details lstack
claude
```

Start a new session after installation. In that session, use `/plugin` to inspect
the installed plugin and command completion to discover `/lstack:<skill>`.
For example, enter `/lstack:code-review` to review the target repository, or
`/lstack:drawio-generator` for the independently exported suite child. There is
no `/lstack` orchestrator. Plugin skills coexist with standalone skills; use the
qualified command to select this copy rather than an unqualified standalone one.
Review the inventory and prerequisites before running any mutating workflow.
Skill-local `agents/` files remain resources, not native plugin agents.

The repository-root marketplace supports direct GitHub installation once its
metadata is committed/pushed; `dist/` remains ignored and is not fetched.
The optional ZIP instead registers an extracted local marketplace. Both use
**lstack**: choose one registration source, not two conflicting names. Inspect
`claude plugin marketplace list` before switching sources. No downloaded or
installed runtime directories are build inputs.

### Update a local installation

Updates are explicit: review a newer trusted commit, check it out, and build and
extract that commit's Claude archive to a **new** staging directory. Package and
plugin versions come from the same manifest; member versions remain unchanged
unless their sources change separately. Merely refreshing a local marketplace
will not fetch this repository, rebuild a ZIP, or select a different staging
path. Existing output ZIPs are never overwritten: use `--output` with a fresh
filename when rebuilding the same version.

For a marketplace whose registered directory already contains the desired
version, the official refresh/update commands are:

```bash
claude plugin marketplace update lstack
claude plugin update lstack@lstack --scope user
```

For this versioned-staging flow, replace the registration after building the new
version. **Removing a marketplace uninstalls its plugins and removes their
activation settings**; inspect `claude plugin marketplace list` and confirm
`lstack` is this local, single-plugin marketplace before doing so. Restore
any deliberate scope/disabled state yourself after reinstalling:

```bash
# Set marketplace to the absolute NEW extracted lstack-claude-VERSION directory.
claude plugin marketplace remove lstack --scope user
claude plugin marketplace add "$marketplace"
claude plugin install lstack@lstack --scope user
claude plugin details lstack
```

Restart Claude Code after updating (or use `/reload-plugins` where supported).
For session-only use, restart with `--plugin-dir` pointing to the new plugin
root instead. Keep old artifacts for rollback; nothing is automatically deleted.

Official references: [plugins](https://code.claude.com/docs/en/plugins),
[manifest/layout reference](https://code.claude.com/docs/en/plugins-reference),
[local marketplace walkthrough and path rules](https://code.claude.com/docs/en/plugin-marketplaces),
and [installation, scopes, updates and removal](https://code.claude.com/docs/en/discover-plugins).
Native validation checks manifests; it does not prove all member workflows ran.

## Codex plugin: build, install and access

Follow **Optional ZIP exports: obtain and build** first. Use a current Codex CLI with plugin support;
CLI **0.160.0** is the tested version, not a claimed minimum. The target uses the
recommended portable **Agent Plugins 1.0** root manifest, not the supported
legacy `.codex-plugin/plugin.json` compatibility layout. It needs no hooks, MCP
server, app mapping or compatibility overlay. Build output is fixed by the
committed inputs, never selected by the installed Codex version.

```bash
python3 scripts/build-lstack.py --target codex --check
python3 scripts/build-lstack.py --target codex
python3 -m zipfile -e dist/lstack-codex-0.4.0.zip dist/codex-staging
marketplace="$(pwd)/dist/codex-staging/lstack-codex-0.4.0"
codex plugin marketplace add "$marketplace"
codex plugin marketplace list
codex
```

In Codex CLI enter `/plugins`, choose **lstack** from **lstack-local**, and
install it. Start a **new session** before using bundled skills. Registration
and installation intentionally change your Codex configuration/cache. Keep the
extracted marketplace directory accessible. There is no `codex plugin validate`
or `codex plugin install` command assumed by this runbook. CLI 0.160.0 also
exposes the following commands in its own `--help` (check your version first):

```bash
codex plugin list --available --json --marketplace lstack-local
codex plugin add lstack@lstack-local --json
codex plugin list --json --marketplace lstack-local
```

The generated archive is self-contained:

```text
lstack-codex-0.4.0/
  .agents/plugins/marketplace.json  # lstack-local
  plugins/lstack/
    plugin.json                    # Agent Plugins 1.0, name lstack, version 0.4.0
    README.md
    LICENSE
    manifest.json
    provenance.json
    skills/<member>/SKILL.md        # 41 independent members
```

The marketplace entry uses `source: {"source": "local", "path": "./plugins/lstack"}`,
`policy.installation: AVAILABLE`, `policy.authentication: ON_INSTALL`, and
`category: Productivity`, following the official local example. Its path is
relative to the **marketplace root**, not `.agents/plugins/`. The policy field
is catalog metadata; this skills-only plugin adds no service authentication.
The result JSON reports the extraction-relative `marketplace_root` and
`plugin_root`. Skills and resources stay at the plugin root, not inside the
metadata directory. Skill-local `agents/` remain resources, not native agents.

After installation ask Codex, for example: "Use the lstack code-review skill to
review this repository; confirm which SKILL.md you loaded before proceeding."
The independently exported `drawio-generator` and `excalidraw-generator` are
available alongside `diagram-generator`. Inspect `/plugins` and the skill
picker for the names your client exposes; do not assume Claude's
`/lstack:<skill>` syntax applies to Codex. There is no `/lstack` orchestrator.
If standalone copies coexist, check the selected skill's path rather than
assuming which copy an unqualified invocation loads. Read member prerequisites
and approval gates before running any workflow.

**This repository is not a hosted Codex marketplace.** Do not register
`luongnv89/skills` expecting generated contents to be present remotely. The
source checkout contains authoring metadata, not the ignored generated catalog
or hundreds of duplicated skill files. Clone/build/extract locally, or share a
trusted generated ZIP and extract it before registering its root.

For updates select a newer trusted commit and build/extract to a **new**
directory. CLI 0.160.0 refuses to add an already-registered marketplace name
from a different source, so replace the registration before reinstalling.
These commands intentionally change your Codex configuration. Inspect the
existing registration first and confirm `lstack-local` is this local,
single-plugin marketplace; preserve any deliberate enabled/disabled settings.

```bash
# Set marketplace to the absolute NEW extracted lstack-codex-VERSION directory.
codex plugin marketplace list
codex plugin marketplace remove lstack-local
codex plugin marketplace add "$marketplace"
codex plugin marketplace list
codex plugin add lstack@lstack-local --json
```

Confirm the listed root is the new directory, inspect `/plugins` and restore any
deliberate disabled state, then start a **new session**. Registration replacement
alone is not a plugin update: reinstall using `/plugins` or the version-verified
`plugin add` command above. A marketplace refresh alone does not rebuild this
repository's artifacts. Use a fresh `--output` filename for repeat builds and
retain old artifacts for rollback. Do not assume Claude's update commands apply
to Codex.

### Verification and supported surfaces

Native checks on Codex CLI 0.160.0 use a temporary `HOME`, `CODEX_HOME`, XDG paths
and an empty working directory, with file-only credential storage and no copied
credentials. Marketplace registration/listing, local installation and skill
metadata discovery are checked without model execution. This proves native
loading, not successful execution of every workflow. Desktop installation/UI,
authenticated model sessions and all 41 workflows are not exercised. The
current official overview supports CLI `/plugins` and Codex in the ChatGPT
desktop app, but **not the IDE extension**. This local shell-oriented artifact
is not a public-directory submission or a promise of web/mobile/cloud support.

Official references (checked 2026-10-07):
[portable package and marketplace format](https://developers.openai.com/plugins/build/plugins),
[Agent Plugins 1.0 schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json),
[installation and supported surfaces](https://developers.openai.com/codex/plugins),
and [isolated state via CODEX_HOME](https://developers.openai.com/codex/config-advanced).
For older clients, upgrade to a version supporting this format; no compatibility
artifact is emitted or silently substituted.

## Prerequisites and capability limits

- Members retain their own approval gates, compatibility requirements and tool
  dependencies (for example `git`, authenticated `gh`, `curl`, Herdr, OpenCode,
  browser tooling or App Store access). lstack provisions none of these.
- Internal orchestrator members are bundled, but `asm deps` discovery/acquire
  requires an appropriate registry/install setup. Simply extracting a ZIP or
  putting it in a plugin cache does **not** prove those preflights work. Use the
  installed-directory fallback supported by each member, or configure `asm`
  separately. Dependency-preflight success and runtime execution are not claimed
  by packaging or native skill metadata discovery.
- External `browse` from [garrytan/gstack](https://github.com/garrytan/gstack) is
  used by live-browser branches in `design-optimizer`, `viral-product-evaluator`
  and the optional live-URL path in `dont-make-me-think`. Follow those members' fail-soft evidence options
  when unavailable; screenshots cannot be invented.
- `website-agent-readiness` Phase 4 requires `plan-to-issues` from
  [luongnv89/idd](https://github.com/luongnv89/idd), its `issue-creator` dependency,
  and authenticated GitHub tools. Earlier phases have their own requirements.
  These external skills are **not vendored** or fetched by the builder.
- `issue-work-loop` requires `issue-pr-review` from idd in both ISSUE and PR
  modes, and `issue-resolver` from idd in ISSUE mode only. It also requires
  `asm`, Herdr, `git`, authenticated `gh`, and bundled `herdr-agent` resolved
  through its dependency preflight.
- Claude's namespace and either host's plugin cache do **not** repair the unchanged source
  preflights. Several orchestrators look for global `~/.claude/skills/` or
  `~/.agents/skills/` copies or use `asm deps`; embedded sibling invocations can
  remain unqualified. A bundled sibling's presence is not proof that those
  lookups resolve it. Follow each source's preflight using separately installed
  skills/registry setup when required; even an idd plugin alone may not satisfy
  a global lookup. lstack does not silently rewrite paths, sibling commands or
  dependency declarations, and does not claim all complex workflows run
  plugin-locally. Namespace discovery is distinct from runtime dependency
  compatibility.
- The flattened suite retains child-local resources. Human docs or install
  examples that refer to repository-relative nested source paths still describe
  the original repository, not the extracted layout. Follow the manifest's
  source-to-name mapping; no member instructions are rewritten for this bundle.
- Member-root tests/evals stay in the source repository. Packaging checks prove
  artifact structure/parity/safety, not all 41 workflows' runtime behavior,
  host compatibility, or that a human understood every report.

## Maintain and validate

`packages/lstack/manifest.json` is the single authoring source of the package
version and adapter metadata, not itself a native plugin manifest. Its explicit
five-key `claude` and `codex` contracts generate native metadata. The package
version is the plugin version; member versions remain independent. New/removed
skill definitions need an explicit membership update; catalog drift is rejected.
Bump the package version for a changed distribution contract. Never hand-edit
`dist/` or maintain independent root JSON versions.

Generate and check root Claude projections **from the authoring working tree**:

```bash
python3 scripts/build-lstack.py --write-plugin-metadata
python3 scripts/build-lstack.py --check-plugin-metadata
```

These modes validate canonical membership, existing regular skill paths and the
two root files' exact deterministic render (including version and additive paths).
Check mode is read-only. Write mode updates only `.claude-plugin/plugin.json`
and `marketplace.json`, refusing symlink/non-regular destinations. The two writes
are not transactional: an interruption or I/O failure can leave incomplete or
mismatched metadata. Re-run write mode, then check mode successfully before
staging or publishing. No archive or member source is changed.
Stage regenerated metadata with intended manifest changes when ready to commit.

Optional native validation (no model execution):

```bash
claude plugin validate --json .claude-plugin/plugin.json
claude plugin validate --json .claude-plugin/marketplace.json
claude plugin validate --json --strict .
```

The preserved root `CLAUDE.md` causes strict validation to exit 1 with exactly
this known warning: **"CLAUDE.md at the plugin root is not loaded as project
context. To ship context with your plugin, use a skill (skills/<name>/SKILL.md)
instead."** Baseline only that message on root `CLAUDE.md`, with zero errors
and zero other warnings; do not blanket-ignore warnings or remove the wrapper.
Root plugin and marketplace manifests themselves should have no errors/warnings.
Use disposable `HOME`/`CLAUDE_CONFIG_DIR` without credentials when checking CLI
behavior; a strict nonzero exit alone is not a successful baseline check.

In contrast, optional archive builds and `--check` still use **committed inputs**
and require the running builder to match the selected revision. A local draft
builder cannot pass archive CLI checks against an older HEAD; tests commit
snapshots only in disposable fixture repositories, never the source checkout.
Flattened Claude exports deliberately omit the root's nested `skills` paths;
Codex retains `lstack-local` and its existing output layout.

```bash
python3 tests/test-lstack-packaging.py
python3 tests/test-lstack-claude-packaging.py
python3 tests/test-lstack-codex-packaging.py
python3 scripts/build-lstack.py --check
python3 scripts/build-lstack.py --target claude --check
python3 scripts/build-lstack.py --target codex --check
```

Tests use temporary Git repositories and the standard library, with a real-tree
parity/discovery check. They do not modify installed skills, invoke agents,
acquire dependency leases or run member scripts.
