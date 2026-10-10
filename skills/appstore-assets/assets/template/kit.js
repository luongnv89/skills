// appstore-assets render kit: icons, iOS/macOS primitives, device frames,
// frame and creative layouts. config.js builds screens from these helpers;
// index.html calls renderFromQuery() to draw exactly one asset per page load.

// ---------- Icons: SF Symbol stand-ins (inherit currentColor) ----------
const I = {
  chevronRight: `<svg viewBox="0 0 8 14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 1.5L6.5 7l-5 5.5"/></svg>`,
  chevronLeft: `<svg viewBox="0 0 12 20" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2L2 10l8 8"/></svg>`,
  chevronDown: `<svg viewBox="0 0 12 8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 1.8L6 6.2l4.5-4.4"/></svg>`,
  plus: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 4v16M4 12h16"/></svg>`,
  plusCircle: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="currentColor"/><path d="M12 7v10M7 12h10" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>`,
  check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>`,
  checkCircle: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="currentColor"/><path d="M7 12.4l3.3 3.2L17 8.8" stroke="#fff" stroke-width="2.3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  xmark: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
  search: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="7"/><path d="M15.8 15.8L21 21"/></svg>`,
  gear: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><circle cx="12" cy="12" r="3.2"/><path d="M12 2.5v2.6M12 18.9v2.6M21.5 12h-2.6M5.1 12H2.5M18.7 5.3l-1.8 1.8M7.1 16.9l-1.8 1.8M18.7 18.7l-1.8-1.8M7.1 7.1L5.3 5.3" stroke-linecap="round"/><circle cx="12" cy="12" r="6.6"/></svg>`,
  person: `<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="4.2"/><path d="M3.8 21c.6-4.4 4-7 8.2-7s7.6 2.6 8.2 7z"/></svg>`,
  house: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3l9 7.6V21h-6.2v-6.4H9.2V21H3V10.6z"/></svg>`,
  list: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"><path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1.3" fill="currentColor" stroke="none"/><circle cx="4" cy="12" r="1.3" fill="currentColor" stroke="none"/><circle cx="4" cy="18" r="1.3" fill="currentColor" stroke="none"/></svg>`,
  grid: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2"/><rect x="3" y="13" width="8" height="8" rx="2"/><rect x="13" y="13" width="8" height="8" rx="2"/></svg>`,
  star: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4L2.8 9.5l6.4-.8z"/></svg>`,
  heart: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-8.5-5.2-8.5-11.4A4.9 4.9 0 0 1 12 6.6a4.9 4.9 0 0 1 8.5 3c0 6.2-8.5 11.4-8.5 11.4z"/></svg>`,
  bell: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5a6.5 6.5 0 0 0-6.5 6.5v4.4L3.6 17h16.8l-1.9-3.6V9A6.5 6.5 0 0 0 12 2.5z"/><path d="M9.5 19a2.5 2.5 0 0 0 5 0z"/></svg>`,
  calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="4.5" width="18" height="16.5" rx="3"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4" stroke-linecap="round"/></svg>`,
  clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9.5"/><path d="M12 6.5V12l3.5 2.2" stroke-linecap="round"/></svg>`,
  mapPin: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a7.5 7.5 0 0 0-7.5 7.5C4.5 15 12 22 12 22s7.5-7 7.5-12.5A7.5 7.5 0 0 0 12 2zm0 10.2a2.7 2.7 0 1 1 0-5.4 2.7 2.7 0 0 1 0 5.4z"/></svg>`,
  chart: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="12" width="4" height="9" rx="1.2"/><rect x="10" y="7" width="4" height="14" rx="1.2"/><rect x="17" y="3" width="4" height="18" rx="1.2"/></svg>`,
  photo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><rect x="2.5" y="4" width="19" height="16" rx="3"/><circle cx="8.5" cy="9.5" r="1.8"/><path d="M3 17l5.5-5 4 3.5 3-2.5L21 17"/></svg>`,
  play: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l12-7.5z"/></svg>`,
  mic: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="8.5" y="2.5" width="7" height="12" rx="3.5"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3.5"/></svg>`,
  waveform: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M3 10.5v3M7 7v10M11 4v16M15 8v8M19 6v12M23 10.5v3"/></svg>`,
  arrowUpCircle: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="11.5" fill="currentColor"/><path d="M12 17.5V7M7.5 11.3L12 6.8l4.5 4.5" stroke="#fff" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  share: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3M8 7l4-4 4 4M6 11H5v10h14V11h-1"/></svg>`,
  trash: `<svg viewBox="0 0 24 26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 6h19M9 6V3.5h6V6M5 6l1.2 16a2 2 0 0 0 2 1.8h7.6a2 2 0 0 0 2-1.8L19 6M10 10.5v9M14 10.5v9"/></svg>`,
  lock: `<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="10.5" width="16" height="11" rx="2.6"/><path d="M7.5 10.5V7.8a4.5 4.5 0 0 1 9 0v2.7" fill="none" stroke="currentColor" stroke-width="2.2"/></svg>`,
  shield: `<svg viewBox="0 0 24 28"><path d="M12 1.5l9.5 3.6v8.3c0 6.2-4 10.9-9.5 13.1C6.5 24.3 2.5 19.6 2.5 13.4V5.1z" fill="currentColor"/><rect x="8" y="12.3" width="8" height="6.6" rx="1.3" fill="#fff"/><path d="M9.7 12.4v-1.6a2.3 2.3 0 0 1 4.6 0v1.6" stroke="#fff" stroke-width="1.6" fill="none"/></svg>`,
  key: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="15" r="5"/><path d="M11.6 11.4L21 2M17 6l3 3M14.5 8.5l2 2"/></svg>`,
  bubble: `<svg viewBox="0 0 26 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M3 4.5A2.5 2.5 0 0 1 5.5 2h15A2.5 2.5 0 0 1 23 4.5v11a2.5 2.5 0 0 1-2.5 2.5H11l-5.5 4v-4A2.5 2.5 0 0 1 3 15.5z"/></svg>`,
  sparkles: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 3l1.7 5.3L17 10l-5.3 1.7L10 17l-1.7-5.3L3 10l5.3-1.7zM18.5 14l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9z"/></svg>`,
  folder: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.5 6.5A2.5 2.5 0 0 1 5 4h4.3l2 2.2H19a2.5 2.5 0 0 1 2.5 2.5v9.3A2.5 2.5 0 0 1 19 20.5H5A2.5 2.5 0 0 1 2.5 18z"/></svg>`,
  doc: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="M6 2.5h8l5 5V21a.5.5 0 0 1-.5.5h-12A.5.5 0 0 1 6 21z"/><path d="M14 2.5V8h5M9 13h7M9 17h7" stroke-linecap="round"/></svg>`,
  ellipsis: `<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>`,
  car: `<svg viewBox="0 0 28 22" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 12l2.6-6.4A3 3 0 0 1 9.4 3.7h9.2a3 3 0 0 1 2.8 1.9L24 12"/><rect x="2.5" y="11.5" width="23" height="6.5" rx="2.5"/><path d="M5.5 18v2.3M22.5 18v2.3"/></svg>`,
  signal: `<svg viewBox="0 0 20 12" fill="currentColor"><rect x="0" y="8" width="3.4" height="4" rx="1"/><rect x="5.4" y="5.5" width="3.4" height="6.5" rx="1"/><rect x="10.8" y="2.8" width="3.4" height="9.2" rx="1"/><rect x="16.2" y="0" width="3.4" height="12" rx="1"/></svg>`,
  wifi: `<svg viewBox="0 0 18 13" fill="currentColor"><path d="M9 2.3c2.6 0 5 1 6.8 2.7l1.2-1.3A11.4 11.4 0 0 0 9 .5 11.4 11.4 0 0 0 1 3.7L2.2 5A9.7 9.7 0 0 1 9 2.3zm0 3.6c1.6 0 3.1.6 4.3 1.6l1.2-1.3A8.1 8.1 0 0 0 9 4.1a8.1 8.1 0 0 0-5.5 2.1l1.2 1.3c1.2-1 2.7-1.6 4.3-1.6zm0 3.6c.7 0 1.3.2 1.8.6L9 12.4 7.2 10.1c.5-.4 1.1-.6 1.8-.6z"/></svg>`,
  battery: `<svg viewBox="0 0 28 13"><rect x=".6" y=".6" width="23.6" height="11.8" rx="3.8" fill="none" stroke="currentColor" stroke-opacity=".4" stroke-width="1.1"/><rect x="2.4" y="2.4" width="20" height="8.2" rx="2.3" fill="currentColor"/><path d="M25.8 4.4v4.2c.9-.3 1.5-1.2 1.5-2.1s-.6-1.8-1.5-2.1z" fill="currentColor" fill-opacity=".45"/></svg>`,
};

// sym("name") → a sized icon; sym("<img…>") or sym("<svg…>") wraps raw markup,
// which is how config.js passes bundled brand or provider logos.
// Unknown icon names are collected and fail the manifest instead of rendering as text.
const KIT_ERRORS = [];
const sym = (k) => {
  if (!I[k] && !String(k).trim().startsWith("<")) KIT_ERRORS.push(`unknown icon "${k}" (use a name from I in kit.js or raw <img>/<svg> markup)`);
  return `<span class="sym">${I[k] || (String(k).startsWith("<") ? k : "")}</span>`;
};
const esc = (s) => String(s);

// ---------- iOS primitives ----------
const ui = {
  screen: (body, { bg = "white", dark = false, w = 402, h = 874 } = {}) =>
    `<div class="screen ${bg}${dark ? " dark" : ""}" style="width:${w}px;height:${h}px">${body}</div>`,
  statusBar: ({ onDark = false, pad = false } = {}) =>
    `<div class="statusbar${pad ? " pad" : ""}${onDark ? " on-dark" : ""}"><span>9:41</span><span class="sb-right">${sym("signal")}${sym("wifi")}${sym("battery")}</span></div>`,
  homeIndicator: () => `<div class="home-ind"></div>`,
  navBar: ({ title = "", left = "", right = "" } = {}) =>
    `<div class="navbar"><span class="nb-side">${left}</span><span class="title">${title}</span><span class="nb-side right">${right}</span></div>`,
  largeTitle: (t) => `<h1 class="large-title">${t}</h1>`,
  section: (t) => `<div class="sec-head">${t}</div>`,
  footnote: (t) => `<div class="foot-note">${t}</div>`,
  // accessory: "chevron" | "check" | "toggle-on" | "toggle-off" | "none" | raw HTML
  row: ({ icon, iconBg, title, sub, value, accessory = "chevron" } = {}) => {
    const acc = { chevron: `<span class="row-chev">${I.chevronRight}</span>`, check: `<span class="row-check">${I.check}</span>`,
      "toggle-on": `<span class="toggle on"></span>`, "toggle-off": `<span class="toggle"></span>`, none: "" }[accessory] ?? accessory;
    const ic = icon ? `<span class="row-icon${iconBg ? "" : " plain"}" style="${iconBg ? `background:${iconBg}` : ""}">${sym(icon)}</span>` : "";
    return `<div class="row">${ic}<div class="row-text"><div class="row-title">${title}</div>${sub ? `<div class="row-sub">${sub}</div>` : ""}</div>${value ? `<span class="row-value">${value}</span>` : ""}${acc}</div>`;
  },
  list: (rows, { icons = false } = {}) => `<div class="list${icons ? " with-icons" : ""}">${rows.join("")}</div>`,
  search: (placeholder = "Search") => `<div class="search">${sym("search")}<span>${placeholder}</span></div>`,
  chips: (items, active = 0) => `<div class="chips">${items.map((c, i) =>
    `<span class="chip${i === active ? " on" : ""}">${c.icon ? sym(c.icon) : ""}${c.label ?? c}</span>`).join("")}</div>`,
  button: (label, style = "filled") => `<div class="btn ${style}">${label}</div>`,
  badge: (text, fg = "#2f9e44", bg = "#dff2df") => `<span class="badge" style="color:${fg};background:${bg}">${text}</span>`,
  bubble: (role, html, meta = "") => `<div class="msg ${role}"><div class="bubble">${html}</div>${meta ? `<div class="meta">${meta}</div>` : ""}</div>`,
  messages: (items) => `<div class="msgs">${items.join("")}</div>`,
  composer: (placeholder = "Message") => `<div class="composer"><span class="field">${placeholder}</span><span class="send">${I.arrowUpCircle}</span></div>`,
  tabBar: (items, active = 0) => `<div class="tabbar">${items.map((t, i) =>
    `<span class="tab${i === active ? " on" : ""}">${sym(t.icon)}${t.label}</span>`).join("")}</div>`,
  card: (html, style = "") => `<div class="card" style="${style}">${html}</div>`,
  stat: (value, label) => `<div class="stat-label">${label}</div><div class="stat">${value}</div>`,
  grid2: (cards) => `<div class="grid2">${cards.join("")}</div>`,
  // A real capture fills the whole screen; it carries its own status bar.
  capture: (src) => `<img class="capture" src="${src}" alt="">`,
  split: (sidebar, detail) => `<div class="split"><div class="sidebar">${sidebar}</div><div class="detail">${detail}</div></div>`,
  sideItem: (label, icon, on = false) => `<div class="side-item${on ? " on" : ""}">${sym(icon)}${label}</div>`,
};

// ---------- macOS primitives (content measured in pt, 1 CSS px = 1 pt) ----------
const macui = {
  window: ({ sidebar = "", title = "", tools = [], content = "", dark = false, w = 1200, h = 750 } = {}) =>
    `<div class="mac${dark ? " dark" : ""}" style="width:${w}px;height:${h}px">
      <div class="lights"><i></i><i></i><i></i></div>
      <div class="mac-body">${sidebar ? `<aside class="mac-side">${sidebar}</aside>` : ""}
        <main class="mac-main"><div class="mac-toolbar"${sidebar ? "" : ' style="padding-left:92px"'}><span class="t">${title}</span><span class="spacer"></span>${tools.map(sym).join("")}</div>
        <div class="mac-content">${content}</div></main></div></div>`,
  group: (label) => `<div class="group">${label}</div>`,
  item: (label, icon, on = false) => `<div class="item${on ? " on" : ""}">${sym(icon)}${label}</div>`,
  table: (headers, rows, selected = -1) => `<table class="mac-table"><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr>${rows.map((r, i) =>
    `<tr${i === selected ? ' class="on"' : ""}>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</table>`,
};

// ---------- Devices ----------
// Native point sizes: iPhone 17 Pro 402×874 (corner 55), iPad Pro 13" 1032×1376 (corner 18).
const DEVICE = {
  iphone: { w: 402, h: 874, corner: 55, bezel: 14, island: true },
  ipad: { w: 1032, h: 1376, corner: 18, bezel: 22, island: false },
};

function device(platform, screenHTML, { scale, left, top, cls = "" }) {
  if (platform === "mac") {
    const w = 1200, h = 750;
    return `<div class="macwin ${cls}" style="left:${left}px;top:${top}px;width:${w * scale}px;height:${h * scale}px">
      <div class="screen-scale" style="width:${w}px;height:${h}px;transform:scale(${scale})">${screenHTML}</div></div>`;
  }
  const d = DEVICE[platform], bz = d.bezel * scale, inner = d.corner * scale;
  const W = d.w * scale + bz * 2, H = d.h * scale + bz * 2;
  // iPhone: Dynamic Island inside the screen. iPad: camera dot centered in the top bezel.
  const island = d.island
    ? `<div class="island" style="top:${11 * scale}px;width:${124 * scale}px;height:${36 * scale}px;margin-left:${-62 * scale}px"></div>` : "";
  const camera = d.island ? "" : `<div class="camera" style="top:${bz / 2 - 4}px"></div>`;
  return `<div class="device ${cls}" style="--bz:${bz}px;--inner:${inner}px;--outer:${inner + bz}px;left:${left}px;top:${top}px;width:${W}px;height:${H}px">
    <div class="device-screen"><div class="screen-scale" style="width:${d.w}px;height:${d.h}px;transform:scale(${scale})">${screenHTML}</div>${island}</div>${camera}</div>`;
}
// Rendered width/height of a device at a given scale (used to center it).
function deviceSize(platform, scale) {
  if (platform === "mac") return { w: 1200 * scale, h: 750 * scale };
  const d = DEVICE[platform];
  return { w: (d.w + d.bezel * 2) * scale, h: (d.h + d.bezel * 2) * scale };
}

// Brand motif: arcs radiating from the hero device. Use on wide stages only;
// on narrow portrait frames the arcs show as stray slivers at the edges.
function arcs(cx, cy, radii, W, H, color) {
  return `<svg class="arcs" viewBox="0 0 ${W} ${H}">${radii.map((r, i) => {
    const a = 42 * Math.PI / 180, dx = r * Math.cos(a), dy = r * Math.sin(a);
    const op = [0.22, 0.13, 0.07][i] ?? 0.05, sw = Math.max(3, 9 - i * 2);
    const p = (s) => `<path d="M ${cx + s * dx} ${cy - dy} A ${r} ${r} 0 0 ${s > 0 ? 1 : 0} ${cx + s * dx} ${cy + dy}" stroke="${color}" stroke-opacity="${op}" stroke-width="${sw}" stroke-linecap="round" fill="none"/>`;
    return p(1) + p(-1);
  }).join("")}</svg>`;
}

// ---------- Layouts ----------
// Stage widths in CSS px per platform; render.py supplies the height and zoom.
const STAGE_W = { iphone: 440, ipad: 1032, mac: 1440 };
// Caption and device placement per platform, tuned so text and device never overlap.
const LAYOUT = {
  iphone: { capTop: 54, h1: 41, sub: 16, subGap: 12, subMax: 340, devTop: 236, scale: 0.78, calloutW: 340, calloutTop: 806 },
  ipad: { capTop: 70, h1: 66, sub: 25, subGap: 16, subMax: 760, devTop: 300, scale: 0.72, calloutW: 460, calloutTop: 1150 },
  mac: { capTop: 58, h1: 54, sub: 21, subGap: 12, subMax: 900, devTop: 236, scale: 0.84, calloutW: 420, calloutTop: 700 },
};

function callout(c, top, width, stageW) {
  return `<div class="callout" style="top:${top}px;width:${width}px;left:${(stageW - width) / 2}px"><span class="ci">${sym(c.icon)}</span><div><b>${c.title}</b><span class="t">${c.text}</span></div></div>`;
}

function renderFrame(cfg, frame, platform, stageH) {
  const L = LAYOUT[platform], W = STAGE_W[platform];
  const size = deviceSize(platform, L.scale);
  const screen = frame.screens[platform]();
  const showCallout = frame.callout && (!frame.callout.platforms || frame.callout.platforms.includes(platform));
  return `<section class="stage${frame.dark ? " dark" : ""}" style="width:${W}px;height:${stageH}px">
    <div class="cap" style="top:${L.capTop}px;padding:0 ${Math.round(W * 0.06)}px">
      <h1 style="font-size:${L.h1}px">${frame.headline}</h1>
      ${frame.sub ? `<p style="font-size:${L.sub}px;margin-top:${L.subGap}px;max-width:${L.subMax}px">${frame.sub}</p>` : ""}
    </div>
    ${device(platform, screen, { scale: L.scale, left: (W - size.w) / 2, top: L.devTop })}
    ${showCallout ? callout(frame.callout, L.calloutTop, L.calloutW, W) : ""}
  </section>`;
}

// Creative assets: one idea, focal point centered so device crops keep it.
const CREATIVE = {
  header: { w: 1920, h: 823, capTop: 70, h1: 68, sub: 24, devTop: 250, hero: 0.86, side: 0.74, dx: 330, dy: 70 },
  search: { w: 1920, h: 1280, capTop: 92, h1: 84, sub: 28, devTop: 336, hero: 1.04, side: 0.9, dx: 400, dy: 84 },
  universal: { w: 2622, h: 1475, capTop: 110, h1: 96, sub: 32, devTop: 372, hero: 1.2, side: 1.02, dx: 470, dy: 96 },
};
// A Mac or iPad hero is larger than a phone in points; normalize to phone height.
const HERO_NORM = { iphone: 1, ipad: 874 / 1376 * 1.25, mac: 874 / 750 * 0.85 };

function renderCreative(cfg, kind) {
  const C = CREATIVE[kind], cr = cfg.creatives, frames = Object.fromEntries(cfg.frames.map((f) => [f.id, f]));
  const pick = (ref, s, dx, dy, cls) => {
    const f = frames[ref.frame];
    if (!f || !f.screens[ref.platform]) throw new Error(`creatives: frame "${ref.frame}" has no ${ref.platform} screen`);
    const scale = s * HERO_NORM[ref.platform], sz = deviceSize(ref.platform, scale);
    return { html: device(ref.platform, f.screens[ref.platform](), { scale, left: C.w / 2 - sz.w / 2 + dx, top: C.devTop + dy, cls }), sz };
  };
  const hero = pick(cr.hero, C.hero, 0, 0, "");
  const sides = (cr.sides || []).slice(0, 2).map((ref, i) => pick(ref, C.side, i === 0 ? -C.dx : C.dx, C.dy, "side").html);
  const cy = C.devTop + hero.sz.h / 2, r0 = C.dx + 330 * C.side;
  const headline = (kind === "search" && cr.searchHeadline) || cr.headline;
  const sub = kind === "search" ? (cr.searchSub ?? "") : (cr.sub ?? "");
  return `<section class="stage" style="width:${C.w}px;height:${C.h}px;--glow:${cfg.brand.glow}">
    ${arcs(C.w / 2, cy, [r0, r0 + 90 * C.side, r0 + 190 * C.side], C.w, C.h, cfg.brand.brand)}
    <div class="cap" style="top:${C.capTop}px"><h1 style="font-size:${C.h1}px">${headline}</h1>${sub ? `<p style="font-size:${C.sub}px;margin-top:14px">${sub}</p>` : ""}</div>
    ${sides.join("")}${hero.html}
  </section>`;
}

// ---------- Boot ----------
function applyBrand(cfg) {
  const b = cfg.brand, r = document.documentElement.style;
  const map = { brand: "--brand", brandInk: "--brand-ink", ink: "--ink", muted: "--muted", canvas1: "--canvas-1", canvas2: "--canvas-2", glow: "--glow",
    darkCanvas1: "--dark-1", darkCanvas2: "--dark-2", darkInk: "--dark-ink", darkMuted: "--dark-muted", darkAccent: "--dark-accent" };
  for (const [k, v] of Object.entries(map)) if (b[k]) r.setProperty(v, b[k]);
  const f = cfg.fonts && cfg.fonts.display;
  if (f) {
    const face = document.createElement("style");
    face.textContent = `@font-face{font-family:"Display";src:url(${f.file}) format("woff2");font-weight:${f.weight || "100 900"};font-display:block}`;
    document.head.appendChild(face);
    r.setProperty("--display", `"Display", ${f.fallback || "system-ui, sans-serif"}`);
  }
  // uiTint recolors in-screen accents; css carries app-specific screen styles.
  const extra = document.createElement("style");
  extra.textContent = (cfg.uiTint ? `.screen{--blue:${cfg.uiTint}}` : "") + (cfg.css || "");
  document.head.appendChild(extra);
}

// ?manifest=1 → JSON for render.py; ?frame=ID&cls=iphone-6.3&h=874&zoom=… → one
// screenshot; ?creative=header|search|universal → one creative; no query → contact sheet.
async function renderFromQuery(cfg) {
  applyBrand(cfg);
  const q = new URLSearchParams(location.search), root = document.getElementById("root");
  if (q.get("manifest")) {
    // Build every screen and creative once, into the page, so a broken builder,
    // an unknown icon or a missing image fails here with its frame id instead
    // of rendering a blank or broken PNG.
    const errors = [], html = [];
    for (const f of cfg.frames) for (const p of cfg.platforms) {
      if (!f.screens[p]) continue;
      KIT_ERRORS.length = 0;
      try { html.push(renderFrame(cfg, f, p, 1000)); } catch (e) { errors.push(`frame ${f.id} (${p}): ${e.message}`); }
      errors.push(...KIT_ERRORS.map((m) => `frame ${f.id} (${p}): ${m}`));
    }
    const kinds = cfg.creatives?.enabled ? (cfg.creatives.kinds || Object.keys(CREATIVE)) : [];
    for (const k of kinds.filter((x) => !CREATIVE[x])) errors.push(`creatives.kinds: unknown kind "${k}" (use header, search, universal)`);
    for (const k of kinds.filter((x) => CREATIVE[x])) {
      try { html.push(renderCreative(cfg, k)); } catch (e) { errors.push(`creative ${k}: ${e.message}`); }
    }
    root.innerHTML = html.join("");
    await Promise.all([...root.querySelectorAll("img")].map((img) => img.complete ? null :
      new Promise((ok) => { img.onload = img.onerror = ok; })));
    for (const img of root.querySelectorAll("img")) {
      if (!img.naturalWidth) errors.push(`image not found: ${img.getAttribute("src")} (paths are relative to src/)`);
    }
    await document.fonts.ready;
    const fontOk = !cfg.fonts?.display || document.fonts.check(`700 40px "Display"`);
    // Caption color pairs render.py checks: headline (large text, 3:1) and
    // supporting line (4.5:1) on both canvas stops, light and dark.
    const b = cfg.brand, pairs = [];
    for (const bg of [b.canvas1, b.canvas2]) pairs.push([b.ink, bg, 3], [b.brandInk, bg, 3], [b.muted, bg, 4.5]);
    if (cfg.frames.some((f) => f.dark)) for (const bg of [b.darkCanvas1, b.darkCanvas2]) pairs.push([b.darkInk, bg, 3], [b.darkAccent, bg, 3], [b.darkMuted, bg, 4.5]);
    root.textContent = JSON.stringify({
      app: cfg.app, version: cfg.version, platforms: cfg.platforms, fontOk, errors: [...new Set(errors)],
      contrast: pairs.map(([fg, bg, min]) => ({ fg, bg, min })),
      frames: cfg.frames.map((f) => ({ id: f.id, platforms: cfg.platforms.filter((p) => f.screens[p]) })),
      creatives: kinds.filter((x) => CREATIVE[x]),
    });
    root.id = "manifest";
    return;
  }
  const zoom = +q.get("zoom") || 1;
  if (zoom !== 1) document.documentElement.style.zoom = zoom;
  if (q.get("frame")) {
    const f = cfg.frames.find((x) => x.id === q.get("frame")), platform = (q.get("cls") || "iphone").split("-")[0];
    root.innerHTML = renderFrame(cfg, f, platform, (+q.get("h") || 956) / zoom);
  } else if (q.get("creative")) {
    root.innerHTML = renderCreative(cfg, q.get("creative"));
  } else {
    root.style.cssText = "display:flex;flex-wrap:wrap;gap:24px;padding:24px;align-items:flex-start";
    root.innerHTML = cfg.platforms.flatMap((p) => cfg.frames.filter((f) => f.screens[p]).map((f) =>
      `<div style="zoom:${p === "iphone" ? 0.6 : 0.3}">${renderFrame(cfg, f, p, p === "iphone" ? 956 : p === "ipad" ? 1376 : 900)}</div>`)).join("");
  }
}
