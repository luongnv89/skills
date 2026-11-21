# Finding comments

How Step 1 finds every comment, which languages are in scope, how comments group into units, and which comments are machine-read and never touched.

## Method per language

Prefer a tokenizer or parser, because it never mistakes `#` or `//` inside a string, a URL or a regex literal for a comment. Write any helper script in the audit folder, never in the repository. A scanner is an approximation: record it in the audit and validate it twice. First, run it on tricky lines from the codebase itself (a marker inside a string, a nested comment, a here-document). Then cross-check the whole scope: list every line holding the comment marker that the scanner did not count as a comment, and confirm each sits inside a string, a here-document or an embedded program. Fix the scanner until none is left unexplained.

| Language | Comment forms | Method |
|---|---|---|
| Python | `#` line; docstrings (the first string statement of a module, class or function) | `python3 -m tokenize -e <file>` lists `COMMENT` tokens. For docstrings, use `ast.get_docstring` and the node's line range |
| JavaScript, TypeScript (`.js .jsx .mjs .cjs .ts .tsx .mts .cts`) | `//`, `/* */`, `/** */` | The TypeScript compiler API (`ts.forEachLeadingCommentRange`, `ts.forEachTrailingCommentRange`) or ESLint's `sourceCode.getAllComments()` when the project has them installed. Otherwise a scanner that skips string, template and regex literals |
| Go | `//`, `/* */` | `go/parser` with `parser.ParseComments`, which gives `file.Comments` |
| Rust | `//`, `/* */` (they nest), `///`, `//!` | A scanner that skips string, raw string (`r#"…"#`) and char literals, and counts nesting depth in block comments |
| Swift | `//`, `/* */` (they nest), `///` | SwiftSyntax when the toolchain is present. Otherwise a scanner that nests block comments, skips `"…"`, multi-line `"""…"""` and raw strings (`#"…"#`, any number of `#`), treats `\( … )` and `\#( … )` inside strings as code, and skips regex literals (`#/…/#`, `/…/`) |
| Java, Kotlin, C, C++, C#, Scala, Dart | `//`, `/* */`, `/** */` | A scanner that skips string and char literals, text blocks, raw strings and verbatim strings. Kotlin and Scala block comments nest |
| PHP | `//`, `#`, `/* */` | A scanner that skips strings and here/nowdocs. `#[` starts an attribute, not a comment |
| Ruby | `#`, `=begin … =end` | `Ripper.lex` (`:on_comment` tokens) through `ruby -e`, else a scanner |
| Shell (`.sh .bash .zsh`, Bats test files `.bats`, and files whose shebang names a shell or `bats`) | `#` | A scanner that skips quoted strings and here-documents. `#` starts a comment only at the start of a word: after a space, a tab, a line start, or `;` `\|` `&` `(` `)`. So `$#`, `${#var}`, `${var#x}`, `${var##*/}`, `$((16#ff))` and `a#b` are code |
| SQL | `--`, `/* */` | A scanner that skips quoted strings |
| CSS, SCSS, Less | `/* */` (SCSS and Less also `//`) | A scanner that skips strings and `url(...)` |

HTML, Vue and Svelte templates are in scope only when the user names them (`<!-- -->`, plus each script and style block by its language). A file in another language is left out and listed under `Uncertainty:`.

## Comment units

- A run of line comments on consecutive lines, with nothing else on those lines, is one unit. A blank line, a code line or a machine-read comment ends the run, so a shebang followed by a license line gives two machine-read entries, not one.
- A block comment, doc comment or docstring is one unit, however many lines it spans.
- A comment after code on the same line, or between code on the same line, is an inline unit. It has no own lines.
- Text marked as a comment inside an embedded program (a here-document, a quoted `bash -c '…'`, `awk '…'` or `python3 -c '…'` program) is part of that string, not a comment of the file. Leave it out, and report how many such lines were left out under `Uncertainty:`.
- **Own lines** are the lines that hold only comment text and whitespace. A docstring's own lines are all the lines of its string statement.

## Machine-read comments

These get `M` IDs. They are counted, listed with the reason, and never edited, deleted or banned.

- **Directives** that tools read, for example:
  - Python: `# noqa`, `# type: ignore`, `# pragma: no cover`, `# pylint:`, `# fmt: off/on`, `# isort:`, `# mypy:`, `# pyright:`, `# nosec`.
  - JS/TS: `eslint-disable…`, `eslint-enable`, `eslint-env`, `/* eslint <rule>: … */` config comments, `global`, `@ts-ignore`, `@ts-expect-error`, `@ts-nocheck`, `@ts-check`, `@flow`, `prettier-ignore`, `istanbul ignore`, `c8 ignore`, `v8 ignore`, `/// <reference …/>`, `@jsx`, `@jsxImportSource`, `@jest-environment`, `@vitest-environment`, `/*#__PURE__*/`, `/*@__PURE__*/`, `#__NO_SIDE_EFFECTS__`, `webpackChunkName` and other bundler magic comments, `@vite-ignore`. In doc comments: `@deprecated` (TypeScript and `@typescript-eslint/no-deprecated` read it) and `@internal` (TypeScript's `stripInternal` drops those symbols from published typings). Keep the whole doc comment that carries them. Javadoc `@deprecated` likewise.
  - Fall-through and empty-block markers: `// falls through`, `// fallthrough` and similar in a `switch` (ESLint `no-fallthrough` reads them), and a comment that is the only content of a block a linter would otherwise flag as empty (`no-empty`, an empty `catch`).
  - Go: `//go:build`, `// +build`, `//go:generate`, `//go:embed`, `//go:linkname`, `//export`, the cgo preamble (the comment directly before `import "C"`), `//nolint`, `//lint:ignore`, `// Deprecated:` paragraphs.
  - Swift: `// swift-tools-version:` (the first line of `Package.swift`; SwiftPM reads it), `// swiftlint:`, `// swift-format-ignore`.
  - Others: `# frozen_string_literal:`, `# rubocop:`, `// NOLINT`, `// clang-format off`, `# shellcheck disable=…` and `# shellcheck shell=…`, Bats `# bats test_tags=…` and `# bats file_tags=…`, `<!-- prettier-ignore -->`, Rust tool comments such as `// rustfmt::skip`.
- **File headers:** a shebang, an encoding line (`# -*- coding: … -*-`), `SPDX-License-Identifier`, and a license or copyright block at the top of the file.
- **Generated-code markers:** `Code generated … DO NOT EDIT.`, `@generated`, `<auto-generated>`. A file carrying one is generated, so leave the whole file out of scope.
- **Types in comments:** Python type comments (`# type: int`). In a JavaScript file checked by TypeScript (`checkJs`, `// @ts-check`), JSDoc blocks that carry type tags (`@type`, `@param {…}`, `@returns {…}`, `@typedef`, `@template`).
- **Doc text something reads:**
  - Python docstrings holding doctests (`>>>`), docstrings read through `__doc__` or `inspect.getdoc`, and docstrings frameworks turn into help or schema text: Click, Typer and Fire commands, `argparse` descriptions built from `__doc__`, FastAPI and Django REST route docs.
  - Go example functions' `// Output:` and `// Unordered output:` blocks, which are test assertions.
  - Rust doc comments that hold code blocks, which run as doc tests, unless the block is marked `ignore` or `text`.
  - A shell script's usage text that the script prints by reading its own comments (`sed -n '2,10p' "$0"`, `grep '^#/' "$0"`).
  - Comments that tests or scripts read from source files (*Comments that code reads* below).

If deleting a comment makes a baseline check fail or lowers the number of tests passed (Step 6), it was machine-read after all. Restore it and move it here.

## Comments that code reads

Tests and scripts often check source files with `grep`, `sed`, `awk`, `rg` or a file read plus a regex: a banner a test looks for, a schema block a test parses, a word every probe line must carry. Those comments are machine-read, and running the tests is not enough to find them, because the tests may not run on this machine. Find them statically in Step 1:

1. Collect the source-reading commands in the tests, scripts and CI config: each `grep`, `rg`, `sed`, `awk` or file read whose input is a path in the scope.
2. Make two copies in the audit folder: the base (`git archive HEAD | tar -x`) and the same tree with every `C` entry deleted.
3. Never run a command taken from the repo. From each reader take only two pieces of data: its search pattern and the files it reads. Then run your own fixed command, as an argument list with no shell: `grep -n -E -e <pattern> -- <files>` (`-F` for a fixed string), over the regular files that `git ls-files` lists in each copy. Never follow a symlink and never pass a path outside the copy. A reader whose pattern is not a plain regex or string (a `sed` or `awk` program, a pattern built at run time, a file read inside test code) is judged by reading it: decide from its logic which comments it needs. Never run a test here; tests run only as Gate 0 checks.
4. A pattern whose matches differ between the copies read a comment. Mark each comment it read as machine-read. When it reads only some lines of a unit, the whole unit is machine-read, so the text the reader needs stays together.

A repo-specific reader ("every probe line must contain the word timeout") also goes into the ratchet's known gaps, since the ratchet must allow that comment by a pattern.

## Linters that require doc comments

Look in the lint config for rules that fail when a declaration has no doc comment: ruff or pydocstyle `D1xx`, pylint `missing-*-docstring` (C0114–C0116), Rust `#![deny(missing_docs)]` or `-D missing_docs`, revive `exported`, `jsdoc/require-jsdoc`, SwiftLint `missing_docs`, Checkstyle `JavadocMethod`. When one is on, deleting those doc comments breaks lint. Gate C leaves them out and asks the user one question in its plan: keep them, or also change the lint config (a separate item the user must approve).

## Files left out by default

Generated files, vendored folders (`vendor/`, `third_party/`, `node_modules/`), build output (`dist/`, `build/`, `out/`), minified files (`*.min.*`), lockfiles, notebooks (`.ipynb`), Markdown and other docs, images and SVG, and config files (YAML, TOML, INI, JSON5). Include config files or templates only when the user names them. Report each group and its file count.
