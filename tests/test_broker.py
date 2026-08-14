import pytest

from trading_agent.broker import PaperBrokerStub
from trading_agent.risk import TradePlan


def test_buy_updates_cash_and_positions():
    broker = PaperBrokerStub(starting_cash=10_000)
    fill = broker.submit(TradePlan("AAA", "BUY", 10, 50.0))
    assert fill.shares == 10
    assert broker.cash == 10_000 - 500
    assert broker.positions["AAA"] == 10


def test_sell_updates_cash_and_reduces_position():
    broker = PaperBrokerStub(starting_cash=0, positions={"AAA": 10})
    broker.submit(TradePlan("AAA", "SELL", 4, 50.0))
    assert broker.cash == 200
    assert broker.positions["AAA"] == 6


def test_sell_without_position_raises():
    broker = PaperBrokerStub(starting_cash=0)
    with pytest.raises(ValueError):
        broker.submit(TradePlan("AAA", "SELL", 1, 50.0))


def test_positions_value_uses_given_prices():
    broker = PaperBrokerStub(starting_cash=0, positions={"AAA": 10, "BBB": 5})
    value = broker.positions_value({"AAA": 20.0, "BBB": 10.0})
    assert value == 10 * 20.0 + 5 * 10.0
