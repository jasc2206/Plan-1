from dataclasses import dataclass
from typing import Dict, List

from .risk import TradePlan


@dataclass
class Fill:
    ticker: str
    action: str
    shares: int
    price: float


@dataclass
class PositionPnL:
    ticker: str
    shares: int
    avg_cost: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PaperBrokerStub:
    """Broker simulado en memoria. No requiere credenciales ni hace llamadas de red.

    Se reemplazara por un cliente real de Alpaca (paper trading) en una fase
    posterior, cuando se configuren ALPACA_API_KEY / ALPACA_SECRET_KEY.
    """

    def __init__(
        self,
        starting_cash: float,
        positions: Dict[str, int] = None,
        cost_basis: Dict[str, float] = None,
        realized_pnl: float = 0.0,
    ):
        self.cash = starting_cash
        self.positions: Dict[str, int] = dict(positions) if positions else {}
        self.cost_basis: Dict[str, float] = dict(cost_basis) if cost_basis else {}
        self.realized_pnl = realized_pnl
        self.fills: List[Fill] = []

    def submit(self, plan: TradePlan) -> Fill:
        if plan.action == "BUY":
            self.cash -= plan.value
            self.positions[plan.ticker] = self.positions.get(plan.ticker, 0) + plan.shares
            self.cost_basis[plan.ticker] = self.cost_basis.get(plan.ticker, 0.0) + plan.value
        else:
            held = self.positions.get(plan.ticker, 0)
            shares = min(plan.shares, held)
            if shares <= 0:
                raise ValueError(f"No hay posicion en {plan.ticker} para vender")

            avg_cost = self.cost_basis.get(plan.ticker, 0.0) / held if held else 0.0
            self.realized_pnl += (plan.price - avg_cost) * shares
            self.cash += shares * plan.price
            self.positions[plan.ticker] = held - shares
            self.cost_basis[plan.ticker] = self.cost_basis.get(plan.ticker, 0.0) - avg_cost * shares
            if self.positions[plan.ticker] == 0:
                self.cost_basis.pop(plan.ticker, None)

        fill = Fill(plan.ticker, plan.action, plan.shares, plan.price)
        self.fills.append(fill)
        return fill

    def positions_value(self, prices: Dict[str, float]) -> float:
        return sum(qty * prices.get(ticker, 0.0) for ticker, qty in self.positions.items())

    def position_pnl(self, prices: Dict[str, float]) -> List[PositionPnL]:
        result = []
        for ticker, shares in self.positions.items():
            current_price = prices.get(ticker)
            if shares <= 0 or current_price is None:
                continue
            avg_cost = self.cost_basis.get(ticker, 0.0) / shares
            unrealized = (current_price - avg_cost) * shares
            pct = (current_price - avg_cost) / avg_cost * 100 if avg_cost else 0.0
            result.append(PositionPnL(ticker, shares, avg_cost, current_price, unrealized, pct))
        return result
