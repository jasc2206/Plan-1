from .alpaca_broker import AlpacaBroker
from .config import settings
from .decision_agent import Analysis
from .notifier import get_notifier
from .risk import PortfolioState, RiskManager
from .screener import get_latest_price


def invest_discretionary(ticker: str, action: str, reasoning: str, confidence: float = 0.6) -> None:
    """Ejecuta una operacion discrecional (basada en investigacion de noticias/
    tendencias, no en el screener sistematico), pero pasando por los MISMOS
    limites de riesgo (RiskManager) que el ciclo automatico: tope de 10% del
    portafolio por posicion, reserva minima de efectivo, sin ventas en corto.

    Requiere credenciales de Alpaca configuradas -- solo opera contra la
    cuenta de paper trading, nunca dinero real.
    """
    if not (settings.alpaca_api_key and settings.alpaca_secret_key):
        raise RuntimeError("Se requieren credenciales de Alpaca para operar discrecional")

    notifier = get_notifier()
    broker = AlpacaBroker(settings.alpaca_api_key, settings.alpaca_secret_key)

    price = get_latest_price(ticker)
    if price is None:
        notifier.send(f"🔎 [DISCRECIONAL] {ticker}: no se pudo obtener precio, se omite")
        return

    if broker.has_pending_order(ticker):
        notifier.send(f"🔎 [DISCRECIONAL] {ticker}: ya hay una orden pendiente sin llenar, se omite")
        return

    analysis = Analysis(ticker, action, confidence, reasoning)
    held_shares = broker.positions.get(ticker, 0)
    portfolio = PortfolioState(cash=broker.cash, positions_value=broker.positions_value({ticker: price}))

    plan = RiskManager().size_trade(analysis, price, portfolio, held_shares)
    if plan is None:
        notifier.send(
            f"🔎 [DISCRECIONAL] {ticker}: no paso el chequeo de riesgo "
            f"(sin margen disponible o sin posicion para vender)"
        )
        return

    fill = broker.submit(plan)
    notifier.send(
        f"🔎 [DISCRECIONAL] {fill.action} {fill.shares} {fill.ticker} @ ${fill.price:.2f} "
        f"(valor ${fill.shares * fill.price:.2f})\nRazon: {reasoning}"
    )
