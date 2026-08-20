from trading_agent.decision_agent import Analysis
from trading_agent.risk import PortfolioState, RiskManager


def make_analysis(decision, ticker="TST"):
    return Analysis(ticker, decision, confidence=0.5, reasoning="test")


def test_hold_never_trades():
    risk = RiskManager()
    portfolio = PortfolioState(cash=100_000, positions_value=0)
    assert risk.size_trade(make_analysis("HOLD"), 100.0, portfolio) is None


def test_buy_respects_max_position_pct():
    risk = RiskManager()
    portfolio = PortfolioState(cash=100_000, positions_value=0)
    plan = risk.size_trade(make_analysis("BUY"), 100.0, portfolio)
    assert plan is not None
    assert plan.value <= portfolio.total_value * 0.10 + 1e-6


def test_buy_blocked_when_cash_reserve_would_be_breached():
    risk = RiskManager()
    portfolio = PortfolioState(cash=20_000, positions_value=80_000)
    assert risk.size_trade(make_analysis("BUY"), 100.0, portfolio) is None


def test_sell_requires_held_shares():
    risk = RiskManager()
    portfolio = PortfolioState(cash=100_000, positions_value=0)
    assert risk.size_trade(make_analysis("SELL"), 100.0, portfolio, held_shares=0) is None


def test_sell_never_exceeds_held_shares():
    risk = RiskManager()
    portfolio = PortfolioState(cash=0, positions_value=100_000)
    plan = risk.size_trade(make_analysis("SELL"), 100.0, portfolio, held_shares=5)
    assert plan is not None
    assert plan.shares == 5


def test_buy_skips_when_already_at_target_allocation():
    risk = RiskManager()
    portfolio = PortfolioState(cash=90_000, positions_value=10_000)
    # ya tiene 100 acciones @ $100 = $10,000 = 10% del portafolio (el tope)
    assert risk.size_trade(make_analysis("BUY"), 100.0, portfolio, held_shares=100) is None


def test_buy_tops_up_only_remaining_room():
    risk = RiskManager()
    portfolio = PortfolioState(cash=95_000, positions_value=5_000)
    # ya tiene 50 acciones @ $100 = $5,000; el tope de 10% son $10,000 -> quedan 50 acciones de margen
    plan = risk.size_trade(make_analysis("BUY"), 100.0, portfolio, held_shares=50)
    assert plan is not None
    assert plan.shares == 50
