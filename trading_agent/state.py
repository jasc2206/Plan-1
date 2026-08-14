import json
from pathlib import Path
from typing import Dict

STATE_PATH = Path(__file__).resolve().parent.parent / "trading_agent_state.json"


def load_state(starting_cash: float) -> Dict:
    if not STATE_PATH.exists():
        return {"cash": starting_cash, "positions": {}}
    with STATE_PATH.open() as f:
        return json.load(f)


def save_state(cash: float, positions: Dict[str, int]) -> None:
    with STATE_PATH.open("w") as f:
        json.dump({"cash": cash, "positions": positions}, f, indent=2)
