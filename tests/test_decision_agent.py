from trading_agent.decision_agent import DecisionAgent
from trading_agent.screener import Candidate


def make_candidate(price_change_pct):
    return Candidate(
        "TST", price=100.0, price_change_pct=price_change_pct,
        avg_volume=5_000_000, dollar_volume=500_000_000, opportunity_score=1.0,
    )


def test_rule_based_buy_on_positive_momentum():
    analysis = DecisionAgent()._analyze_with_rules(make_candidate(3.0))
    assert analysis.decision == "BUY"


def test_rule_based_sell_on_negative_momentum():
    analysis = DecisionAgent()._analyze_with_rules(make_candidate(-3.0))
    assert analysis.decision == "SELL"


def test_rule_based_hold_on_small_move():
    analysis = DecisionAgent()._analyze_with_rules(make_candidate(0.5))
    assert analysis.decision == "HOLD"
