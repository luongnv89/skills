# ETF Evaluator — HTML Output Template

Use this template as the **rendering contract** for Phase 6. The scorecard data model stays in `references/scorecard-template.md`; this file defines how that data is presented.

## Rules

1. **Single self-contained file.** All CSS lives in a `<style>` block in `<head>`. No CDN links, no external fonts, no JS libraries, no images.
2. **No JavaScript.** The report is static HTML + CSS only.
3. **Escape all dynamic text.** Fund names, source URLs, notes, and any user-provided text must be HTML-escaped (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;`). Never insert raw unescaped text.
4. **Replace every `{{PLACEHOLDER}}`** with actual data. Leave **no** `{{...}}` tokens in the final file.
5. **File naming:** `~/etf-evaluations/{{ISIN}}_etf_evaluation.html` (sanitize ISIN/ticker for filesystem safety).
6. **Verdict class:** apply exactly one of `verdict-invest`, `verdict-consider`, or `verdict-avoid` to the verdict card.
7. **Rating classes:** apply exactly one of `rating-good`, `rating-fair`, `rating-poor`, or `rating-unverified` to each rating badge.

## Design System

- **Palette:** navy header (`#1e293b`), white cards, light gray background (`#f8fafc`), semantic accents — green `#16a34a` (Good/Invest), amber `#d97706` (Fair/Consider), red `#dc2626` (Poor/Avoid), slate `#64748b` (Unverified).
- **Typography:** system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif`). Tabular numbers for all financial values.
- **Layout:** max-width `960px`, centered. Card-based sections with subtle shadow.
- **Tables:** full-width within cards, striped rows, scrollable on mobile (`overflow-x: auto` wrapper).
- **Print:** remove shadows, ensure black text on white background, avoid page breaks inside sections.

## Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ETF Evaluation — {{FUND_NAME}} ({{TICKER}})</title>
<style>
  /* ===== Design tokens ===== */
  :root{
    --bg:#f8fafc; --card:#ffffff; --header:#1e293b; --header-text:#f1f5f9;
    --line:#e2e8f0; --line-soft:#f1f5f9;
    --ink:#0f172a; --ink-soft:#475569; --ink-faint:#94a3b8;
    --green:#16a34a; --green-bg:#f0fdf4; --green-border:#bbf7d0;
    --amber:#d97706; --amber-bg:#fffbeb; --amber-border:#fde68a;
    --red:#dc2626; --red-bg:#fef2f2; --red-border:#fecaca;
    --slate:#64748b; --slate-bg:#f8fafc; --slate-border:#e2e8f0;
    --radius:10px; --shadow:0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --maxw:960px;
  }
  *, *::before, *::after{box-sizing:border-box}
  body{margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; line-height:1.6; -webkit-font-smoothing:antialiased}
  a{color:var(--green); text-decoration:none} a:hover{text-decoration:underline}
  .wrap{max-width:var(--maxw); margin:0 auto; padding:0 20px}

  /* ===== Header ===== */
  header{background:var(--header); color:var(--header-text); padding:40px 0 36px}
  header .wrap{display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:16px}
  header h1{margin:0; font-size:clamp(1.6rem,4vw,2.2rem); font-weight:700; letter-spacing:-.02em; line-height:1.15}
  header .subtitle{font-size:14px; color:var(--ink-faint); margin-top:6px}
  header .meta{font-size:13px; color:var(--ink-faint); text-align:right; line-height:1.7}
  header .meta span{display:block}

  /* ===== Verdict card ===== */
  .verdict-card{margin:-20px auto 32px; position:relative; z-index:1; max-width:var(--maxw); padding:0 20px}
  .verdict{border-radius:var(--radius); padding:28px 32px; box-shadow:var(--shadow)}
  .verdict-invest{background:var(--green-bg); border:1.5px solid var(--green-border)}
  .verdict-consider{background:var(--amber-bg); border:1.5px solid var(--amber-border)}
  .verdict-avoid{background:var(--red-bg); border:1.5px solid var(--red-border)}
  .verdict .badge{display:inline-block; font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:4px 14px; border-radius:999px}
  .verdict-invest .badge{background:var(--green); color:#fff}
  .verdict-consider .badge{background:var(--amber); color:#fff}
  .verdict-avoid .badge{background:var(--red); color:#fff}
  .verdict .rationale{margin:14px 0 0; font-size:15px; color:var(--ink-soft); line-height:1.65}
  .verdict .rationale strong{color:var(--ink)}

  /* ===== Section ===== */
  section{margin-bottom:28px}
  .sec-head{display:flex; align-items:baseline; gap:12px; margin-bottom:16px; padding-bottom:10px; border-bottom:2px solid var(--header)}
  .sec-head h2{margin:0; font-size:1.25rem; font-weight:700; color:var(--header)}
  .sec-head .n{font-family:monospace; font-size:11px; color:var(--ink-faint); background:var(--line-soft); padding:2px 8px; border-radius:4px}

  /* ===== Card ===== */
  .card{background:var(--card); border-radius:var(--radius); box-shadow:var(--shadow); padding:24px 28px; margin-bottom:16px}

  /* ===== Info grid ===== */
  .info-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); border-radius:var(--radius); overflow:hidden}
  .info-grid div{background:var(--card); padding:14px 18px}
  .info-grid dt{font-size:10.5px; letter-spacing:.1em; text-transform:uppercase; color:var(--ink-faint); margin:0 0 4px; font-weight:600}
  .info-grid dd{margin:0; font-size:14px; color:var(--ink); font-weight:500}

  /* ===== Scorecard table ===== */
  .table-wrap{overflow-x:auto; -webkit-overflow-scrolling:touch}
  table{width:100%; border-collapse:collapse; font-size:14px}
  thead th{text-align:left; padding:10px 14px; background:var(--line-soft); font-size:11.5px; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-faint); font-weight:600; border-bottom:2px solid var(--line); white-space:nowrap}
  tbody td{padding:14px; border-bottom:1px solid var(--line-soft); vertical-align:top; color:var(--ink-soft)}
  tbody tr:last-child td{border-bottom:none}
  tbody tr:hover{background:#fafbfc}
  .mono{font-family:"SF Mono",SFMono-Regular,ui-monospace,"Cascadia Code","Menlo",monospace; font-size:13px}
  .tabular{font-variant-numeric:tabular-nums}

  /* ===== Rating badges ===== */
  .rating{display:inline-block; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; padding:3px 10px; border-radius:999px; white-space:nowrap}
  .rating-good{background:var(--green-bg); color:var(--green); border:1px solid var(--green-border)}
  .rating-fair{background:var(--amber-bg); color:var(--amber); border:1px solid var(--amber-border)}
  .rating-poor{background:var(--red-bg); color:var(--red); border:1px solid var(--red-border)}
  .rating-unverified{background:var(--slate-bg); color:var(--slate); border:1px solid var(--slate-border)}

  /* ===== Summary badges ===== */
  .summary{display:flex; flex-wrap:wrap; gap:20px; margin-top:16px; padding-top:16px; border-top:1px solid var(--line)}
  .summary .label{font-size:12px; color:var(--ink-faint); font-weight:600; letter-spacing:.04em; text-transform:uppercase}
  .summary .value{font-size:14px; color:var(--ink); font-weight:600}

  /* ===== Comparison table ===== */
  .compare-note{font-size:14px; color:var(--ink-soft); margin-top:14px; line-height:1.65}

  /* ===== Risks ===== */
  .risk-list{list-style:none; padding:0; margin:0}
  .risk-list li{padding:10px 0; border-bottom:1px solid var(--line-soft); font-size:14px; color:var(--ink-soft); line-height:1.6}
  .risk-list li:last-child{border-bottom:none}
  .risk-list li::before{content:"⚠"; margin-right:10px; font-size:13px}

  /* ===== Bottom line ===== */
  .bottom-line{font-size:15px; color:var(--ink); line-height:1.7; font-weight:500}

  /* ===== Sources ===== */
  .source-list{list-style:none; padding:0; margin:0}
  .source-list li{padding:6px 0; font-size:13px; color:var(--ink-soft); border-bottom:1px solid var(--line-soft)}
  .source-list li:last-child{border-bottom:none}
  .source-list a{color:var(--green)}

  /* ===== Disclaimer ===== */
  footer{margin-top:40px; padding:28px 0; border-top:1px solid var(--line); text-align:center}
  footer p{font-size:12px; color:var(--ink-faint); line-height:1.7; max-width:720px; margin:0 auto}
  footer strong{color:var(--ink-soft)}

  /* ===== Print ===== */
  @media print{
    body{background:#fff; color:#000}
    header{background:#1e293b; -webkit-print-color-adjust:exact; print-color-adjust:exact}
    .verdict{box-shadow:none; border-width:2px}
    .card{box-shadow:none; border:1px solid #ddd}
    .rating{border-width:2px; -webkit-print-color-adjust:exact; print-color-adjust:exact}
    thead th{background:#f1f5f9; -webkit-print-color-adjust:exact; print-color-adjust:exact}
    section{break-inside:avoid}
    a{color:#000; text-decoration:underline}
  }

  /* ===== Mobile ===== */
  @media(max-width:640px){
    header{padding:28px 0 24px}
    header .wrap{flex-direction:column; align-items:flex-start}
    header .meta{text-align:left}
    .verdict{padding:20px 22px}
    .card{padding:18px 16px}
    .info-grid{grid-template-columns:repeat(2,1fr)}
    thead th, tbody td{padding:10px 12px; font-size:13px}
  }
</style>
</head>
<body>

<!-- ===== HEADER ===== -->
<header>
  <div class="wrap">
    <div>
      <h1>{{FUND_NAME}}</h1>
      <div class="subtitle">{{TICKER}} · {{ISIN}} · {{INDEX_NAME}} ({{INDEX_PROVIDER}})</div>
    </div>
    <div class="meta">
      <span>Evaluated: {{DATE}}</span>
      <span>Data as of: {{DATA_AS_OF}}</span>
      <span>Investor: {{INVESTOR_CONTEXT}}</span>
    </div>
  </div>
</header>

<!-- ===== VERDICT ===== -->
<div class="verdict-card">
  <div class="verdict verdict-{{VERDICT_CLASS}}">
    <span class="badge">{{VERDICT_TEXT}}</span>
    <p class="rationale">{{VERDICT_RATIONALE}}</p>
  </div>
</div>

<div class="wrap">

  <!-- ===== FUND DETAILS ===== -->
  <section>
    <div class="sec-head"><span class="n">01</span><h2>Fund Details</h2></div>
    <dl class="info-grid">
      <div><dt>Share Class</dt><dd>{{SHARE_CLASS}} ({{DISTRIBUTION_POLICY}})</dd></div>
      <div><dt>Currency</dt><dd>{{FUND_CURRENCY}}</dd></div>
      <div><dt>Domicile</dt><dd>{{DOMICILE}}</dd></div>
      <div><dt>Structure</dt><dd>{{STRUCTURE}}</dd></div>
      <div><dt>Replication</dt><dd>{{REPLICATION_METHOD}}</dd></div>
      <div><dt>Provider</dt><dd>{{PROVIDER}}</dd></div>
      <div><dt>Inception</dt><dd>{{INCEPTION_DATE}}</dd></div>
      <div><dt>Listing</dt><dd>{{LISTING_EXCHANGE}}</dd></div>
    </dl>
  </section>

  <!-- ===== SCORECARD ===== -->
  <section>
    <div class="sec-head"><span class="n">02</span><h2>10-Point Scorecard</h2></div>
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th style="width:36px">#</th>
              <th>Criterion</th>
              <th style="width:110px">Rating</th>
              <th>Value (source · as-of)</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            <!-- REPEAT:scorecard-row — one <tr> per checklist item -->
            <tr>
              <td class="mono tabular">{{ROW_NUM}}</td>
              <td><strong>{{CRITERION_NAME}}</strong></td>
              <td><span class="rating rating-{{RATING_CLASS}}">{{RATING_TEXT}}</span></td>
              <td class="mono tabular">{{VALUE_CELL}}</td>
              <td>{{NOTES_CELL}}</td>
            </tr>
            <!-- /REPEAT:scorecard-row -->
          </tbody>
        </table>
      </div>
      <!-- Summary -->
      <div class="summary">
        <div><span class="label">Core 5:</span> <span class="value">{{CORE_SUMMARY}}</span></div>
        <div><span class="label">Bonus 5:</span> <span class="value">{{BONUS_SUMMARY}}</span></div>
        <div><span class="label">Total Good:</span> <span class="value" style="color:var(--green)">{{COUNT_GOOD}}</span></div>
        <div><span class="label">Total Fair:</span> <span class="value" style="color:var(--amber)">{{COUNT_FAIR}}</span></div>
        <div><span class="label">Total Poor:</span> <span class="value" style="color:var(--red)">{{COUNT_POOR}}</span></div>
        <div><span class="label">Unverified:</span> <span class="value" style="color:var(--slate)">{{COUNT_UNVERIFIED}}</span></div>
      </div>
    </div>
  </section>

  <!-- ===== COMPARISON ===== -->
  <section>
    <div class="sec-head"><span class="n">03</span><h2>Comparison vs Similar ETFs</h2></div>
    <div class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Fund</th>
              <th>TER</th>
              <th>AUM</th>
              <th>Replication</th>
              <th>Domicile</th>
              <th>Tracking</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            <!-- REPEAT:compare-row -->
            <tr>
              <td><strong>{{COMP_FUND_NAME}}</strong><br><span class="mono" style="font-size:12px;color:var(--ink-faint)">{{COMP_ISIN}}</span></td>
              <td class="mono tabular">{{COMP_TER}}</td>
              <td class="mono tabular">{{COMP_AUM}}</td>
              <td>{{COMP_REPLICATION}}</td>
              <td>{{COMP_DOMICILE}}</td>
              <td class="mono tabular">{{COMP_TRACKING}}</td>
              <td>{{COMP_NOTE}}</td>
            </tr>
            <!-- /REPEAT:compare-row -->
          </tbody>
        </table>
      </div>
      <p class="compare-note">{{COMPARE_NOTE}}</p>
    </div>
  </section>

  <!-- ===== RISKS ===== -->
  <section>
    <div class="sec-head"><span class="n">04</span><h2>Key Risks</h2></div>
    <div class="card">
      <ul class="risk-list">
        <!-- REPEAT:risk-item -->
        <li>{{RISK_TEXT}}</li>
        <!-- /REPEAT:risk-item -->
      </ul>
    </div>
  </section>

  <!-- ===== BOTTOM LINE ===== -->
  <section>
    <div class="sec-head"><span class="n">05</span><h2>Bottom Line</h2></div>
    <div class="card">
      <p class="bottom-line">{{BOTTOM_LINE}}</p>
    </div>
  </section>

  <!-- ===== SOURCES ===== -->
  <section>
    <div class="sec-head"><span class="n">06</span><h2>Sources</h2></div>
    <div class="card">
      <ol class="source-list">
        <!-- REPEAT:source-item -->
        <li>{{SOURCE_TEXT}}</li>
        <!-- /REPEAT:source-item -->
      </ol>
    </div>
  </section>

  <!-- ===== DISCLAIMER ===== -->
  <footer>
    <p>Data as of <strong>{{DATA_AS_OF}}</strong>. Figures marked "Unverified" could not be confirmed from a public source and should be checked on the official factsheet before investing. This is an educational evaluation, <strong>not personalized financial advice</strong>; past performance does not guarantee future results. Do your own research.</p>
  </footer>

</div>
</body>
</html>
```

## Section-by-section guide

| Section | Placeholders to fill | Notes |
|---------|---------------------|-------|
| Header | `FUND_NAME`, `TICKER`, `ISIN`, `INDEX_NAME`, `INDEX_PROVIDER`, `DATE`, `DATA_AS_OF`, `INVESTOR_CONTEXT` | Header is dark navy; keep fund name prominent |
| Verdict | `VERDICT_CLASS` (invest/consider/avoid), `VERDICT_TEXT`, `VERDICT_RATIONALE` | Class controls the card color |
| Fund Details | All `{{...}}` in the `<dl>` grid | 8 key attributes as a compact grid |
| Scorecard | Repeat `<tr>` 10 times, one per checklist item | Each row: number, criterion name, rating badge, value+source, notes |
| Comparison | Repeat `<tr>` 1–3 times (this fund + alternatives) | First row is always the evaluated fund |
| Risks | Repeat `<li>` per risk | Use the bullet icon (⚠) from CSS |
| Bottom Line | Single paragraph | 1–3 sentences restating verdict + position guidance |
| Sources | Repeat `<li>` per source | Include URL as `<a>` tag where applicable |
| Footer | `DATA_AS_OF` | Standard disclaimer, do not modify text |
