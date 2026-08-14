from dataclasses import dataclass
from typing import List, Optional

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


class StockScreener:
    def __init__(self):
        self.universe = settings.stock_universe

    def screen(self) -> List[Candidate]:
        candidates = [c for c in (self._evaluate(t) for t in self.universe) if c is not None]
        candidates.sort(key=lambda c: c.opportunity_score, reverse=True)
        return candidates[: settings.max_candidates]

    def _evaluate(self, ticker: str) -> Optional[Candidate]:
        try:
            hist = yf.Ticker(ticker, session=_session).history(period="5d")
        except Exception as exc:
            print(f"[screener] no se pudo obtener datos de {ticker}: {exc}")
            return None

        if len(hist) < 2:
            return None

        latest_price = float(hist["Close"].iloc[-1])
        prev_price = float(hist["Close"].iloc[-2])
        price_change_pct = (latest_price - prev_price) / prev_price * 100
        avg_volume = float(hist["Volume"].mean())
        dollar_volume = avg_volume * latest_price

        if dollar_volume < settings.min_dollar_volume or abs(price_change_pct) < settings.min_price_change_pct:
            return None

        opportunity_score = abs(price_change_pct) * 0.6 + min(dollar_volume / 1_000_000_000, 10) * 0.4
        return Candidate(ticker, latest_price, price_change_pct, avg_volume, dollar_volume, opportunity_score)


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
