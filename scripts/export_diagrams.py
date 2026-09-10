#!/usr/bin/env python3
"""Export editable, uncompressed draw.io mxGraph diagrams to PNG with Pillow.

The XML is the authoritative source of labels, geometry, connections and colours.
This is a small documented mxGraph renderer, not a diagrams.net screenshot or its
native renderer. It supports the rectangles, text, ellipses, explicit edge points,
and basic style properties used by this project's diagrams. Unsupported shapes or
compressed draw.io files fail explicitly instead of producing misleading exports.

Usage:
    python scripts/export_diagrams.py
    python scripts/export_diagrams.py docs/diagrams/example.drawio --scale 2

Requires Pillow. No browser, network access, credentials or external service is
used. Each PNG is saved next to its .drawio source unless --output-dir is supplied.
"""

from __future__ import annotations

import argparse
import html
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc


ROOT = Path(__file__).resolve().parents[1]
PALETTE = {"none": None}


def style_map(raw: str) -> dict[str, str]:
    result = {}
    for item in raw.split(";"):
        if item:
            key, separator, value = item.partition("=")
            result[key] = value if separator else "1"
    return result


def label_text(raw: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    value = re.sub(r"</(?:div|p)>", "\n", value, flags=re.IGNORECASE)
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def colour(value: str | None, fallback: str) -> str | None:
    return PALETTE.get(value, value) if value is not None else fallback


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu")
        / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/Library/Fonts") / ("Arial Bold.ttf" if bold else "Arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError as exc:
        raise ValueError("Install a Segoe UI, DejaVu Sans or Arial TrueType font.") from exc


def wrapped_lines(text: str, face, max_width: float, draw) -> list[str]:
    lines = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            if line and draw.textlength(candidate, font=face) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if draw.textlength(line, font=face) > max_width:
            raise ValueError(f"Label contains a word wider than its cell: {line!r}")
        lines.append(line)
    return lines


def render(source: Path, destination: Path, scale: float) -> tuple[int, int]:
    root = ET.parse(source).getroot()
    if root.tag == "mxGraphModel":
        model = root
    elif root.tag == "mxfile":
        pages = root.findall("diagram")
        if len(pages) != 1:
            raise ValueError("Expected one uncompressed diagram page per .drawio file.")
        model = pages[0].find("mxGraphModel")
    else:
        model = None
    if model is None:
        raise ValueError("Expected uncompressed draw.io XML containing mxGraphModel.")

    width = int(float(model.get("pageWidth", "1760")))
    height = int(float(model.get("pageHeight", "1000")))
    canvas = Image.new("RGB", (round(width * scale), round(height * scale)), "white")
    draw = ImageDraw.Draw(canvas)
    cells = {cell.get("id"): cell for cell in model.findall("./root/mxCell")}
    boxes = {}

    def box(cell_id: str) -> tuple[float, float, float, float]:
        if cell_id in boxes:
            return boxes[cell_id]
        cell = cells[cell_id]
        geometry = cell.find("mxGeometry")
        if geometry is None:
            return (0, 0, 0, 0)
        x, y, w, h = (float(geometry.get(key, "0")) for key in ("x", "y", "width", "height"))
        parent = cells.get(cell.get("parent"))
        if parent is not None and parent.get("vertex") == "1":
            px, py, _, _ = box(parent.get("id"))
            x, y = x + px, y + py
        if x < 0 or y < 0 or x + w > width or y + h > height:
            raise ValueError(f"Cell {cell_id} lies outside the diagram page.")
        boxes[cell_id] = (x, y, w, h)
        return boxes[cell_id]

    def position(cell_id: str, style: dict, prefix: str) -> tuple[float, float]:
        x, y, w, h = box(cell_id)
        return (x + w * float(style.get(prefix + "X", ".5")),
                y + h * float(style.get(prefix + "Y", ".5")))

    def polyline(points: list[tuple[float, float]], stroke, line_width: int, dashed: bool):
        if not stroke:
            return
        if not dashed:
            draw.line(points, fill=stroke, width=line_width, joint="curve")
            return
        for start, end in zip(points, points[1:]):
            length = math.dist(start, end)
            if length == 0:
                continue
            unit = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
            for offset in range(0, math.ceil(length), max(1, round(13 * scale))):
                stop = min(length, offset + 7 * scale)
                draw.line([(start[0] + unit[0] * offset, start[1] + unit[1] * offset),
                           (start[0] + unit[0] * stop, start[1] + unit[1] * stop)],
                          fill=stroke, width=line_width)

    def text_in_box(value: str, bounds: tuple, style: dict, cell_id: str):
        text = label_text(value)
        if not text:
            return
        x, y, w, h = (coordinate * scale for coordinate in bounds)
        spacing = float(style.get("spacing", "12")) * scale
        top_padding = float(style.get("spacingTop", "0")) * scale
        face = font(max(1, round(float(style.get("fontSize", "21")) * scale)),
                    bool(int(style.get("fontStyle", "0")) & 1))
        lines = wrapped_lines(text, face, w - 2 * spacing, draw)
        ascent, descent = face.getmetrics()
        line_height = (ascent + descent) * 1.15
        total_height = len(lines) * line_height
        if total_height > h - 2 * spacing - top_padding + 1:
            raise ValueError(f"Label in {cell_id!r} does not fit vertically; enlarge its geometry.")
        valign = style.get("verticalAlign", "middle")
        yy = (y + spacing + top_padding if valign == "top" else
              y + h - spacing - total_height if valign == "bottom" else
              y + (h - total_height) / 2)
        for line in lines:
            line_width = draw.textlength(line, font=face)
            align = style.get("align", "center")
            xx = (x + spacing if align == "left" else
                  x + w - spacing - line_width if align == "right" else
                  x + (w - line_width) / 2)
            draw.text((xx, yy), line, font=face,
                      fill=colour(style.get("fontColor"), "#17243B"), anchor="lt")
            yy += line_height

    # Containers are drawn first, then edges, then foreground cells and labels.
    # Set background=1 on a containing rectangle whose connections must be visible.
    for background in (True, False):
        if not background:
            for cell_id, cell in cells.items():
                if cell.get("edge") != "1":
                    continue
                style = style_map(cell.get("style", ""))
                geometry = cell.find("mxGeometry")
                if geometry is None:
                    raise ValueError(f"Edge {cell_id} has no geometry.")
                if cell.get("source") and cell.get("target"):
                    points = [position(cell.get("source"), style, "exit")]
                    points.extend((float(point.get("x", "0")), float(point.get("y", "0")))
                                  for point in geometry.findall("./Array[@as='points']/mxPoint"))
                    points.append(position(cell.get("target"), style, "entry"))
                else:
                    start = geometry.find("mxPoint[@as='sourcePoint']")
                    end = geometry.find("mxPoint[@as='targetPoint']")
                    if start is None or end is None:
                        raise ValueError(f"Edge {cell_id} needs endpoints or source/target cells.")
                    points = [(float(p.get("x", "0")), float(p.get("y", "0"))) for p in (start, end)]
                points = [(x * scale, y * scale) for x, y in points]
                stroke = colour(style.get("strokeColor"), "#60748E")
                pen = max(1, round(float(style.get("strokeWidth", "2")) * scale))
                polyline(points, stroke, pen, style.get("dashed") == "1")
                if style.get("endArrow", "classic") != "none" and len(points) > 1:
                    a, b = points[-2:]
                    length = math.dist(a, b)
                    if length > 0:
                        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
                        tip, wing = 12 * scale, 5 * scale
                        draw.polygon([b, (b[0] - tip * ux + wing * uy, b[1] - tip * uy - wing * ux),
                                      (b[0] - tip * ux - wing * uy, b[1] - tip * uy + wing * ux)], fill=stroke)
                if cell.get("value"):
                    raise ValueError(f"Use a separate text cell for edge labels ({cell_id}).")

        for cell_id, cell in cells.items():
            if cell.get("vertex") != "1":
                continue
            style = style_map(cell.get("style", ""))
            if (style.get("background") == "1") != background:
                continue
            shape = style.get("shape", "rectangle")
            if shape not in ("rectangle", "ellipse"):
                raise ValueError(f"Unsupported shape {shape!r} in {cell_id!r}.")
            x, y, w, h = box(cell_id)
            rect = tuple(round(value * scale) for value in (x, y, x + w, y + h))
            fill = colour(style.get("fillColor"), "#FFFFFF")
            stroke = colour(style.get("strokeColor"), "#BCCADA")
            pen = max(1, round(float(style.get("strokeWidth", "1.5")) * scale))
            if style.get("text") != "1":
                if shape == "ellipse":
                    draw.ellipse(rect, fill=fill, outline=stroke, width=pen)
                elif style.get("rounded") == "1":
                    draw.rounded_rectangle(rect, radius=round(13 * scale), fill=fill, outline=stroke, width=pen)
                else:
                    draw.rectangle(rect, fill=fill, outline=stroke, width=pen)
            text_in_box(cell.get("value", ""), (x, y, w, h), style, cell_id)

    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG", dpi=(96 * scale, 96 * scale), optimize=True)
    return canvas.size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", type=Path, help=".drawio source files; defaults to docs/diagrams/*.drawio")
    parser.add_argument("--scale", type=float, default=1.5, help="Pixels per diagram coordinate (default: 1.5)")
    parser.add_argument("--output-dir", type=Path, help="Optional destination directory")
    args = parser.parse_args()
    if not 0.5 <= args.scale <= 4:
        parser.error("--scale must be between 0.5 and 4")
    sources = args.sources or sorted((ROOT / "docs" / "diagrams").glob("*.drawio"))
    if not sources:
        parser.error("No .drawio source files found")
    for source in sources:
        destination = ((args.output_dir / (source.stem + ".png"))
                       if args.output_dir else source.with_suffix(".png"))
        try:
            size = render(source, destination, args.scale)
        except (OSError, ValueError, ET.ParseError) as exc:
            print(f"ERROR: {source}: {exc}", file=sys.stderr)
            return 1
        print(f"Exported {destination} ({size[0]} x {size[1]}) from {source.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
