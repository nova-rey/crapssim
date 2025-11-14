"""
API vs Vanilla RNG Parity Demo

This script is a developer tool, not part of the public library import surface.
It:

- Starts an API session with a fixed seed.
- Rolls 25 times via /session/roll and records the dice.
- Runs 25 rolls via the vanilla CrapsSim engine with the same seed.
- Compares the sequences and writes a markdown report to:
    crapssim_api/docs/API_RNG_PARITY_RUN.md

Intended usage (from repo root):

    python -m pip install -e ".[api]"
    PYTHONPATH=. python crapssim_api/tools/api_rng_parity_demo.py

FastAPI / pydantic remain optional dependencies; if they are missing, this
script will print a message and exit with code 0 (no effect on normal users).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pytest  # type: ignore[import-untyped]


def _ensure_optional_dependency(module_name: str) -> None:
    """Ensure the optional FastAPI dependency is present."""

    try:
        pytest.importorskip(module_name)
    except pytest.skip.Exception:
        print(
            "API RNG parity demo requires optional dependency "
            f"'{module_name}'. Install the API extras to run this tool."
        )
        raise SystemExit(0)


# Guard: only run if FastAPI stack is available.
_ensure_optional_dependency("fastapi")
_ensure_optional_dependency("pydantic")

from fastapi import FastAPI  # type: ignore[import-untyped]
from fastapi.testclient import TestClient  # type: ignore[import-untyped]

from crapssim_api.http import router  # type: ignore[import-untyped]

SEED = 424242
N_ROLLS = 25
PROFILE = "test-profile"


def _build_api_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _start_api_session(client: TestClient, seed: int) -> str:
    """
    Start a new API session with the given seed.

    Uses the same payload shape as other API tests:
        { "spec": {"table_profile": "test-profile"}, "seed": <seed> }
    """
    resp = client.post(
        "/session/start",
        json={"spec": {"table_profile": PROFILE}, "seed": seed},
    )
    resp.raise_for_status()
    payload = resp.json()
    return str(payload["session_id"])


def _roll_api_sequence(client: TestClient, session_id: str, n: int) -> List[Tuple[int, int]]:
    """
    Call /session/roll n times and collect (d1, d2) pairs.
    """
    results: List[Tuple[int, int]] = []
    for _ in range(n):
        resp = client.post("/session/roll", json={"session_id": session_id})
        resp.raise_for_status()
        snap = resp.json()["snapshot"]
        dice = snap.get("dice") or []
        if len(dice) != 2:
            raise RuntimeError(f"Unexpected dice payload from API: {dice!r}")
        d1, d2 = int(dice[0]), int(dice[1])
        results.append((d1, d2))
    return results


def _roll_vanilla_sequence(seed: int, n: int) -> List[Tuple[int, int]]:
    """
    Run n rolls through the vanilla CrapsSim engine with the same RNG behavior
    used by the API.

    IMPORTANT:
    - Use the same seeding mechanism that the HTTP layer uses when it builds
      the Table / Dice for a session. If the HTTP layer constructs a Table with
      a specific seed parameter, mirror that here. If it seeds a Dice instance
      directly, mirror that instead.
    - Do NOT introduce new seeding behavior; reuse existing constructors or
      helpers so that this script is exercising the same RNG path.
    """
    from crapssim.table import Table  # type: ignore[import-untyped]

    table = Table(seed=seed)
    results: List[Tuple[int, int]] = []
    for _ in range(n):
        table.dice.roll()
        d1, d2 = table.dice.result
        results.append((int(d1), int(d2)))
    return results


def _render_markdown(
    seed: int,
    n_rolls: int,
    vanilla_rolls: List[Tuple[int, int]],
    api_rolls: List[Tuple[int, int]],
) -> str:
    """
    Build a markdown report comparing vanilla vs API dice sequences.
    """
    parity_ok = vanilla_rolls == api_rolls

    lines: List[str] = []
    lines.append("# CrapsSim API — RNG Parity Demo")
    lines.append("")
    lines.append(f"- Seed: `{seed}`")
    lines.append(f"- Rolls compared: `{n_rolls}`")
    lines.append(f"- Parity: `{'MATCH' if parity_ok else 'MISMATCH'}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    if parity_ok:
        lines.append(
            "The vanilla CrapsSim dice sequence and the API `/session/roll` dice "
            "sequence are identical for this seed and call pattern."
        )
    else:
        lines.append(
            "The vanilla CrapsSim dice sequence and the API `/session/roll` dice "
            "sequence **do not** match for this seed and call pattern."
        )
    lines.append("")
    lines.append("## Roll-by-Roll Comparison")
    lines.append("")
    lines.append("| Roll # | Vanilla (d1+d2) | API (d1+d2) | Match? |")
    lines.append("| ------ | --------------- | ----------- | ------ |")
    for idx in range(n_rolls):
        v = vanilla_rolls[idx] if idx < len(vanilla_rolls) else ("-", "-")
        a = api_rolls[idx] if idx < len(api_rolls) else ("-", "-")
        v_str = f"{v[0]}+{v[1]}"
        a_str = f"{a[0]}+{a[1]}"
        match = "✅" if v == a else "❌"
        lines.append(f"| {idx + 1} | {v_str} | {a_str} | {match} |")

    lines.append("")
    lines.append("## Raw Sequences")
    lines.append("")
    lines.append("### Vanilla CrapsSim")
    lines.append("")
    lines.append("```text")
    lines.append(str(vanilla_rolls))
    lines.append("```")
    lines.append("")
    lines.append("### API `/session/roll`")
    lines.append("")
    lines.append("```text")
    lines.append(str(api_rolls))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    client = _build_api_client()

    # API path
    session_id = _start_api_session(client, SEED)
    api_rolls = _roll_api_sequence(client, session_id, N_ROLLS)

    # Vanilla path
    vanilla_rolls = _roll_vanilla_sequence(SEED, N_ROLLS)

    # Render and write markdown
    project_root = Path(__file__).resolve().parents[1]
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    out_path = docs_dir / "API_RNG_PARITY_RUN.md"

    markdown = _render_markdown(SEED, N_ROLLS, vanilla_rolls, api_rolls)
    out_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote RNG parity report to {out_path}")


if __name__ == "__main__":
    main()
