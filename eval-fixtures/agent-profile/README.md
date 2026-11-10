# agent-profile eval fixtures

Setup for the evals in `meta/agent-profile/evals/evals.json`:

- `profiles.json`: copy to `$XDG_CONFIG_HOME/agent-profile/profiles.json` in a sandbox
  (`XDG_CONFIG_HOME` and `XDG_CACHE_HOME` pointing into a temp dir). It holds the global
  profiles `cc-sonnet`, `codex-high` and `shared`.
- `project-profiles.json`: copy to `.agent-profiles.json` at the root of a throwaway git
  repo; its `shared` overrides the global one.

No file holds a credential.
