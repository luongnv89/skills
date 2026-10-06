#!/usr/bin/env python3
"""
Screenshot Pre-processor for UI Review

Analyzes screenshot images and produces a structured report that a UI reviewer
agent can consume without needing to process raw images at runtime.

Uses only Pillow, OpenCV, and NumPy (no OCR, no external APIs).

Usage:
    python process_screenshots.py <path1> [path2 ...] [--json] [--markdown]
    python process_screenshots.py <directory> [--recursive] [--json] [--markdown]

Output:
    --json     : Structured JSON report (default when piping)
    --markdown : Human-readable markdown report (default when writing to file)
    Both formats are always produced; --json writes to stdout, --markdown to stderr.

Dependencies:
    Pillow, opencv-python, numpy (all available in the skills environment)
"""

import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as exc:
    print(
        f"✗ Missing Python package: {exc.name or exc}. "
        "Install the dependencies with: python3 -m pip install pillow opencv-python numpy",
        file=sys.stderr,
    )
    sys.exit(2)


# ── Supported formats ────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB (well above GitHub's 10 MB limit)


# ── Data classes ─────────────────────────────────────────────────────


@dataclass
class Region:
    """A detected visual region in the screenshot."""

    label: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    description: str = ""


@dataclass
class ColorPalette:
    """Dominant colors extracted from the image."""

    primary: str  # hex
    secondary: str  # hex
    accent: str  # hex
    background: str  # hex
    text: str  # hex
    total_unique: int = 0


@dataclass
class ImageCollection:
    """Supported images collected from inputs plus paths that were not found."""

    images: list[Path]
    missing: list[str]


@dataclass
class ScreenshotAnalysis:
    """Complete analysis of a single screenshot."""

    filename: str
    file_size_bytes: int
    format: str
    width: int
    height: int
    aspect_ratio: float
    color_palette: Optional[ColorPalette] = None
    regions: list = field(default_factory=list)
    layout_summary: str = ""
    text_regions_estimated: int = 0
    interactive_elements_estimated: int = 0
    visual_density: str = "low"  # low, medium, high
    quality_score: float = 1.0
    warnings: list = field(default_factory=list)


# ── Validation ───────────────────────────────────────────────────────


def validate_image(path: Path) -> Optional[str]:
    """Return an error string if the image is invalid, else None."""
    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Not a file: {path}"
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return f"Unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        return f"File too large: {size / 1024 / 1024:.1f} MB (max {MAX_FILE_SIZE / 1024 / 1024:.0f} MB)"
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as e:
        return f"Corrupt image: {e}"
    return None


# ── Metadata extraction ─────────────────────────────────────────────


def extract_metadata(path: Path) -> dict:
    """Extract basic image metadata."""
    with Image.open(path) as img:
        w, h = img.size
        return {
            "filename": path.name,
            "file_size_bytes": path.stat().st_size,
            "format": img.format or "unknown",
            "width": w,
            "height": h,
            "aspect_ratio": round(w / h, 3) if h > 0 else 0,
            "mode": img.mode,
            "has_alpha": img.mode in ("RGBA", "LA", "PA"),
        }


# ── Color palette ────────────────────────────────────────────────────


def extract_color_palette(path: Path) -> ColorPalette:
    """Extract dominant colors using k-means-like clustering via OpenCV."""
    img = cv2.imread(str(path))
    if img is None:
        return ColorPalette(
            primary="#000000",
            secondary="#000000",
            accent="#000000",
            background="#ffffff",
            text="#000000",
        )

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pixels = img.reshape(-1, 3).astype(np.float32)

    # Use k-means to find dominant colors
    # Clamp num_colors to available pixels to avoid OpenCV k-means crash on small images
    num_colors = min(8, len(pixels))
    if num_colors == 0:
        return ColorPalette(
            primary="#000000",
            secondary="#000000",
            accent="#000000",
            background="#ffffff",
            text="#000000",
        )
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    compactness, labels, centers = cv2.kmeans(
        pixels, num_colors, None, criteria, 10, flags
    )

    # Sort by frequency
    unique, counts = np.unique(labels, return_counts=True)
    sorted_indices = np.argsort(-counts)
    centers = centers[sorted_indices]

    def rgb_to_hex(rgb):
        r, g, b = [int(c) for c in rgb]
        return f"#{r:02x}{g:02x}{b:02x}"

    total_pixels = len(pixels)
    bg_color = _find_background_color(centers, counts, total_pixels)
    text_color = _find_text_color(img)
    primary = rgb_to_hex(centers[0]) if len(centers) > 0 else "#000000"
    secondary = rgb_to_hex(centers[1]) if len(centers) > 1 else "#888888"
    accent = rgb_to_hex(centers[2]) if len(centers) > 2 else "#3498db"

    return ColorPalette(
        primary=primary,
        secondary=secondary,
        accent=accent,
        background=bg_color,
        text=text_color,
        total_unique=len(unique),
    )


def _find_background_color(centers, counts, total):
    """Heuristic: the most widespread light color is the background."""
    candidates = []
    for i, (center, count) in enumerate(zip(centers, counts)):
        brightness = np.mean(center)
        saturation = np.std(center)
        coverage = count / total
        # Background tends to be bright, low saturation, high coverage
        score = brightness * 0.4 + (255 - saturation) * 0.3 + coverage * 255 * 0.3
        candidates.append((score, i))
    candidates.sort(reverse=True)
    idx = candidates[0][1]
    r, g, b = [int(c) for c in centers[idx]]
    return f"#{r:02x}{g:02x}{b:02x}"


def _find_text_color(img):
    """Heuristic: the darkest common color is text color."""
    pixels = img.reshape(-1, 3)
    # Look at the darkest 10% of pixels
    brightnesses = np.mean(pixels, axis=1)
    dark_mask = brightnesses < np.percentile(brightnesses, 10)
    dark_pixels = pixels[dark_mask]
    if len(dark_pixels) == 0:
        return "#000000"
    dark_mean = np.mean(dark_pixels, axis=0)
    r, g, b = [int(c) for c in dark_mean]
    return f"#{r:02x}{g:02x}{b:02x}"


# ── Layout analysis ─────────────────────────────────────────────────


def analyze_layout(img_path: Path) -> tuple[list[Region], str]:
    """Detect visual regions and produce a layout summary."""
    img = cv2.imread(str(img_path))
    if img is None:
        return [], "Unable to load image"

    h, w = img.shape[:2]
    regions = []

    # 1. Detect navigation bars (horizontal bars at top)
    nav_regions = _detect_nav_bars(img, w, h)
    regions.extend(nav_regions)

    # 2. Detect buttons (rectangular colored regions with text-like contrast)
    button_regions = _detect_buttons(img, w, h)
    regions.extend(button_regions)

    # 3. Detect image/media placeholders
    image_regions = _detect_image_regions(img, w, h)
    regions.extend(image_regions)

    # 4. Detect text blocks (regions with high text-like texture)
    text_regions = _detect_text_blocks(img, w, h)
    regions.extend(text_regions)

    # 5. Detect footer (horizontal bar at bottom)
    footer_regions = _detect_footer(img, w, h)
    regions.extend(footer_regions)

    # Sort regions top-to-bottom, left-to-right
    regions.sort(key=lambda r: (r.y // 50 * 50, r.x))

    # Build layout summary
    summary = _build_layout_summary(regions, w, h)

    return regions, summary


def _detect_nav_bars(img, w, h) -> list[Region]:
    """Detect navigation bars near the top of the image."""
    regions = []
    # Analyze the top 15% of the image
    top_region = img[int(h * 0.0) : int(h * 0.15), :]
    if top_region.size == 0:
        return regions

    # Check for color consistency (nav bars tend to have uniform backgrounds)
    std_dev = np.std(top_region.astype(np.float32))
    mean_color = np.mean(top_region, axis=(0, 1))

    # If the top strip has low standard deviation, it's likely a nav bar
    if std_dev < 40:
        regions.append(
            Region(
                label="navigation_bar",
                x=0,
                y=0,
                width=w,
                height=int(h * 0.15),
                confidence=min(1.0, (40 - std_dev) / 20),
                description=f"Top navigation bar (height ~{int(h * 0.15)}px, bg: {mean_color_to_hex(mean_color)})",
            )
        )

    return regions


def _detect_buttons(img, w, h) -> list[Region]:
    """Detect button-like elements using color contrast and shape analysis."""
    regions = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold to find regions with different colors from background
    # Use adaptive threshold to find text-like and button-like regions
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    button_count = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 1000 or area > w * h * 0.3:  # Skip tiny or huge regions
            continue

        x, y, cw, ch = cv2.boundingRect(contour)

        # Buttons are typically wider than tall, with moderate size
        if 0.5 < cw / max(ch, 1) < 4 and 2000 < area < w * h * 0.1:
            # Check if this region has a distinct color from surroundings
            roi = img[y : y + ch, x : x + cw]
            roi_std = np.std(roi)
            if roi_std > 20:  # Has some color variation (text or icon inside)
                confidence = min(1.0, area / 10000)
                regions.append(
                    Region(
                        label="button",
                        x=x,
                        y=y,
                        width=cw,
                        height=ch,
                        confidence=round(confidence, 2),
                        description=f"Button-like element at ({x},{y}) {cw}x{ch}px",
                    )
                )
                button_count += 1
                if button_count >= 20:  # Cap to avoid noise
                    break

    return regions


def _detect_image_regions(img, w, h) -> list[Region]:
    """Detect potential image/media placeholders."""
    regions = []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Look for large uniform-color rectangles that could be image placeholders
    blur = cv2.GaussianBlur(gray, (15, 15), 0)
    edges = cv2.Canny(blur, 30, 80)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < w * h * 0.02 or area > w * h * 0.5:  # 2%-50% of image
            continue

        x, y, cw, ch = cv2.boundingRect(contour)
        aspect = cw / max(ch, 1)

        # Images are typically rectangular with aspect ratio between 0.5 and 3
        if 0.5 < aspect < 3 and area > 5000:
            roi = img[y : y + ch, x : x + cw]
            roi_std = np.std(roi.astype(np.float32))
            # Image placeholders tend to have moderate std dev
            if 15 < roi_std < 80:
                regions.append(
                    Region(
                        label="image_placeholder",
                        x=x,
                        y=y,
                        width=cw,
                        height=ch,
                        confidence=round(min(1.0, roi_std / 50), 2),
                        description=f"Image/media placeholder at ({x},{y}) {cw}x{ch}px",
                    )
                )

    return regions


def _detect_text_blocks(img, w, h) -> list[Region]:
    """Estimate text regions using edge density analysis."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Use Sobel operator to find text-like edges
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)

    # Divide image into grid cells and measure edge density
    grid_x, grid_y = 10, 8
    cell_w, cell_h = w // grid_x, h // grid_y
    text_block_count = 0

    for gy in range(grid_y):
        for gx in range(grid_x):
            y1, y2 = gy * cell_h, (gy + 1) * cell_h
            x1, x2 = gx * cell_w, (gx + 1) * cell_w
            cell = magnitude[y1:y2, x1:x2]
            density = np.mean(cell > 30)

            if density > 0.15:  # High edge density = likely text
                text_block_count += 1

    return [
        Region(
            label="text_region",
            x=0,
            y=0,
            width=w,
            height=h,
            confidence=0.7,
            description=f"Estimated {text_block_count} text-containing regions across the layout",
        )
    ]


def _detect_footer(img, w, h) -> list[Region]:
    """Detect footer areas at the bottom of the image."""
    regions = []
    bottom_region = img[int(h * 0.85) :, :]
    if bottom_region.size == 0:
        return regions

    std_dev = np.std(bottom_region.astype(np.float32))
    mean_color = np.mean(bottom_region, axis=(0, 1))

    if std_dev < 50:
        regions.append(
            Region(
                label="footer",
                x=0,
                y=int(h * 0.85),
                width=w,
                height=int(h * 0.15),
                confidence=min(1.0, (50 - std_dev) / 25),
                description=f"Potential footer area (height ~{int(h * 0.15)}px, bg: {mean_color_to_hex(mean_color)})",
            )
        )

    return regions


def mean_color_to_hex(mean_color) -> str:
    """Convert numpy mean color array to hex string."""
    r, g, b = [int(c) for c in mean_color]
    return f"#{r:02x}{g:02x}{b:02x}"


def _build_layout_summary(regions: list[Region], w: int, h: int) -> str:
    """Build a human-readable layout summary from detected regions."""
    if not regions:
        return "No distinct regions detected — flat layout or low contrast"

    by_label = {}
    for r in regions:
        by_label.setdefault(r.label, []).append(r)

    parts = []

    if "navigation_bar" in by_label:
        nav = by_label["navigation_bar"][0]
        parts.append(f"Navigation bar at top ({nav.width}x{nav.height}px)")

    if "button" in by_label:
        btns = by_label["button"]
        parts.append(f"{len(btns)} button-like elements detected")

    if "image_placeholder" in by_label:
        imgs = by_label["image_placeholder"]
        parts.append(f"{len(imgs)} image/media placeholder(s)")

    if "footer" in by_label:
        foot = by_label["footer"][0]
        parts.append(f"Footer area at bottom ({foot.width}x{foot.height}px)")

    if "text_region" in by_label:
        text = by_label["text_region"][0]
        parts.append(text.description)

    return (
        "; ".join(parts)
        if parts
        else "Layout detected but no standard UI elements identified"
    )


# ── Visual density ───────────────────────────────────────────────────


def estimate_visual_density(img_path: Path) -> str:
    """Estimate how visually dense the screenshot is (low/medium/high)."""
    img = cv2.imread(str(img_path))
    if img is None:
        return "unknown"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Use Laplacian variance as a proxy for visual complexity
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    if laplacian_var < 50:
        return "low"
    elif laplacian_var < 500:
        return "medium"
    else:
        return "high"


# ── Quality assessment ──────────────────────────────────────────────


def assess_quality(img_path: Path) -> tuple[float, list[str]]:
    """Assess screenshot quality and return (score, warnings)."""
    img = cv2.imread(str(img_path))
    warnings = []

    if img is None:
        return 0.0, ["Failed to load image"]

    h, w = img.shape[:2]
    score = 1.0

    # Check resolution
    if w < 320 or h < 240:
        score -= 0.3
        warnings.append(f"Low resolution: {w}x{h} — may miss detail")

    if w > 3840 or h > 2160:
        score -= 0.1
        warnings.append(
            f"Very high resolution: {w}x{h} — may be unnecessarily detailed"
        )

    # Check for blur (Laplacian variance)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var < 10:
        score -= 0.3
        warnings.append("Image appears blurry or very smooth — low detail")

    # Check for excessive compression artifacts
    # Only run on lossy formats — re-encoding a lossless PNG as JPEG always introduces artifacts
    with Image.open(img_path) as img_for_fmt:
        fmt = img_for_fmt.format or "unknown"
    if fmt.lower() in ("jpeg", "jpg", "webp"):
        _, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        original = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if original is not None:
            diff = cv2.absdiff(img, original)
            artifact_ratio = np.count_nonzero(diff) / (w * h * 3)
            if artifact_ratio > 0.05:
                score -= 0.2
                warnings.append("Significant compression artifacts detected")

    return round(max(0.0, min(1.0, score)), 2), warnings


# ── Main pipeline ───────────────────────────────────────────────────


def analyze_single(path: Path) -> ScreenshotAnalysis:
    """Run the full analysis pipeline on a single image."""
    meta = extract_metadata(path)

    palette = extract_color_palette(path)
    regions, layout_summary = analyze_layout(path)
    density = estimate_visual_density(path)
    quality, warnings = assess_quality(path)

    # Estimate counts from regions
    btn_count = sum(1 for r in regions if r.label == "button")
    # Extract text region count from the composite text_region description
    text_count = 0
    for r in regions:
        if r.label == "text_region" and r.description.startswith("Estimated"):
            parts = r.description.split()
            for i, p in enumerate(parts):
                if p == "Estimated" and i + 1 < len(parts):
                    try:
                        text_count = int(parts[i + 1])
                    except ValueError:
                        pass
                    break
    # Fallback: if parsing failed, estimate from layout_summary keyword
    if text_count == 0 and "text-containing regions" in layout_summary.lower():
        text_count = 1  # conservative estimate

    return ScreenshotAnalysis(
        filename=path.name,
        file_size_bytes=meta["file_size_bytes"],
        format=meta["format"],
        width=meta["width"],
        height=meta["height"],
        aspect_ratio=meta["aspect_ratio"],
        color_palette=palette,
        regions=regions,
        layout_summary=layout_summary,
        text_regions_estimated=text_count,
        interactive_elements_estimated=btn_count,
        visual_density=density,
        quality_score=quality,
        warnings=warnings,
    )


def collect_images(paths: list[str], recursive: bool = False) -> ImageCollection:
    """Collect supported images and report input paths that do not exist."""
    images = []
    missing = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            glob_pattern = "**/*" if recursive else "*"
            for ext in SUPPORTED_EXTENSIONS:
                images.extend(path.glob(f"{glob_pattern}{ext}"))
            for ext in {e.upper() for e in SUPPORTED_EXTENSIONS}:
                images.extend(path.glob(f"{glob_pattern}{ext}"))
        elif path.is_file():
            images.append(path)
        else:
            missing.append(str(path))
    # Deduplicate by absolute path
    seen = set()
    unique = []
    for img in images:
        abs_path = img.resolve()
        if abs_path not in seen:
            seen.add(abs_path)
            unique.append(img)
    return ImageCollection(images=sorted(unique), missing=missing)


def build_report(analyses: list[ScreenshotAnalysis]) -> dict:
    """Build the final report structure."""
    return {
        "version": "1.0.0",
        "tool": "process_screenshots",
        "image_count": len(analyses),
        "total_size_bytes": sum(a.file_size_bytes for a in analyses),
        "average_quality": round(
            sum(a.quality_score for a in analyses) / max(len(analyses), 1), 2
        ),
        "images": [asdict(a) for a in analyses],
    }


def format_markdown(report: dict) -> str:
    """Format the report as a human-readable markdown document."""
    lines = [
        "# Screenshot Analysis Report",
        "",
        f"**{report['image_count']} image(s) analyzed** | "
        f"**Total size:** {report['total_size_bytes'] / 1024:.0f} KB | "
        f"**Avg quality:** {report['average_quality']}/1.0",
        "",
        "---",
        "",
    ]

    for img in report["images"]:
        lines.append(f"## {img['filename']}")
        lines.append("")
        lines.append("| Property | Value |")
        lines.append("|---|---|")
        lines.append(f"| Format | {img['format']} |")
        lines.append(f"| Dimensions | {img['width']} × {img['height']} px |")
        lines.append(f"| Aspect Ratio | {img['aspect_ratio']} |")
        lines.append(f"| File Size | {img['file_size_bytes'] / 1024:.1f} KB |")
        lines.append(f"| Visual Density | {img['visual_density']} |")
        lines.append(f"| Quality Score | {img['quality_score']}/1.0 |")
        lines.append(f"| Text Regions | ~{img['text_regions_estimated']} |")
        lines.append(
            f"| Interactive Elements | ~{img['interactive_elements_estimated']} |"
        )
        lines.append("")

        if img.get("color_palette"):
            cp = img["color_palette"]
            lines.append("### Color Palette")
            lines.append("")
            lines.append("| Role | Color |")
            lines.append("|---|---|")
            lines.append(f"| Primary | `{cp['primary']}` |")
            lines.append(f"| Secondary | `{cp['secondary']}` |")
            lines.append(f"| Accent | `{cp['accent']}` |")
            lines.append(f"| Background | `{cp['background']}` |")
            lines.append(f"| Text | `{cp['text']}` |")
            lines.append("")

        lines.append("### Layout")
        lines.append("")
        lines.append(f"> {img['layout_summary']}")
        lines.append("")

        if img["regions"]:
            lines.append("### Detected Regions")
            lines.append("")
            lines.append("| Type | Position | Size | Confidence | Description |")
            lines.append("|---|---|---|---|---|")
            for r in img["regions"]:
                lines.append(
                    f"| {r['label']} | ({r['x']}, {r['y']}) | "
                    f"{r['width']}×{r['height']} | {r['confidence']} | {r['description']} |"
                )
            lines.append("")

        if img.get("warnings"):
            lines.append("### Warnings")
            lines.append("")
            for w in img["warnings"]:
                lines.append(f"- ⚠️ {w}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── CLI entry point ─────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Screenshot pre-processor for UI review — analyzes images and produces structured reports.",
        epilog="Example: python process_screenshots.py screenshot1.png screenshot2.png --json",
    )
    parser.add_argument(
        "paths", nargs="+", help="Image files or directories to analyze"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Recurse into directories"
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        dest="output_json",
        help="Output JSON report to stdout (default when piping)",
    )
    parser.add_argument(
        "--markdown", "-m", action="store_true", help="Output markdown report to stderr"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Write markdown report to file instead of stderr",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )

    args = parser.parse_args()

    # Collect images
    if not args.quiet:
        print(f"● Collecting images from {len(args.paths)} path(s)...", file=sys.stderr)

    collection = collect_images(args.paths, recursive=args.recursive)
    image_paths = collection.images
    missing_paths = collection.missing

    # Report missing inputs before validating any images that were found.
    for path in missing_paths:
        print(f"✗ Path not found: {path}", file=sys.stderr)

    if not image_paths:
        if not missing_paths:
            print("○ No supported images found in the supplied paths.", file=sys.stderr)
        print(
            "Pass an existing PNG, JPEG, GIF, WebP, or BMP path; add --recursive for directories.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.quiet:
        print(f"  Found {len(image_paths)} image(s)", file=sys.stderr)

    # Validate and analyze
    analyses = []
    errors = []

    for i, img_path in enumerate(image_paths, 1):
        if not args.quiet:
            print(
                f"  [{i}/{len(image_paths)}] Analyzing {img_path.name}...",
                file=sys.stderr,
            )

        error = validate_image(img_path)
        if error:
            errors.append((str(img_path), error))
            continue

        try:
            analysis = analyze_single(img_path)
            analyses.append(analysis)
        except Exception as e:
            errors.append((str(img_path), str(e)))

    if not analyses and errors:
        for path, err in errors:
            print(f"✗ {path}: {err}", file=sys.stderr)
        print(
            "Use a readable, non-empty supported image and retry; inspect the per-path errors above.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build report
    report = build_report(analyses)

    # Output
    json_output = json.dumps(report, indent=2, default=str)
    md_output = format_markdown(report)

    # Control output streams with --json / --markdown flags
    output_json = args.output_json or (not args.markdown)  # default: both
    output_md = args.markdown or (not args.output_json)  # default: both

    if output_json:
        print(json_output)

    if output_md and args.output:
        Path(args.output).write_text(md_output)
        if not args.quiet:
            print(f"  ✓ Markdown report written to {args.output}", file=sys.stderr)
    elif output_md:
        print(md_output, file=sys.stderr)

    # Summary
    if not args.quiet:
        print("\n◆ Analysis Complete", file=sys.stderr)
        print("┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄", file=sys.stderr)
        print(f"  Analyzed:    {len(analyses)} image(s)", file=sys.stderr)
        if errors:
            print(f"  Errors:      {len(errors)} (see above)", file=sys.stderr)
        print(
            f"  Total size:  {report['total_size_bytes'] / 1024:.0f} KB",
            file=sys.stderr,
        )
        print(f"  Avg quality: {report['average_quality']}/1.0", file=sys.stderr)
        print("┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄", file=sys.stderr)
        print("  Result:      DONE", file=sys.stderr)


if __name__ == "__main__":
    main()
