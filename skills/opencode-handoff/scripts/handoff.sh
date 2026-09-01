#!/usr/bin/env bash
# handoff.sh — hand a limit-blocked OpenCode session over to a fresh sandbox.
#
# Creates an opencode-sandbox container for a project with the host's agent
# setup mounted but WITHOUT the host's OpenCode config, token, or key, then
# opens a detached tmux session attached to it. OpenCode inside the container
# is unauthenticated on purpose — that is what gives it a fresh usage
# allowance. Log in inside the panel.
#
# Usage:
#   handoff.sh --project DIR [options]
#
# Required:
#   --project DIR        project to hand off (mounted read-write at /workspace)
#
# Optional:
#   --name NAME          container name (default: opencode-handoff-<project>-<epoch>)
#   --session NAME       tmux session name (default: derived from the container)
#   --image IMAGE        docker image (default: ghcr.io/luongnv89/devbox:latest;
#                        passed through to run_opencode.sh)
#   --no-ssh             do not mount ~/.ssh
#   --no-github          do not mount ~/.config/gh or inject GH_TOKEN
#   --no-tmux            create the container and print the attach command, but
#                        do not create a tmux session
#   --sandbox-script P   path to opencode-sandbox's run_opencode.sh (default:
#                        resolved from the sibling skill, then ~/.claude/skills)
#
# The container is KEPT on exit. Remove it only when the user confirms:
#   docker rm -f <container>
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() { grep '^#' "${BASH_SOURCE[0]}" | sed -e '1d' -e 's/^# \{0,1\}//'; }

PROJECT_DIR=""
CONTAINER_NAME=""
SESSION_NAME=""
IMAGE="ghcr.io/luongnv89/devbox:latest"
SANDBOX_SCRIPT=""
WITH_SSH=1
WITH_GITHUB=1
WITH_TMUX=1

while [ $# -gt 0 ]; do
  case "$1" in
    --project|--name|--session|--image|--sandbox-script)
      if [ $# -lt 2 ]; then
        echo "Error: '$1' requires a value but none was given. Run with --help for usage." >&2
        exit 1
      fi
      ;;
  esac
  case "$1" in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --name) CONTAINER_NAME="$2"; shift 2 ;;
    --session) SESSION_NAME="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --sandbox-script) SANDBOX_SCRIPT="$2"; shift 2 ;;
    --no-ssh) WITH_SSH=0; shift ;;
    --no-github) WITH_GITHUB=0; shift ;;
    --no-tmux) WITH_TMUX=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: unknown argument '$1'. Run with --help for usage." >&2; exit 1 ;;
  esac
done

if [ -z "$PROJECT_DIR" ]; then
  echo "Error: --project DIR is required (the project to hand off)." >&2
  exit 1
fi
if [ ! -d "$PROJECT_DIR" ]; then
  echo "Error: project directory '$PROJECT_DIR' does not exist or is not a directory." >&2
  exit 1
fi
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

# --- resolve opencode-sandbox's run_opencode.sh --------------------------
if [ -z "$SANDBOX_SCRIPT" ]; then
  for candidate in \
    "$SCRIPT_DIR/../../opencode-sandbox/scripts/run_opencode.sh" \
    "$HOME/.claude/skills/opencode-sandbox/scripts/run_opencode.sh" \
    "$HOME/.agents/skills/opencode-sandbox/scripts/run_opencode.sh"; do
    if [ -f "$candidate" ]; then
      SANDBOX_SCRIPT="$(cd "$(dirname "$candidate")" && pwd)/$(basename "$candidate")"
      break
    fi
  done
fi
if [ -z "$SANDBOX_SCRIPT" ] || [ ! -f "$SANDBOX_SCRIPT" ]; then
  cat >&2 <<'EOF'
Error: could not find opencode-sandbox's run_opencode.sh.

  To fix:  asm install https://github.com/luongnv89/skills --skill opencode-sandbox
           (or pass --sandbox-script /path/to/run_opencode.sh)

This skill composes opencode-sandbox; it does not duplicate its container logic.
EOF
  exit 1
fi

# The two flags this handoff depends on. An older opencode-sandbox without them
# would silently mount the host's OpenCode credentials — the one thing this
# skill exists to prevent — so fail loudly instead.
for required_flag in --no-opencode-config --with-agents; do
  if ! grep -q -- "$required_flag" "$SANDBOX_SCRIPT"; then
    cat >&2 <<EOF
Error: '$SANDBOX_SCRIPT' does not support $required_flag.

  To fix:  update opencode-sandbox to v2.1.0 or newer.

Without it the container would inherit the host's OpenCode config and token,
defeating the purpose of the handoff (a fresh usage allowance).
EOF
    exit 1
  fi
done

if [ -z "$CONTAINER_NAME" ]; then
  slug="$(basename -- "$PROJECT_DIR" | tr -cd 'a-zA-Z0-9._-' | tr '[:upper:]' '[:lower:]')"
  [ -n "$slug" ] || slug="project"
  case "$slug" in
    [a-zA-Z0-9]*) ;;
    *) slug="p${slug}" ;;
  esac
  CONTAINER_NAME="opencode-handoff-${slug}-$(date +%s)"
fi

# --- create the container ------------------------------------------------
sandbox_args=(--project "$PROJECT_DIR" --start-only --name "$CONTAINER_NAME"
              --no-opencode-config --with-agents)
[ -n "$IMAGE" ] && sandbox_args+=(--image "$IMAGE")
[ "$WITH_SSH" = "1" ] || sandbox_args+=(--no-ssh)
[ "$WITH_GITHUB" = "1" ] || sandbox_args+=(--no-github)

echo "Creating handoff container '$CONTAINER_NAME' for $PROJECT_DIR..." >&2
bash "$SANDBOX_SCRIPT" "${sandbox_args[@]}"

# --- verify the credential boundary before handing the panel over --------
# AC: the OpenCode config, token, and key must be absent from the container.
# Probe first: without this, a `docker exec` that fails for any reason would
# make every `test -e` below fail too, and absence-by-failure would read as a
# clean boundary. Prove the checks can actually run before trusting them.
if ! docker exec "$CONTAINER_NAME" true 2>/dev/null; then
  echo "Error: cannot exec into '$CONTAINER_NAME' — the credential boundary could not be verified." >&2
  echo "Inspect with: docker logs '$CONTAINER_NAME'" >&2
  echo "Remove it with: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi

leaked=0

# Host credential directories must not be bind-mounted. The skills/ subdirectory
# is a different source path, so it is allowed. Resolve realpaths so a skills/
# directory that is actually a symlink to the parent still fails closed.
host_opencode_config=""
host_opencode_data=""
if [ -d "$HOME/.config/opencode" ]; then
  host_opencode_config="$(cd "$HOME/.config/opencode" && pwd -P)"
fi
if [ -d "$HOME/.local/share/opencode" ]; then
  host_opencode_data="$(cd "$HOME/.local/share/opencode" && pwd -P)"
fi
mounts=""
if ! mounts="$(docker inspect -f '{{range .Mounts}}{{.Source}}|{{.Destination}}{{println}}{{end}}' "$CONTAINER_NAME")"; then
  echo "Error: cannot inspect mounts of '$CONTAINER_NAME' — the credential boundary could not be verified." >&2
  echo "Remove it with: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi
while IFS='|' read -r src dest; do
  [ -n "${src:-}" ] || continue
  resolved="$src"
  if [ -d "$src" ]; then
    resolved="$(cd "$src" && pwd -P)"
  elif [ -e "$src" ]; then
    resolved="$(cd "$(dirname -- "$src")" && pwd -P)/$(basename -- "$src")"
  fi
  if [ -n "$host_opencode_config" ] && [ "$resolved" = "$host_opencode_config" ]; then
    echo "Error: host OpenCode config is mounted at '$dest' inside '$CONTAINER_NAME' (source: $src)." >&2
    leaked=1
  fi
  if [ -n "$host_opencode_data" ] && [ "$resolved" = "$host_opencode_data" ]; then
    echo "Error: host OpenCode data dir is mounted at '$dest' inside '$CONTAINER_NAME' (source: $src)." >&2
    leaked=1
  fi
done <<< "$mounts"

# auth.json / service.json must not exist under any OpenCode config or data
# path in the container (image leftovers, a project that is $HOME, a leaked
# file inside the skills/ submount). Searching only those trees avoids
# false positives on unrelated auth.json files in the project.
found_files=""
if ! found_files="$(docker exec "$CONTAINER_NAME" sh -c '
  for dir in /root/.config/opencode /root/.local/share/opencode /root/.opencode \
             /workspace/.config/opencode /workspace/.local/share/opencode /workspace/.opencode; do
    if [ -d "$dir" ]; then
      find "$dir" \( -name auth.json -o -name service.json \) -print
    fi
  done
  if [ -d /home ]; then
    find /home \( -name auth.json -o -name service.json \) \
      \( -path "*/.config/opencode/*" -o -path "*/.local/share/opencode/*" -o -path "*/.opencode/*" \) \
      -print
  fi
')"; then
  echo "Error: credential search failed inside '$CONTAINER_NAME' — the boundary could not be verified." >&2
  echo "Remove it with: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi
if [ -n "$found_files" ]; then
  echo "Error: OpenCode credential files are present inside '$CONTAINER_NAME':" >&2
  printf '%s\n' "$found_files" | while IFS= read -r p; do
    [ -n "$p" ] || continue
    echo "  $p" >&2
  done
  leaked=1
fi

if [ "$leaked" = "1" ]; then
  echo "Refusing to hand over. Inspect the mounts with: docker inspect '$CONTAINER_NAME'" >&2
  echo "Remove the container with: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi
echo "Credential boundary: OK (no OpenCode config, token, or key in the container)." >&2

if docker exec "$CONTAINER_NAME" test -d /root/.agents/skills 2>/dev/null; then
  agent_count="$(docker exec "$CONTAINER_NAME" sh -c 'ls /root/.agents/skills | wc -l' 2>/dev/null | tr -d ' ')"
  echo "Global agent setup: $agent_count skills under /root/.agents/skills." >&2
else
  echo "Warning: /root/.agents/skills is not present in the container — the global agent setup did not mount. Check that ~/.agents exists on the host." >&2
fi
if docker exec "$CONTAINER_NAME" test -d /workspace/.agents 2>/dev/null; then
  echo "Project-local agent setup: /workspace/.agents (same relative path as on the host)." >&2
fi

OPENCODE_CLI="$(docker exec "$CONTAINER_NAME" sh -c '
  if command -v opencode2 >/dev/null 2>&1; then
    command -v opencode2
  elif command -v opencode >/dev/null 2>&1; then
    command -v opencode
  fi
' 2>/dev/null || true)"
if [ -z "$OPENCODE_CLI" ]; then
  echo "Error: neither 'opencode2' nor 'opencode' is available in container '$CONTAINER_NAME'. Use an image with the OpenCode CLI installed." >&2
  echo "Remove the container with: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi

ATTACH_CMD="docker exec -it ${CONTAINER_NAME} zsh"

if [ "$WITH_TMUX" != "1" ]; then
  echo "SESSION_NAME=" >&2
  echo "ATTACH_COMMAND=${ATTACH_CMD}" >&2
  exit 0
fi

# --- open the panel ------------------------------------------------------
if ! command -v tmux >/dev/null 2>&1; then
  echo "Warning: tmux is not on PATH — skipping the panel. Attach by hand:" >&2
  echo "  ${ATTACH_CMD}" >&2
  echo "SESSION_NAME=" >&2
  echo "ATTACH_COMMAND=${ATTACH_CMD}" >&2
  exit 0
fi

if [ -z "$SESSION_NAME" ]; then
  SESSION_NAME="$(printf '%s' "$CONTAINER_NAME" | tr -cd 'a-zA-Z0-9_-')"
fi
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  echo "Error: tmux session '$SESSION_NAME' already exists. Pass --session with a unique name." >&2
  echo "Attach the container by hand meanwhile: ${ATTACH_CMD}" >&2
  exit 1
fi

# Detached, never `tmux attach-session` from a non-TTY tool.
tmux new-session -d -s "$SESSION_NAME" -c "$PROJECT_DIR" "$ATTACH_CMD"

cat >&2 <<EOF

SESSION_NAME=${SESSION_NAME}
ATTACH_COMMAND=${ATTACH_CMD}

Open the panel:

  tmux attach-session -t ${SESSION_NAME}

Then, inside it (OpenCode starts unauthenticated — this is the fresh allowance):

  ${OPENCODE_CLI} auth login
  ${OPENCODE_CLI}

Container kept: ${CONTAINER_NAME}. Remove it only when you confirm:
  docker rm -f ${CONTAINER_NAME}
EOF
