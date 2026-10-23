"""CLI reprodutível do pipeline e da consulta."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voc.usecase.rag import RagService


def make_service(root: Path) -> "RagService":
    from voc.infrastructure.index import VectorIndex
    from voc.infrastructure.models import LocalEmbedder, LocalGenerator
    from voc.infrastructure.storage import read_json
    from voc.usecase.rag import RagService

    settings = read_json(root / "config/models.json")
    return RagService(
        VectorIndex(root, LocalEmbedder(root)),
        LocalGenerator(root),
        min_similarity=float(settings["min_similarity"]),
        min_evidence=int(settings["min_evidence"]),
        top_k=int(settings["top_k"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Voz do Cliente — RAG local sobre avaliações Olist"
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    commands = parser.add_subparsers(dest="command", required=True)
    download_parser = commands.add_parser("download", help="Baixar os CSVs oficiais Olist")
    download_parser.add_argument("--zip", type=Path, help="Usar ZIP já baixado do Kaggle")
    commands.add_parser("models", help="Baixar modelos locais em revisões fixas")
    commands.add_parser("prepare", help="Limpar textos, construir metadados e auditar")
    commands.add_parser("index", help="Gerar embeddings e índice vetorial")
    commands.add_parser("reproduce", help="Reconstruir em pasta temporária e comparar hashes")
    ask = commands.add_parser("ask", help="Consultar avaliações com evidências")
    ask.add_argument("question")
    ask.add_argument("--min-score", type=int, default=1)
    ask.add_argument("--max-score", type=int, default=5)
    ask.add_argument("--start-date", default="")
    ask.add_argument("--end-date", default="")
    ask.add_argument("--category", default="")
    ask.add_argument("--late-only", action="store_true")
    ask.add_argument("--retrieve-only", action="store_true")
    ask.add_argument("--output", type=Path)
    evaluate = commands.add_parser("evaluate", help="Avaliar recuperação e abstenção")
    evaluate.add_argument("--generate", action="store_true", help="Também executar o LLM local")
    evaluate.add_argument("--split", choices=["dev", "test", "all"], default="test")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "download":
        from voc.infrastructure.dataset import download

        download(root, args.zip)
        result = {"status": "downloaded"}
    elif args.command == "models":
        from voc.infrastructure.models import fetch_models

        fetch_models(root)
        result = {"status": "models_downloaded"}
    elif args.command == "prepare":
        from voc.infrastructure.dataset import prepare

        result = prepare(root)
    elif args.command == "index":
        from voc.infrastructure.index import build_index
        from voc.infrastructure.models import LocalEmbedder

        result = build_index(root, LocalEmbedder(root))
    elif args.command == "ask":
        from voc.domain.entities import Filters

        result = asdict(
            make_service(root).ask(
                args.question,
                Filters(
                    args.min_score,
                    args.max_score,
                    args.start_date,
                    args.end_date,
                    args.category,
                    args.late_only,
                ),
                retrieve_only=args.retrieve_only,
            )
        )
        if args.output:
            from voc.infrastructure.storage import write_json

            write_json(args.output, result)
    elif args.command == "reproduce":
        from voc.usecase.reproduce import reproduce

        result = reproduce(root)
    else:
        from voc.usecase.evaluate import evaluate

        result = evaluate(root, generate=args.generate, split=args.split)
    print(json.dumps(result, ensure_ascii=False, indent=2))
