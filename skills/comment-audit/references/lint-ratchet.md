# Banning new comments with a ratchet

Gate D adds a check that fails when a file in scope gains a comment line, and that lets existing comments stay until someone deletes them. The **baseline** records how many comment lines each file has after Step 6. A file may only go down from its baseline, and a new file starts at zero. The check counts lines, not comment units, so growing an existing comment block also fails.

Machine-read comments (`references/comment-syntax.md`) are never counted, so directives and license headers stay legal.

## Pick the mechanism

| Stack | Mechanism |
|---|---|
| JavaScript or TypeScript with ESLint 9.24 or later and a flat config | A local `no-comments` rule plus ESLint's bulk suppressions (*ESLint route*) |
| Python | The check script below, run from the project's lint command |
| Anything else, or ESLint older than 9.24 | The same script, extended with a counter for the language (*Other languages*). Python 3 runs it; the plan lists Python 3 as a requirement when the project does not already use it |

No standard linter bans all comments. Ruff's `ERA001` and similar rules catch only commented-out code, and `godox` or `no-warning-comments` catch only marker words. None of them is a comment ban. Never add a third-party plugin the project does not already use without listing it in the Gate D plan as a new dependency.

In a repo with several languages, cover each language in scope: the ESLint route for JS and TS plus the script for the rest, or one script that dispatches on the file extension. List each language left uncovered.

## ESLint route

Check the version first: `npx --no-install eslint --version`. Add a config object for the scope to the existing `eslint.config.*`:

```js
const MACHINE_READ = /^\s*(eslint|global\s|globals\s|exported\s|@ts-|@flow|prettier-ignore|istanbul\s|c8\s|v8\s|webpack|@vite-ignore|@jsx|@jest-environment|@vitest-environment|[#@]__PURE__|#__NO_SIDE_EFFECTS__|falls?\s?through|\/\s*<reference\s)/i;

const noComments = {
  meta: { type: "suggestion", schema: [], messages: { banned: "New code comments are banned here: record decisions in an ADR and work in an issue." } },
  create(context) {
    return {
      Program() {
        for (const comment of context.sourceCode.getAllComments()) {
          if (comment.type === "Shebang" || MACHINE_READ.test(comment.value)) continue;
          const holder = context.sourceCode.getNodeByRangeIndex(comment.range[0]);
          if (holder && holder.type === "BlockStatement" && holder.body.length === 0) continue;
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

Extend `MACHINE_READ` with any other machine-read form the inventory found (license headers, JSDoc type blocks in checked JS). The rule also skips a comment that is the only content of an empty block, which `no-empty` relies on. The config file is code under the ban too, so it carries no comments of its own; remove the placeholder line above when you edit the real file. The snippet is an ES module config (`eslint.config.js` with `"type": "module"`, or `.mjs`); for a CommonJS config, assign the array to `module.exports` instead.

Then write the baseline: `npx eslint --suppress-rule local/no-comments <scope>`. That creates `eslint-suppressions.json`, which counts violations per file and rule. It must be committed. From then on:

- a file with more comment lines than its suppressed count fails `eslint`;
- a file with fewer also fails, with "There are suppressions left that do not occur anymore", until someone runs `npx eslint --prune-suppressions` and commits the lower count. That is the ratchet tightening.

If the project passes `--suppressions-location`, use the same path in every command.

## Check script (Python)

Put it where the repo keeps tooling scripts (`scripts/check_comments.py`), set `SCOPE` to the audit scope, and run it from the repo root. It reads tracked and untracked (not ignored) files in scope. It counts every comment line that is not machine-read, every docstring line except docstrings holding doctests or read by a Click or Typer command, and every line of a bare string used as a comment. It has three modes:

| Command | Does |
|---|---|
| `python3 scripts/check_comments.py --init` | Writes `comment-baseline.json` from the tree. Refuses if the file already exists |
| `python3 scripts/check_comments.py` | Fails when a file has more comment lines than its baseline, naming the lines. Also fails when a count went down, until the baseline is updated |
| `python3 scripts/check_comments.py --update` | Lowers the baseline to the current counts and drops deleted files. Refuses to raise any count, except that a renamed file may carry the count of the path it replaced |

```python
import ast
import io
import re
import json
import subprocess
import sys
import tokenize
from pathlib import Path

BASELINE = Path("comment-baseline.json")
SCOPE = ["."]
DIRECTIVES = ("noqa", "type:", "pragma:", "pylint:", "fmt:", "isort:", "mypy:", "pyright:", "ruff:", "nosec")
HEADER_LINE = re.compile(r"#\s*(copyright\b|\(c\)|©|spdx-license-identifier:|licensed under\b|license:)", re.IGNORECASE)
READ_DECORATORS = ("command", "group")


def scoped_files():
    tracked = ["git", "ls-files", "-z", "--", *SCOPE]
    untracked = ["git", "ls-files", "-z", "--others", "--exclude-standard", "--", *SCOPE]
    paths = set()
    for cmd in (tracked, untracked):
        out = subprocess.run(cmd, capture_output=True, check=True).stdout.decode("utf-8")
        paths.update(p for p in out.split("\0") if p.endswith(".py") and Path(p).is_file())
    return sorted(paths)


def header_rows(lines):
    top = []
    for number, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("#"):
            break
        top.append(number)
    last = max((r for r in top if HEADER_LINE.match(lines[r - 1].lstrip())), default=0)
    return set(r for r in top if r <= last)


def machine_read(text, row, header):
    body = text.lstrip("#").strip()
    if row == 1 and text.startswith("#!"):
        return True
    if row <= 2 and "coding" in body and "-*-" in body:
        return True
    return row in header or body.startswith(DIRECTIVES)


def read_by_framework(node):
    for deco in getattr(node, "decorator_list", []):
        target = deco.func if isinstance(deco, ast.Call) else deco
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", "")
        if name in READ_DECORATORS:
            return True
    return False


def comment_rows(path):
    source = Path(path).read_text(encoding="utf-8")
    lines = source.splitlines()
    header = header_rows(lines)
    rows = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and not machine_read(token.string, token.start[0], header):
            rows.append(token.start[0])
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                first = node.body[0]
                docstrings.add(id(first))
                if ">>>" not in doc and not read_by_framework(node):
                    rows.extend(range(first.lineno, first.end_lineno + 1))
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            if id(node) not in docstrings:
                rows.extend(range(node.lineno, node.end_lineno + 1))
    return sorted(set(rows))


def counts_or_errors():
    counts, errors = {}, []
    for path in scoped_files():
        try:
            counts[path] = len(comment_rows(path))
        except (SyntaxError, UnicodeDecodeError, tokenize.TokenError) as exc:
            errors.append(f"{path}: cannot be read ({exc.__class__.__name__}: {exc})")
    return counts, errors


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def write(counts):
    BASELINE.write_text(json.dumps({p: n for p, n in counts.items() if n}, indent=2, sort_keys=True) + "\n")


def main(argv):
    counts, errors = counts_or_errors()
    if errors:
        print("\n".join(errors))
        return 1
    if argv[1:] == ["--init"]:
        if BASELINE.exists():
            sys.exit(f"{BASELINE} exists; use --update to lower it")
        write(counts)
        files = sum(1 for n in counts.values() if n)
        print(f"baseline written: {plural(sum(counts.values()), 'comment line')} in {plural(files, 'file')}")
        return 0
    baseline = json.loads(BASELINE.read_text())
    if argv[1:] == ["--update"]:
        moved = sum(n for p, n in baseline.items() if p not in counts)
        raised = {p: n - baseline.get(p, 0) for p, n in counts.items() if n > baseline.get(p, 0)}
        if sum(raised.values()) > moved:
            sys.exit("refusing to raise the baseline for: " + ", ".join(sorted(raised)))
        write(counts)
        print(f"baseline lowered to {plural(sum(counts.values()), 'comment line')}")
        return 0
    failed = False
    moved = sum(n for p, n in baseline.items() if p not in counts)
    for path, n in counts.items():
        allowed = baseline.get(path, 0)
        if n > allowed and not (path not in baseline and n <= moved):
            rows = ", ".join(str(r) for r in comment_rows(path))
            print(f"{path}: {plural(n, 'comment line')}, baseline {allowed} (lines {rows}); new comments are banned")
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

- Deleting one comment and adding another in the same file keeps the count, so it passes. So does adding comments to a new file while deleting a file that had as many.
- Prose added to a docstring that holds doctests or is read by a Click or Typer command is not counted.
- A real comment that starts with a directive word (`# noqa this looks odd`) or a header word at the top of a file (`# Copyright-free note`) is not counted.
- A file that does not parse fails the check with its name, without counting.

The check guards against habit, not against someone working around it, and code review catches the rest.

### Other languages

Keep the same three modes, the same JSON format and line counting, and add a counter for each language in scope, following `references/comment-syntax.md`: a scanner for shell, Swift or Rust, `go/parser` called through a small Go program for Go. Skip each machine-read form the inventory recorded for that language. Test the counter on the inventory's own files before writing the baseline: its total must equal the comment lines Step 1 found after Step 6, minus the machine-read ones.

## Wiring

Run the check where lint already runs, in this order of preference:

1. the existing lint command (`package.json` `lint` script, Makefile `lint` target, `tox -e lint`);
2. an existing pre-commit configuration (a `local` hook);
3. an existing CI job, as one more step.

When the repo has none of these, the Gate D plan offers three options and the user picks one: a new command in the project's own task file (an npm script, a Makefile target, a `justfile` recipe) that developers run by hand; a new pre-commit configuration; or a new CI workflow, which runs only once the repo has a remote CI service. Name the exact file and line that change.

## Proving it

Run the probes after the ratchet commit, so every probe can be undone with `git checkout -- <file>` (and `git clean` of a probe file this run created). Run each probe and revert it:

1. The check passes on the tree.
2. Add one comment line inside a file in scope, including directly under an existing comment. The check fails and names the file.
3. Delete one counted comment. The check asks for a baseline update. After `--update` (or `--prune-suppressions`), the file's count is lower and the check passes. Revert both the file and the baseline.
4. Add a directive the inventory recorded, on a line it actually applies to (`# noqa: E501` on a long line, `// eslint-disable-next-line` above a real violation). The check still passes. A directive that disables nothing raises ESLint's unused-directive warning, which fails under `--max-warnings 0`.

Record each probe's command and exit status for the report.
