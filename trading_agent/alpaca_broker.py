from typing import Dict, List

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.requests import GetOrdersRequest, MarketOrderRequest

from .broker import Fill, PositionPnL
from .config import settings
from .risk import TradePlan


def _is_crypto(ticker: str) -> bool:
    return ticker.endswith("-USD")


def _to_order_symbol(ticker: str) -> str:
    """Nuestro ticker interno (ej. 'XRP-USD') -> simbolo de orden de Alpaca ('XRP/USD')."""
    return ticker.replace("-USD", "/USD") if _is_crypto(ticker) else ticker


def _to_internal_ticker(alpaca_symbol: str) -> str:
    """Simbolo que devuelve Alpaca en posiciones ('XRPUSD', sin separador) -> 'XRP-USD'."""
    if "/" in alpaca_symbol:
        return alpaca_symbol.replace("/", "-")
    if alpaca_symbol.endswith("USD"):
        base = alpaca_symbol[:-3]
        crypto_bases = {t[:-4] for t in settings.stock_universe if t.endswith("-USD")}
        if base in crypto_bases:
            return f"{base}-USD"
    return alpaca_symbol


class AlpacaBroker:
    """Broker real contra la cuenta de PAPER TRADING de Alpaca (nunca dinero real)."""

    def __init__(self, api_key: str, secret_key: str):
        self.client = TradingClient(api_key, secret_key, paper=True)

    @property
    def cash(self) -> float:
        return float(self.client.get_account().cash)

    @property
    def positions(self) -> Dict[str, int]:
        return {_to_internal_ticker(p.symbol): int(float(p.qty)) for p in self.client.get_all_positions()}

    def has_pending_order(self, ticker: str) -> bool:
        symbol = _to_order_symbol(ticker)
        request = GetOrdersRequest(status=QueryOrderStatus.OPEN, symbols=[symbol])
        return len(self.client.get_orders(request)) > 0

    def submit(self, plan: TradePlan) -> Fill:
        side = OrderSide.BUY if plan.action == "BUY" else OrderSide.SELL
        order = MarketOrderRequest(
            symbol=_to_order_symbol(plan.ticker),
            qty=plan.shares,
            side=side,
            time_in_force=TimeInForce.GTC if _is_crypto(plan.ticker) else TimeInForce.DAY,
        )
        self.client.submit_order(order)
        return Fill(plan.ticker, plan.action, plan.shares, plan.price)

    def positions_value(self, prices: Dict[str, float]) -> float:
        return sum(float(p.market_value) for p in self.client.get_all_positions())

    def position_pnl(self, prices: Dict[str, float]) -> List[PositionPnL]:
        result = []
        for p in self.client.get_all_positions():
            ticker = _to_internal_ticker(p.symbol)
            shares = int(float(p.qty))
            avg_cost = float(p.avg_entry_price)
            current_price = float(p.current_price) if p.current_price else prices.get(ticker, avg_cost)
            result.append(PositionPnL(
                ticker, shares, avg_cost, current_price,
                float(p.unrealized_pl), float(p.unrealized_plpc) * 100,
            ))
        return result
