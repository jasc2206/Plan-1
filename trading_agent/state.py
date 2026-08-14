import json
from pathlib import Path
from typing import Dict

STATE_PATH = Path(__file__).resolve().parent.parent / "trading_agent_state.json"


def load_state(starting_cash: float) -> Dict:
    if not STATE_PATH.exists():
        return {"cash": starting_cash, "positions": {}, "cost_basis": {}, "realized_pnl": 0.0}
    with STATE_PATH.open() as f:
        data = json.load(f)
    data.setdefault("cost_basis", {})
    data.setdefault("realized_pnl", 0.0)
    return data


def save_state(cash: float, positions: Dict[str, int], cost_basis: Dict[str, float], realized_pnl: float) -> None:
    with STATE_PATH.open("w") as f:
        json.dump(
            {"cash": cash, "positions": positions, "cost_basis": cost_basis, "realized_pnl": realized_pnl},
            f,
            indent=2,
        )
