# Design rules

Rules for every page in this project. Follow them unless a request says otherwise.

1. Colours come only from the custom properties in `tokens.css`. Never write a hex, `rgb()` or `hsl()` value in a component rule.
2. Surfaces and text are flat: no gradients, glows, grain or text shadows.
3. Type: one family, "Source Sans 3". Sizes 14, 16, 20, 28 and 40 px only. Weights 400 and 600 only.
4. Motion: only a state change animates. Entries take `--duration-enter` (200 ms) with `ease-out`; exits take `--duration-exit` (120 ms) with `ease-in`. Nothing animates on page load or on scroll.
5. Shadows go only on menus, dialogs and toasts. Cards use a 1 px `--color-border` border and never sit inside another card.
6. Buttons and inputs use `--radius` (6 px). No pill shapes.
7. Every colour has a dark value in `tokens.css` under `prefers-color-scheme: dark`.
