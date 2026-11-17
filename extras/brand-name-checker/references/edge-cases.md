# Edge Cases

Handling rules for unusual inputs and source failures. `SKILL.md` → *Edge Cases* links here; the risk policy in `SKILL.md` → *Step 5: Risk Assessment* always wins over anything below.

- **Exact social handle taken on any of the 6 platforms**: apply the Early-Exit Rule. Skip all remaining checks, report them as `Skipped (not cleared)`, and return an Abandon recommendation with alternative name suggestions labeled unverified.
- **Rate-limited registry API** (HTTP 429 or a rate-limit message): retry once after 5 seconds. If it is still blocked, mark the registry as "unchecked"/unknown and note it in the report — do not skip silently. Apply the unknown policy; do not infer availability.
- **Trademark database unavailable**: note the outage per database and mark the affected check unknown. Do not lower a known High finding. Without a known High finding, use provisional Moderate + Modify pending verification.
- **Name contains special characters or spaces**: normalize to slug form (for example `my tool` → `my-tool`) before all checks, and report both the original and the normalized forms.
- **Very short names (1-3 characters)**: flag the elevated trademark collision risk upfront. Abbreviations are almost always claimed across social and trademark databases.
- **Name already in use by a well-known brand (typosquat risk)**: escalate to High even if every technical check passes.
- **No web tools available**: return the `BLOCKED` report from `SKILL.md` → *Output Format*. Never fill statuses from memory.
