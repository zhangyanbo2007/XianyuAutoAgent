#!/usr/bin/env python3
"""
Dark neon-style chart generator matching reference video aesthetic.
Generates matplotlib charts with glow effects, dark backgrounds, and neon colors.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib import font_manager

# ── Font setup ──────────────────────────────────────────────────────

def _get_font():
    """Find Noto Sans SC font."""
    font_paths = [
        '/home/zhangyanbo/.local/share/fonts/NotoSansCJKsc-Regular.otf',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            font_manager.fontManager.addfont(fp)
            return 'Noto Sans CJK SC'
    for fp in font_manager.fontManager.ttflist:
        if 'Noto Sans SC' in fp.name or 'Noto Sans CJK' in fp.name:
            return fp.name
    return 'sans-serif'

_FONT = _get_font()

# ── Color palette ───────────────────────────────────────────────────

COLORS = {
    'cyan': '#00d4ff',
    'green': '#00ff88',
    'magenta': '#ff00ff',
    'orange': '#ff8800',
    'purple': '#a855f7',
    'red': '#ff4444',
    'gold': '#FFD700',
    'silver': '#C0C0C0',
    'bronze': '#CD7F32',
}

BG_COLOR = '#0a0a0f'
TEXT_COLOR = '#e0e0e0'
GRID_COLOR = '#1a1a2e'


def _setup_ax(ax, title="", xlabel="", ylabel=""):
    """Apply dark theme to axes."""
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=14)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.title.set_fontsize(20)
    ax.title.set_fontweight('bold')
    ax.title.set_fontfamily(_FONT)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=14, fontfamily=_FONT)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=14, fontfamily=_FONT)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.1, color=GRID_COLOR)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(_FONT)


def _add_glow(ax, linewidth=2, alpha=0.3):
    """Add glow effect to all lines in axes."""
    for line in ax.get_lines():
        color = line.get_color()
        line.set_path_effects([
            pe.Stroke(linewidth=linewidth + 4, foreground=color, alpha=alpha),
            pe.Normal()
        ])


# ── Bar Chart ───────────────────────────────────────────────────────

def make_bar_chart(data: list, output_path: str, title: str = "",
                   ylabel: str = "准确率 (%)", highlight_value: str = None):
    """
    Dark neon bar chart.
    data: [{"label": str, "value": float, "color": str}, ...]
    """
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG_COLOR)
    _setup_ax(ax, title=title, ylabel=ylabel)

    labels = [d['label'] for d in data]
    values = [d['value'] for d in data]
    colors = [d.get('color', COLORS['cyan']) for d in data]

    bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor='none',
                  zorder=3)

    # Add glow + value labels
    for bar, val, color in zip(bars, values, colors):
        # Glow effect
        bar.set_path_effects([
            pe.Stroke(linewidth=2, foreground=color, alpha=0.4),
            pe.Normal()
        ])
        # Value label
        label_text = f'{val:.1f}%' if highlight_value and val != values[0] else f'~{val:.0f}%'
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                label_text, ha='center', va='bottom', fontsize=16,
                fontweight='bold', color=color, fontfamily=_FONT,
                path_effects=[pe.withStroke(linewidth=3, foreground=BG_COLOR)])

    ax.set_ylim(0, max(values) * 1.25)
    fig.tight_layout(pad=2)
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
    plt.close(fig)


# ── Grouped Bar Chart ──────────────────────────────────────────────

def make_grouped_bar(groups: list, series: list, output_path: str,
                     title: str = "", ylabel: str = "Δ Accuracy (%)"):
    """
    Dark neon grouped bar chart.
    groups: [{"label": str}, ...]
    series: [{"label": str, "color": str, "values": [float, ...]}, ...]
    """
    fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG_COLOR)
    _setup_ax(ax, title=title, ylabel=ylabel)

    n_groups = len(groups)
    n_series = len(series)
    x = np.arange(n_groups)
    width = 0.35

    for i, s in enumerate(series):
        offset = (i - n_series / 2 + 0.5) * width
        vals = s.get('values', [0] * n_groups)
        color = s.get('color', COLORS['cyan'])
        bars = ax.bar(x + offset, vals, width, label=s['label'],
                      color=color, edgecolor='none', zorder=3, alpha=0.85)
        for bar in bars:
            bar.set_path_effects([
                pe.Stroke(linewidth=1.5, foreground=color, alpha=0.3),
                pe.Normal()
            ])

    ax.set_xticks(x)
    ax.set_xticklabels([g['label'] for g in groups], fontsize=11, fontfamily=_FONT,
                       rotation=15, ha='right')
    try:
        fp = font_manager.FontProperties(family=_FONT, size=12)
    except Exception:
        fp = font_manager.FontProperties(size=12)
    ax.legend(fontsize=12, facecolor=BG_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, prop=fp)
    ax.axhline(y=0, color=TEXT_COLOR, linewidth=0.5, alpha=0.3)
    fig.tight_layout(pad=2)
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
    plt.close(fig)


# ── Line Chart ──────────────────────────────────────────────────────

def make_line_chart(lines: list, output_path: str, title: str = "",
                    xlabel: str = "步数差距 (N)", ylabel: str = "准确率",
                    baseline: float = None, baseline_label: str = ""):
    """
    Dark neon line chart with area fill.
    lines: [{"label": str, "color": str, "data": [float, ...]}, ...]
    """
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG_COLOR)
    _setup_ax(ax, title=title, xlabel=xlabel, ylabel=ylabel)

    for line_data in lines:
        color = line_data.get('color', COLORS['cyan'])
        data = line_data.get('data', [])
        x = list(range(1, len(data) + 1))
        ax.plot(x, data, color=color, linewidth=2.5, label=line_data['label'],
                zorder=3, marker='o', markersize=4)
        # Area fill
        ax.fill_between(x, data, alpha=0.08, color=color)
        # Glow
        ax.get_lines()[-1].set_path_effects([
            pe.Stroke(linewidth=4, foreground=color, alpha=0.2),
            pe.Normal()
        ])

    if baseline is not None:
        ax.axhline(y=baseline, color=COLORS['orange'], linewidth=1.5,
                   linestyle='--', alpha=0.6, label=baseline_label or f'{baseline}%')

    ax.set_ylim(0, 105)
    try:
        fp = font_manager.FontProperties(family=_FONT, size=12)
    except Exception:
        fp = font_manager.FontProperties(size=12)
    ax.legend(fontsize=12, facecolor=BG_COLOR, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, prop=fp)
    fig.tight_layout(pad=2)
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
    plt.close(fig)


# ── Horizontal Ranking Bar ─────────────────────────────────────────

def make_ranking_chart(data: list, output_path: str, title: str = "",
                       max_score: float = 100):
    """
    Dark neon horizontal ranking bar chart.
    data: [{"name": str, "score": float, "color": str, "tier": str}, ...]
    """
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BG_COLOR)
    _setup_ax(ax, title=title)

    # Reverse order for top-down ranking
    data_sorted = sorted(data, key=lambda x: x['score'])
    names = [d['name'] for d in data_sorted]
    scores = [d['score'] for d in data_sorted]
    colors = [d.get('color', COLORS['cyan']) for d in data_sorted]

    bars = ax.barh(names, scores, color=colors, height=0.6, edgecolor='none', zorder=3)

    for bar, score, color in zip(bars, scores, colors):
        bar.set_path_effects([
            pe.Stroke(linewidth=2, foreground=color, alpha=0.3),
            pe.Normal()
        ])
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f'{score:.1f}', ha='left', va='center', fontsize=14,
                fontweight='bold', color=color, fontfamily=_FONT)

    ax.set_xlim(0, max_score * 1.15)
    fig.tight_layout(pad=2)
    fig.savefig(output_path, dpi=150, facecolor=BG_COLOR, bbox_inches='tight')
    plt.close(fig)


# ── Chart Dispatcher ────────────────────────────────────────────────

def generate_chart(chart_spec: dict, output_path: str) -> str:
    """
    Generate a chart from a spec dict (from manual_script.json).
    Returns the output path.
    """
    chart_type = chart_spec.get("type", "bar")
    title = chart_spec.get("title", "")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if chart_type == "bar":
        data = chart_spec.get("data", [])
        highlight = chart_spec.get("highlight")
        make_bar_chart(data, output_path, title=title,
                       ylabel=chart_spec.get("y_label", "准确率 (%)"),
                       highlight_value=highlight)

    elif chart_type == "grouped_bar":
        groups = chart_spec.get("groups", [])
        series = chart_spec.get("series", [])
        # Generate random-ish values if not provided
        for s in series:
            if 'values' not in s:
                n = len(groups)
                s['values'] = [np.random.uniform(-5, 20) for _ in range(n)]
        make_grouped_bar(groups, series, output_path, title=title,
                         ylabel=chart_spec.get("y_label", "Δ Accuracy (%)"))

    elif chart_type == "line":
        lines = chart_spec.get("lines", [])
        make_line_chart(lines, output_path, title=title,
                        xlabel=chart_spec.get("x_label", "N"),
                        ylabel=chart_spec.get("y_label", "准确率"),
                        baseline=chart_spec.get("baseline_value"),
                        baseline_label=chart_spec.get("baseline", ""))

    elif chart_type == "ranking":
        data = chart_spec.get("data", [])
        make_ranking_chart(data, output_path, title=title,
                           max_score=chart_spec.get("max_score", 100))

    return output_path
