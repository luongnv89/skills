# Verification Steps

Run these checks in Phase 5 step 2 (and again after a regeneration), from `PROJECT_DIR`. Each check gives an observed count for the Final Report `Evidence:` line. A check passes only when its stated condition holds; a heading's presence alone does not pass.

1. **11 numbered sections.** Pass when the count is 11 or more.

   ```bash
   grep -cE '^## ([1-9]|1[01])\. ' tad.md
   ```

2. **Mermaid diagram.** Pass when the count is 1 or more, and the line after each fence starts with `graph`, `flowchart`, `sequenceDiagram` or `erDiagram`.

   ```bash
   grep -c '^```mermaid' tad.md
   grep -A1 '^```mermaid' tad.md
   ```

3. **No bare "latest" in the stack.** Pass when the count is 0, or each match carries a date.

   ```bash
   awk '/^## 3\. /,/^## 4\. /' tad.md | grep -ci 'latest'
   ```

4. **One mitigation per risk.** Pass when the count equals the number of risk rows in §10.

   ```bash
   awk '/^## 10\. /,/^## 11\. /' tad.md | grep -c 'Mitigation:'
   ```

5. **Costs with currency and cadence.** Pass when the count is 1 or more. Every cost row in §6 and §11.3 shows a currency and a cadence, or `TBD`.

   ```bash
   grep -cE '[$€£][0-9][0-9,.]*[kK]?( per month|/mo|/month| per year|/yr)|TBD' tad.md
   ```

6. **Security standard named.** Pass when the count is 1 or more.

   ```bash
   awk '/^## 7\. /,/^## 8\. /' tad.md | grep -ciE 'OWASP|OAuth|OIDC|JWT|SAML|WebAuthn'
   ```

7. **Backup (`modify` mode only).** Pass when the command exits 0.

   ```bash
   test -s tad.md.bak.<timestamp>
   ```

Check 7 does not apply in `create` mode. Report it as `n/a` and count only the checks that apply (6/6 in `create` mode, 7/7 in `modify` mode).

For check 2, read each Mermaid block and confirm balanced brackets and braces. If `mmdc` is installed, also run `mmdc -i tad.md -o /tmp/tad-check.svg`. If a block still fails after one regeneration, replace it with a bulleted text flow and note it on the `Uncertainty:` line.

These checks verify structure and the named patterns only. They do not prove that the architecture fits the product; that remains for the user's review.
