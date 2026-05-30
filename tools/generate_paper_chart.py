#!/usr/bin/env python3
"""Generate a compact paper-style LSTR benchmark figure.

The figure intentionally keeps only benchmark names, method labels, and
quantitative metrics so it can be used directly in the manuscript.
"""

from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "public" / "image" / "paper_benchmark_chart.svg"
PNG_OUT = ROOT / "public" / "image" / "paper_benchmark_chart.png"

WIDTH = 1800
HEIGHT = 1200
MAX_Y = 100.0

COLORS = {
    "dp": "#4E79A7",
    "fm": "#59A14F",
    "maniflow": "#F28E2B",
    "act": "#9C755F",
    "rdt": "#8CD17D",
    "pi0": "#B07AA1",
    "upvla": "#76B7B2",
    "lstr": "#E15759",
    "grid": "#DFE5EF",
    "axis": "#7A8798",
    "text": "#111827",
    "muted": "#4B5563",
}

MAIN_METHODS = [
    ("dp", "DP", "10"),
    ("fm", "FMP", "10"),
    ("maniflow", "ManiFlow", "10"),
    ("lstr", "LSTR", "1"),
]

MAIN_BENCHMARKS = [
    ("Adroit", {"dp": 38.1, "fm": 39.0, "maniflow": 74.3, "lstr": 78.3}),
    ("DexArt", {"dp": 53.6, "fm": 53.3, "maniflow": 56.3, "lstr": 64.8}),
    ("RoboTwin 1.0", {"dp": 28.8, "fm": 27.1, "maniflow": 46.1, "lstr": 59.8}),
    ("Overall", {"dp": 39.4, "fm": 38.8, "maniflow": 56.5, "lstr": 65.3}),
]

ROBOTWIN2_CLEAN = [
    ("dp", "DP", 39.3),
    ("act", "ACT", 41.3),
    ("rdt", "RDT", 49.1),
    ("pi0", "pi0", 53.9),
    ("upvla", "UP-VLA", 60.7),
    ("lstr", "LSTR", 72.9),
]

ROBOTWIN2_RANDOMIZED = [
    ("maniflow", "ManiFlow", 28.5),
    ("lstr", "LSTR", 37.8),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def attrs(values: dict[str, object]) -> str:
    return " ".join(f'{key}="{esc(value)}"' for key, value in values.items() if value is not None)


def tag(name: str, values: dict[str, object], content: str | None = "") -> str:
    attr_text = attrs(values)
    prefix = f"<{name} {attr_text}" if attr_text else f"<{name}"
    if content is None:
        return f"{prefix}/>"
    return f"{prefix}>{content}</{name}>"


def text(
    x: float,
    y: float,
    content: str,
    size: int = 28,
    weight: int | str = 400,
    fill: str | None = None,
    anchor: str = "start",
    extra: dict[str, object] | None = None,
) -> str:
    values: dict[str, object] = {
        "x": round(x, 2),
        "y": round(y, 2),
        "font-size": size,
        "font-weight": weight,
        "fill": fill or COLORS["text"],
        "text-anchor": anchor,
    }
    if extra:
        values.update(extra)
    return tag("text", values, esc(content))


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    rx: float = 0,
    stroke: str | None = None,
    stroke_width: float = 2,
) -> str:
    return tag(
        "rect",
        {
            "x": round(x, 2),
            "y": round(y, 2),
            "width": round(width, 2),
            "height": round(height, 2),
            "rx": rx,
            "ry": rx,
            "fill": fill,
            "stroke": stroke,
            "stroke-width": stroke_width if stroke else None,
        },
        None,
    )


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2) -> str:
    return tag(
        "line",
        {
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2),
            "stroke": stroke,
            "stroke-width": width,
        },
        None,
    )


def chart_y(value: float, y: float, height: float, max_y: float = MAX_Y) -> float:
    return y + height - (value / max_y) * height


def draw_axes(x: float, y: float, width: float, height: float) -> list[str]:
    parts: list[str] = []
    for tick in range(0, 101, 20):
        ty = chart_y(tick, y, height)
        parts.append(line(x, ty, x + width, ty, COLORS["grid"], width=2))
        parts.append(text(x - 20, ty + 8, str(tick), size=24, fill=COLORS["muted"], anchor="end"))
    parts.append(line(x, y, x, y + height, COLORS["axis"], width=2.5))
    parts.append(line(x, y + height, x + width, y + height, COLORS["axis"], width=2.5))
    return parts


def draw_y_label(x: float, y: float, label: str) -> str:
    return text(
        x,
        y,
        label,
        size=28,
        weight=700,
        fill=COLORS["muted"],
        anchor="middle",
        extra={"transform": f"rotate(-90 {x} {y})"},
    )


def draw_legend(items: list[tuple[str, str, str]], x: float, y: float) -> list[str]:
    parts: list[str] = []
    cursor = x
    for key, label, nfe in items:
        parts.append(rect(cursor, y - 22, 30, 18, COLORS[key], rx=3))
        parts.append(text(cursor + 42, y - 4, f"{label} / {nfe} NFE", size=24, fill=COLORS["text"]))
        cursor += 245 if len(label) < 5 else 320
    return parts


def draw_main_panel() -> list[str]:
    parts: list[str] = []
    x, y, width, height = 150, 145, 1580, 395
    parts.append(text(x, 68, "Main benchmarks", size=38, weight=850))
    parts.extend(draw_legend(MAIN_METHODS, x + 390, 68))
    parts.extend(draw_axes(x, y, width, height))
    parts.append(draw_y_label(55, y + height / 2, "Success rate (%)"))

    group_w = width / len(MAIN_BENCHMARKS)
    bar_w = 62
    gap = 18
    bars_w = len(MAIN_METHODS) * bar_w + (len(MAIN_METHODS) - 1) * gap

    for index, (benchmark, values) in enumerate(MAIN_BENCHMARKS):
        center = x + group_w * (index + 0.5)
        x0 = center - bars_w / 2
        for method_index, (key, _, _) in enumerate(MAIN_METHODS):
            value = values[key]
            bx = x0 + method_index * (bar_w + gap)
            by = chart_y(value, y, height)
            is_lstr = key == "lstr"
            parts.append(
                rect(
                    bx,
                    by,
                    bar_w,
                    y + height - by,
                    COLORS[key],
                    rx=4,
                    stroke="#9F1239" if is_lstr else None,
                    stroke_width=3,
                )
            )
            parts.append(text(bx + bar_w / 2, by - 10, f"{value:.1f}", size=22, weight=700, fill=COLORS[key], anchor="middle"))
        parts.append(text(center, y + height + 52, benchmark, size=29, weight=800, anchor="middle"))
    return parts


def draw_robotwin2_panel() -> list[str]:
    parts: list[str] = []
    x, y, width, height = 150, 725, 1580, 325
    parts.append(text(x, 660, "RoboTwin 2.0", size=38, weight=850))
    parts.extend(draw_axes(x, y, width, height))
    parts.append(draw_y_label(55, y + height / 2, "Success rate (%)"))

    clean_center = x + width * 0.36
    rand_center = x + width * 0.82
    clean_bar_w = 66
    clean_gap = 26
    clean_total = len(ROBOTWIN2_CLEAN) * clean_bar_w + (len(ROBOTWIN2_CLEAN) - 1) * clean_gap
    clean_x0 = clean_center - clean_total / 2

    for index, (key, label, value) in enumerate(ROBOTWIN2_CLEAN):
        bx = clean_x0 + index * (clean_bar_w + clean_gap)
        by = chart_y(value, y, height)
        is_lstr = key == "lstr"
        parts.append(
            rect(
                bx,
                by,
                clean_bar_w,
                y + height - by,
                COLORS[key],
                rx=4,
                stroke="#9F1239" if is_lstr else None,
                stroke_width=3,
            )
        )
        parts.append(text(bx + clean_bar_w / 2, by - 10, f"{value:.1f}", size=22, weight=700, fill=COLORS[key], anchor="middle"))
        parts.append(text(bx + clean_bar_w / 2, y + height + 45, label, size=23, weight=700, anchor="middle"))

    rand_bar_w = 78
    rand_gap = 54
    rand_total = len(ROBOTWIN2_RANDOMIZED) * rand_bar_w + (len(ROBOTWIN2_RANDOMIZED) - 1) * rand_gap
    rand_x0 = rand_center - rand_total / 2

    for index, (key, label, value) in enumerate(ROBOTWIN2_RANDOMIZED):
        bx = rand_x0 + index * (rand_bar_w + rand_gap)
        by = chart_y(value, y, height)
        is_lstr = key == "lstr"
        parts.append(
            rect(
                bx,
                by,
                rand_bar_w,
                y + height - by,
                COLORS[key],
                rx=4,
                stroke="#9F1239" if is_lstr else None,
                stroke_width=3,
            )
        )
        parts.append(text(bx + rand_bar_w / 2, by - 10, f"{value:.1f}", size=22, weight=700, fill=COLORS[key], anchor="middle"))
        parts.append(text(bx + rand_bar_w / 2, y + height + 45, label, size=23, weight=700, anchor="middle"))

    parts.append(text(clean_center, y + height + 92, "demo_clean", size=28, weight=800, anchor="middle"))
    parts.append(text(rand_center, y + height + 92, "demo_randomized", size=28, weight=800, anchor="middle"))
    parts.append(line(x + width * 0.64, y - 28, x + width * 0.64, y + height + 62, COLORS["grid"], width=2.5))
    return parts


def write_svg() -> None:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
    ]
    parts.extend(draw_main_panel())
    parts.extend(draw_robotwin2_panel())
    parts.append("</g></svg>")

    SVG_OUT.parent.mkdir(parents=True, exist_ok=True)
    SVG_OUT.write_text("\n".join(parts), encoding="utf-8")


def render_png() -> None:
    script = """
const sharp = require('sharp');
sharp(process.argv[1]).png().toFile(process.argv[2]).catch((error) => {
  console.error(error);
  process.exit(1);
});
"""
    subprocess.run(["node", "-e", script, str(SVG_OUT), str(PNG_OUT)], cwd=ROOT, check=True)


def main() -> int:
    write_svg()
    render_png()
    print(f"Wrote {SVG_OUT.relative_to(ROOT)}")
    print(f"Wrote {PNG_OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
