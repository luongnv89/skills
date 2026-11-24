# appstore-review-checker eval fixtures

Metadata-only listings in `fastlane/metadata/<locale>/` layout, used by evals 14 and 15 in `meta/appstore-review-checker/evals/evals.json` (#696).

| Fixture | Source | Expected |
|---------|--------|----------|
| `subtitle-and-keyword-brands/` | As submitted on 2026-11-22 and rejected by App Review on 2026-11-24 under 4.1(c), "subtitle contains … Claude, Codex and Grok". Only the fields given in #696 are included. | `4.1-c` FAIL for each of the three subtitles (en-US, de-DE, ja); `2.3.7-keywords` FAIL for `Grok` and `Cursor` in the ja keywords; the en-US promotional text naming services is not a 4.1-c FAIL |
| `clean-description-brands/` | Synthetic. Generic name, subtitle and keywords; supported services named only in the description and promotional text. | No 4.1-c, 2.3.7-keywords or 5.2.1 FAIL for the brands; at most a WARNING |
