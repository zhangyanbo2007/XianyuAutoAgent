"""Generate professional data charts using matplotlib."""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

# --- Style Configuration ---
BG_COLOR = "#0a0a0f"
PANEL_COLOR = "#111827"
ACCENT_BLUE = "#38bdf8"
ACCENT_PINK = "#f472b6"
ACCENT_GREEN = "#4ade80"
ACCENT_PURPLE = "#a78bfa"
ACCENT_ORANGE = "#fb923c"
ACCENT_RED = "#f87171"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#1e293b"

# Find Chinese font
def _get_chinese_font():
    font_paths = [
        os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf"),
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return fm.FontProperties(fname=path)
    return fm.FontProperties()

FONT_PROP = _get_chinese_font()

def _setup_style():
    plt.rcParams.update({
        'figure.facecolor': BG_COLOR,
        'axes.facecolor': PANEL_COLOR,
        'axes.edgecolor': GRID_COLOR,
        'axes.labelcolor': TEXT_COLOR,
        'text.color': TEXT_COLOR,
        'xtick.color': TEXT_COLOR,
        'ytick.color': TEXT_COLOR,
        'grid.color': GRID_COLOR,
        'grid.alpha': 0.3,
        'font.family': 'sans-serif',
        'figure.dpi': 150,
        'axes.linewidth': 1.5,
        'patch.linewidth': 1.5,
        'lines.linewidth': 3,
        'lines.markersize': 10,
    })

_setup_style()


def bar_chart(title: str, categories: list, values: list, colors: list = None,
              ylabel: str = "", subtitle: str = "", output_path: str = None) -> str:
    """Create a professional bar chart with modern styling."""
    if colors is None:
        colors = [ACCENT_BLUE, ACCENT_PINK, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE][:len(categories)]

    fig, ax = plt.subplots(figsize=(16, 9))

    # Create bars with rounded corners effect
    bars = ax.bar(categories, values, color=colors, width=0.6, edgecolor='none', zorder=3,
                  alpha=0.9)

    # Add glow effect to bars
    for bar, color in zip(bars, colors):
        # Add subtle shadow
        bar.set_edgecolor(color)
        bar.set_linewidth(2)

    # Add value labels on bars with better styling
    for bar, val in zip(bars, values):
        label = f'{val:.1f}%' if isinstance(val, float) and val <= 100 else f'{val:.0f}'
        # Add background rectangle behind text
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                label, ha='center', va='bottom', fontsize=18, fontweight='bold', color='white',
                fontproperties=FONT_PROP,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.8, edgecolor='none'))

    ax.set_title(title, fontsize=28, fontweight='bold', pad=25, fontproperties=FONT_PROP,
                 color='white')
    if subtitle:
        ax.text(0.5, 1.02, subtitle, transform=ax.transAxes, ha='center', fontsize=14,
                color='#94a3b8', fontproperties=FONT_PROP)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=16, fontproperties=FONT_PROP, color='#94a3b8')

    # Set x-axis labels
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontproperties=FONT_PROP, fontsize=14, color='white')

    # Style grid
    ax.grid(axis='y', alpha=0.15, zorder=0, linestyle='--')
    ax.set_axisbelow(True)

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#334155')
    ax.spines['bottom'].set_color('#334155')

    # Set y limit with padding
    ax.set_ylim(0, max(values) * 1.25)

    # Add gradient background effect
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack([gradient] * 256)
    ax.imshow(gradient.T, aspect='auto', cmap=plt.cm.Greys_r, alpha=0.03,
              extent=[ax.get_xlim()[0], ax.get_xlim()[1], ax.get_ylim()[0], ax.get_ylim()[1]],
              zorder=0)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', facecolor=BG_COLOR, dpi=150)
    plt.close(fig)
    return output_path


def grouped_bar_chart(title: str, categories: list, groups: dict, colors: dict = None,
                      ylabel: str = "", output_path: str = None) -> str:
    """Create a grouped bar chart for comparing multiple series."""
    if colors is None:
        color_list = [ACCENT_BLUE, ACCENT_PINK, ACCENT_GREEN, ACCENT_PURPLE]
        colors = {k: color_list[i % len(color_list)] for i, k in enumerate(groups.keys())}

    fig, ax = plt.subplots(figsize=(16, 9))

    x = np.arange(len(categories))
    n_groups = len(groups)
    width = 0.8 / n_groups

    for i, (group_name, values) in enumerate(groups.items()):
        offset = (i - n_groups/2 + 0.5) * width
        bars = ax.bar(x + offset, values, width, label=group_name,
                      color=colors[group_name], edgecolor='none', zorder=3)

        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=11, color=TEXT_COLOR,
                    fontproperties=FONT_PROP)

    ax.set_title(title, fontsize=24, fontweight='bold', pad=20, fontproperties=FONT_PROP)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontproperties=FONT_PROP, fontsize=13)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=14, fontproperties=FONT_PROP)
    ax.legend(prop=FONT_PROP, fontsize=12, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR)
    ax.grid(axis='y', alpha=0.2, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(0, max(max(v) for v in groups.values()) * 1.25)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def line_chart(title: str, x_labels: list, series: dict, colors: dict = None,
               ylabel: str = "", xlabel: str = "", output_path: str = None) -> str:
    """Create a line chart with modern styling."""
    if colors is None:
        color_list = [ACCENT_BLUE, ACCENT_PINK, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_ORANGE]
        colors = {k: color_list[i % len(color_list)] for i, k in enumerate(series.keys())}

    fig, ax = plt.subplots(figsize=(16, 9))

    for name, values in series.items():
        color = colors[name]
        # Plot line with glow effect
        ax.plot(x_labels, values, marker='o', markersize=12, linewidth=4,
                label=name, color=color, zorder=3, alpha=0.9,
                markeredgecolor='white', markeredgewidth=2)
        # Add subtle fill under line
        ax.fill_between(x_labels, values, alpha=0.1, color=color)

    ax.set_title(title, fontsize=28, fontweight='bold', pad=25, fontproperties=FONT_PROP,
                 color='white')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=16, fontproperties=FONT_PROP, color='#94a3b8')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=16, fontproperties=FONT_PROP, color='#94a3b8')

    # Style legend
    legend = ax.legend(prop=FONT_PROP, fontsize=14, facecolor=PANEL_COLOR, edgecolor=GRID_COLOR,
                       loc='upper right', framealpha=0.9)
    for text in legend.get_texts():
        text.set_color('white')

    # Style grid
    ax.grid(alpha=0.15, zorder=0, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#334155')
    ax.spines['bottom'].set_color('#334155')

    # Set tick colors
    ax.tick_params(colors='white', labelsize=12)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', facecolor=BG_COLOR, dpi=150)
    plt.close(fig)
    return output_path


def radar_chart(title: str, categories: list, series: dict, colors: dict = None,
                output_path: str = None) -> str:
    """Create a radar/spider chart."""
    if colors is None:
        color_list = [ACCENT_BLUE, ACCENT_PINK, ACCENT_GREEN]
        colors = {k: color_list[i % len(color_list)] for i, k in enumerate(series.keys())}

    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.set_facecolor(PANEL_COLOR)
    fig.set_facecolor(BG_COLOR)

    for name, values in series.items():
        vals = values + values[:1]
        ax.plot(angles, vals, 'o-', linewidth=3, label=name, color=colors[name])
        ax.fill(angles, vals, alpha=0.15, color=colors[name])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=FONT_PROP, fontsize=13)
    ax.set_title(title, fontsize=24, fontweight='bold', pad=30, fontproperties=FONT_PROP)
    ax.legend(prop=FONT_PROP, fontsize=12, loc='upper right',
              bbox_to_anchor=(1.3, 1.1), facecolor=PANEL_COLOR, edgecolor=GRID_COLOR)
    ax.grid(color=GRID_COLOR, alpha=0.3)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def ranking_chart(title: str, models: list, scores: list, colors: list = None,
                  output_path: str = None) -> str:
    """Create a horizontal ranking chart."""
    if colors is None:
        # Gradient from gold to silver to bronze
        n = len(models)
        colors = [ACCENT_BLUE] * n
        if n > 0: colors[0] = "#fbbf24"  # gold
        if n > 1: colors[1] = "#94a3b8"  # silver
        if n > 2: colors[2] = "#fb923c"  # bronze

    fig, ax = plt.subplots(figsize=(16, 10))

    y_pos = np.arange(len(models))
    bars = ax.barh(y_pos, scores, color=colors, height=0.6, edgecolor='none', zorder=3)

    # Add score labels
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + max(scores)*0.01, bar.get_y() + bar.get_height()/2,
                f'{score:.1f}', va='center', fontsize=14, fontweight='bold', color=TEXT_COLOR,
                fontproperties=FONT_PROP)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(models, fontproperties=FONT_PROP, fontsize=14)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=24, fontweight='bold', pad=20, fontproperties=FONT_PROP)
    ax.grid(axis='x', alpha=0.2, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(0, max(scores) * 1.15)

    plt.tight_layout()
    if output_path:
        fig.savefig(output_path, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    os.makedirs("/tmp/charts_test", exist_ok=True)

    bar_chart(
        "人类 vs AI 记忆准确率",
        ["人类", "GPT-5.4", "Qwen3.5", "InternVL3.5"],
        [90, 27, 35, 15],
        [ACCENT_GREEN, ACCENT_BLUE, ACCENT_PINK, ACCENT_PURPLE],
        ylabel="准确率 (%)",
        output_path="/tmp/charts_test/bar.png",
    )
    print("Test charts saved to /tmp/charts_test/")
