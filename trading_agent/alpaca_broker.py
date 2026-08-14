from typing import Dict, List

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from .broker import Fill, PositionPnL
from .risk import TradePlan


class AlpacaBroker:
    """Broker real contra la cuenta de PAPER TRADING de Alpaca (nunca dinero real)."""

    def __init__(self, api_key: str, secret_key: str):
        self.client = TradingClient(api_key, secret_key, paper=True)

    @property
    def cash(self) -> float:
        return float(self.client.get_account().cash)

    @property
    def positions(self) -> Dict[str, int]:
        return {p.symbol: int(float(p.qty)) for p in self.client.get_all_positions()}

    def submit(self, plan: TradePlan) -> Fill:
        side = OrderSide.BUY if plan.action == "BUY" else OrderSide.SELL
        order = MarketOrderRequest(
            symbol=plan.ticker,
            qty=plan.shares,
            side=side,
            time_in_force=TimeInForce.DAY,
        )
        self.client.submit_order(order)
        return Fill(plan.ticker, plan.action, plan.shares, plan.price)

    def positions_value(self, prices: Dict[str, float]) -> float:
        return sum(float(p.market_value) for p in self.client.get_all_positions())

    def position_pnl(self, prices: Dict[str, float]) -> List[PositionPnL]:
        result = []
        for p in self.client.get_all_positions():
            shares = int(float(p.qty))
            avg_cost = float(p.avg_entry_price)
            current_price = float(p.current_price) if p.current_price else prices.get(p.symbol, avg_cost)
            result.append(PositionPnL(
                p.symbol, shares, avg_cost, current_price,
                float(p.unrealized_pl), float(p.unrealized_plpc) * 100,
            ))
        return result
