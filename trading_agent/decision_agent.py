from dataclasses import dataclass
from typing import Literal

from .config import settings
from .screener import Candidate

Decision = Literal["BUY", "SELL", "HOLD"]
VALID_DECISIONS = {"BUY", "SELL", "HOLD"}


@dataclass
class Analysis:
    ticker: str
    decision: Decision
    confidence: float
    reasoning: str


class DecisionAgent:
    """Usa Claude si hay ANTHROPIC_API_KEY configurada; si no, cae a reglas simples de momentum."""

    def analyze(self, candidate: Candidate) -> Analysis:
        if settings.anthropic_api_key:
            return self._analyze_with_claude(candidate)
        return self._analyze_with_rules(candidate)

    def _analyze_with_rules(self, candidate: Candidate) -> Analysis:
        if candidate.price_change_pct >= settings.min_price_change_pct:
            return Analysis(
                candidate.ticker, "BUY", 0.5,
                f"Momentum positivo: {candidate.price_change_pct:+.2f}% con volumen alto",
            )
        if candidate.price_change_pct <= -settings.min_price_change_pct:
            return Analysis(
                candidate.ticker, "SELL", 0.5,
                f"Momentum negativo: {candidate.price_change_pct:+.2f}%",
            )
        return Analysis(candidate.ticker, "HOLD", 0.5, "Movimiento insuficiente para actuar")

    def _analyze_with_claude(self, candidate: Candidate) -> Analysis:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        prompt = (
            f"Accion {candidate.ticker}: precio ${candidate.price:.2f}, "
            f"cambio {candidate.price_change_pct:+.2f}%, volumen medio {candidate.avg_volume:,.0f}. "
            "Responde en una sola linea con el formato exacto: DECISION|CONFIANZA|RAZON "
            "donde DECISION es BUY, SELL o HOLD, CONFIANZA es un numero entre 0 y 1."
        )
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        parts = (text.split("|", 2) + ["HOLD", "0.5", ""])[:3]
        decision_str, confidence_str, reasoning = parts

        decision: Decision = decision_str.strip().upper() if decision_str.strip().upper() in VALID_DECISIONS else "HOLD"
        try:
            confidence = max(0.0, min(1.0, float(confidence_str.strip())))
        except ValueError:
            confidence = 0.5

        return Analysis(candidate.ticker, decision, confidence, reasoning.strip() or "sin justificacion")
