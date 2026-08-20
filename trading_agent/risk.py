from dataclasses import dataclass
from typing import Optional

from .config import settings
from .decision_agent import Analysis


@dataclass
class PortfolioState:
    cash: float
    positions_value: float

    @property
    def total_value(self) -> float:
        return self.cash + self.positions_value


@dataclass
class TradePlan:
    ticker: str
    action: str
    shares: int
    price: float

    @property
    def value(self) -> float:
        return self.shares * self.price


class RiskManager:
    """Limites duros de tamano de posicion y reserva de efectivo. Nunca opera sobre HOLD."""

    def size_trade(
        self, analysis: Analysis, price: float, portfolio: PortfolioState, held_shares: int = 0
    ) -> Optional[TradePlan]:
        if analysis.decision == "HOLD" or price <= 0:
            return None

        max_position_value = portfolio.total_value * settings.max_position_pct

        if analysis.decision == "SELL":
            if held_shares < 1:
                return None
            shares = min(held_shares, int(max_position_value // price))
        else:
            # No sigue comprando una posicion que ya alcanzo su tope de asignacion
            held_value = held_shares * price
            remaining_room = max(max_position_value - held_value, 0)
            min_reserve = portfolio.total_value * settings.min_cash_reserve_pct
            available_cash = portfolio.cash - min_reserve
            position_value = min(remaining_room, max(available_cash, 0))
            shares = int(position_value // price)

        if shares < 1:
            return None

        return TradePlan(analysis.ticker, analysis.decision, shares, price)
