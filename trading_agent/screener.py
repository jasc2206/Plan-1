from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
import yfinance as yf

from .config import settings

# yfinance usa curl_cffi (suplantacion TLS) por defecto para evitar el
# bloqueo de bots de Yahoo; eso no funciona detras de proxies con
# reterminacion TLS. Una sesion requests normal si funciona.
_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})


@dataclass
class Candidate:
    ticker: str
    price: float
    price_change_pct: float
    avg_volume: float
    dollar_volume: float
    opportunity_score: float
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None


def _compute_rsi(closes, period: int = 14) -> Optional[float]:
    """RSI de Wilder. None si no hay suficiente historia."""
    if len(closes) < period + 1:
        return None
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def _compute_macd(
    closes, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """(macd, señal, histograma). (None, None, None) si no hay suficiente historia."""
    if len(closes) < slow + signal:
        return None, None, None
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), float(histogram.iloc[-1])


class StockScreener:
    def __init__(self):
        self.universe = settings.stock_universe

    def screen(self) -> List[Candidate]:
        candidates = [c for c in (self._evaluate(t) for t in self.universe) if c is not None]
        candidates.sort(key=lambda c: c.opportunity_score, reverse=True)
        return candidates[: settings.max_candidates]

    def _evaluate(self, ticker: str) -> Optional[Candidate]:
        try:
            # 3mo da suficiente historia para RSI(14) y MACD(12,26,9); el
            # cambio de precio y el volumen reciente siguen usando solo los
            # ultimos dias, igual que antes.
            hist = yf.Ticker(ticker, session=_session).history(period="3mo")
        except Exception as exc:
            print(f"[screener] no se pudo obtener datos de {ticker}: {exc}")
            return None

        if len(hist) < 2:
            return None

        latest_price = float(hist["Close"].iloc[-1])
        prev_price = float(hist["Close"].iloc[-2])
        price_change_pct = (latest_price - prev_price) / prev_price * 100
        avg_volume = float(hist["Volume"].tail(5).mean())
        dollar_volume = avg_volume * latest_price

        if dollar_volume < settings.min_dollar_volume or abs(price_change_pct) < settings.min_price_change_pct:
            return None

        rsi = _compute_rsi(hist["Close"])
        macd, macd_signal, macd_hist = _compute_macd(hist["Close"])

        opportunity_score = abs(price_change_pct) * 0.6 + min(dollar_volume / 1_000_000_000, 10) * 0.4
        return Candidate(
            ticker, latest_price, price_change_pct, avg_volume, dollar_volume, opportunity_score,
            rsi, macd, macd_signal, macd_hist,
        )


def get_latest_price(ticker: str) -> Optional[float]:
    """Precio actual de cualquier ticker, sin pasar por los filtros del screener.

    Se usa para valorar posiciones ya abiertas que no aparecen en la
    watchlist del dia (porque no cumplen el filtro de movimiento/volumen).
    """
    try:
        hist = yf.Ticker(ticker, session=_session).history(period="1d")
    except Exception as exc:
        print(f"[screener] no se pudo obtener precio de {ticker}: {exc}")
        return None
    if hist.empty:
        return None
    return float(hist["Close"].iloc[-1])
