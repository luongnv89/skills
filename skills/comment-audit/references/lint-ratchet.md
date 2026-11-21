# Banning new comments with a ratchet

Gate D adds a check that fails when a file in scope gains a comment line, and that lets existing comments stay until someone deletes them. The **baseline** records how many comment lines each file has after Step 6. A file may only go down from its baseline, and a new file starts at zero. The check counts lines, not comment units, so growing an existing comment block also fails.

Machine-read comments (`references/comment-syntax.md`) are never counted, so directives and license headers stay legal.

## Pick the mechanism

| Stack | Mechanism |
|---|---|
| JavaScript or TypeScript with ESLint 9.24 or later and a flat config | A local `no-comments` rule plus ESLint's bulk suppressions (*ESLint route*) |
| Python | The check script below, run from the project's lint command |
| Anything else, or ESLint older than 9.24 | The same script shape in the repo's main language, counting with the tokenizer from `references/comment-syntax.md` |

No standard linter bans all comments. Ruff's `ERA001` and similar rules catch only commented-out code, and `godox` or `no-warning-comments` catch only marker words. None of them is a comment ban. Never add a third-party plugin the project does not already use without listing it in the Gate D plan as a new dependency.

In a repo with several languages, cover each language in scope: the ESLint route for JS and TS plus the script for the rest, or one script that dispatches on the file extension. List each language left uncovered.

## ESLint route

Check the version first: `npx --no-install eslint --version`. Add a config object for the scope to the existing `eslint.config.*`:

```js
const MACHINE_READ = /^\s*(eslint|global\s|globals\s|exported\s|@ts-|prettier-ignore|istanbul\s|c8\s|v8\s|webpack|@vite-ignore|@jsx|\/\s*<reference\s)/;

const noComments = {
  meta: { type: "suggestion", schema: [], messages: { banned: "New code comments are banned here: record decisions in an ADR and work in an issue." } },
  create(context) {
    return {
      Program() {
        for (const comment of context.sourceCode.getAllComments()) {
          if (comment.type === "Shebang" || MACHINE_READ.test(comment.value)) continue;
          for (let line = comment.loc.start.line; line <= comment.loc.end.line; line += 1) {
            context.report({ loc: { start: { line, column: 0 }, end: { line, column: 0 } }, messageId: "banned" });
          }
        }
      },
    };
  },
};

export default [
  // ...the existing config objects
  {
    files: ["<scope glob>"],
    plugins: { local: { rules: { "no-comments": noComments } } },
    rules: { "local/no-comments": "error" },
  },
];
```

Extend `MACHINE_READ` with any other machine-read form the inventory found (license headers, JSDoc type blocks in checked JS). The config file is code under the ban too, so it carries no comments of its own. Remove the placeholder line above when you edit the real file.

Then write the baseline: `npx eslint --suppress-rule local/no-comments <scope>`. That creates `eslint-suppressions.json`, which counts violations per file and rule. It must be committed. From then on:

- a file with more comment lines than its suppressed count fails `eslint`;
- a file with fewer also fails, with "There are suppressions left that do not occur anymore", until someone runs `npx eslint --prune-suppressions` and commits the lower count. That is the ratchet tightening.

If the project passes `--suppressions-location`, use the same path in every command.

## Check script (Python)

Put it where the repo keeps tooling scripts (`scripts/check_comments.py`), set `SCOPE` to the audit scope, and run it from the repo root. It counts every comment line that is not machine-read, plus every docstring line except docstrings holding doctests. It has three modes:

| Command | Does |
|---|---|
| `python3 scripts/check_comments.py --init` | Writes `comment-baseline.json` from the tree. Refuses if the file already exists |
| `python3 scripts/check_comments.py` | Fails when a file has more comment lines than its baseline, naming the lines. Also fails when a count went down, until the baseline is updated |
| `python3 scripts/check_comments.py --update` | Lowers the baseline to the current counts and drops deleted files. Refuses to raise any count |

```python
import ast
import io
import json
import subprocess
import sys
import tokenize
from pathlib import Path

BASELINE = Path("comment-baseline.json")
SCOPE = ["."]
DIRECTIVES = ("noqa", "type:", "pragma:", "pylint:", "fmt:", "isort:", "mypy:", "pyright:", "ruff:")
HEADER_WORDS = ("copyright", "license", "spdx-license-identifier")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "--", *SCOPE], capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if p.endswith(".py"))


def header_rows(lines):
    rows = []
    for number, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("#"):
            break
        rows.append(number)
    top = " ".join(lines[r - 1].lower() for r in rows)
    return set(rows) if any(word in top for word in HEADER_WORDS) else set()


def machine_read(text, row, header):
    body = text.lstrip("#").strip().lower()
    if row == 1 and text.startswith("#!"):
        return True
    if row <= 2 and "coding" in body and "-*-" in body:
        return True
    return row in header or body.startswith(DIRECTIVES)


def comment_rows(path):
    source = Path(path).read_text(encoding="utf-8")
    lines = source.splitlines()
    header = header_rows(lines)
    rows = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and not machine_read(token.string, token.start[0], header):
            rows.append(token.start[0])
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None and ">>>" not in doc:
                first = node.body[0]
                rows.extend(range(first.lineno, first.end_lineno + 1))
    return sorted(rows)


def current_counts():
    return {path: len(comment_rows(path)) for path in tracked_files()}


def main(argv):
    counts = current_counts()
    if argv[1:] == ["--init"]:
        if BASELINE.exists():
            sys.exit(f"{BASELINE} exists; use --update to lower it")
        BASELINE.write_text(json.dumps({p: n for p, n in counts.items() if n}, indent=2, sort_keys=True) + "\n")
        print(f"baseline written: {sum(counts.values())} comment lines in {sum(1 for n in counts.values() if n)} files")
        return 0
    baseline = json.loads(BASELINE.read_text())
    if argv[1:] == ["--update"]:
        raised = [p for p, n in counts.items() if n > baseline.get(p, 0)]
        if raised:
            sys.exit("refusing to raise the baseline for: " + ", ".join(raised))
        BASELINE.write_text(json.dumps({p: n for p, n in counts.items() if n}, indent=2, sort_keys=True) + "\n")
        print(f"baseline lowered to {sum(counts.values())} comment lines")
        return 0
    failed = False
    for path, n in counts.items():
        allowed = baseline.get(path, 0)
        if n > allowed:
            rows = ", ".join(str(r) for r in comment_rows(path))
            print(f"{path}: {n} comment lines, baseline {allowed} (lines {rows}); new comments are banned")
            failed = True
    stale = [p for p, n in baseline.items() if counts.get(p, 0) < n]
    if stale:
        print("baseline can go down for: " + ", ".join(stale) + "; run with --update and commit the baseline")
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

The script carries no comments, because it is under the ban too. Known gaps, which go in the Gate D plan:

- Prose added to a docstring that holds doctests is not counted.
- A real comment that starts with a directive word (`# noqa this looks odd`) is not counted.

The check guards against habit, not against someone working around it, and code review catches the rest.

For another language, keep the same three modes, the same JSON format and the same line counting, and count with that language's tokenizer: `go/parser` with `parser.ParseComments` for Go, or the TypeScript compiler API without ESLint.

## Wiring

Run the check where lint already runs, in this order of preference:

1. the existing lint command (`package.json` `lint` script, Makefile `lint` target, `tox -e lint`);
2. an existing pre-commit configuration (a `local` hook);
3. an existing CI job, as one more step.

Add a new CI workflow only if none of these exist, and list it in the plan. Name the exact file and line that change.

## Proving it

After writing the mechanism and the baseline, run each probe and revert it:

1. The check passes on the tree.
2. Add one comment line inside a file in scope, including directly under an existing comment. The check fails and names the file.
3. Delete one counted comment. The check asks for a baseline update. After `--update` (or `--prune-suppressions`), the file's count is lower and the check passes.
4. Add a directive the inventory recorded (`# noqa: E501`, `// eslint-disable-next-line`). The check still passes.

Record each probe's command and exit status for the report.
