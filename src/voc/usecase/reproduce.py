"""Reconstrução desde os CSVs de origem em diretório vazio e temporário."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from voc.domain.entities import Filters
from voc.infrastructure.dataset import download, prepare
from voc.infrastructure.index import VectorIndex, build_index
from voc.infrastructure.models import LocalEmbedder
from voc.infrastructure.storage import digest, write_json


def reproduce(root: Path) -> dict[str, object]:
    embedder = LocalEmbedder(root)
    original = VectorIndex(root, embedder)
    with TemporaryDirectory(prefix="fiap-voc-reproduce-") as temporary:
        rebuilt = Path(temporary)
        (rebuilt / "config").mkdir()
        shutil.copyfile(root / "config/models.json", rebuilt / "config/models.json")
        download(rebuilt, root / "data/raw/olist.zip")
        prepare(rebuilt)
        build_index(rebuilt, embedder)
        paths = [
            "data/processed/reviews.parquet",
            "artifacts/index/chunks.parquet",
            "artifacts/index/embeddings.npy",
        ]
        files = {
            name: {"expected": digest(root / name), "reproduced": digest(rebuilt / name)}
            for name in paths
        }
        equal = all(row["expected"] == row["reproduced"] for row in files.values())
        replica = VectorIndex(rebuilt, embedder)
        query = "atraso na entrega"
        a, _ = original.search(query, Filters(max_score=2))
        b, _ = replica.search(query, Filters(max_score=2))
        same_ids = [item.document_id for item in a] == [item.document_id for item in b]
        same_scores = bool(
            np.allclose(
                [item.similarity for item in a], [item.similarity for item in b], atol=1e-7, rtol=0
            )
        )
        report = {
            "status": "verified" if equal and same_ids and same_scores else "diverged",
            "files": files,
            "exact_hashes_equal": equal,
            "retrieval_ids_equal": same_ids,
            "retrieval_scores_equal_atol_1e_7": same_scores,
            "query": query,
            "config_sha256": digest(root / "config/models.json"),
            "note": "Reconstrói preparação, chunks e embeddings desde o ZIP original, em pasta temporária. Reutiliza os pesos locais congelados; não retreina nem baixa outro modelo. Geração é validada separadamente na avaliação RAG e no smoke da interface.",
        }
    write_json(root / "reports/reproducibility.json", report)
    if report["status"] != "verified":
        raise ValueError("Reprodução divergiu. Consulte reports/reproducibility.json.")
    return report
