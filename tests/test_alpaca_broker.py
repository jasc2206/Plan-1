from trading_agent import alpaca_broker as ab
from trading_agent.config import settings


def test_to_order_symbol_translates_crypto():
    assert ab._to_order_symbol("XRP-USD") == "XRP/USD"
    assert ab._to_order_symbol("PAXG-USD") == "PAXG/USD"


def test_to_order_symbol_leaves_equities_unchanged():
    assert ab._to_order_symbol("AAPL") == "AAPL"


def test_to_internal_ticker_maps_crypto_position_symbol(monkeypatch):
    monkeypatch.setattr(settings, "stock_universe", ["AAPL", "XRP-USD", "PAXG-USD"])
    assert ab._to_internal_ticker("XRPUSD") == "XRP-USD"
    assert ab._to_internal_ticker("PAXGUSD") == "PAXG-USD"


def test_to_internal_ticker_leaves_equities_unchanged(monkeypatch):
    monkeypatch.setattr(settings, "stock_universe", ["AAPL", "XRP-USD"])
    assert ab._to_internal_ticker("AAPL") == "AAPL"


def test_to_internal_ticker_ignores_usd_suffix_outside_universe(monkeypatch):
    # una acción hipotética que termine en USD no debe confundirse con cripto
    # si no esta declarada en el universo de cripto configurado
    monkeypatch.setattr(settings, "stock_universe", ["AAPL"])
    assert ab._to_internal_ticker("FOOUSD") == "FOOUSD"


class FakeTradingClient:
    def __init__(self, open_orders):
        self._open_orders = open_orders

    def get_orders(self, request):
        return [o for o in self._open_orders if o in request.symbols]


def test_has_pending_order_true_when_open_order_exists():
    broker = ab.AlpacaBroker.__new__(ab.AlpacaBroker)
    broker.client = FakeTradingClient(open_orders=["AAPL"])
    assert broker.has_pending_order("AAPL") is True


def test_has_pending_order_false_when_no_open_order():
    broker = ab.AlpacaBroker.__new__(ab.AlpacaBroker)
    broker.client = FakeTradingClient(open_orders=[])
    assert broker.has_pending_order("AAPL") is False
