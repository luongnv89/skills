# btop-Inspired Styling — cli-builder

Every CLI this skill builds takes its look from [btop](https://github.com/aristocratos/btop) (Apache-2.0): rounded boxes with the title set into the border, gradient meters, braille graphs, and colors named by role in one theme. The values below come from btop's default theme and drawing code (`src/btop_theme.cpp`, `src/btop_draw.cpp`). Reuse the look and these tables; never copy btop's C++.

**Borrow the look, not the runtime.** A CLI built here prints its output and exits. It opens no alternate screen, runs no key or mouse loop, and never moves the cursor up to redraw earlier lines. A repeating view (`--watch`) appends one plain line per sample. If the user asks for a live, refreshing btop-like screen, say in Step 1 that it is a TUI, which this skill does not build, and offer the append-only form.

Contents: 1. The design's Visual style section · 2. Three decisions per stream · 3. Theme roles · 4. Components · 5. Example · 6. Libraries · 7. Verify

## 1. The design's Visual style section

Write these five items in the Step 2 design document:

1. **Components per command** — which command prints a box, table, meter, sparkline, or status (section 4), and which prints only plain text.
2. **Theme** — the roles in section 3, plus any change the user asks for.
3. **Fallbacks** — plain output for pipes and machine formats, no color for `NO_COLOR` and `--no-color`, ASCII glyphs outside a UTF-8 locale (section 2).
4. **Implementation** — the styling library or the zero-dependency module, plus the width function (section 6). A library is a new runtime dependency, so name it here for approval.
5. **Mockup** — one command's styled output, drawn like section 5.

If the user explicitly declines the btop style, in the request or at design approval, replace the five items with `Visual style: <the style the user chose> — btop style declined by the user`. Keep section 2's plain-output rules and section 7's tests 1-3; skip tests 4-7, the forced demo, and the two `Uncertainty:` lines of section 7.

## 2. Three decisions per stream

Make these decisions in the style module, right after argument parsing, so `--no-color` and the command's `--format` are known. Make them separately for stdout and for stderr, because stdout can be piped while stderr is still a terminal. Commands read the result; they never test the terminal themselves.

**A. Styled or plain.** The stream is plain when any of these is true; otherwise it is styled:

- The stream is stdout, and the command prints a machine format (`--format json`, `csv`, or any other format a program parses). This rule wins over `FORCE_COLOR`. It does not apply to stderr.
- `TERM` is `dumb`.
- The stream is not a TTY, and `FORCE_COLOR` is unset, empty, or `0`.

Plain output carries the same records and fields as styled output: one record per line, fields separated by one tab, no header row, and no frames, meters, graphs, truncation, or escape codes.

**B. Color tier** (styled streams only). Apply the first rule that matches:

1. `--no-color` is given, or `NO_COLOR` is set to a non-empty value → **none**: no escape sequences at all, not even bold or faint. This rule wins over `FORCE_COLOR`.
2. `COLORTERM` is `truecolor` or `24bit` → **24-bit**.
3. `TERM` contains `256color` → **256**.
4. Otherwise → **16**.

On Windows, enable virtual-terminal processing before the first escape code. If it cannot be enabled, use tier none.

**C. Glyph set** (styled streams only). Use **Unicode** when the stream's encoding is UTF-8; otherwise use **ASCII**. In Python, read `sys.stdout.encoding` or `sys.stderr.encoding`. Elsewhere, read the first set variable of `LC_ALL`, `LC_CTYPE`, `LANG` and look for `UTF-8` or `utf8`; on Windows, treat a set `WT_SESSION` as UTF-8.

Give every render function an explicit mode argument (styled or plain, color tier, glyph set), so tests can render each path without a terminal (section 7). Section 6 says how to pass the same decisions to a library.

## 3. Theme roles

One theme maps each role to the escape codes of the active color tier. Command code names a role (`title`, `accent`, and so on); it never contains an escape code or a hex value.

btop paints its own dark background. A CLI does not own the background, so the theme never sets a background color, and body text keeps the terminal's default color. Four btop colors fail on one background or the other: on a white terminal, `main_fg` `#cccccc` measures 1.6:1 and `title` `#eeeeee` 1.2:1; on a black terminal, `inactive_fg` `#404040` measures 2.0:1 and `div_line` `#303030` 1.6:1. The roles below replace those four with text attributes.

| Role | btop key | 24-bit | 16-color (btop TTY theme) | Use for |
|------|----------|--------|---------------------------|---------|
| `text` | `main_fg` | terminal default | terminal default | body text |
| `title` | `title` | bold | bold | box titles, table headers |
| `accent` | `hi_fg` | `#b54040` + bold | `91` + bold | flags and command names in help, key letters |
| `dim` | `inactive_fg` | faint (SGR 2) | faint (SGR 2) | units, hints, defaults, empty meter cells |
| `border` | `cpu_box`, `mem_box`, `net_box`, `proc_box` | `#556d59`, `#6c6c4b`, `#5c588d`, `#805252` | `32`, `33`, `35`, `31` | box lines and title notches: `cpu_box` by default, the others to tell up to four sections apart |
| `low` → `mid` → `high` | `cpu_start`, `cpu_mid`, `cpu_end` | `#77ca9b` → `#cbc06c` → `#dc4c4c` | `92` → `93` → `91` | meter and sparkline gradient; status symbols for ok, warning, error |

The `accent` and `border` colors read on both backgrounds: 3.2:1 or more on black and 5.4:1 or more on white. On a dark-gray (`#1e1e1e`) terminal `accent` drops to 3.0:1, which is why `accent` text is also bold.

**256 tier.** Convert each 24-bit value as btop does. If `round(r/11)`, `round(g/11)`, and `round(b/11)` are equal, use grey `232 + round(r/11)`. Otherwise use `16 + 36*round(r/51) + 6*round(g/51) + round(b/51)`.

**Rounding.** Every `round` in this file rounds half up, as btop's C++ does. Python's `round()` rounds half to even, so use `math.floor(x + 0.5)`.

**Gradient.** Build 101 steps (0-100): linear from `low` to `mid` over 0-50, and from `mid` to `high` over 50-100. In the 16 tier, use `low` for 0-33, `mid` for 34-66, and `high` for 67-100. On a white terminal `low` and `mid` measure about 2:1, so color never carries a value alone: every meter prints its number, and every status prints its word in the `text` role.

## 4. Components

Each component gives its Unicode form and its ASCII form. Draw the ASCII form when the glyph set is ASCII. Measure every width with the width function from section 6, never with string length.

**Box with a title in the border.**

- Draw corners `╭ ╮ ╰ ╯` and lines `─ │` in the `border` role.
- Place the title after one `─`, between the notches `┐` and `┌`: `╭─┐deploy-tool status┌───╮`. Draw the title in the `title` role and the notches in the `border` role.
- Place an optional footer the same way on the bottom line, between `┘` and `└`: `╰─┘3 services · 2 up└───╯`.
- Divide sections inside a box with `├───┤`.
- Size the box to the terminal width: `COLUMNS` if set, otherwise the stream's terminal size, otherwise 80. Shorten a value or title that does not fit, ending it with `…` (`...` in ASCII).
- ASCII: corners `+`, lines `-` and `|`, notches `[` and `]`: `+-[deploy-tool status]---+`.

**Meter.** A row of `width` cells, then the value.

- Fill cell `i` (1 to `width`) when `value >= round(i * 100 / width)`, as btop does.
- Draw a filled cell as `■` in the gradient color at that cell's position, so a full meter runs `low` → `high` from left to right.
- Draw an empty cell as `■` in the `dim` role. When the color tier is none, draw it as `·` instead: without color, a filled `■` and an empty `■` look the same.
- Print the value after the meter, right-aligned: ` 72%`.
- ASCII: filled `#`, empty `.`.

**Sparkline** (a time series on one line). Each braille cell shows two samples: pair samples 1-2, 3-4, and so on, repeating the last sample when the count is odd. Scale each sample to a level from 0 to 4: `round(sample / max * 4)`, where `max` is the known ceiling (100 for percentages) or else the series maximum. Take the cell from btop's `braille_up` table below: the line is the first sample's level, and the position in that line (0-4) is the second sample's level.

```text
level 0: " ⢀⢠⢰⢸"
level 1: "⡀⣀⣠⣰⣸"
level 2: "⡄⣄⣤⣴⣼"
level 3: "⡆⣆⣦⣶⣾"
level 4: "⡇⣇⣧⣷⣿"
```

- Color each cell with the gradient at the larger of its two samples, as a share of `max`.
- Print the minimum, maximum, and last value after the sparkline. Some fonts lack braille (btop's README notes the same limit), so the numbers carry the data.
- ASCII: print only the three numbers.

**Table.**

- Draw the header row in the `title` role, with no rule under it, as in btop's process list.
- Right-align numbers. Draw units in the `dim` role.
- Put the table in a box when it is the command's main output.

**Status.** A symbol in the level color, then a word in the `text` role: `● up` (`low`), `▲ degraded` (`mid`), `✗ down` (`high`). ASCII: `+ up`, `! degraded`, `x down`.

**Help text.** Style `--help` only through a hook that the argument parser already provides, for example clap `Styles`, picocli `ColorScheme`, or typer's rich help. Use the `accent` role for flags and commands, and the `title` role for headings. Pass the color tier to that hook (section 6); if the hook cannot drop every escape code for tier none, leave `--help` plain. If the parser has no such hook, leave `--help` plain. Never replace the parser's help generator.

**Errors (stderr).** Print `✗ error:` in the `high` color and bold, then the message in `text`. On the next line, print `hint:` and the fix in the `dim` role. ASCII: `x error:`. Style the error only when stderr is styled (section 2).

**Progress (stderr).** Show progress only when stderr is a real TTY, whatever `FORCE_COLOR` says, and only for an operation that takes longer than 2 seconds. Draw one line and redraw it with `\r`: a meter when the total is known, otherwise the item count and elapsed time (`1,204 files · 3.1s`). Clear the line before the result prints.

## 5. Example: a status command

Styled, Unicode glyphs, color tier none, so empty meter cells show as `·`. With color on, the border is `#556d59`, the title is bold, filled cells run green → yellow → red, and empty cells are faint `■`.

```text
╭─┐deploy-tool status┌───────────────────────────────────╮
│ service   state       cpu                          mem │
│ api       ● up        ■■■■■■■■■■■■■·····  72%  1.2 GiB │
│ worker    ● up        ■■■■■·············  31%  640 MiB │
│ cron      ✗ down      ··················   0%      0 B │
╰─┘3 services · 2 up└────────────────────────────────────╯
```

Styled, ASCII glyphs:

```text
+-[deploy-tool status]-----------------------------------+
| service   state       cpu                          mem |
| api       + up        #############.....  72%  1.2 GiB |
| worker    + up        #####.............  31%  640 MiB |
| cron      x down      ..................   0%      0 B |
+-[3 services, 2 up]-------------------------------------+
```

Plain (piped stdout): the same records, tab-separated (`→` marks a tab here), no header.

```text
api→up→72%→1.2 GiB
worker→up→31%→640 MiB
cron→down→0%→0 B
```

## 6. Libraries

The argument parser still comes from `references/cli-libraries.md`. For styling, choose one of two implementations and name it in the design:

- **Zero-dependency module** — raw ANSI SGR codes plus sections 2-4, in one file.
- **Styling library** — from the table below.

Either way, the CLI needs a **width function** that counts terminal cells (CJK and emoji take two) whenever a box or table holds user-supplied text, box titles included. Name it in the design too.

| Language | Styling library | Width function | Pass the section 2 decision with |
|----------|-----------------|----------------|----------------------------------|
| Python | rich | built in (`rich.cells.cell_len`) | `Console(force_terminal=..., color_system=None` or `"standard"`/`"256"`/`"truecolor")`; never `no_color`, which keeps bold and faint |
| JavaScript/TS | chalk (v5 is ESM-only; use chalk 4 in a CommonJS project) | string-width | `new Chalk({level: 0-3})`, one instance per stream |
| Go | lipgloss v1 | built in (`lipgloss.Width`) | `lipgloss.SetColorProfile(...)` |
| Rust | anstream + anstyle | unicode-width | `AutoStream::new(stream, ColorChoice::Always` or `Never)` |
| Java/Kotlin | picocli `CommandLine.Help.Ansi` (16 colors only; use raw SGR for 256 and 24-bit) | JLine `AttributedString.columnLength` or a zero-width-aware helper | `Help.Ansi.ON` or `OFF` |
| Ruby | pastel (16 colors only; use raw SGR for 256 and 24-bit) | unicode-display_width | `Pastel.new(enabled: ...)` |

Libraries and parsers run their own terminal detection, and it can disagree with section 2: some ignore `FORCE_COLOR`, and some strip escape codes whenever the stream is not a TTY. Turn that detection off by passing the decision explicitly to every layer that writes output, including the parser (for example `click.echo(..., color=...)` and clap `Command::color(...)`).

None of these libraries draws the btop title notch (`┐title┌`) as a built-in border style. Build that top line in the style module.

## 7. Verify

Add these tests with the Phase 2 output-formatting tasks. Build each subprocess environment explicitly: remove `FORCE_COLOR`, `NO_COLOR`, `CLICOLOR_FORCE`, and `COLUMNS`, set `TERM=xterm-256color` and `LANG=en_US.UTF-8`, then add the variables the test names. Test runners such as Jest export `FORCE_COLOR` to their workers.

1. Run a command that prints a box on a terminal, with stdout captured (not a TTY). Check that stdout contains no ESC byte (`0x1b`) and no `╭`.
2. Run a `--format json` command with `FORCE_COLOR=1`. Check that stdout parses as JSON and contains no ESC byte.
3. Run the box command with `FORCE_COLOR=1` and `NO_COLOR=1`. Check that stdout contains no ESC byte.
4. Run the box command with `FORCE_COLOR=1`. Check that stdout contains an ESC byte and `╭─┐`. This test fails when a library or parser strips the styling.
5. Call the renderer with an explicit mode: styled, 16 colors, Unicode. Check that the output contains `\x1b[` and `╭─┐`.
6. Call the renderer with the ASCII glyph set. Check that every character is below `0x80`.
7. Call the meter with value 50, width 10, and color tier none. Check that the output is 5 `■`, 5 `·`, and ` 50%`.

Demo (SKILL.md Step 4, item 5), from Phase 2 on:

1. Run one approved example invocation plain, and show the output.
2. Run the same invocation with `env -u NO_COLOR TERM=xterm-256color FORCE_COLOR=1`, and show the output. The chat can print its escape codes raw. If the output contains no ESC byte, the demo fails (SKILL.md Step 4, item 3).
3. If `script` is available, run the same invocation once under a pseudo-terminal, to exercise the real TTY path: `script -q /dev/null <cmd>` on macOS, `script -qc "<cmd>" /dev/null` on Linux.

No one has yet seen the styled output the way a user sees it in their terminal. Under `Uncertainty:`, list `styled output not viewed in a real terminal` until the user confirms they ran the tool in one. List `light-background terminal not tried` until someone tries one.
