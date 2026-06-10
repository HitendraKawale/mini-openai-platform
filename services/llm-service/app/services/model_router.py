"""Difficulty-based model routing.

Pure functions only (stdlib, no app imports) so the logic can be unit
tested in isolation. The route handler supplies configuration.
"""

from dataclasses import dataclass

COMPLEX_MARKERS = (
    "why",
    "how",
    "explain",
    "compare",
    "contrast",
    "analyze",
    "analyse",
    "summarize",
    "summarise",
    "design",
    "implement",
    "prove",
    "derive",
    "step by step",
    "trade-off",
    "tradeoff",
    "architecture",
    "optimize",
    "debug",
)

CODE_MARKERS = ("```", "def ", "class ", "function ", "SELECT ", "import ")

AUTO_MODEL = "auto"


@dataclass
class RoutingDecision:
    model: str
    decision: str  # "explicit" | "routed_small" | "routed_large" | "default"
    difficulty: float | None = None


def score_difficulty(prompt: str) -> float:
    """Heuristic difficulty score in [0, 1].

    Long prompts (e.g. RAG prompts carrying retrieved context), reasoning
    keywords, multi-part questions and code all push the score up.
    """
    words = prompt.split()
    lowered = prompt.lower()

    length_score = min(len(words) / 200.0, 1.0)
    marker_hits = sum(1 for marker in COMPLEX_MARKERS if marker in lowered)
    marker_score = min(marker_hits / 3.0, 1.0)
    question_score = min(lowered.count("?") / 3.0, 1.0)
    code_score = 1.0 if any(marker in prompt for marker in CODE_MARKERS) else 0.0

    score = (
        0.45 * length_score
        + 0.35 * marker_score
        + 0.10 * question_score
        + 0.10 * code_score
    )
    return round(min(score, 1.0), 4)


def choose_model(
    prompt: str,
    requested_model: str | None,
    small_model: str,
    large_model: str,
    routing_enabled: bool,
    threshold: float,
) -> RoutingDecision:
    if requested_model and requested_model != AUTO_MODEL:
        return RoutingDecision(model=requested_model, decision="explicit")

    if not routing_enabled:
        return RoutingDecision(model=large_model, decision="default")

    difficulty = score_difficulty(prompt)
    if difficulty < threshold:
        return RoutingDecision(
            model=small_model, decision="routed_small", difficulty=difficulty
        )
    return RoutingDecision(
        model=large_model, decision="routed_large", difficulty=difficulty
    )


def fallback_model(
    chosen_model: str, small_model: str, large_model: str
) -> str | None:
    """The other tier to try when the chosen model fails, if any."""
    if chosen_model == small_model and large_model != small_model:
        return large_model
    if chosen_model == large_model and small_model != large_model:
        return small_model
    return None
