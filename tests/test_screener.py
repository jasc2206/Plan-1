import pandas as pd

from trading_agent import screener as screener_module
from trading_agent.config import settings


class FakeTicker:
    def __init__(self, ticker, session=None):
        self.ticker = ticker

    def history(self, period="5d"):
        data = {
            "NVDA": {"close": [100, 110], "volume": [2_000_000, 2_000_000]},
            "FLAT": {"close": [50, 50.1], "volume": [2_000_000, 2_000_000]},
            "LOWVOL": {"close": [50, 55], "volume": [10_000, 10_000]},
            # precio alto, pocas unidades: pasaria el volumen en dolares aunque
            # no llegue al viejo umbral de 1M de "unidades"
            "HIGHPRICE": {"close": [5_000, 5_300], "volume": [2_000, 2_000]},
            # precio muy bajo, millones de unidades: liquidez real en dolares
            # es minima aunque el conteo de unidades sea enorme
            "PENNY": {"close": [0.001, 0.0011], "volume": [5_000_000, 5_000_000]},
        }.get(self.ticker)
        if data is None:
            return pd.DataFrame()
        return pd.DataFrame({"Close": data["close"], "Volume": data["volume"]})


def test_screen_filters_by_volume_and_movement(monkeypatch):
    monkeypatch.setattr(screener_module, "yf", type("FakeModule", (), {"Ticker": FakeTicker}))
    monkeypatch.setattr(settings, "stock_universe", ["NVDA", "FLAT", "LOWVOL"])

    candidates = screener_module.StockScreener().screen()
    tickers = [c.ticker for c in candidates]

    assert "NVDA" in tickers
    assert "FLAT" not in tickers
    assert "LOWVOL" not in tickers


def test_dollar_volume_normalizes_across_asset_types(monkeypatch):
    monkeypatch.setattr(screener_module, "yf", type("FakeModule", (), {"Ticker": FakeTicker}))
    monkeypatch.setattr(settings, "stock_universe", ["HIGHPRICE", "PENNY"])

    candidates = screener_module.StockScreener().screen()
    tickers = [c.ticker for c in candidates]

    assert "HIGHPRICE" in tickers  # $10.6M/dia en dolares, aunque solo 2,000 unidades
    assert "PENNY" not in tickers  # $5,500/dia en dolares, pese a 5M de unidades


def test_compute_rsi_returns_none_with_insufficient_data():
    closes = pd.Series([100.0, 101.0, 102.0])
    assert screener_module._compute_rsi(closes, period=14) is None


def test_compute_rsi_near_100_for_pure_uptrend():
    closes = pd.Series([100.0 + i for i in range(30)])  # solo ganancias, sin perdidas
    rsi = screener_module._compute_rsi(closes, period=14)
    assert rsi > 95


def test_compute_rsi_near_0_for_pure_downtrend():
    closes = pd.Series([130.0 - i for i in range(30)])  # solo perdidas, sin ganancias
    rsi = screener_module._compute_rsi(closes, period=14)
    assert rsi < 5


def test_compute_macd_returns_none_with_insufficient_data():
    closes = pd.Series([float(i) for i in range(10)])
    assert screener_module._compute_macd(closes) == (None, None, None)


def test_compute_macd_positive_for_sustained_uptrend():
    closes = pd.Series([100.0 + i * 0.5 for i in range(60)])
    macd, macd_signal, macd_hist = screener_module._compute_macd(closes)
    assert macd > 0
    assert macd > macd_signal  # tendencia sostenida -> linea MACD por encima de la señal


def test_screen_attaches_indicators_when_history_is_long_enough(monkeypatch):
    long_close = [100.0 + i * 0.3 for i in range(60)] + [200.0]  # ultimo salto dispara el filtro
    long_volume = [2_000_000] * 61

    class LongHistoryTicker:
        def __init__(self, ticker, session=None):
            self.ticker = ticker

        def history(self, period="3mo"):
            return pd.DataFrame({"Close": long_close, "Volume": long_volume})

    monkeypatch.setattr(screener_module, "yf", type("FakeModule", (), {"Ticker": LongHistoryTicker}))
    monkeypatch.setattr(settings, "stock_universe", ["LONGHIST"])

    candidates = screener_module.StockScreener().screen()
    assert len(candidates) == 1
    assert candidates[0].rsi is not None
    assert candidates[0].macd is not None
    assert candidates[0].macd_signal is not None
