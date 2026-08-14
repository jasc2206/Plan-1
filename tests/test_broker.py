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


def test_buy_tracks_cost_basis():
    broker = PaperBrokerStub(starting_cash=10_000)
    broker.submit(TradePlan("AAA", "BUY", 10, 50.0))
    broker.submit(TradePlan("AAA", "BUY", 10, 70.0))
    # costo promedio ponderado: (10*50 + 10*70) / 20 = 60
    assert broker.cost_basis["AAA"] == 500 + 700
    pnl = broker.position_pnl({"AAA": 90.0})[0]
    assert pnl.avg_cost == 60.0
    assert pnl.unrealized_pnl == (90.0 - 60.0) * 20


def test_sell_realizes_pnl_against_avg_cost():
    broker = PaperBrokerStub(starting_cash=0, positions={"AAA": 10}, cost_basis={"AAA": 500.0})
    broker.submit(TradePlan("AAA", "SELL", 4, 80.0))
    # costo promedio era 50; vendio 4 a 80 -> ganancia realizada de 4*(80-50)=120
    assert broker.realized_pnl == 120.0
    assert broker.cost_basis["AAA"] == 500.0 - 50.0 * 4


def test_sell_full_position_clears_cost_basis():
    broker = PaperBrokerStub(starting_cash=0, positions={"AAA": 10}, cost_basis={"AAA": 500.0})
    broker.submit(TradePlan("AAA", "SELL", 10, 80.0))
    assert "AAA" not in broker.cost_basis


def test_position_pnl_skips_tickers_without_price():
    broker = PaperBrokerStub(starting_cash=0, positions={"AAA": 10}, cost_basis={"AAA": 500.0})
    assert broker.position_pnl({}) == []
