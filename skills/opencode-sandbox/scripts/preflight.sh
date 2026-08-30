#!/usr/bin/env bash
# preflight.sh — ensure Docker is running and the docker-dev image is present.
#
# Usage: preflight.sh [image]
#   image   defaults to ghcr.io/luongnv89/u2604dev:latest
set -euo pipefail

IMAGE="${1:-ghcr.io/luongnv89/u2604dev:latest}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: 'docker' is not on PATH. Install Docker Desktop (https://www.docker.com/products/docker-desktop/) or Docker Engine, then retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Attempting to start it..." >&2
  case "$(uname -s)" in
    Darwin)
      open -a Docker
      ;;
    *)
      echo "Error: Docker daemon is not reachable and this script only knows how to auto-start it on macOS ('open -a Docker'). Start Docker manually (e.g. 'systemctl start docker' on Linux) and retry." >&2
      exit 1
      ;;
  esac
  ready=0
  for _ in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 2
  done
  if [ "$ready" -ne 1 ]; then
    echo "Error: Docker daemon still not reachable after 60s of waiting. Open Docker Desktop manually, confirm 'docker info' succeeds, then retry." >&2
    exit 1
  fi
fi

echo "Docker daemon: ready" >&2

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Pulling $IMAGE (first run only; cached on this machine afterward)..." >&2
  if ! docker pull "$IMAGE"; then
    echo "Error: 'docker pull $IMAGE' failed. Check network access, and that the image name/tag is correct (see https://github.com/luongnv89/docker-dev for the current list of published images)." >&2
    exit 1
  fi
fi

echo "Image ready: $IMAGE" >&2
