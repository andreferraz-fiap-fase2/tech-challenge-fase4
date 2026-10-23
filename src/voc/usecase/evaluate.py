"""Smoke evaluation reproduzível; não substitui avaliação humana de relevância."""

import json
from dataclasses import asdict
from pathlib import Path

from voc.domain.entities import Filters
from voc.infrastructure.storage import digest, read_json, write_json
from voc.views.cli import make_service


def evaluate(root: Path, generate: bool = False, split: str = "test") -> dict[str, object]:
    cases = json.loads((root / "evaluation/questions.json").read_text(encoding="utf-8"))
    service = make_service(root)
    rows = []
    for case in cases:
        if split != "all" and case["split"] != split:
            continue
        result = service.ask(
            case["question"], Filters(**case.get("filters", {})), retrieve_only=not generate
        )
        has_evidence = result.status in {"answered", "generation_abstained", "retrieval_only"}
        rows.append(
            {
                "case_id": case["id"],
                "expected_answerable": case["answerable"],
                "gate_correct": has_evidence == case["answerable"],
                "result": asdict(result),
            }
        )
        print(f"{case['id']}: {result.status}", flush=True)
    answerable = [row for row in rows if row["expected_answerable"]]
    unanswerable = [row for row in rows if not row["expected_answerable"]]
    report = {
        "source_sha256": {
            path.relative_to(root).as_posix(): digest(path)
            for path in sorted((root / "src").rglob("*.py"))
        },
        "split": split,
        "generation_executed": generate,
        "cases": len(rows),
        "evidence_gate_accuracy": sum(row["gate_correct"] for row in rows) / len(rows),
        "answerable_gate_recall": sum(row["gate_correct"] for row in answerable) / len(answerable)
        if answerable
        else None,
        "unanswerable_abstention_rate": sum(row["gate_correct"] for row in unanswerable)
        / len(unanswerable)
        if unanswerable
        else None,
        "generated_answers": sum(row["result"]["status"] == "answered" for row in rows),
        "note": "Pequeno conjunto autoral de smoke tests. Gate correto não prova relevância ou suporte factual. Testes de referências avaliam formato, não verdade. Nenhum recall de documentos é estimado.",
        "config": read_json(root / "config/models.json"),
        "questions_sha256": digest(root / "evaluation/questions.json"),
        "rows": rows,
    }
    write_json(
        root / f"reports/evaluation_{split}_{'rag' if generate else 'retrieval'}.json", report
    )
    return {key: value for key, value in report.items() if key != "rows"}
