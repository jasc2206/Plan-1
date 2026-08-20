import pytest

from trading_agent import discretionary
from trading_agent.broker import Fill
from trading_agent.config import settings


class FakeNotifier:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


class FakeBroker:
    def __init__(self, cash=100_000.0, positions=None, pending=False):
        self.cash = cash
        self._positions = positions or {}
        self._pending = pending
        self.submitted = None

    def __call__(self, *_args, **_kwargs):
        return self

    @property
    def positions(self):
        return self._positions

    def has_pending_order(self, ticker):
        return self._pending

    def positions_value(self, prices):
        return sum(qty * prices.get(t, 0.0) for t, qty in self._positions.items())

    def submit(self, plan):
        self.submitted = plan
        return Fill(plan.ticker, plan.action, plan.shares, plan.price)


@pytest.fixture(autouse=True)
def alpaca_creds(monkeypatch):
    monkeypatch.setattr(settings, "alpaca_api_key", "fake-key")
    monkeypatch.setattr(settings, "alpaca_secret_key", "fake-secret")


def test_requires_alpaca_credentials(monkeypatch):
    monkeypatch.setattr(settings, "alpaca_api_key", "")
    monkeypatch.setattr(settings, "alpaca_secret_key", "")
    with pytest.raises(RuntimeError):
        discretionary.invest_discretionary("AAPL", "BUY", "porque si")


def test_buys_when_price_available_and_risk_allows(monkeypatch):
    fake_broker = FakeBroker(cash=100_000.0)
    fake_notifier = FakeNotifier()
    monkeypatch.setattr(discretionary, "AlpacaBroker", fake_broker)
    monkeypatch.setattr(discretionary, "get_notifier", lambda: fake_notifier)
    monkeypatch.setattr(discretionary, "get_latest_price", lambda ticker: 100.0)

    discretionary.invest_discretionary("NEWTICKER", "BUY", "tendencia fuerte en noticias")

    assert fake_broker.submitted is not None
    assert fake_broker.submitted.action == "BUY"
    assert any("DISCRECIONAL" in m for m in fake_notifier.messages)


def test_skips_when_no_price(monkeypatch):
    fake_broker = FakeBroker()
    fake_notifier = FakeNotifier()
    monkeypatch.setattr(discretionary, "AlpacaBroker", fake_broker)
    monkeypatch.setattr(discretionary, "get_notifier", lambda: fake_notifier)
    monkeypatch.setattr(discretionary, "get_latest_price", lambda ticker: None)

    discretionary.invest_discretionary("BADTICKER", "BUY", "razon")

    assert fake_broker.submitted is None


def test_skips_when_pending_order_exists(monkeypatch):
    fake_broker = FakeBroker(pending=True)
    fake_notifier = FakeNotifier()
    monkeypatch.setattr(discretionary, "AlpacaBroker", fake_broker)
    monkeypatch.setattr(discretionary, "get_notifier", lambda: fake_notifier)
    monkeypatch.setattr(discretionary, "get_latest_price", lambda ticker: 100.0)

    discretionary.invest_discretionary("AAPL", "BUY", "razon")

    assert fake_broker.submitted is None


def test_skips_when_risk_manager_blocks(monkeypatch):
    # cash muy por debajo de la reserva minima -> RiskManager no deja comprar
    fake_broker = FakeBroker(cash=0.0)
    fake_notifier = FakeNotifier()
    monkeypatch.setattr(discretionary, "AlpacaBroker", fake_broker)
    monkeypatch.setattr(discretionary, "get_notifier", lambda: fake_notifier)
    monkeypatch.setattr(discretionary, "get_latest_price", lambda ticker: 100.0)

    discretionary.invest_discretionary("AAPL", "BUY", "razon")

    assert fake_broker.submitted is None
