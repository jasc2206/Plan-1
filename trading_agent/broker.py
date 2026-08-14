from dataclasses import dataclass, field
from typing import Dict, List

from .risk import TradePlan


@dataclass
class Fill:
    ticker: str
    action: str
    shares: int
    price: float


class PaperBrokerStub:
    """Broker simulado en memoria. No requiere credenciales ni hace llamadas de red.

    Se reemplazara por un cliente real de Alpaca (paper trading) en una fase
    posterior, cuando se configuren ALPACA_API_KEY / ALPACA_SECRET_KEY.
    """

    def __init__(self, starting_cash: float, positions: Dict[str, int] = None):
        self.cash = starting_cash
        self.positions: Dict[str, int] = dict(positions) if positions else {}
        self.fills: List[Fill] = []

    def submit(self, plan: TradePlan) -> Fill:
        if plan.action == "BUY":
            self.cash -= plan.value
            self.positions[plan.ticker] = self.positions.get(plan.ticker, 0) + plan.shares
        else:
            held = self.positions.get(plan.ticker, 0)
            shares = min(plan.shares, held)
            if shares <= 0:
                raise ValueError(f"No hay posicion en {plan.ticker} para vender")
            self.cash += shares * plan.price
            self.positions[plan.ticker] = held - shares

        fill = Fill(plan.ticker, plan.action, plan.shares, plan.price)
        self.fills.append(fill)
        return fill

    def positions_value(self, prices: Dict[str, float]) -> float:
        return sum(qty * prices.get(ticker, 0.0) for ticker, qty in self.positions.items())
