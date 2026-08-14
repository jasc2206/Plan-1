from .alpaca_broker import AlpacaBroker
from .broker import PaperBrokerStub
from .config import settings
from .decision_agent import DecisionAgent
from .notifier import get_notifier
from .risk import PortfolioState, RiskManager
from .screener import StockScreener
from .state import load_state, save_state


def make_broker():
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        return AlpacaBroker(settings.alpaca_api_key, settings.alpaca_secret_key), False
    saved = load_state(settings.starting_cash)
    return PaperBrokerStub(starting_cash=saved["cash"], positions=saved["positions"]), True


def run_cycle() -> None:
    notifier = get_notifier()
    broker, is_simulated = make_broker()
    mode = "SIMULADO en memoria (sin credenciales Alpaca)" if is_simulated else "Alpaca PAPER TRADING"
    notifier.send(f"=== Ciclo de trading [{mode}] ===")

    candidates = StockScreener().screen()
    if not candidates:
        notifier.send("No se encontraron candidatos que cumplan los criterios de screening.")
        return

    notifier.send(f"Watchlist ({len(candidates)}): " + ", ".join(c.ticker for c in candidates))

    agent = DecisionAgent()
    risk = RiskManager()

    for candidate in candidates:
        analysis = agent.analyze(candidate)
        notifier.send(
            f"{candidate.ticker}: {analysis.decision} "
            f"(confianza {analysis.confidence:.0%}) - {analysis.reasoning}"
        )

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

    if is_simulated:
        save_state(broker.cash, broker.positions)

    notifier.send(f"Efectivo restante: ${broker.cash:,.2f}")
    notifier.send(f"Posiciones: {broker.positions}")
    notifier.send("=== Fin del ciclo ===")


if __name__ == "__main__":
    run_cycle()
