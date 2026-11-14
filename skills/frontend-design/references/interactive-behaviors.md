# Interactive Behaviors (UI SDK, beta)

Read this in step 4 when the interface has an **interactive part**: anything that opens (menu, popover, dialog, select, combobox, tooltip), a selection (listbox, multi-select, tree, grid cells), keyboard movement inside a group (arrow keys, typeahead, one tab stop), drag and drop or reordering, resizing, or a long virtualized list. A page of static sections, links and plain buttons has none; skip this file.

Hand-written keyboard and focus code is where generated interfaces break most: a focus trap that leaks, arrow keys that skip items, a popup that ignores Escape or an outside click, ARIA that says one thing while the keys do another. Don't write that layer by hand when a tested one fits.

## Contents

- [Pick the source](#pick-the-source)
- [Behavior map](#behavior-map)
- [Using UI SDK](#using-ui-sdk)
- [Fallback: hand-written](#fallback-hand-written)
- [Report it](#report-it)

## Pick the source

Take the first row that matches, and name the choice in the Design Thinking report:

| Situation | Interaction source |
|---|---|
| The project already uses a component or headless library that covers this part (`@ui-sdk/*`, Radix, React Aria, Headless UI, Ark UI, Melt UI, Bits UI, Reka UI, …) | That library. Never add a second one next to it (Edge Cases: *Existing codebase*). |
| React, Vue, Svelte, Solid or web components, and the user approves a beta dependency | **UI SDK** behaviors and components, below. |
| No package manager or build step (a single `index.html`) and the user approves a beta dependency loaded from a URL | UI SDK web components without a bundler: `https://ui-sdk.dev/web.js` (see https://ui-sdk.dev/web.md). Not for offline or air-gapped targets. |
| Another framework (Angular, Qwik, …), offline or air-gapped, a "no new dependencies" rule, or the user declines the beta | Hand-written, per the fallback below. |

Adding UI SDK is a new dependency: list it with the files in step 4, so the step 5 approval covers it. "Just build it" without a stated preference → propose it in the one-line direction and continue.

## Behavior map

UI SDK (https://ui-sdk.dev, https://github.com/vercel-labs/ui, Apache-2.0, by Vercel) ships each interaction as a headless *behavior* in `@ui-sdk/core`, plus ready components built from them in `@ui-sdk/react`, `/vue`, `/svelte`, `/solid` and `/web`. Prefer a shipped component (a Select, Menu, Dialog, Combobox); compose behaviors only for a part it doesn't ship.

| Interaction | Behavior in `@ui-sdk/core` |
|---|---|
| Anything that opens: menu, popover, dialog, select list | `createPopup` (with `popupState`, `popupTrigger`, `popupContent`) |
| One tab stop, arrow keys through a group (toolbar, tabs, radio group) | `createRovingFocus`; cells by row and column: `createGridFocus` |
| A highlight that moves through options and filters as you type | `createListbox`; first-letter jumps: `createTypeahead` |
| Single or multiple selection | `createSelection` |
| Focus when the focused item is removed | `createFocusRecovery` |
| Reorder by drag and by keyboard | `createReorder`; a drag of your own: `bindDrag` |
| Resize a panel or column | `createResize` |
| Long lists | `createVirtualizer` |

These names come from `@ui-sdk/core` `0.1.0-beta.2`. In the project, the installed package's docs win over this table.

## Using UI SDK

1. **Beta.** UI SDK is in beta (`0.1.0-beta.x`) and its APIs may change. Pin the exact version in `package.json` (no `^` or `~` range) and say so in the Final Report.
2. **Install** `@ui-sdk/core` and the framework's package with the project's package manager.
3. **Read the installed docs, not memory:** `node_modules/@ui-sdk/<framework>/docs/llms.txt` first, then only the pages the task needs (e.g. `docs/components/select.md`). Search `docs/core.md` by heading (it's large). Import from each component's own entry, like `@ui-sdk/react/select`; never from `@ui-sdk/core/internal/*`.
4. **Style it with this skill's rules.** UI SDK renders no styles of its own. The aesthetic direction, the Default Style Guide and the Default Quality Bar still apply; style its parts and states (`data-*` attributes) to them. Its optional default look (`@ui-sdk/core/web.css`) is not the direction unless the brief asks for it.
5. **Verify by keyboard** in step 7, for each interactive part: Tab in and out, the arrow keys, Enter and Space, Escape closes and returns focus to the trigger, and focus stays visible throughout. Record any check that could not run.
6. **Agent access (optional, only when asked).** UI SDK can expose a page's controls to an agent (`createAgent`) and to a browser's built-in agent through WebMCP (`registerTools`). WebMCP is an early proposal with an early preview in Chrome; it does nothing in browsers without it. Treat it as an extra, never a requirement, and keep the `allow` check that asks before consequential actions.

The UI SDK team also publishes a `ui-sdk` agent skill for this work. This skill neither loads nor installs it; the user may add it for later sessions (`npx skills add vercel-labs/ui --skill ui-sdk`, or `asm install github:vercel-labs/ui --path packages/core/skills/ui-sdk`). Mention it under `Decision:` when UI SDK was used.

## Fallback: hand-written

Follow the WAI-ARIA Authoring Practices pattern for the part (https://www.w3.org/WAI/ARIA/apg/patterns/). Write its roles, states and keys down before coding, and decide in writing: where focus lands on open and on Tab, whether selection follows focus, who owns Escape, and where focus goes when the focused item leaves. Run the same keyboard walk as step 5 above.

## Report it

- `Evidence:` the interaction source per part (library, UI SDK + version, or hand-written) and the keyboard walk result.
- `Uncertainty:` "UI SDK is beta (pinned <version>); APIs may change", when used.
- `Decision:` when UI SDK was used and nothing else needs approval: `No approval needed.` followed, on the same line, by the optional `ui-sdk` skill install for later sessions.
