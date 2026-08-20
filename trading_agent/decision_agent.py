from dataclasses import dataclass
from typing import Literal

from .config import settings
from .screener import Candidate

Decision = Literal["BUY", "SELL", "HOLD"]
VALID_DECISIONS = {"BUY", "SELL", "HOLD"}

RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0


@dataclass
class Analysis:
    ticker: str
    decision: Decision
    confidence: float
    reasoning: str


class DecisionAgent:
    """Usa Claude si hay ANTHROPIC_API_KEY configurada; si no, cae a reglas de
    momentum confirmadas con RSI y MACD."""

    def analyze(self, candidate: Candidate) -> Analysis:
        if settings.anthropic_api_key:
            return self._analyze_with_claude(candidate)
        return self._analyze_with_rules(candidate)

    def _analyze_with_rules(self, candidate: Candidate) -> Analysis:
        momentum_buy = candidate.price_change_pct >= settings.min_price_change_pct
        momentum_sell = candidate.price_change_pct <= -settings.min_price_change_pct

        macd_bullish = candidate.macd is not None and candidate.macd > candidate.macd_signal
        macd_bearish = candidate.macd is not None and candidate.macd < candidate.macd_signal
        rsi_text = f", RSI(14)={candidate.rsi:.1f}" if candidate.rsi is not None else ""

        if momentum_buy:
            if candidate.rsi is not None and candidate.rsi >= RSI_OVERBOUGHT:
                return Analysis(
                    candidate.ticker, "HOLD", 0.5,
                    f"Momentum positivo ({candidate.price_change_pct:+.2f}%) pero "
                    f"RSI en sobrecompra ({candidate.rsi:.1f}), se descarta la compra",
                )
            confidence = 0.5 + (0.15 if macd_bullish else 0.0)
            confirm = "MACD confirma" if macd_bullish else "MACD no confirma"
            return Analysis(
                candidate.ticker, "BUY", min(confidence, 0.9),
                f"Momentum positivo: {candidate.price_change_pct:+.2f}%{rsi_text}, {confirm}",
            )

        if momentum_sell:
            if candidate.rsi is not None and candidate.rsi <= RSI_OVERSOLD:
                return Analysis(
                    candidate.ticker, "HOLD", 0.5,
                    f"Momentum negativo ({candidate.price_change_pct:+.2f}%) pero "
                    f"RSI en sobreventa ({candidate.rsi:.1f}), se descarta la venta",
                )
            confidence = 0.5 + (0.15 if macd_bearish else 0.0)
            confirm = "MACD confirma" if macd_bearish else "MACD no confirma"
            return Analysis(
                candidate.ticker, "SELL", min(confidence, 0.9),
                f"Momentum negativo: {candidate.price_change_pct:+.2f}%{rsi_text}, {confirm}",
            )

        return Analysis(candidate.ticker, "HOLD", 0.5, "Movimiento insuficiente para actuar")

    def _analyze_with_claude(self, candidate: Candidate) -> Analysis:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        indicators = ""
        if candidate.rsi is not None:
            indicators += f", RSI(14)={candidate.rsi:.1f}"
        if candidate.macd is not None:
            indicators += (
                f", MACD={candidate.macd:.4f} (señal={candidate.macd_signal:.4f}, "
                f"histograma={candidate.macd_hist:.4f})"
            )
        prompt = (
            f"Accion {candidate.ticker}: precio ${candidate.price:.2f}, "
            f"cambio {candidate.price_change_pct:+.2f}%, volumen medio {candidate.avg_volume:,.0f}{indicators}. "
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
