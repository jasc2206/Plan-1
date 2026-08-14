from .alpaca_broker import AlpacaBroker
from .broker import PaperBrokerStub
from .config import settings
from .decision_agent import DecisionAgent
from .notifier import get_notifier
from .risk import PortfolioState, RiskManager
from .screener import StockScreener, get_latest_price
from .state import load_state, save_state


def make_broker():
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        return AlpacaBroker(settings.alpaca_api_key, settings.alpaca_secret_key), False
    saved = load_state(settings.starting_cash)
    broker = PaperBrokerStub(
        starting_cash=saved["cash"],
        positions=saved["positions"],
        cost_basis=saved["cost_basis"],
        realized_pnl=saved["realized_pnl"],
    )
    return broker, True


def report_pnl(notifier, broker, candidates) -> None:
    held_tickers = [t for t, qty in broker.positions.items() if qty > 0]
    if not held_tickers:
        return

    known_prices = {c.ticker: c.price for c in candidates}
    prices = {t: known_prices.get(t, get_latest_price(t)) for t in held_tickers}
    prices = {t: p for t, p in prices.items() if p is not None}

    pnl_list = broker.position_pnl(prices)
    if not pnl_list:
        return

    notifier.send("--- P&L por posicion ---")
    total_unrealized = 0.0
    for pnl in pnl_list:
        emoji = "📈" if pnl.unrealized_pnl >= 0 else "📉"
        notifier.send(
            f"{emoji} {pnl.ticker}: {pnl.shares} @ costo prom ${pnl.avg_cost:.2f} -> "
            f"actual ${pnl.current_price:.2f} | P&L ${pnl.unrealized_pnl:+,.2f} ({pnl.unrealized_pnl_pct:+.2f}%)"
        )
        total_unrealized += pnl.unrealized_pnl

    notifier.send(f"P&L no realizado (total): ${total_unrealized:+,.2f}")
    if hasattr(broker, "realized_pnl"):
        notifier.send(f"P&L realizado acumulado: ${broker.realized_pnl:+,.2f}")


def run_cycle() -> None:
    notifier = get_notifier()
    broker, is_simulated = make_broker()
    mode = "SIMULADO en memoria (sin credenciales Alpaca)" if is_simulated else "Alpaca PAPER TRADING"
    notifier.send(f"=== Ciclo de trading [{mode}] ===")

    candidates = StockScreener().screen()
    if not candidates:
        notifier.send("No se encontraron candidatos que cumplan los criterios de screening.")
    else:
        notifier.send(f"Watchlist ({len(candidates)}): " + ", ".join(c.ticker for c in candidates))

        agent = DecisionAgent()
        risk = RiskManager()

        for candidate in candidates:
            analysis = agent.analyze(candidate)
            notifier.send(
                f"{candidate.ticker}: {analysis.decision} "
                f"(confianza {analysis.confidence:.0%}) - {analysis.reasoning}"
            )

            if broker.has_pending_order(candidate.ticker):
                notifier.send(f"{candidate.ticker}: ya hay una orden pendiente sin llenar, se omite para no duplicar")
                continue

            portfolio = PortfolioState(
                cash=broker.cash,
                positions_value=broker.positions_value({candidate.ticker: candidate.price}),
            )
            held_shares = broker.positions.get(candidate.ticker, 0)
            plan = risk.size_trade(analysis, candidate.price, portfolio, held_shares)
            if plan is None:
                continue

            fill = broker.submit(plan)
            notifier.send(
                f"[{'SIMULADO' if is_simulated else 'ALPACA PAPER'}] {fill.action} {fill.shares} "
                f"{fill.ticker} @ ${fill.price:.2f} (valor ${fill.shares * fill.price:.2f})"
            )

    report_pnl(notifier, broker, candidates)

    if is_simulated:
        save_state(broker.cash, broker.positions, broker.cost_basis, broker.realized_pnl)

    notifier.send(f"Efectivo restante: ${broker.cash:,.2f}")
    notifier.send(f"Posiciones: {broker.positions}")
    notifier.send("=== Fin del ciclo ===")


if __name__ == "__main__":
    run_cycle()
