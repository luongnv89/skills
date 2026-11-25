# Detail Sections

Everything after the landing section. Use this order, and skip a section that has no source content. Prefer tables, lists, code blocks, and diagrams to paragraphs. No paragraph runs past 3 sentences.

| # | Section | Contents | Sources |
|---|---|---|---|
| 1 | `## Features` or `## Why <name>` | 3 to 6 rows or bullets, each 15 words or fewer, outcome first | README, docs, the entry points in code |
| 2 | `## How it works` | One mermaid diagram and at most 3 sentences, only when the project has 3 or more components or a multi-stage flow | Code structure, docs |
| 3 | `## Usage` | One `###` per further task: a sentence, the command, its output. Then the options or API table | Argument definitions, docs, examples, tests |
| 4 | `## Configuration` | Config files, environment variables, defaults | Config readers in source, `.env.example`, docs |
| 5 | `## Installation options` | Other install methods, requirements, upgrade, uninstall | The sources of the install command |
| 6 | `## Comparison` | A table against named alternatives, with real data only | README, docs, benchmarks in the repo |
| 7 | `## FAQ` | 3 to 5 questions that the README or docs raise, or that issue or support questions the user supplies raise, each answered in 1 or 2 sentences. Skip the section when neither source gives a question | README, docs, issue or support questions the user supplies |
| 8 | `## Contributing` or `## Development` | Dev setup and test commands, and a link to `CONTRIBUTING.md` when it exists | Manifest scripts, `CONTRIBUTING.md` |
| 9 | `## License` | The license name, linked to `LICENSE` | `LICENSE` |
| 10 | Preserved content | Original material that fits no section above, each part in its own `<details>` block | The backup |

## Section rules

- **Features:** lead with the outcome, not the mechanism. "Shows only warnings and errors" beats "Level filter".
- **How it works:** pick the diagram type by shape. Pipeline: `graph LR`. Client and server: `graph TD`. States: `stateDiagram-v2`. Request flow: `sequenceDiagram`. Several small diagrams beat one large one.
- **Usage:** take every flag in the options table from the argument definitions. Add a flag that the source defines and the old README omits, and cite it in `Evidence:`.
- **Comparison and FAQ:** skip the section rather than invent a row or a question.
- **Badges** (landing line): use only badges whose target exists: a CI workflow file, `LICENSE`, or the registry the install command uses.
- **Rewrite:** merge each original section into its matching row. When two original sections overlap, keep every fact once.

## Preserved content block

```markdown
<details>
<summary>API reference</summary>

[original content, unchanged]

</details>
```
