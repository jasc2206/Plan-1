from trading_agent import alpaca_broker as ab


def test_to_order_symbol_translates_crypto():
    assert ab._to_order_symbol("XRP-USD") == "XRP/USD"
    assert ab._to_order_symbol("PAXG-USD") == "PAXG/USD"


def test_to_order_symbol_leaves_equities_unchanged():
    assert ab._to_order_symbol("AAPL") == "AAPL"


class FakeAsset:
    def __init__(self, symbol):
        self.symbol = symbol


class FakeTradingClient:
    def __init__(self, open_orders=None, crypto_symbols=None):
        self._open_orders = open_orders or []
        self._crypto_symbols = crypto_symbols or []

    def get_orders(self, request):
        return [o for o in self._open_orders if o in request.symbols]

    def get_all_assets(self, request):
        return [FakeAsset(s) for s in self._crypto_symbols]


def make_broker(**kwargs):
    broker = ab.AlpacaBroker.__new__(ab.AlpacaBroker)
    broker.client = FakeTradingClient(**kwargs)
    broker._crypto_bases = None
    return broker


def test_to_internal_ticker_maps_crypto_position_symbol():
    broker = make_broker(crypto_symbols=["XRP/USD", "PAXG/USD"])
    assert broker._to_internal_ticker("XRPUSD") == "XRP-USD"
    assert broker._to_internal_ticker("PAXGUSD") == "PAXG-USD"


def test_to_internal_ticker_leaves_equities_unchanged():
    broker = make_broker(crypto_symbols=["XRP/USD"])
    assert broker._to_internal_ticker("AAPL") == "AAPL"


def test_to_internal_ticker_ignores_usd_suffix_outside_crypto_list():
    broker = make_broker(crypto_symbols=[])
    assert broker._to_internal_ticker("FOOUSD") == "FOOUSD"


def test_to_internal_ticker_recognizes_ticker_outside_configured_universe():
    # discrecional: un ticker cripto que Alpaca soporta pero que no esta en
    # STOCK_UNIVERSE debe reconocerse igual, consultando la lista real de Alpaca
    broker = make_broker(crypto_symbols=["DOGE/USD"])
    assert broker._to_internal_ticker("DOGEUSD") == "DOGE-USD"


def test_crypto_bases_are_cached_after_first_call():
    broker = make_broker(crypto_symbols=["XRP/USD"])
    broker._to_internal_ticker("XRPUSD")
    broker.client._crypto_symbols = []  # si volviera a consultar, ya no veria XRP
    assert broker._to_internal_ticker("XRPUSD") == "XRP-USD"


def test_has_pending_order_true_when_open_order_exists():
    broker = make_broker(open_orders=["AAPL"])
    assert broker.has_pending_order("AAPL") is True


def test_has_pending_order_false_when_no_open_order():
    broker = make_broker(open_orders=[])
    assert broker.has_pending_order("AAPL") is False
