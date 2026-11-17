# Leading terms — /website-agent-readiness

Glossary for the scan → triage → plan → issues pipeline. Kept out of `SKILL.md` so it costs no context window until a term is actually in question.

## Terms

- **check** — one of the scanner's 22 tests, keyed camelCase (`linkHeaders`, `dnsAid`)
  inside one of five **categories**. Status is `pass`, `fail`, or `neutral`.
- **failing check** — status `fail`. One failing check becomes exactly one plan task.
  `neutral` is informational and is never filed.
- **fix prompt** — the scanner's own remediation prose for a failing check. The task
  description is this text, never something this skill composes.
- **guide URL** — the scanner's hosted implementation guide for a check
  (`/.well-known/agent-skills/<slug>/SKILL.md`). **Cited in the task, never fetched
  or applied** — fetching and implementing them is out of scope.
- **scan-faithful** — every word of the plan traces to the scan response. Never open the
  target site's source, never guess at its stack, never add a task the scan did not fail.
- **approval gate** — a full stop. The run ends its turn and waits for the user.

