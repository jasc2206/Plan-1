from trading_agent.decision_agent import DecisionAgent
from trading_agent.screener import Candidate


def make_candidate(price_change_pct, rsi=None, macd=None, macd_signal=None):
    return Candidate(
        "TST", price=100.0, price_change_pct=price_change_pct,
        avg_volume=5_000_000, dollar_volume=500_000_000, opportunity_score=1.0,
        rsi=rsi, macd=macd, macd_signal=macd_signal,
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


def test_rule_based_suppresses_buy_when_overbought():
    candidate = make_candidate(3.0, rsi=75.0, macd=1.0, macd_signal=0.5)
    analysis = DecisionAgent()._analyze_with_rules(candidate)
    assert analysis.decision == "HOLD"
    assert "sobrecompra" in analysis.reasoning


def test_rule_based_suppresses_sell_when_oversold():
    candidate = make_candidate(-3.0, rsi=25.0, macd=-1.0, macd_signal=-0.5)
    analysis = DecisionAgent()._analyze_with_rules(candidate)
    assert analysis.decision == "HOLD"
    assert "sobreventa" in analysis.reasoning


def test_rule_based_buy_confidence_higher_with_macd_confirmation():
    confirmed = make_candidate(3.0, rsi=55.0, macd=1.0, macd_signal=0.5)  # macd > signal
    unconfirmed = make_candidate(3.0, rsi=55.0, macd=0.5, macd_signal=1.0)  # macd < signal

    confirmed_analysis = DecisionAgent()._analyze_with_rules(confirmed)
    unconfirmed_analysis = DecisionAgent()._analyze_with_rules(unconfirmed)

    assert confirmed_analysis.decision == "BUY"
    assert unconfirmed_analysis.decision == "BUY"
    assert confirmed_analysis.confidence > unconfirmed_analysis.confidence


def test_rule_based_sell_confidence_higher_with_macd_confirmation():
    confirmed = make_candidate(-3.0, rsi=45.0, macd=-1.0, macd_signal=-0.5)  # macd < signal
    unconfirmed = make_candidate(-3.0, rsi=45.0, macd=-0.5, macd_signal=-1.0)  # macd > signal

    confirmed_analysis = DecisionAgent()._analyze_with_rules(confirmed)
    unconfirmed_analysis = DecisionAgent()._analyze_with_rules(unconfirmed)

    assert confirmed_analysis.decision == "SELL"
    assert unconfirmed_analysis.decision == "SELL"
    assert confirmed_analysis.confidence > unconfirmed_analysis.confidence


def test_rule_based_works_without_indicators():
    # candidatos sin suficiente historia para RSI/MACD (None) no deben fallar
    analysis = DecisionAgent()._analyze_with_rules(make_candidate(3.0))
    assert analysis.decision == "BUY"
