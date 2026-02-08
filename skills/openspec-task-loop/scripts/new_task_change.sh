#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <change-id> <capability> [task-id]"
  echo "Example: $0 task-2-3-pin-crud dashboard 2.3"
  exit 1
fi

CHANGE_ID="$1"
CAPABILITY="$2"
TASK_ID="${3:-unknown}"
ROOT="openspec/changes/${CHANGE_ID}"
SPEC_DIR="${ROOT}/specs/${CAPABILITY}"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

mkdir -p "${SPEC_DIR}"

cat > "${ROOT}/.openspec.yaml" <<YAML
schema: spec-driven
createdAt: ${NOW}
changeId: ${CHANGE_ID}
sourceTask: ${TASK_ID}
YAML

cat > "${ROOT}/proposal.md" <<MD
# Proposal: ${CHANGE_ID}

## Why
TODO

## Scope
- In scope:
  - TODO
- Out of scope:
  - TODO

## Acceptance Criteria
- [ ] TODO
- [ ] TODO

## Risks
- TODO
MD

cat > "${ROOT}/design.md" <<MD
# Design: ${CHANGE_ID}

## Approach
TODO

## Files Affected
- TODO

## Decisions
- Decision: TODO
- Rationale: TODO
- Tradeoff: TODO

## Validation Plan
- TODO
MD

cat > "${ROOT}/tasks.md" <<MD
# Tasks: ${CHANGE_ID}

- [ ] 1. TODO
- [ ] 2. TODO
- [ ] 3. Run validation checks
- [ ] 4. Update docs/spec delta if needed
MD

cat > "${SPEC_DIR}/spec.md" <<MD
# ${CAPABILITY} Specification Delta

### Requirement: TODO
- The system SHALL TODO.

#### Scenario: Happy path
- GIVEN TODO
- WHEN TODO
- THEN TODO

#### Scenario: Edge case
- GIVEN TODO
- WHEN TODO
- THEN TODO
MD

echo "Created OpenSpec task change scaffold: ${ROOT}"
