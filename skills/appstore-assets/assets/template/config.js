// Per-app content for the asset set. Rewrite every value for the target app.
// Every example string below carries a placeholder marker (TODO followed by a
// colon); render.py refuses to run while any marker remains, so no template
// text can reach a PNG. Screens must mirror real app views: cite the source
// file above each builder, and use realistic, all-ages sample content.
window.APP_CONFIG = {
  app: "TODO: App name",
  version: "TODO: 1.0.0",
  // Only platforms the app actually ships: any of "iphone", "ipad", "mac".
  platforms: ["iphone", "ipad", "mac"],

  // Marketing canvas tokens. render.py checks every caption pair: headline
  // colors need 3:1 and the supporting line 4.5:1 on both canvas stops.
  // The dark* tokens style frames marked dark: true (brand-colored frames).
  brand: {
    brand: "#3b82f6", brandInk: "#1d5fd6", ink: "#0c1424", muted: "#4a5568",
    canvas1: "#f4f7fc", canvas2: "#e6edf8", glow: "rgba(59,130,246,.13)",
    darkCanvas1: "#1f4fc4", darkCanvas2: "#12306f", darkInk: "#ffffff", darkMuted: "#dbe5f7", darkAccent: "#ffd479",
  },
  // Accent used inside the recreated app UI (the app's tint, sampled from code or captures).
  uiTint: "#3b86f7",
  // Optional styles for custom screen HTML and polish overrides; injected after kit.css.
  css: "",
  // Caption face downloaded by fetch_font.py into fonts/; delete this key to use the system face.
  fonts: { display: { file: "fonts/display.woff2", weight: "200 800", fallback: "system-ui, sans-serif" } },

  // Story order: the first three frames carry the core promise (search shows them).
  frames: [
    {
      id: "01-hero",
      headline: "TODO: Benefit, line one.<br><em>Accent line two.</em>",
      sub: "TODO: One sentence that adds to the screen, not describes it.",
      screens: {
        // Source: TODO: path/to/ListView.swift:12
        iphone: () => ui.screen(
          ui.statusBar() + ui.largeTitle("TODO: Title") + ui.search("TODO: Search placeholder") +
          ui.list([
            ui.row({ icon: "doc", iconBg: "#34c759", title: "TODO: Row title", sub: "TODO: Row detail" }),
            ui.row({ icon: "star", iconBg: "#ff9500", title: "TODO: Row title", sub: "TODO: Row detail" }),
          ], { icons: true }) +
          ui.tabBar([{ icon: "list", label: "TODO: Tab" }, { icon: "gear", label: "TODO: Tab" }], 0) +
          ui.homeIndicator(), { bg: "grouped" }),
        // Source: TODO: path/to/SplitView.swift:30
        ipad: () => ui.screen(
          ui.statusBar({ pad: true }) + ui.split(
            ui.largeTitle("TODO: Title") + ui.sideItem("TODO: Section", "list", true) + ui.sideItem("TODO: Section", "star"),
            ui.navBar({ title: "TODO: Detail title" }) + ui.grid2([ui.card(ui.stat("TODO: 42", "TODO: Label")), ui.card(ui.stat("TODO: 7", "TODO: Label"))])),
          { bg: "grouped", w: 1032, h: 1376 }),
        // Source: TODO: path/to/MacContentView.swift:20
        mac: () => macui.window({
          title: "TODO: Window title", tools: ["search", "plus"],
          sidebar: macui.group("TODO: Group") + macui.item("TODO: Item", "list", true) + macui.item("TODO: Item", "star"),
          content: macui.table(["TODO: Column", "TODO: Column"], [["TODO: Cell", "TODO: Cell"]], 0),
        }),
      },
    },
    {
      id: "02-feature",
      dark: true,  // a brand-colored frame; remove for a light one
      headline: "TODO: Second benefit.<br><em>Accent.</em>",
      sub: "TODO: Supporting sentence.",
      // Optional floating card for one fact the screen cannot show.
      callout: { icon: "lock", title: "TODO: Short fact", text: "TODO: One supporting line.", platforms: ["iphone"] },
      screens: {
        // Source: TODO: captures/feature.png, a clean simulator capture
        iphone: () => ui.screen(ui.capture("captures/TODO: feature.png")),
      },
    },
  ],

  // Creative assets (product page header, search results, universal): set
  // enabled: true only when the user asked for them or approved them.
  creatives: {
    enabled: false,
    kinds: ["header", "search", "universal"],  // keep only the placements the user asked for
    headline: "TODO: One clear idea. <em>Accent.</em>",
    sub: "TODO: One supporting line.",
    searchHeadline: "TODO: State the obvious.<br><em>Accent.</em>",
    searchSub: "",
    hero: { platform: "iphone", frame: "01-hero" },
    sides: [{ platform: "iphone", frame: "02-feature" }],
  },
};
