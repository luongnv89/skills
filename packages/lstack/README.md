# lstack

**lstack 0.2.0** distributes this repository's maintained first-party Agent
Skills as a platform-neutral ZIP or a skills-only Claude Code plugin with a
local marketplace. It is a package, not a new skill or runtime. The Codex adapter
remains separate work (#395). There are no plugin hooks, MCP servers, native
plugin agents, npm publications or automatic dependency installers.

## Contents and scope

[manifest.json](manifest.json) explicitly lists all **41** current tracked skill
definitions: 39 top-level skills plus `drawio-generator` and
`excalidraw-generator`, the two children of `diagram-generator`. Every member is
exported as a separately discoverable `skills/<name>/SKILL.md` directory. The
umbrella copy excludes those children's subtrees, so no skill occurs twice.
Flat task orchestrators continue to share independently exported members.

Included files keep their original bytes and Git executable modes: `SKILL.md`,
references, scripts, agents, assets and human-facing docs. Package version 0.2.0
is independent of both the catalog release and member versions. Generated
`provenance.json` records the full source commit, manifest/builder SHA-256,
original member versions, and source/destination/hash/mode for every member file.
The root MIT `LICENSE`, package README and manifest accompany the payload.

Excluded: member-root `evals/` and `tests/` (development fixtures), untracked,
ignored, downloaded and installed copies, retired skills, `*-workspace/`, runtime
folders (`.git`, `.gitissue`, `.claude`, `.agents`, `.pi`, `.asm-improver`,
`node_modules`, `dist`, `build`, `__pycache__`, `.venv`, `venv`), editor/OS scratch,
`.env*`, `credentials*`, `secrets*`, SSH key files and credential-like extensions.
The builder rejects included symlinks/submodules, unsafe paths, conflicting
member names and known live-key/private-key patterns. This is a conservative
filter, **not a general secret detector**; inspect inputs before distribution.

## Obtain and build

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

The default output is `dist/lstack-0.2.0.zip` (ignored by Git). The JSON result
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
python3 -m zipfile -l dist/lstack-0.2.0.zip
python3 -m zipfile -e dist/lstack-0.2.0.zip /tmp/lstack-staging
```

Layout:

```text
lstack-0.2.0/
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
replacing it; don't nest the entire `lstack-0.2.0` directory as one skill. For
example, after installing `code-review`, ask the agent to review the target
repository using that skill and verify it loaded the intended definition.
There is no `/lstack` entry point or automatic dependency installation.

ZIP extraction does not reliably restore executable permissions on every host.
If a member invokes a script directly, restore its executable bit from the
`mode` field in provenance; invoking Python scripts through `python3` is another
option where the member documents it. No bundled scripts run during build or
extraction.

## Claude Code plugin: build, install and access

First follow **Obtain and build** to clone and select a trusted committed
checkout. Use a current Claude Code CLI with plugin support. Generate the Claude
target and extract it into an unused staging location; keep that location if you
register its marketplace. The following uses ignored `dist/` under the clone:

```bash
python3 scripts/build-lstack.py --target claude --check
python3 scripts/build-lstack.py --target claude
python3 -m zipfile -e dist/lstack-claude-0.2.0.zip dist/claude-staging
marketplace="$(pwd)/dist/claude-staging/lstack-claude-0.2.0"
plugin="$marketplace/plugins/lstack"
claude plugin validate "$plugin"
claude plugin validate "$marketplace"
```

The archive contains actual plugin contents, not a listing pointing at missing
files. The result JSON reports `marketplace_root` and `plugin_root` relative to
the extraction directory. Its layout is:

```text
lstack-claude-0.2.0/
  .claude-plugin/marketplace.json   # lstack-local, source ./plugins/lstack
  plugins/lstack/
    .claude-plugin/plugin.json     # name lstack, version 0.2.0
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
claude plugin install lstack@lstack-local --scope user
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

**This repository is not a hosted Claude marketplace.** Do not run
`claude plugin marketplace add luongnv89/skills` expecting lstack to be listed:
generated `dist/` files are absent from a fetched repository. Clone/build/extract
first, or share the trusted generated ZIP and have the recipient extract it.
No downloaded/installed runtime directories are build inputs.

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
claude plugin marketplace update lstack-local
claude plugin update lstack@lstack-local --scope user
```

For this versioned-staging flow, replace the registration after building the new
version. **Removing a marketplace uninstalls its plugins and removes their
activation settings**; inspect `claude plugin marketplace list` and confirm
`lstack-local` is this local, single-plugin marketplace before doing so. Restore
any deliberate scope/disabled state yourself after reinstalling:

```bash
# Set marketplace to the absolute NEW extracted lstack-claude-VERSION directory.
claude plugin marketplace remove lstack-local --scope user
claude plugin marketplace add "$marketplace"
claude plugin install lstack@lstack-local --scope user
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

## Prerequisites and capability limits

- Members retain their own approval gates, compatibility requirements and tool
  dependencies (for example `git`, authenticated `gh`, `curl`, Herdr, OpenCode,
  browser tooling or App Store access). lstack provisions none of these.
- Internal orchestrator members are bundled, but `asm deps` discovery/acquire
  requires an appropriate registry/install setup. Simply extracting a ZIP or
  putting it in a plugin cache does **not** prove those preflights work. Use the
  installed-directory fallback supported by each member, or configure `asm`
  separately. No runtime execution or host-native discovery is claimed here.
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
- Claude's namespace and plugin cache do **not** repair the unchanged source
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

The manifest is an internal versioned contract, not itself a native plugin
manifest. Its explicit `claude` metadata generates the native plugin manifest
and local marketplace; the package version is the plugin version. New/removed tracked skill definitions require an explicit
membership update: the builder rejects catalog/manifest drift. Bump the package
version when changing its published membership/layout contract; member versions
still follow the catalog's ordinary source-edit rules. Never hand-edit `dist/`.

```bash
python3 tests/test-lstack-packaging.py
python3 tests/test-lstack-claude-packaging.py
python3 scripts/build-lstack.py --check
python3 scripts/build-lstack.py --target claude --check
```

Tests use temporary Git repositories and the standard library, with a real-tree
parity/discovery check. They do not modify installed skills, invoke agents,
acquire dependency leases or run member scripts.
