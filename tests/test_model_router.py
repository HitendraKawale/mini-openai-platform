import importlib.util
from pathlib import Path

# llm-service and rag-service both use the top-level package name "app",
# and conftest puts rag-service on sys.path. Load the router (which is
# dependency-free by design) directly from its file instead.
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "llm-service"
    / "app"
    / "services"
    / "model_router.py"
)
spec = importlib.util.spec_from_file_location("model_router", MODULE_PATH)
model_router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_router)

SMALL = "llama3.2:3b"
LARGE = "phi3:latest"


def choose(prompt, requested=None, enabled=True, threshold=0.3):
    return model_router.choose_model(
        prompt=prompt,
        requested_model=requested,
        small_model=SMALL,
        large_model=LARGE,
        routing_enabled=enabled,
        threshold=threshold,
    )


def test_simple_question_scores_easier_than_reasoning_question():
    simple = model_router.score_difficulty("What is the capital of France?")
    complex_ = model_router.score_difficulty(
        "Explain step by step why HNSW indexes trade recall for speed, "
        "and compare the architecture against brute-force search."
    )

    assert simple < complex_


def test_long_rag_prompt_scores_high():
    rag_prompt = "Context:\n" + " ".join(["word"] * 300) + "\nQuestion: why?"

    assert model_router.score_difficulty(rag_prompt) >= 0.45


def test_scores_stay_in_unit_interval():
    assert 0.0 <= model_router.score_difficulty("") <= 1.0
    assert 0.0 <= model_router.score_difficulty("why " * 500 + "?" * 50) <= 1.0


def test_simple_prompt_routes_small():
    decision = choose("What is the capital of France?")

    assert decision.model == SMALL
    assert decision.decision == "routed_small"
    assert decision.difficulty is not None


def test_hard_prompt_routes_large():
    decision = choose(
        "Explain step by step why HNSW indexes trade recall for speed, "
        "and compare the architecture against brute-force search. "
        "How would you optimize and debug a slow index?"
    )

    assert decision.model == LARGE
    assert decision.decision == "routed_large"


def test_explicit_model_is_pinned():
    decision = choose("What is 2+2?", requested="mistral:latest")

    assert decision.model == "mistral:latest"
    assert decision.decision == "explicit"
    assert decision.difficulty is None


def test_auto_is_treated_as_unspecified():
    decision = choose("What is 2+2?", requested="auto")

    assert decision.decision == "routed_small"


def test_disabled_routing_uses_large_model():
    decision = choose("What is 2+2?", enabled=False)

    assert decision.model == LARGE
    assert decision.decision == "default"


def test_fallback_model_is_the_other_tier():
    assert model_router.fallback_model(SMALL, SMALL, LARGE) == LARGE
    assert model_router.fallback_model(LARGE, SMALL, LARGE) == SMALL
    assert model_router.fallback_model(SMALL, SMALL, SMALL) is None
