from app.services.prompt_builder import build_rag_prompt


def test_prompt_builder_includes_context_and_question():
    query = "How does RAG work?"
    context_chunks = [
        "RAG retrieves relevant chunks.",
        "The language model answers using retrieved context.",
    ]

    prompt = build_rag_prompt(query, context_chunks)

    assert "How does RAG work?" in prompt
    assert "RAG retrieves relevant chunks." in prompt
    assert "The language model answers using retrieved context." in prompt
    assert "Answer:" in prompt
