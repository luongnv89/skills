# Coding-agent CLIs

Install only after Node.js LTS is on PATH (`node -v`, `npm -v`). Prefer official documented commands. Confirm any `curl | sh` URL before running.

Skip a tool if `command -v` already finds it and `--version` works.

## Claude Code

Preferred (native installer — check [Anthropic's current setup page](https://docs.anthropic.com/en/docs/claude-code/setup) if this drifts):

```bash
# Unix — confirm URL with the user
curl -fsSL https://claude.ai/install.sh | bash
```

Fallback (needs Node 18+):

```bash
npm install -g @anthropic-ai/claude-code
```

Windows: prefer `winget search claude` / the official Windows installer from the same docs page; npm global also works.

Verify: `claude --version`. Login is interactive (`claude`) — do not paste API keys into the skill log.

## Codex (OpenAI)

```bash
npm install -g @openai/codex
```

macOS alternative if the formula exists: `brew install codex` (only if `brew info codex` looks official).

Verify: `codex --version`.

## Pi

This user's Pi is the [pi-coding-agent](https://www.npmjs.com/package/@mariozechner/pi-coding-agent) (see `pi-extensions` / `pi-web-access` notes):

```bash
npm install -g @mariozechner/pi-coding-agent
```

Verify: `pi --version`. Optional later: `pi-web-access` — do not install extras unless asked.

## OpenCode

macOS:

```bash
brew install anomalyco/tap/opencode
```

Cross-platform (Node/bun):

```bash
npm install -g opencode-ai
# or: bun add -g opencode-ai
```

Windows: `winget search opencode` first; otherwise npm global.

Verify: `opencode --version`.

## PATH

"Installed but `command not found`" is almost always the npm global bin missing from PATH — fix per
`optimize.md#npm-global-bin-not-on-path`.

## Auth

Leave auth to the first interactive run of each CLI. Never write keys into `~/.zshrc` from this skill.
