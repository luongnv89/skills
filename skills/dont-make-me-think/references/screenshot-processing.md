# Screenshot Pre-processing Reference

When a screenshot is provided as input, run `scripts/process_screenshots.py` before visual analysis. This produces structured data so the agent doesn't need to generate image-processing code at runtime.

## Usage

```bash
# Single image
python3 scripts/process_screenshots.py screenshot.png

# Multiple images
python3 scripts/process_screenshots.py img1.png img2.png img3.png

# Directory (non-recursive)
python3 scripts/process_screenshots.py ./screenshots/

# Directory (recursive)
python3 scripts/process_screenshots.py ./screenshots/ --recursive

# Write markdown report to file
python3 scripts/process_screenshots.py screenshot.png -o report.md

# Quiet mode (suppress progress)
python3 scripts/process_screenshots.py screenshot.png --quiet
```

## Output

Two outputs are always produced:

1. **JSON to stdout** — structured data for the agent to consume programmatically
2. **Markdown to stderr** — human-readable report for quick verification

Use `-o report.md` to write markdown to a file instead of stderr.

## What the Script Extracts

### Metadata
- Filename, file size, format, dimensions, aspect ratio, color mode, alpha channel flag

### Color Palette (8-color k-means)
- Primary, secondary, accent, background, text colors (hex)
- Total unique color count

### Layout Regions (OpenCV-based heuristics)
- **Navigation bars** — horizontal uniform-color strips at top
- **Buttons** — rectangular regions with text-like contrast
- **Image placeholders** — large uniform rectangles with moderate std dev
- **Text blocks** — regions with high edge density (Sobel operator)
- **Footer** — horizontal uniform-color strips at bottom

### Visual Density
- Low / Medium / High — based on Laplacian variance

### Quality Score (0.0–1.0)
- Penalizes: low resolution, excessive resolution, blur, compression artifacts

### Warnings
- Conditions that may distort the review: blur, heavy compression, very low or excessive resolution, unreadable text regions

## How to Use the Output in a Review

1. **Parse the JSON** (stdout) to get factual data
2. **Populate the scorecard** with visual_density and quality_score
3. **Reference the color palette** when discussing design consistency
4. **Use layout regions** to pinpoint where issues are located
5. **Check warnings** for quality concerns that might affect the review

Example:
```json
{
  "images": [{
    "visual_density": "high",
    "quality_score": 0.8,
    "color_palette": { "primary": "#242223", "background": "#ab99a7" },
    "layout_summary": "Footer at bottom; 17 text regions",
    "interactive_elements_estimated": 3
  }]
}
```

This tells the reviewer: the page is dense, slightly compressed, dark-on-light theme, with ~3 interactive elements.

## Supported Formats

PNG, JPG/JPEG, GIF, WEBP, BMP, TIFF. Max file size: 50 MB.

## Dependencies

- Pillow 12.x
- OpenCV 4.x
- NumPy

All are available in the skills environment. No external APIs or OCR engines required.
