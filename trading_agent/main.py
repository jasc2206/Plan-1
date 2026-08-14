from .broker import PaperBrokerStub
from .config import settings
from .decision_agent import DecisionAgent
from .notifier import get_notifier
from .risk import PortfolioState, RiskManager
from .screener import StockScreener


def run_cycle() -> None:
    notifier = get_notifier()
    notifier.send("=== Ciclo de trading [DRY-RUN, sin broker real conectado] ===")

    candidates = StockScreener().screen()
    if not candidates:
        notifier.send("No se encontraron candidatos que cumplan los criterios de screening.")
        return

    notifier.send(f"Watchlist ({len(candidates)}): " + ", ".join(c.ticker for c in candidates))

    agent = DecisionAgent()
    risk = RiskManager()
    broker = PaperBrokerStub(starting_cash=settings.starting_cash)

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
            f"[SIMULADO] {fill.action} {fill.shares} {fill.ticker} @ ${fill.price:.2f} "
            f"(valor ${fill.shares * fill.price:.2f})"
        )

    notifier.send(f"Efectivo simulado restante: ${broker.cash:,.2f}")
    notifier.send(f"Posiciones simuladas: {broker.positions}")
    notifier.send("=== Fin del ciclo ===")


if __name__ == "__main__":
    run_cycle()
