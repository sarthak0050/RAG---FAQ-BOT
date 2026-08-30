from __future__ import annotations

import json
import sys

from code.retrieval.retriever import answer_question


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    question = " ".join(args).strip()
    if not question:
        question = sys.stdin.read().strip()
    if not question:
        print("usage: python -m code.retrieval \"your question\"", file=sys.stderr)
        return 2

    result = answer_question(question)

    print("=" * 70)
    print("Q:", question)
    print("=" * 70)
    if result.get("warning"):
        print("WARNING:", result["warning"])
    kind = result["kind"]
    print(f"KIND: {kind}")

    if result.get("generation_error"):
        print(f"GENERATION: skipped ({result['generation_error']})")
        print("(retrieval ran; set MISTRAL_API_KEY to enable answer generation)")
    else:
        print()
        print("ANSWER:", result["answer"])

    if result.get("source_url"):
        print("SOURCE:", result["source_url"])
    if result.get("last_updated"):
        print("LAST UPDATED:", "Last updated from sources: " + result["last_updated"])

    print()
    print("RETRIEVED (top chunks):")
    if result["retrieved"]:
        for row in result["retrieved"]:
            print(
                f"  {row['score']}  {row['fund_name'][:30]:<30} "
                f"{row['source_url']}"
            )
    else:
        print("  (no retrieval ran - gated before embedding)")

    debug = json.dumps(result, ensure_ascii=False, indent=2)
    print()
    print("RAW RESULT:")
    print(debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())