# Design rules

Rules for every page in this project. Follow them unless a request says otherwise.

1. Colors come only from the custom properties in `:root` in `index.html`. Add a new color there first; never write a hex value inside a component rule.
2. Headings use Fraunces at weight 600; body text uses Source Serif 4 at weight 400. No other weights.
3. Every button, input and container has a 2px corner radius.
4. Sections are separated by a 1px `--color-border` top rule and 96px of vertical padding. Sections never get their own background color.
5. Primary buttons are a `--color-text` fill with `--color-surface` text; secondary buttons are a 1px `--color-text` border with no fill.
