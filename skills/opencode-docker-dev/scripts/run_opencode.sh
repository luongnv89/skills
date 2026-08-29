#!/usr/bin/env bash
# run_opencode.sh — run OpenCode non-interactively, sandboxed in a
# luongnv89/docker-dev container. The container is kept by default so you can
# attach a shell; pass --rm to restore auto-remove.
#
# Agents: use two invocations so the user sees the attach command before
# OpenCode blocks — --start-only, then --exec-in NAME with --message.
# A single --project + --message invocation still works (start then exec).
#
# Usage:
#   run_opencode.sh --project DIR --start-only [options]
#   run_opencode.sh --project DIR --message "task" --exec-in NAME [options]
#   run_opencode.sh --project DIR --message "task" [options]
#
# Required:
#   --project DIR          local directory to mount read-write at /workspace
#   --message TEXT          prompt text passed to `opencode run`
#                           (not required with --start-only)
#
# Optional:
#   --file PATH              host file to copy to /scratch inside the
#                             container, passed via opencode --file.
#                             For long/complex tasks: write them to a file, pass --file, and give
#                             a short --message like "Follow the attached file's instructions exactly."
#   --with-claude-skills      mount ~/.claude (and ~/.agents, for symlinked skills) read-only
#   --with-git-identity       mount ~/.gitconfig read-only, for correct commit authorship
#   --image IMAGE             docker image (default: ghcr.io/luongnv89/u2604dev:latest)
#   --format FORMAT           opencode output format: default | json (default: default)
#   --model MODEL             opencode model to use (e.g. opencode/muse-spark-1.2-contributor-free)
#   --name NAME               container name (default: opencode-dev-<project>-<epoch>)
#   --start-only              create the keep-alive container, print the attach
#                             command, exit 0 (does not run OpenCode)
#   --exec-in NAME            run OpenCode in an already-started container
#   --rm                      remove the container when this script exits (opt-in;
#                             default is to keep it running so you can attach)
#
# Never mounts ~/.ssh or injects a GH token/GH_TOKEN — see
# references/mounts-and-credentials.md for why, and what to do if a task
# genuinely needs push/publish access.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  grep '^#' "${BASH_SOURCE[0]}" | sed -e '1d' -e 's/^# \{0,1\}//'
}

IMAGE="ghcr.io/luongnv89/u2604dev:latest"
FORMAT="default"
MODEL=""
PROJECT_DIR=""
MESSAGE=""
TASK_FILE=""
WITH_CLAUDE_SKILLS=0
WITH_GIT_IDENTITY=0
CONTAINER_NAME=""
REMOVE_ON_EXIT=0
RAN_OPENCODE=0
START_ONLY=0
EXEC_IN=""

while [ $# -gt 0 ]; do
  case "$1" in
    --project|--message|--file|--image|--format|--model|--name|--exec-in)
      if [ $# -lt 2 ]; then
        echo "Error: '$1' requires a value but none was given. Run with --help for usage." >&2
        exit 1
      fi
      ;;
  esac
  case "$1" in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --file) TASK_FILE="$2"; shift 2 ;;
    --with-claude-skills) WITH_CLAUDE_SKILLS=1; shift ;;
    --with-git-identity) WITH_GIT_IDENTITY=1; shift ;;
    --image) IMAGE="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --name) CONTAINER_NAME="$2"; shift 2 ;;
    --start-only) START_ONLY=1; shift ;;
    --exec-in) EXEC_IN="$2"; shift 2 ;;
    --rm) REMOVE_ON_EXIT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Error: unknown argument '$1'. Run with --help for usage." >&2; exit 1 ;;
  esac
done

if [ -z "$PROJECT_DIR" ]; then
  echo "Error: --project DIR is required (the local project directory to mount at /workspace)." >&2
  exit 1
fi
if [ ! -e "$PROJECT_DIR" ]; then
  echo "Error: project directory '$PROJECT_DIR' does not exist." >&2
  exit 1
fi
if [ ! -d "$PROJECT_DIR" ]; then
  echo "Error: project directory '$PROJECT_DIR' exists but is not a directory." >&2
  exit 1
fi
if [ "$START_ONLY" = "1" ] && [ -n "$EXEC_IN" ]; then
  echo "Error: pass either --start-only or --exec-in NAME, not both." >&2
  exit 1
fi
if [ "$START_ONLY" = "1" ] && [ "$REMOVE_ON_EXIT" = "1" ]; then
  echo "Error: --rm cannot be combined with --start-only (the container would be deleted before OpenCode runs). Pass --rm on the --exec-in invocation instead." >&2
  exit 1
fi
if [ "$START_ONLY" != "1" ] && [ -z "$MESSAGE" ]; then
  echo "Error: --message TEXT is required (the prompt to send to OpenCode). For long/complex tasks, write them to a file and pass --file plus a short --message like \"Follow the attached file's instructions exactly.\"" >&2
  exit 1
fi
if [ -n "$TASK_FILE" ] && [ ! -f "$TASK_FILE" ]; then
  echo "Error: --file path '$TASK_FILE' does not exist." >&2
  exit 1
fi
case "$FORMAT" in
  default|json) ;;
  *) echo "Error: --format must be 'default' or 'json', got '$FORMAT'." >&2; exit 1 ;;
esac

PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

if [ -n "$EXEC_IN" ]; then
  CONTAINER_NAME="$EXEC_IN"
fi

if [ -z "$CONTAINER_NAME" ]; then
  slug="$(basename -- "$PROJECT_DIR" | tr -cd 'a-zA-Z0-9._-' | tr '[:upper:]' '[:lower:]')"
  if [ -z "$slug" ]; then
    slug="project"
  fi
  case "$slug" in
    [a-zA-Z0-9]*) ;;
    *) slug="p${slug}" ;;
  esac
  CONTAINER_NAME="opencode-dev-${slug}-$(date +%s)"
fi

bash "$SCRIPT_DIR/preflight.sh" "$IMAGE"

print_attach_block() {
  cat >&2 <<EOF

CONTAINER_NAME=${CONTAINER_NAME}

Attach (copy-paste into another terminal):

  docker exec -it ${CONTAINER_NAME} zsh

EOF
}

ensure_running() {
  local state
  if ! docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "Error: container '$CONTAINER_NAME' does not exist." >&2
    echo "Fix: start a new one with --start-only, or pass a name from 'docker ps -a --filter label=opencode-docker-dev=1'." >&2
    exit 1
  fi
  state="$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")"
  if [ "$state" = "true" ]; then
    return 0
  fi
  echo "Container '$CONTAINER_NAME' exists but is not running. Starting it..." >&2
  if ! docker start "$CONTAINER_NAME" >/dev/null; then
    echo "Error: 'docker start $CONTAINER_NAME' failed. Inspect with: docker logs '$CONTAINER_NAME'" >&2
    exit 1
  fi
  if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" != "true" ]; then
    echo "Error: container '$CONTAINER_NAME' did not stay running after docker start. Inspect with: docker logs '$CONTAINER_NAME'" >&2
    exit 1
  fi
}

run_opencode_in_container() {
  local oc_ec=0
  local opencode_args=(run "$MESSAGE")
  RAN_OPENCODE=1
  if [ -n "$TASK_FILE" ]; then
    local basename
    basename="$(basename -- "$TASK_FILE")"
    if ! docker exec "$CONTAINER_NAME" mkdir -p /scratch; then
      echo "Error: could not create /scratch inside container '$CONTAINER_NAME'." >&2
      exit 1
    fi
    if ! docker cp "$TASK_FILE" "$CONTAINER_NAME:/scratch/$basename"; then
      echo "Error: 'docker cp' failed to copy '$TASK_FILE' into the container." >&2
      exit 1
    fi
    opencode_args+=("--file=/scratch/$basename")
  fi
  opencode_args+=(--auto --format "$FORMAT")
  if [ -n "$MODEL" ]; then
    opencode_args+=(--model "$MODEL")
  fi
  set +e
  docker exec -w /workspace "$CONTAINER_NAME" opencode "${opencode_args[@]}"
  oc_ec=$?
  set -e
  if [ "$REMOVE_ON_EXIT" != "1" ]; then
    echo "Container kept: $CONTAINER_NAME (still running)." >&2
    echo "Ask the user before removing it. If they confirm: docker rm -f ${CONTAINER_NAME}" >&2
  fi
  exit "$oc_ec"
}

cleanup() {
  if [ "$REMOVE_ON_EXIT" = "1" ] && [ "$RAN_OPENCODE" = "1" ]; then
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

# --- --exec-in: OpenCode in an already-created container -----------------
if [ -n "$EXEC_IN" ]; then
  ensure_running
  print_attach_block
  run_opencode_in_container
fi

# --- create a new keep-alive container -----------------------------------
if docker container inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "Error: a container named '$CONTAINER_NAME' already exists (name collision)." >&2
  echo "Fix: pass --name with a unique value (e.g. a timestamp suffix), or --exec-in '$CONTAINER_NAME' to reuse it." >&2
  echo "Remove it only if the user confirms destroying the kept container: docker rm -f '$CONTAINER_NAME'" >&2
  exit 1
fi

MOUNTS=(-v "${PROJECT_DIR}:/workspace")

if [ -d "$HOME/.config/opencode" ]; then
  MOUNTS+=(-v "$HOME/.config/opencode:/root/.config/opencode")
else
  echo "Warning: $HOME/.config/opencode not found — the container will have no OpenCode auth/config and may prompt to log in. Run 'opencode' once on the host first if this task needs a real provider." >&2
fi

if [ "$WITH_CLAUDE_SKILLS" = "1" ]; then
  if [ -d "$HOME/.claude" ]; then
    MOUNTS+=(-v "$HOME/.claude:/root/.claude:ro")
    # ~/.claude/skills/<name> is frequently a symlink to ~/.agents/skills/<name>.
    # Mounting ~/.claude alone leaves that symlink dangling inside the
    # container (ls shows the entry, but reading the file 404s) — mount
    # ~/.agents too whenever it exists so skill files actually resolve.
    if [ -d "$HOME/.agents" ]; then
      MOUNTS+=(-v "$HOME/.agents:/root/.agents:ro")
    fi
  else
    echo "Warning: --with-claude-skills was requested but $HOME/.claude does not exist; skipping." >&2
  fi
fi

if [ "$WITH_GIT_IDENTITY" = "1" ]; then
  if [ -f "$HOME/.gitconfig" ]; then
    MOUNTS+=(-v "$HOME/.gitconfig:/root/.gitconfig:ro")
  else
    echo "Warning: --with-git-identity was requested but $HOME/.gitconfig does not exist; skipping." >&2
  fi
fi

echo "Starting OpenCode container (image: $IMAGE, workspace: $PROJECT_DIR, name: $CONTAINER_NAME)..." >&2

if ! docker run -d \
  --name "$CONTAINER_NAME" \
  --label opencode-docker-dev=1 \
  "${MOUNTS[@]}" \
  -w /workspace \
  "$IMAGE" \
  sleep infinity >/dev/null; then
  echo "Error: 'docker run' failed to start container '$CONTAINER_NAME'. See the docker error above." >&2
  exit 1
fi
if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null || true)" != "true" ]; then
  echo "Error: container '$CONTAINER_NAME' was created but is not running. Inspect with: docker logs '$CONTAINER_NAME'" >&2
  exit 1
fi

print_attach_block

if [ "$START_ONLY" = "1" ]; then
  echo "Container started. Run OpenCode next with: --exec-in $CONTAINER_NAME --project '$PROJECT_DIR' --message \"...\"" >&2
  exit 0
fi

run_opencode_in_container
