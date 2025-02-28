"""Script to call retrieval on the Kaggle dataset."""

import csv
import json
import logging

import configargparse

import sage.config
from sage.retriever import build_retriever_from_args

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main():
    parser = configargparse.ArgParser(
        description="Runs retrieval on the Kaggle dataset.", ignore_unknown_config_file_keys=True
    )
    parser.add("--benchmark", required=True, help="Path to the Kaggle dataset.")
    parser.add("--output-file", required=True, help="Path to the output file with predictions.")

    sage.config.add_config_args(parser)
    sage.config.add_llm_args(parser)  # Necessary for --multi-query-retriever, which calls an LLM.
    sage.config.add_embedding_args(parser)
    sage.config.add_vector_store_args(parser)
    sage.config.add_reranking_args(parser)
    args = parser.parse_args()
    sage.config.validate_vector_store_args(args)

    retriever = build_retriever_from_args(args)

    with open(args.benchmark, "r") as f:
        benchmark = csv.DictReader(f)
        benchmark = [row for row in benchmark]

    outputs = []
    for question_idx, item in enumerate(benchmark):
        print(f"Processing question {question_idx}...")

        retrieved = retriever.invoke(item["question"])
        # Sort by score in descending order.
        retrieved = sorted(
            retrieved, key=lambda doc: doc.metadata.get("score", doc.metadata.get("relevance_score")), reverse=True
        )
        # Keep top 3, since the Kaggle competition only evaluates the top 3.
        retrieved = retrieved[:3]
        retrieved_filenames = [doc.metadata["file_path"] for doc in retrieved]
        outputs.append((item["id"], json.dumps(retrieved_filenames)))

    with open(args.output_file, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["id", "documents"])
        csv_writer.writerows(outputs)


if __name__ == "__main__":
    main()
