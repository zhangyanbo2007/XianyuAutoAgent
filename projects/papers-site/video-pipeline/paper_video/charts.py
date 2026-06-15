"""Chart generation wrapper — bridges the storyboard ``chart`` spec to
``chart_generator_v2`` which produces dark neon PNGs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Add parent dir so we can import chart_generator_v2
_PARENT = str(Path(__file__).resolve().parents[1])
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from chart_generator_v2 import generate_chart as _gen_chart


def generate_charts(sections: list[dict[str, Any]], out_dir: str | Path) -> dict[int, str]:
    """Generate chart PNGs for sections that have a ``chart`` spec. Returns {index: path}."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    chart_paths: dict[int, str] = {}
    for i, sec in enumerate(sections):
        chart_spec = sec.get("chart")
        if not isinstance(chart_spec, dict) or not chart_spec.get("type"):
            continue
        out_path = out_dir / f"chart_{i:02d}.png"
        if out_path.exists():
            chart_paths[i] = str(out_path)
            print(f"  [chart] Slide {i:02d}: SKIP (exists)")
            continue
        print(f"  [chart] Slide {i:02d}: {chart_spec.get('type')}...", end=" ", flush=True)
        try:
            _gen_chart(chart_spec, str(out_path))
            if out_path.exists():
                chart_paths[i] = str(out_path)
                print("OK")
            else:
                print("FAILED (no output)")
        except Exception as e:
            print(f"ERROR: {e}")
    return chart_paths
