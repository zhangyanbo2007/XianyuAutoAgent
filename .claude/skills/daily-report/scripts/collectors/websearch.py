"""WebSearch needs collector — outputs a list of queries for Claude to supplement via WebSearch.

This collector does NOT call WebSearch directly. It produces a "needs_websearch" list
that Claude reads in Step 1b and executes with the WebSearch tool.
"""

from typing import Optional


def collect(
    board: str,
    config: dict,
    date: str,
    proxy: Optional[str] = None,
) -> tuple[list[dict], list[dict]]:
    """Generate websearch needs list and deterministic items.

    Returns:
        (items, needs_websearch): Empty items list (websearch doesn't produce deterministic results),
        plus the list of queries Claude should run via WebSearch.
    """
    needs_ws = config.get("needs_websearch", [])
    ws_for_board = [w for w in needs_ws if board in w.get("boards", [])]

    if ws_for_board:
        print(f"[websearch] Board={board}: {len(ws_for_board)} queries for Claude to run")
    else:
        print(f"[websearch] Board={board}: no websearch queries needed")

    return [], ws_for_board
