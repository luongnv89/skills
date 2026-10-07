# lstack

**lstack 0.1.0** is a platform-neutral ZIP distribution of this repository's
maintained first-party Agent Skills. It is a package, not a new skill or runtime.
Claude Code and Codex plugin adapters are separate work (#396 and #395); this
package has no plugin manifest, hooks, MCP server, npm publication or installer.

## Contents and scope

[manifest.json](manifest.json) explicitly lists all **41** current tracked skill
definitions: 39 top-level skills plus `drawio-generator` and
`excalidraw-generator`, the two children of `diagram-generator`. Every member is
exported as a separately discoverable `skills/<name>/SKILL.md` directory. The
umbrella copy excludes those children's subtrees, so no skill occurs twice.
Flat task orchestrators continue to share independently exported members.

Included files keep their original bytes and Git executable modes: `SKILL.md`,
references, scripts, agents, assets and human-facing docs. Package version 0.1.0
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

The default output is `dist/lstack-0.1.0.zip` (ignored by Git). The JSON result
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
python3 -m zipfile -l dist/lstack-0.1.0.zip
python3 -m zipfile -e dist/lstack-0.1.0.zip /tmp/lstack-staging
```

Layout:

```text
lstack-0.1.0/
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
replacing it; don't nest the entire `lstack-0.1.0` directory as one skill. For
example, after installing `code-review`, ask the agent to review the target
repository using that skill and verify it loaded the intended definition.
There is no `/lstack` entry point or automatic dependency installation.

ZIP extraction does not reliably restore executable permissions on every host.
If a member invokes a script directly, restore its executable bit from the
`mode` field in provenance; invoking Python scripts through `python3` is another
option where the member documents it. No bundled scripts run during build or
extraction.

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
  used by live-browser branches in `design-optimizer` and
  `viral-product-evaluator`. Follow those members' fail-soft evidence options
  when unavailable; screenshots cannot be invented.
- `website-agent-readiness` Phase 4 requires `plan-to-issues` from
  [luongnv89/idd](https://github.com/luongnv89/idd), its `issue-creator` dependency,
  and authenticated GitHub tools. Earlier phases have their own requirements.
  These external skills are **not vendored** or fetched by the builder.
- The flattened suite retains child-local resources. Human docs or install
  examples that refer to repository-relative nested source paths still describe
  the original repository, not the extracted layout. Follow the manifest's
  source-to-name mapping; no member instructions are rewritten for this bundle.
- Member-root tests/evals stay in the source repository. Packaging checks prove
  artifact structure/parity/safety, not all 41 workflows' runtime behavior,
  host compatibility, or that a human understood every report.

## Maintain and validate

The manifest is an internal versioned contract for later adapters, not a native
Claude/Codex manifest. New/removed tracked skill definitions require an explicit
membership update: the builder rejects catalog/manifest drift. Bump the package
version when changing its published membership/layout contract; member versions
still follow the catalog's ordinary source-edit rules. Never hand-edit `dist/`.

```bash
python3 tests/test-lstack-packaging.py
python3 scripts/build-lstack.py --check
```

Tests use temporary Git repositories and the standard library, with a real-tree
parity/discovery check. They do not modify installed skills, invoke agents,
acquire dependency leases or run member scripts.
