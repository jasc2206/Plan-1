import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in ("1", "true", "yes")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def _list_env(name: str, default: str) -> List[str]:
    return [t.strip() for t in os.getenv(name, default).split(",") if t.strip()]


@dataclass
class Settings:
    dry_run: bool = field(default_factory=lambda: _bool_env("DRY_RUN", True))

    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    alpaca_api_key: str = field(default_factory=lambda: os.getenv("ALPACA_API_KEY", ""))
    alpaca_secret_key: str = field(default_factory=lambda: os.getenv("ALPACA_SECRET_KEY", ""))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))

    stock_universe: List[str] = field(default_factory=lambda: _list_env(
        "STOCK_UNIVERSE",
        "NVDA,MSFT,AAPL,GOOGL,AMZN,META,AVGO,TSLA,NFLX,AMD,CSCO,COST,ASML,MU,PLTR",
    ))

    min_volume: int = field(default_factory=lambda: _int_env("MIN_VOLUME", 1_000_000))
    min_price_change_pct: float = field(default_factory=lambda: _float_env("MIN_PRICE_CHANGE_PCT", 2.0))
    max_candidates: int = field(default_factory=lambda: _int_env("MAX_CANDIDATES", 5))

    starting_cash: float = field(default_factory=lambda: _float_env("STARTING_CASH", 100_000.0))
    max_position_pct: float = field(default_factory=lambda: _float_env("MAX_POSITION_PCT", 0.10))
    min_cash_reserve_pct: float = field(default_factory=lambda: _float_env("MIN_CASH_RESERVE_PCT", 0.20))
    max_daily_trades: int = field(default_factory=lambda: _int_env("MAX_DAILY_TRADES", 5))


settings = Settings()
