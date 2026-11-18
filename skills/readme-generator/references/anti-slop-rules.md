# Anti-Slop Rules

AI-written READMEs have predictable tells that make developers distrust the project. Apply these rules to every prose line: the pitch, section intros, feature lines, and FAQ answers. They skip code, commands, and content preserved in `<details>` blocks.

## Banned phrases — never write these or close variants

| Pattern | Why it's slop | Write instead |
|---|---|---|
| "Whether you're a ... or a ..." | Fake inclusivity, says nothing | Name the primary audience directly |
| "In today's fast-paced..." | Generic filler | Cut entirely |
| "Seamless/seamlessly" | Meaningless modifier | Describe what actually happens |
| "Robust/robust solution" | Empty adjective | State the specific capability |
| "Leverage/utilize" | Jargon for "use" | "use" |
| "Cutting-edge/state-of-the-art" | Unsubstantiated claim | Cite the specific technique or benchmark |
| "Elevate/supercharge/turbocharge" | Hype with no content | State the measurable improvement |
| "Game-changer/revolutionary" | Unearned superlative | Let the reader decide |
| "Look no further" | Salesy | Cut entirely |
| "Say goodbye to X" | Cliche | State what the project does instead |
| "Unlock/unleash/harness" | Filler verbs | Name the outcome |
| "Best-in-class/world-class" | Unsubstantiated | Cite proof or cut |
| "Dive deep/deep dive" | Padding | Cut, or write "details" |
| "It's worth noting that" | Throat-clearing | Cut, and state the thing |
| "Streamline your workflow" | Generic promise | Describe the specific workflow change |
| "Comprehensive solution" | Says nothing | State what it covers |

## Structural slop

- An "Introduction" or "Overview" section before Install
- Padding sentences that repeat the pitch in other words
- Rhetorical questions ("Tired of X? Want to Y?")
- Exclamation marks for enthusiasm
- Emoji anywhere: headings, body text, badges, or section labels
- Vague benefits without specifics ("saves you time", "boosts productivity")
- Filler transitions ("Furthermore", "Moreover", "Additionally", "In conclusion")
- Feature lists with no outcome

## The test

Read each sentence and ask: does it give the reader information they didn't already have? If not, cut it.

Then run the three-part copy test on the pitch and each feature line. Rewrite a failing line from the project's facts, or cut it:

1. **Visualizable:** the reader can picture a person, an object, or an action. "Shows only the log lines at warn level and above" passes. "Streamline your logging" fails.
2. **Falsifiable:** the reader can check it, and it would be false if the project did not do it. A fact from a project file stands behind it.
3. **Only-we-can-say:** a competitor could not paste it unchanged. It names this project's mechanism, number, or use.

The copy test draws on "The secret behind viral product launches" by Kyle Jeong with Tereza Tizkova (x.com/kylejeong/status/2119925224334586085, 2026-11-09; practitioner advice, not platform rules).
