#!/usr/bin/env python3
"""RAG evaluation harness with quality gates.

Uploads the eval corpus, runs every golden question against the RAG
service, and grades the results:

- retrieval: hit rate (recall@k) and mean reciprocal rank, judged by
  whether retrieved chunks contain the expected phrases
- answers (optional, requires the LLM): faithfulness scored 1-5 by an
  LLM judge comparing the generated answer to the reference answer

Exits non-zero when any metric falls below its threshold, so it can be
used as a CI quality gate:

    python evals/run_eval.py --retrieval-only --min-hit-rate 0.8 --min-mrr 0.5
"""

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

from metrics import find_hit_rank, hit_rate, mean_reciprocal_rank

EVALS_DIR = Path(__file__).resolve().parent

JUDGE_PROMPT_TEMPLATE = """You are grading the answer of a question-answering system.

Question:
{query}

Reference answer:
{reference}

System answer:
{answer}

Score how well the system answer agrees with the reference answer on a scale of 1 to 5:
5 = fully consistent with the reference
3 = partially correct or incomplete
1 = wrong, contradictory, or refuses to answer

Reply with only a single integer from 1 to 5.

Score:"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the RAG evaluation harness")
    parser.add_argument("--base-url", default="http://localhost:8003",
                        help="rag-service base URL")
    parser.add_argument("--llm-url", default="http://localhost:8001",
                        help="llm-service base URL (used for the judge)")
    parser.add_argument("--golden", default=str(EVALS_DIR / "golden.jsonl"))
    parser.add_argument("--corpus", default=str(EVALS_DIR / "corpus"))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--retrieval-only", action="store_true",
                        help="skip generation and judging (no LLM needed)")
    parser.add_argument("--skip-upload", action="store_true",
                        help="assume the corpus is already indexed")
    parser.add_argument("--min-hit-rate", type=float, default=0.0)
    parser.add_argument("--min-mrr", type=float, default=0.0)
    parser.add_argument("--min-faithfulness", type=float, default=0.0,
                        help="minimum average judge score (1-5 scale)")
    parser.add_argument("--report", default=str(EVALS_DIR / "report.json"))
    parser.add_argument("--timeout", type=float, default=180.0)
    return parser.parse_args()


def load_golden(path: str) -> list[dict]:
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def upload_corpus(client: httpx.Client, base_url: str, corpus_dir: str) -> None:
    corpus_path = Path(corpus_dir)
    files = sorted(p for p in corpus_path.iterdir() if p.is_file())
    if not files:
        raise SystemExit(f"No corpus files found in {corpus_dir}")

    for path in files:
        response = client.post(
            f"{base_url}/documents/upload",
            files={"file": (path.name, path.read_bytes(), "text/plain")},
        )
        response.raise_for_status()
        data = response.json()
        print(f"  uploaded {path.name}: {data['chunk_count']} chunks")


def judge_answer(client: httpx.Client, llm_url: str, query: str,
                 reference: str, answer: str) -> int | None:
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        query=query, reference=reference, answer=answer
    )
    response = client.post(
        f"{llm_url}/generate",
        json={
            "prompt": prompt,
            "max_new_tokens": 8,
            "temperature": 0.0,
            "do_sample": False,
        },
    )
    response.raise_for_status()
    text = response.json()["generated_text"]

    match = re.search(r"[1-5]", text)
    return int(match.group()) if match else None


def main() -> int:
    args = parse_args()
    golden = load_golden(args.golden)

    with httpx.Client(timeout=args.timeout) as client:
        if not args.skip_upload:
            print(f"Uploading corpus from {args.corpus}")
            upload_corpus(client, args.base_url, args.corpus)

        endpoint = "/retrieve" if args.retrieval_only else "/query"
        results = []

        print(f"\nRunning {len(golden)} golden queries against {endpoint}")
        for item in golden:
            response = client.post(
                f"{args.base_url}{endpoint}",
                json={"query": item["query"], "top_k": args.top_k},
            )
            response.raise_for_status()
            data = response.json()

            source_texts = [s["text"] for s in data["sources"]]
            rank = find_hit_rank(source_texts, item["expected_phrases"])

            result = {
                "id": item["id"],
                "query": item["query"],
                "hit_rank": rank,
            }

            if not args.retrieval_only:
                result["answer"] = data["answer"]
                result["cached"] = data.get("cached", False)
                result["judge_score"] = judge_answer(
                    client,
                    args.llm_url,
                    item["query"],
                    item["reference_answer"],
                    data["answer"],
                )

            results.append(result)
            rank_label = f"rank {rank}" if rank else "MISS"
            judge_label = (
                f"  judge {result['judge_score']}/5"
                if result.get("judge_score") is not None
                else ""
            )
            print(f"  {item['id']}  {rank_label:7}{judge_label}  {item['query']}")

    ranks = [r["hit_rank"] for r in results]
    summary = {
        "queries": len(results),
        "top_k": args.top_k,
        "hit_rate": round(hit_rate(ranks), 4),
        "mrr": round(mean_reciprocal_rank(ranks), 4),
    }

    judge_scores = [
        r["judge_score"] for r in results if r.get("judge_score") is not None
    ]
    if judge_scores:
        summary["avg_faithfulness"] = round(
            sum(judge_scores) / len(judge_scores), 4
        )

    report = {"summary": summary, "results": results}
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\nSummary: {json.dumps(summary)}")
    print(f"Report written to {args.report}")

    failures = []
    if summary["hit_rate"] < args.min_hit_rate:
        failures.append(
            f"hit_rate {summary['hit_rate']} < min {args.min_hit_rate}"
        )
    if summary["mrr"] < args.min_mrr:
        failures.append(f"mrr {summary['mrr']} < min {args.min_mrr}")
    if judge_scores and summary["avg_faithfulness"] < args.min_faithfulness:
        failures.append(
            f"avg_faithfulness {summary['avg_faithfulness']} "
            f"< min {args.min_faithfulness}"
        )

    if failures:
        print("\nQUALITY GATE FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nQuality gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
