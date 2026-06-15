#!/usr/bin/env python3
"""Convert Markdown to WeChat-compatible HTML with inline CSS.

WeChat MP strips <style> tags, <script>, and external image URLs.
This tool converts markdown to HTML with all CSS applied inline,
making it suitable for pasting into the WeChat MP editor source mode.

Supports multiple theme presets (fox-orange, midnight-ink, b612-starlight,
scholar-green) and special callout syntax (> !提示, > !警告, > !信息).

Usage:
  python3 md2wechat_html.py --input <md-file> --output <html-file> [--theme fox-orange]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

# Theme presets with their aesthetic properties
THEME_PRESETS = {
    "fox-orange": {
        "name": "狐狸橙增强版",
        "accent": "#ff6b35",
        "accent_gradient": "linear-gradient(to right,#ff6b35,#ff8f5e)",
        "accent_light": "#fff3e0",
        "accent_gradient_bg": "linear-gradient(135deg,#fff8f0,#fff3e0)",
        "text_color": "#333333",
        "h2_color": "#1a1a1a",
        "strong_color": "#ff6b35",
        "link_color": "#576b95",
        "font_stack": "Georgia,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',serif",
        "divider_char": "◇ ◇ ◇",
        "divider_color": "#ff6b35",
        "dark_mode": False,
        "callout_tip_bg": "linear-gradient(135deg,#f0fff4,#dcfce7)",
        "callout_tip_border": "#22c55e",
        "callout_tip_color": "#166534",
        "callout_warning_bg": "linear-gradient(135deg,#fef2f2,#fee2e2)",
        "callout_warning_border": "#ef4444",
        "callout_warning_color": "#991b1b",
        "callout_info_bg": "linear-gradient(135deg,#eff6ff,#dbeafe)",
        "callout_info_border": "#3b82f6",
        "callout_info_color": "#1e40af",
        "blockquote_bg": "linear-gradient(135deg,#fff8f0,#fff3e0)",
        "blockquote_border": "#ff6b35",
        "blockquote_shadow": "0 1px 3px rgba(0,0,0,0.05)",
        "table_header_bg": "linear-gradient(to right,#ff6b35,#ff8f5e)",
        "table_header_color": "#ffffff",
        "fox_bg": "linear-gradient(135deg,#fff8f0,#fff3e0)",
        "fox_border": "#ff6b35",
    },
    "midnight-ink": {
        "name": "深蓝墨色",
        "accent": "#e2b714",
        "accent_gradient": "linear-gradient(to right,#e2b714,#c9a50e)",
        "accent_light": "#16213e",
        "accent_gradient_bg": "linear-gradient(135deg,#16213e,#1a1a2e)",
        "text_color": "#c8c8d0",
        "h2_color": "#e2b714",
        "strong_color": "#e2b714",
        "link_color": "#e2b714",
        "font_stack": "Georgia,'SimSun','宋体','PingFang SC',serif",
        "divider_char": "◇ ◇ ◇",
        "divider_color": "#e2b714",
        "dark_mode": True,
        "callout_tip_bg": "linear-gradient(135deg,#1a2e1a,#1a1a2e)",
        "callout_tip_border": "#4ade80",
        "callout_tip_color": "#86efac",
        "callout_warning_bg": "linear-gradient(135deg,#2e1a1a,#1a1a2e)",
        "callout_warning_border": "#f87171",
        "callout_warning_color": "#fca5a5",
        "callout_info_bg": "linear-gradient(135deg,#1a1a40,#1a1a2e)",
        "callout_info_border": "#60a5fa",
        "callout_info_color": "#93c5fd",
        "blockquote_bg": "linear-gradient(135deg,#16213e,#1a1a2e)",
        "blockquote_border": "#e2b714",
        "blockquote_shadow": "0 1px 4px rgba(0,0,0,0.2)",
        "table_header_bg": "linear-gradient(to right,#e2b714,#c9a50e)",
        "table_header_color": "#1a1a2e",
        "fox_bg": "linear-gradient(135deg,#16213e,#1a1a2e)",
        "fox_border": "#e2b714",
    },
    "b612-starlight": {
        "name": "小王子星光",
        "accent": "#ffd700",
        "accent_gradient": "linear-gradient(to right,#ffd700,#ffed4a)",
        "accent_light": "rgba(255,255,255,0.15)",
        "accent_gradient_bg": "linear-gradient(135deg,rgba(255,255,255,0.15),rgba(255,255,255,0.08))",
        "text_color": "#e0e0f0",
        "h2_color": "#ffd700",
        "strong_color": "#ffd700",
        "link_color": "#ffd700",
        "font_stack": "'KaiTi','楷体','PingFang SC','Hiragino Sans GB','Microsoft YaHei',serif",
        "divider_char": "★ ★ ★",
        "divider_color": "#ffd700",
        "dark_mode": True,
        "callout_tip_bg": "linear-gradient(135deg,rgba(74,222,128,0.2),rgba(74,222,128,0.1))",
        "callout_tip_border": "#4ade80",
        "callout_tip_color": "#86efac",
        "callout_warning_bg": "linear-gradient(135deg,rgba(248,113,113,0.2),rgba(248,113,113,0.1))",
        "callout_warning_border": "#f87171",
        "callout_warning_color": "#fca5a5",
        "callout_info_bg": "linear-gradient(135deg,rgba(96,165,250,0.2),rgba(96,165,250,0.1))",
        "callout_info_border": "#60a5fa",
        "callout_info_color": "#93c5fd",
        "blockquote_bg": "linear-gradient(135deg,rgba(255,255,255,0.15),rgba(255,255,255,0.08))",
        "blockquote_border": "#ffd700",
        "blockquote_shadow": "0 2px 6px rgba(0,0,0,0.15)",
        "table_header_bg": "linear-gradient(to right,#ffd700,#ffed4a)",
        "table_header_color": "#4a3080",
        "fox_bg": "linear-gradient(135deg,rgba(255,215,0,0.15),rgba(255,215,0,0.08))",
        "fox_border": "#ffd700",
    },
    "scholar-green": {
        "name": "学院绿",
        "accent": "#4a7c28",
        "accent_gradient": "linear-gradient(to right,#4a7c28,#2d5016)",
        "accent_light": "#f5f1e8",
        "accent_gradient_bg": "linear-gradient(135deg,#f5f1e8,#ede8d8)",
        "text_color": "#3d3d2d",
        "h2_color": "#2d5016",
        "strong_color": "#2d5016",
        "link_color": "#2d5016",
        "font_stack": "'SimSun','宋体','KaiTi','楷体','PingFang SC',serif",
        "divider_char": "◇ ◇ ◇",
        "divider_color": "#4a7c28",
        "dark_mode": False,
        "callout_tip_bg": "linear-gradient(135deg,#f0f5e0,#e8edcc)",
        "callout_tip_border": "#4ade80",
        "callout_tip_color": "#166534",
        "callout_warning_bg": "linear-gradient(135deg,#f5eee8,#ede0d8)",
        "callout_warning_border": "#c87040",
        "callout_warning_color": "#8b4513",
        "callout_info_bg": "linear-gradient(135deg,#e8f0f5,#d8e4ed)",
        "callout_info_border": "#4080b0",
        "callout_info_color": "#1e40af",
        "blockquote_bg": "linear-gradient(135deg,#f5f1e8,#ede8d8)",
        "blockquote_border": "#4a7c28",
        "blockquote_shadow": "0 1px 3px rgba(0,0,0,0.06)",
        "table_header_bg": "linear-gradient(to right,#4a7c28,#2d5016)",
        "table_header_color": "#f5f1e8",
        "fox_bg": "linear-gradient(135deg,#f0f5e8,#e8ede0)",
        "fox_border": "#4a7c28",
    },
}


def load_css_styles(css_path: str) -> dict[str, dict[str, str]]:
    """Parse a CSS file into a dict of {selector: {property: value}}.

    Only handles simple selectors (tag names, .class names).
    Ignores @rules, comments, and complex selectors.
    """
    styles: dict[str, dict[str, str]] = {}
    if not css_path or not os.path.exists(css_path):
        return styles

    with open(css_path, "r", encoding="utf-8") as f:
        css_text = f.read()

    # Remove comments
    css_text = re.sub(r"/\*.*?\*/", "", css_text)

    # Parse simple rule blocks
    for match in re.finditer(r"([^{}]+?)\s*\{([^{}]+)\}", css_text):
        selectors = match.group(1).strip().split(",")
        properties_str = match.group(2).strip()
        props: dict[str, str] = {}
        for prop_match in re.finditer(r"([\w-]+)\s*:\s*([^;]+)", properties_str):
            props[prop_match.group(1).strip()] = prop_match.group(2).strip()
        for sel in selectors:
            sel = sel.strip()
            if sel:
                styles[sel] = props

    return styles


def css_dict_to_inline(props: dict[str, str]) -> str:
    """Convert a {property: value} dict to an inline style string."""
    return "; ".join(f"{k}: {v}" for k, v in props.items())


def get_inline_style(tag: str, classes: list[str], styles: dict[str, dict[str, str]]) -> str:
    """Get inline CSS for an HTML tag based on parsed CSS styles."""
    merged: dict[str, str] = {}
    tag_key = tag.lower()
    if tag_key in styles:
        merged.update(styles[tag_key])
    for cls in classes:
        class_key = f".{cls}"
        if class_key in styles:
            merged.update(class_key in styles and styles[class_key])
    return css_dict_to_inline(merged) if merged else ""


def preprocess_callout_syntax(md_text: str) -> str:
    """Convert callout syntax in markdown before rendering.

    > !提示 content  →  <section class="tip-callout">content</section>
    > !警告 content  →  <section class="warning-callout">content</section>
    > !信息 content  →  <section class="info-callout">content</section>

    Multi-line callouts: consecutive > !type lines are grouped into one callout block.
    """
    lines = md_text.split("\n")
    result_lines = []
    callout_buffer = []
    callout_type = None

    def flush_callout():
        nonlocal callout_type, callout_buffer
        if callout_buffer and callout_type:
            content = "\n".join(callout_buffer)
            # Render the content markdown inside the callout
            md = MarkdownIt("commonmark", {"html": True}).enable("strikethrough")
            rendered = md.render(content)
            result_lines.append(f'<section class="{callout_type}">{rendered}</section>')
            callout_buffer.clear()
            callout_type = None

    for line in lines:
        # Match callout pattern: > !提示, > !警告, > !信息, > !tip, > !warning, > !info
        callout_match = re.match(r"^>\s*!(提示|tip|警告|warning|信息|info)\s+(.+)$", line)
        if callout_match:
            type_raw = callout_match.group(1).lower()
            content = callout_match.group(2)
            type_map = {"提示": "tip-callout", "tip": "tip-callout",
                        "警告": "warning-callout", "warning": "warning-callout",
                        "信息": "info-callout", "info": "info-callout"}
            detected_type = type_map.get(type_raw, "info-callout")

            # If type changed, flush previous callout
            if callout_type and callout_type != detected_type:
                flush_callout()

            callout_type = detected_type
            callout_buffer.append(content)
        elif line.startswith("> ") and callout_type:
            # Continuation line of a callout block
            callout_buffer.append(line[2:])
        else:
            # Non-callout line — flush any buffered callout
            flush_callout()
            result_lines.append(line)

    # Flush any remaining callout at end of document
    flush_callout()

    return "\n".join(result_lines)


def build_theme_inline_styles(theme: dict) -> dict[str, str]:
    """Build compact inline style strings from theme preset dict.

    Returns a dict mapping element names to their inline style strings,
    optimized for WeChat's 20KB limit.
    """
    t = theme
    dark = t["dark_mode"]

    styles = {
        "body": (
            f"max-width:100%;font-family:{t['font_stack']};font-size:15px;"
            f"line-height:2;color:{t['text_color']};padding:12px 16px;"
            f"word-break:break-word"
        ),
        # Dark themes need background on body section wrapper
        "body_bg": (
            f"background:{t['accent_gradient_bg']}" if dark else ""
        ),
        "h1": (
            f"font-size:24px;font-weight:bold;margin:35px 0 20px;"
            f"text-align:center;color:{t['h2_color']};line-height:1.4"
        ),
        "h2_accent_bar": (
            f"height:3px;background:{t['accent_gradient']};"
            f"border-radius:2px;margin:0 0 20px"
        ),
        "h2": (
            f"font-size:22px;font-weight:bold;margin:35px 0 20px;"
            f"padding-bottom:10px;color:{t['h2_color']};line-height:1.4"
        ),
        "h3": (
            f"font-size:15px;font-weight:bold;margin:25px 0 14px;"
            f"padding:6px 12px;border-left:3px solid {t['accent']};"
            f"background:linear-gradient(90deg,{t.get('accent_light', '#f5f5f5')},transparent);"
            f"color:{t['text_color']};line-height:1.4"
        ),
        "h4": (
            f"font-size:14px;font-weight:600;margin:20px 0 14px;"
            f"color:{t['text_color']}"
        ),
        "strong": f"color:{t['strong_color']}",
        "strong_decorated": (
            f"color:{t['strong_color']};text-decoration:underline;"
            f"text-decoration-color:rgba({_hex_to_rgba_dec(t['strong_color'])},0.3);"
            f"text-underline-offset:3px"
        ),
        "a": f"color:{t['link_color']}",
        "blockquote": (
            f"margin:20px 0;padding:14px 18px;"
            f"background:{t['blockquote_bg']};border-radius:8px;"
            f"border-left:3px solid {t['blockquote_border']};"
            f"color:{t['text_color']};font-size:14px;line-height:1.8;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
        "fox_commentary": (
            f"margin:16px 0;padding:12px 16px;"
            f"background:{t['fox_bg']};border-radius:8px;"
            f"border-left:3px solid {t['fox_border']};font-size:14px;"
            f"color:{t['text_color']};line-height:1.8;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
        "table": (
            f"width:100%;border-collapse:separate;border-spacing:0;"
            f"margin:15px 0;font-size:13px;border-radius:8px;"
            f"overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.08)"
        ),
        "th": (
            f"background:{t['table_header_bg']};"
            f"color:{t['table_header_color']};padding:10px 12px;"
            f"text-align:left;font-weight:bold;font-size:13px"
        ),
        "td": (
            f"border-bottom:1px solid rgba({_hex_to_rgba_dec(t['accent'])},0.15);"
            f"padding:10px 12px;text-align:left;font-size:13px;line-height:1.6;"
            f"color:{t['text_color']}"
        ),
        "pre": (
            f"background:{t['accent_gradient_bg'] if dark else '#f6f8fa'};"
            f"padding:16px;border-radius:8px;overflow-x:auto;margin:20px 0;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
        "code_inline": (
            f"background:{t['accent_light'] if dark else '#f0f0f0'};"
            f"padding:2px 6px;border-radius:4px;font-size:13px;"
            f"color:{t['strong_color']};font-family:'Menlo','Monaco','Consolas',monospace"
        ),
        "img": (
            f"max-width:100%;border-radius:6px;margin:15px 0;display:block"
        ),
        "decorative_divider": (
            f"text-align:center;margin:30px 0;color:{t['divider_color']};"
            f"font-size:12px;letter-spacing:6px"
        ),
        "tip_callout": (
            f"margin:16px 0;padding:12px 16px;"
            f"background:{t['callout_tip_bg']};border-radius:8px;"
            f"border-left:3px solid {t['callout_tip_border']};"
            f"color:{t['callout_tip_color']};font-size:14px;line-height:1.8;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
        "warning_callout": (
            f"margin:16px 0;padding:12px 16px;"
            f"background:{t['callout_warning_bg']};border-radius:8px;"
            f"border-left:3px solid {t['callout_warning_border']};"
            f"color:{t['callout_warning_color']};font-size:14px;line-height:1.8;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
        "info_callout": (
            f"margin:16px 0;padding:12px 16px;"
            f"background:{t['callout_info_bg']};border-radius:8px;"
            f"border-left:3px solid {t['callout_info_border']};"
            f"color:{t['callout_info_color']};font-size:14px;line-height:1.8;"
            f"box-shadow:{t['blockquote_shadow']}"
        ),
    }
    return styles


def _hex_to_rgba_dec(hex_color: str) -> str:
    """Convert #rrggbb to '255,107,53' format for rgba()."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"{r},{g},{b}"


def convert_markdown_to_wechat_html(
    md_text: str,
    styles: dict[str, dict[str, str]],
    feishu_url: str = "",
    theme_name: str = "fox-orange",
) -> str:
    """Convert markdown text to WeChat-compatible HTML with inline styles.

    Uses markdown-it for parsing, then applies inline CSS to each element.
    Handles special patterns like callout blocks and fox commentary.

    When theme_name is provided, uses theme preset for styling instead of
    parsed CSS styles (more consistent, gradient-aware).
    """
    # Preprocess callout syntax before markdown rendering
    md_text = preprocess_callout_syntax(md_text)

    md = MarkdownIt("commonmark", {"html": True}).enable("table").enable("strikethrough")
    html_raw = md.render(md_text)

    result = html_raw

    # Get theme preset if available
    theme = THEME_PRESETS.get(theme_name)
    if theme:
        theme_styles = build_theme_inline_styles(theme)
    else:
        # Fallback: use parsed CSS styles (legacy mode)
        theme_styles = None

    if theme_styles:
        # === Theme-based styling (new) ===

        # Body wrapper with theme background (dark themes need background)
        body_bg_extra = f";{theme_styles['body_bg']}" if theme_styles.get("body_bg") else ""
        body_inline = f"{theme_styles['body']}{body_bg_extra}"

        # h1
        result = re.sub(
            r"<h1>",
            f'<h1 style="{theme_styles["h1"]}">',
            result,
        )

        # h2 — insert accent bar before h2, and style h2 itself
        accent_bar = f'<section style="{theme_styles["h2_accent_bar"]}"></section>'
        result = re.sub(
            r"<h2(\s[^>]*)?>",
            lambda m: f'{accent_bar}<h2 style="{theme_styles["h2"]}">',
            result,
        )

        # h3, h4
        result = re.sub(r"<h3(\s[^>]*)?>", f'<h3 style="{theme_styles["h3"]}">', result)
        result = re.sub(r"<h4(\s[^>]*)?>", f'<h4 style="{theme_styles["h4"]}">', result)

        # strong — decorated with underline
        result = re.sub(r"<strong>", f'<strong style="{theme_styles["strong_decorated"]}">', result)

        # a (preserve href)
        result = re.sub(
            r'<a\s+href="([^"]*)"([^>]*)>',
            lambda m: f'<a href="{m.group(1)}" style="{theme_styles["a"]}">',
            result,
        )

        # blockquote — enhanced with gradient bg + rounded corners + shadow
        result = re.sub(r"<blockquote>", f'<blockquote style="{theme_styles["blockquote"]}">', result)

        # table, th, td
        result = re.sub(r"<table>", f'<table style="{theme_styles["table"]}">', result)
        result = re.sub(r"<th>", f'<th style="{theme_styles["th"]}">', result)
        result = re.sub(r"<td>", f'<td style="{theme_styles["td"]}">', result)

        # pre
        result = re.sub(r"<pre>", f'<pre style="{theme_styles["pre"]}">', result)

        # code (inline, not inside pre)
        result = re.sub(r"<code>", f'<code style="{theme_styles["code_inline"]}">', result)

        # img
        result = re.sub(
            r'<img\s+src="([^"]*)"([^>]*)>',
            lambda m: f'<img src="{m.group(1)}"{m.group(2)} style="{theme_styles["img"]}">',
            result,
        )

        # hr → decorative divider
        divider_content = theme["divider_char"]
        result = re.sub(
            r"<hr\s*/?>",
            f'<section style="{theme_styles["decorative_divider"]}">{divider_content}</section>',
            result,
        )

        # Fox commentary — upgrade blockquote containing 狐狸点评
        result = re.sub(
            r'<blockquote\s+style="[^"]*">\s*<p>\s*<strong\s+style="[^"]*">狐狸点评',
            f'<blockquote style="{theme_styles["fox_commentary"]}">\n<p><strong style="{theme_styles["strong"]}">狐狸点评',
            result,
        )

        # Callout blocks — apply theme styles to preprocessed callout sections
        for callout_type in ["tip-callout", "warning-callout", "info-callout"]:
            style_key = callout_type.replace("-", "_")
            if style_key in theme_styles:
                result = re.sub(
                    rf'<section\s+class="{callout_type}">',
                    f'<section style="{theme_styles[style_key]}">',
                    result,
                )
                # Remove the class attribute since we've inlined the style
                result = re.sub(
                    rf'<section\s+style="{re.escape(theme_styles[style_key])}"\s+class="{callout_type}">',
                    f'<section style="{theme_styles[style_key]}">',
                    result,
                )

        # Remove code style inside pre (pre handles it)
        result = re.sub(
            r'<pre[^>]*><code\s+style="[^"]*">',
            lambda m: m.group(0).split("<code")[0] + "<code>",
            result,
        )

        # Split label lines for mobile readability
        split_labels = ["标题：", "作者：", "链接：", "要点："]
        for label in split_labels:
            result = re.sub(
                rf'(<strong\s+style="[^"]*">{label})',
                rf"<br/>\1",
                result,
            )
        result = re.sub(r"<p><br/>", "<p>", result)

        # Wrap in body container
        result = f'<section style="{body_inline}">{result}</section>'

    else:
        # === Legacy CSS-based styling (fallback) ===
        minimal_styles = {
            "h1": "font-size:24px;font-weight:bold;margin:35px 0 20px;text-align:center;color:#1a1a1a;line-height:1.4",
            "h3": "font-size:17px;font-weight:bold;margin:28px 0 16px;color:#2d2d2d;line-height:1.4",
            "h4": "font-size:16px;font-weight:bold;margin:24px 0 10px;color:#3d3d3d",
            "pre": "background:#f6f8fa;padding:12px;border-radius:4px;margin:15px 0;font-size:13px",
            "td": "border:1px solid #ddd;padding:8px 10px;font-size:13px;line-height:1.6",
            "code": "background:#f0f0f0;padding:2px 6px;border-radius:3px;font-size:13px;color:#d14;font-family:monospace",
        }

        for tag, mini_style in minimal_styles.items():
            pattern = rf"<{tag}(\s[^>]*)?>(?!.*?</{tag}.*?<{tag})"
            def replace_minimal(m):
                existing_attrs = m.group(1) or ""
                if "style=" in existing_attrs:
                    return m.group(0)
                if existing_attrs:
                    return f"<{tag}{existing_attrs} style=\"{mini_style}\">"
                return f"<{tag} style=\"{mini_style}\">"
            result = re.sub(pattern, replace_minimal, result)

        result = re.sub(r"<h2(\s[^>]*)?>", '<h2 style="font-size:20px;margin:35px 0 20px;border-bottom:2px solid #ff6b35;padding-bottom:10px;color:#1a1a1a">', result)
        result = re.sub(r"<strong>", '<strong style="color:#ff6b35">', result)
        result = re.sub(r'<a\s+href="([^"]*)"([^>]*)>', lambda m: f'<a href="{m.group(1)}" style="color:#576b95">', result)
        result = re.sub(r"<table>", '<table style="width:100%;border-collapse:collapse;margin:15px 0;font-size:13px">', result)
        result = re.sub(r"<th>", '<th style="background:#ff6b35;color:#fff;padding:8px 10px;font-size:13px">', result)
        result = re.sub(r"<blockquote>", '<blockquote style="margin:16px 0;padding:12px 18px;background:#f8f9fa;border-left:3px solid #ff6b35;color:#666;font-size:14px;line-height:1.8">', result)
        result = re.sub(r"<hr\s*/?>", '<hr style="border:none;border-top:1px solid #e0e0e0;margin:20px 0"/>', result)
        result = re.sub(r'<img\s+src="([^"]*)"([^>]*)>', lambda m: f'<img src="{m.group(1)}"{m.group(2)} style="max-width:100%;border-radius:4px;margin:15px 0;display:block">', result)

        # Remove code style inside pre
        result = re.sub(r'<pre[^>]*><code\s+style="[^"]*">', lambda m: m.group(0).split("<code")[0] + "<code>", result)

        # Split label lines
        split_labels = ["标题：", "作者：", "链接：", "要点："]
        for label in split_labels:
            result = re.sub(rf'(<strong\s+style="[^"]*">{label})', rf"<br/>\1", result)
        result = re.sub(r"<p><br/>", "<p>", result)

        fox_style = "margin:16px 0;padding:10px 16px;background:#fff3e0;border-left:2px solid #ff6b35;font-size:14px;color:#555;line-height:1.8"
        result = re.sub(
            r'<blockquote\s+style="[^"]*">\s*<p>\s*<strong\s+style="[^"]*">狐狸点评',
            f'<blockquote style="{fox_style}">\n<p><strong style="color:#ff6b35">狐狸点评',
            result,
        )

        # Callout blocks in legacy mode — minimal styling
        callout_legacy = {
            "tip-callout": "margin:16px 0;padding:12px 16px;background:#f0fff4;border-left:3px solid #22c55e;border-radius:6px;color:#166534;font-size:14px;line-height:1.8",
            "warning-callout": "margin:16px 0;padding:12px 16px;background:#fef2f2;border-left:3px solid #ef4444;border-radius:6px;color:#991b1b;font-size:14px;line-height:1.8",
            "info-callout": "margin:16px 0;padding:12px 16px;background:#eff6ff;border-left:3px solid #3b82f6;border-radius:6px;color:#1e40af;font-size:14px;line-height:1.8",
        }
        for callout_type, callout_style in callout_legacy.items():
            result = re.sub(
                rf'<section\s+class="{callout_type}">',
                f'<section style="{callout_style}">',
                result,
            )

        body_inline = "max-width:100%;font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;font-size:15px;line-height:2;color:#333333;padding:12px 16px;word-break:break-word"
        result = f'<section style="{body_inline}">{result}</section>'

    return result


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from markdown text."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


def check_content_limits(html: str) -> tuple[bool, str]:
    """Check if HTML content meets WeChat MP limits."""
    char_count = len(html)
    size_kb = len(html.encode("utf-8")) / 1024

    warnings = []
    if char_count > 20000:
        warnings.append(f"Content exceeds 20,000 character limit ({char_count} chars)")
    if size_kb > 1000:
        warnings.append(f"Content exceeds 1MB size limit ({size_kb:.1f} KB)")

    return len(warnings) == 0, "; ".join(warnings) if warnings else ""


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to WeChat-compatible HTML with inline CSS")
    parser.add_argument("--input", required=True, help="Input markdown file path")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--style", default=None, help="CSS style file path (legacy mode, default: bundled wechat-style.css)")
    parser.add_argument("--theme", default="fox-orange",
                        choices=list(THEME_PRESETS.keys()),
                        help="Theme preset (fox-orange/midnight-ink/b612-starlight/scholar-green)")
    parser.add_argument("--strip-frontmatter", action="store_true", help="Strip YAML frontmatter from input")
    parser.add_argument("--feishu-url", default="", help="Feishu document URL to link in each section")
    parser.add_argument("--check-limits", action="store_true", help="Check WeChat content size limits and report warnings")
    parser.add_argument("--json", action="store_true", help="Output result as JSON (with metadata)")

    args = parser.parse_args()

    # Default style file (legacy mode)
    if not args.style:
        default_css = Path(__file__).parent.parent / "config" / "wechat-style.css"
        args.style = str(default_css) if default_css.exists() else None

    # Read input markdown
    with open(args.input, "r", encoding="utf-8") as f:
        md_text = f.read()

    if args.strip_frontmatter:
        md_text = strip_frontmatter(md_text)

    # Load CSS styles (used in legacy mode only, or as fallback)
    styles = load_css_styles(args.style)

    # Convert to WeChat HTML with theme preset
    html = convert_markdown_to_wechat_html(md_text, styles, feishu_url=args.feishu_url, theme_name=args.theme)

    # Check content limits
    is_valid, warning = check_content_limits(html)

    # Write output
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    if args.json:
        result = {
            "input": args.input,
            "output": args.output,
            "theme": args.theme,
            "theme_name": THEME_PRESETS[args.theme]["name"],
            "css_used": args.style,
            "char_count": len(html),
            "size_kb": round(len(html.encode("utf-8")) / 1024, 1),
            "valid": is_valid,
            "warning": warning,
        }
        print(json.dumps(result, indent=2))
    else:
        print(f"Converted: {args.input} -> {args.output}")
        print(f"  Theme: {args.theme} ({THEME_PRESETS[args.theme]['name']})")
        print(f"  Characters: {len(html)}")
        print(f"  Size: {len(html.encode('utf-8')) / 1024:.1f} KB")
        if warning:
            print(f"  WARNING: {warning}")


if __name__ == "__main__":
    main()