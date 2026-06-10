from metrics import find_hit_rank, hit_rate, mean_reciprocal_rank


def test_find_hit_rank_returns_first_matching_chunk():
    sources = [
        "chunking splits documents into pieces",
        "similarity is measured with cosine similarity between vectors",
        "cosine similarity compares angles",
    ]

    assert find_hit_rank(sources, ["cosine similarity"]) == 2


def test_find_hit_rank_is_case_and_whitespace_insensitive():
    sources = ["HNSW stands for Hierarchical   Navigable Small World."]

    assert find_hit_rank(sources, ["hierarchical navigable small world"]) == 1


def test_find_hit_rank_returns_none_on_miss():
    sources = ["completely unrelated text"]

    assert find_hit_rank(sources, ["cosine similarity"]) is None


def test_find_hit_rank_matches_any_phrase():
    sources = ["the overlap region protects facts that straddle two chunks"]

    assert find_hit_rank(sources, ["share a band of words", "straddle two chunks"]) == 1


def test_hit_rate():
    assert hit_rate([1, None, 2, None]) == 0.5
    assert hit_rate([]) == 0.0


def test_mean_reciprocal_rank():
    assert mean_reciprocal_rank([1, 2, None, 4]) == (1.0 + 0.5 + 0.25) / 4
    assert mean_reciprocal_rank([]) == 0.0
    assert mean_reciprocal_rank([None, None]) == 0.0
