def build_rag_prompt(query: str, context_chunks: list[str]) -> str:
    context_block = "\n\n".join(
        [f"[Context {idx+1}]\n{chunk}" for idx, chunk in enumerate(context_chunks)]
    )

    return f"""You are a helpful AI assistant.
Answer the user's question using only the provided context.
If the answer is not contained in the context, say that the context does not contain enough information.

Context:
{context_block}

Question:
{query}

Answer:"""