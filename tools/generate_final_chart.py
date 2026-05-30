#!/usr/bin/env python3
"""Generate the LSTR benchmark summary figure for the website.

The numbers come from the current LSTR manuscript tables:
- Main simulation averages: Adroit, DexArt, RoboTwin 1.0, and overall average.
- RoboTwin 2.0 averages: demo_clean and demo_randomized protocols.

The real-robot panel is intentionally kept behind INCLUDE_REAL_ROBOT so the
website can expose it later after the physical experiments are finalized.

The figure is written as SVG first, then rendered to PNG using the project's
existing sharp dependency. This avoids requiring matplotlib.
"""

from __future__ import annotations

import html
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "public" / "image" / "final_chart.svg"
PNG_OUT = ROOT / "public" / "image" / "final_chart.png"

WIDTH = 2400
HEIGHT = 1000
MAX_Y = 100.0
INCLUDE_REAL_ROBOT = False

COLORS = {
    "dp": "#3b82f6",
    "fm": "#14b8a6",
    "maniflow": "#f59e0b",
    "act": "#8b5cf6",
    "rdt": "#6366f1",
    "pi0": "#ec4899",
    "upvla": "#22c55e",
    "rcaf": "#a855f7",
    "lstr": "#ef2f2f",
    "lstr_edge": "#b91c1c",
    "grid": "#d9dee7",
    "axis": "#64748b",
    "text": "#111827",
    "muted": "#64748b",
    "panel": "#ffffff",
    "panel_stroke": "#d6dbe5",
}

MAIN_METHODS = [
    ("dp", "DP", "NFE=10"),
    ("fm", "Flow Matching", "NFE=10"),
    ("maniflow", "ManiFlow", "NFE=10"),
    ("lstr", "LSTR", "NFE=1"),
]

MAIN_BENCHMARKS = [
    {
        "label": "Adroit",
        "values": {"dp": 38.1, "fm": 39.0, "maniflow": 74.3, "lstr": 78.3},
        "baseline": "maniflow",
    },
    {
        "label": "DexArt",
        "values": {"dp": 53.6, "fm": 53.3, "maniflow": 56.3, "lstr": 64.8},
        "baseline": "maniflow",
    },
    {
        "label": "RoboTwin 1.0",
        "values": {"dp": 28.8, "fm": 27.1, "maniflow": 46.1, "lstr": 59.8},
        "baseline": "maniflow",
    },
    {
        "label": "Overall",
        "values": {"dp": 39.4, "fm": 38.8, "maniflow": 56.5, "lstr": 65.3},
        "baseline": "maniflow",
    },
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

REAL_TRIALS = [
    {"task": "Pick & Place Random 30", "dp": (1, 20), "rcaf": (3, 20), "lstr": (5, 20)},
    {"task": "Pick & Place Random 60", "dp": (4, 20), "rcaf": (7, 20), "lstr": (10, 20), "pi0": (6, 20)},
    {"task": "Pick & Place Regular", "dp": (12, 20), "rcaf": (20, 20), "lstr": (20, 20)},
    {"task": "Stand Bottle Regular", "dp": (2, 20), "rcaf": (14, 20), "lstr": (18, 20)},
    {"task": "Drop Pen Regular", "dp": (8, 20), "rcaf": (10, 20), "lstr": (13, 20)},
]

REAL_METHODS = [
    ("dp", "Diffusion Policy"),
    ("rcaf", "DP+RCAF"),
    ("lstr", "DP+LSTR"),
]


def real_average(method: str) -> float:
    rates = [100.0 * row[method][0] / row[method][1] for row in REAL_TRIALS if method in row]
    return round(sum(rates) / len(rates), 1)


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
    size: int = 32,
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


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 2, dash: str | None = None) -> str:
    return tag(
        "line",
        {
            "x1": round(x1, 2),
            "y1": round(y1, 2),
            "x2": round(x2, 2),
            "y2": round(y2, 2),
            "stroke": stroke,
            "stroke-width": width,
            "stroke-dasharray": dash,
        },
        None,
    )


def chart_y(value: float, y: float, height: float, max_y: float = MAX_Y) -> float:
    return y + height - (value / max_y) * height


def panel(x: float, y: float, width: float, height: float, title: str, subtitle: str) -> list[str]:
    return [
        rect(x, y, width, height, COLORS["panel"], rx=26, stroke=COLORS["panel_stroke"], stroke_width=2),
        text(x + 34, y + 58, title, size=34, weight=800),
        text(x + 34, y + 98, subtitle, size=22, fill=COLORS["muted"]),
    ]


def draw_axes(x: float, y: float, width: float, height: float, tick_size: int = 21) -> list[str]:
    parts: list[str] = []
    for tick in range(0, 101, 20):
        ty = chart_y(tick, y, height)
        parts.append(line(x, ty, x + width, ty, COLORS["grid"], width=2, dash="8 8" if tick else None))
        parts.append(text(x - 18, ty + 7, str(tick), size=tick_size, fill=COLORS["muted"], anchor="end"))
    parts.append(line(x, y, x, y + height, COLORS["axis"], width=2.5))
    parts.append(line(x, y + height, x + width, y + height, COLORS["axis"], width=2.5))
    return parts


def draw_lstr_badge(x: float, y: float, delta: float, label: str | None = None) -> list[str]:
    badge = label or f"+{delta:.1f}"
    width = len(badge) * 15 + 38
    return [
        rect(x - width / 2, y - 33, width, 42, COLORS["lstr"], rx=10),
        text(x, y - 4, badge, size=24, weight=800, fill="#ffffff", anchor="middle"),
    ]


def draw_main_panel() -> list[str]:
    parts = panel(
        70,
        160,
        1330,
        730,
        "Main simulation averages",
        "Adroit, DexArt, RoboTwin 1.0, and overall average from Table 1.",
    )
    plot_x, plot_y, plot_w, plot_h = 150, 305, 1170, 455
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h))
    parts.append(
        text(
            plot_x - 82,
            plot_y + plot_h / 2,
            "Success rate (%)",
            size=24,
            weight=700,
            anchor="middle",
            extra={"transform": f"rotate(-90 {plot_x - 82} {plot_y + plot_h / 2})"},
        )
    )

    group_w = plot_w / len(MAIN_BENCHMARKS)
    bar_w = 44
    bar_gap = 14
    method_count = len(MAIN_METHODS)
    bars_w = method_count * bar_w + (method_count - 1) * bar_gap

    for index, benchmark in enumerate(MAIN_BENCHMARKS):
        group_center = plot_x + group_w * (index + 0.5)
        x0 = group_center - bars_w / 2
        values = benchmark["values"]
        for method_index, (key, _, _) in enumerate(MAIN_METHODS):
            value = values[key]
            bx = x0 + method_index * (bar_w + bar_gap)
            by = chart_y(value, plot_y, plot_h)
            is_lstr = key == "lstr"
            parts.append(
                rect(
                    bx,
                    by,
                    bar_w,
                    plot_y + plot_h - by,
                    COLORS[key],
                    rx=5,
                    stroke=COLORS["lstr_edge"] if is_lstr else None,
                    stroke_width=4,
                )
            )
            if is_lstr:
                parts.append(text(bx + bar_w / 2, by - 13, f"{value:.1f}", size=24, weight=800, fill=COLORS[key], anchor="middle"))
                delta = value - values[benchmark["baseline"]]
                parts.extend(draw_lstr_badge(bx + bar_w / 2, by - 55, delta))
        parts.append(
            text(
                group_center,
                plot_y + plot_h + 38,
                benchmark["label"],
                size=27 if benchmark["label"] == "RoboTwin 1.0" else 30,
                weight=800,
                anchor="middle",
            )
        )

    legend_items = [
        (plot_x + 28, 835, MAIN_METHODS[0]),
        (plot_x + 420, 835, MAIN_METHODS[1]),
        (plot_x + 28, 875, MAIN_METHODS[2]),
        (plot_x + 420, 875, MAIN_METHODS[3]),
    ]
    for legend_x, legend_y, (key, label, nfe) in legend_items:
        parts.append(rect(legend_x, legend_y - 22, 34, 20, COLORS[key], rx=3))
        parts.append(text(legend_x + 46, legend_y - 4, f"{label} ({nfe})", size=21, fill=COLORS["text"]))
    return parts


def draw_robotwin2_panel() -> list[str]:
    parts = panel(
        1450,
        160,
        880,
        730,
        "RoboTwin 2.0 averages",
        "Clean and randomized protocols are shown separately.",
    )
    plot_x, plot_y, plot_w, plot_h = 1525, 305, 735, 455
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h, tick_size=20))
    parts.append(text(plot_x + 225, plot_y + plot_h + 50, "demo_clean", size=28, weight=800, anchor="middle"))
    parts.append(text(plot_x + 600, plot_y + plot_h + 50, "demo_randomized", size=28, weight=800, anchor="middle"))

    clean_x0 = plot_x + 22
    bar_w = 42
    gap = 14
    for index, (key, label, value) in enumerate(ROBOTWIN2_CLEAN):
        bx = clean_x0 + index * (bar_w + gap)
        by = chart_y(value, plot_y, plot_h)
        parts.append(rect(bx, by, bar_w, plot_y + plot_h - by, COLORS[key], rx=5, stroke=COLORS["lstr_edge"] if key == "lstr" else None, stroke_width=4))
        parts.append(
            text(
                bx + bar_w / 2,
                plot_y + plot_h + 96,
                label,
                size=17,
                weight=700,
                anchor="middle",
                extra={"transform": f"rotate(-28 {bx + bar_w / 2} {plot_y + plot_h + 96})"},
            )
        )
        if key == "lstr":
            parts.append(text(bx + bar_w / 2, by - 13, f"{value:.1f}", size=23, weight=800, fill=COLORS[key], anchor="middle"))
            parts.extend(draw_lstr_badge(bx + bar_w / 2, by - 55, value - 60.7))

    rand_x0 = plot_x + 520
    rand_gap = 28
    for index, (key, label, value) in enumerate(ROBOTWIN2_RANDOMIZED):
        bx = rand_x0 + index * (bar_w + rand_gap)
        by = chart_y(value, plot_y, plot_h)
        parts.append(rect(bx, by, bar_w, plot_y + plot_h - by, COLORS[key], rx=5, stroke=COLORS["lstr_edge"] if key == "lstr" else None, stroke_width=4))
        parts.append(
            text(
                bx + bar_w / 2,
                plot_y + plot_h + 96,
                label,
                size=17,
                weight=700,
                anchor="middle",
                extra={"transform": f"rotate(-28 {bx + bar_w / 2} {plot_y + plot_h + 96})"},
            )
        )
        if key == "lstr":
            parts.append(text(bx + bar_w / 2, by - 13, f"{value:.1f}", size=23, weight=800, fill=COLORS[key], anchor="middle"))
            parts.extend(draw_lstr_badge(bx + bar_w / 2, by - 55, value - 28.5))

    return parts


def draw_real_panel() -> list[str]:
    parts = panel(
        70,
        950,
        2260,
        410,
        "SO-ARM100 real-robot deployment",
        "Average over five tasks, 20 trials per task. pi0 completed only one listed task; other runs were aborted by safety triggers.",
    )
    x0, y0 = 520, 1082
    max_w = 1310
    row_h = 78
    averages = [(key, label, real_average(key)) for key, label in REAL_METHODS]
    for row_index, (key, label, value) in enumerate(averages):
        y = y0 + row_index * row_h
        parts.append(text(120, y + 33, label, size=30, weight=800))
        parts.append(rect(x0, y, max_w, 44, "#edf2f7", rx=10))
        parts.append(rect(x0, y, max_w * value / 100.0, 44, COLORS[key], rx=10, stroke=COLORS["lstr_edge"] if key == "lstr" else None, stroke_width=3))
        parts.append(text(x0 + max_w * value / 100.0 + 24, y + 33, f"{value:.1f}%", size=30, weight=800, fill=COLORS[key]))

    note_x, note_y = 1940, 1094
    parts.append(rect(note_x, note_y, 320, 156, "#fff7ed", rx=18, stroke="#fdba74", stroke_width=2))
    parts.append(text(note_x + 28, note_y + 48, "pi0 note", size=28, weight=800, fill="#c2410c"))
    parts.append(text(note_x + 28, note_y + 88, "1/5 tasks completed", size=23, fill=COLORS["text"]))
    parts.append(text(note_x + 28, note_y + 123, "30% on valid task", size=23, fill=COLORS["text"]))
    return parts


def write_svg() -> None:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f8fafc"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
        text(70, 78, "LSTR Experimental Summary", size=48, weight=900),
        text(70, 120, "Current manuscript data: simulation averages and RoboTwin 2.0 protocols.", size=25, fill=COLORS["muted"]),
    ]
    parts.extend(draw_main_panel())
    parts.extend(draw_robotwin2_panel())
    if INCLUDE_REAL_ROBOT:
        parts.extend(draw_real_panel())
        footer_y = 1430
    else:
        footer_y = 955
    parts.append(text(70, footer_y, "All training-only LSTR components are removed at inference; LSTR uses 1 NFE in reported comparisons.", size=25, fill=COLORS["muted"]))
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
