from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from voc.domain.entities import Filters
from voc.infrastructure.index import VectorIndex, build_index
from voc.infrastructure.storage import write_json


class FakeEmbedder:
    def chunks(self, text: str) -> list[str]:
        return [text]

    def encode(self, texts: list[str], progress: bool = False) -> np.ndarray:
        return np.array(
            [[1, 0] if "atraso" in text else [0, 1] for text in texts], dtype=np.float32
        )


def build_fixture(root: Path) -> VectorIndex:
    write_json(
        root / "config/models.json",
        {
            "embedding_model": "fake",
            "embedding_revision": "fixed",
            "document_tokens": 120,
            "chunk_overlap_tokens": 20,
        },
    )
    records = [
        {
            "document_id": "a",
            "review_id": "ra",
            "order_id": "oa",
            "text": "atraso",
            "score": 1,
            "date": "2018-01-05",
            "purchase_date": "2018-01-01",
            "categories": "a|b",
            "late": True,
        },
        {
            "document_id": "b",
            "review_id": "rb",
            "order_id": "ob",
            "text": "atraso",
            "score": 5,
            "date": "2018-01-06",
            "purchase_date": "2018-01-02",
            "categories": "b",
            "late": False,
        },
        {
            "document_id": "c",
            "review_id": "rc",
            "order_id": "oc",
            "text": "ótimo",
            "score": 5,
            "date": "2018-03-01",
            "purchase_date": "2018-02-01",
            "categories": "c",
            "late": pd.NA,
        },
    ]
    target = root / "data/processed/reviews.parquet"
    target.parent.mkdir(parents=True)
    pd.DataFrame(records).to_parquet(target, index=False)
    embedder = FakeEmbedder()
    build_index(root, embedder)
    return VectorIndex(root, embedder)


def test_filter_is_applied_before_top_k_and_deduplication(tmp_path: Path) -> None:
    index = build_fixture(tmp_path)
    rows, count = index.search("atraso", Filters(min_score=5), top_k=1)
    assert rows[0].document_id == "b"
    assert count == 2
    rows, count = index.search("atraso", Filters(), top_k=3)
    assert count == 3
    assert len(rows) == 2  # avaliações textualmente idênticas não inflacionam o contexto


def test_delivery_missing_is_not_considered_late(tmp_path: Path) -> None:
    index = build_fixture(tmp_path)
    rows, count = index.search("atraso", Filters(late_only=True))
    assert count == 1
    assert rows[0].document_id == "a"


def test_category_membership_and_purchase_date_filter(tmp_path: Path) -> None:
    index = build_fixture(tmp_path)
    rows, count = index.search("atraso", Filters(category="a", end_date="2018-01-02"))
    assert count == 1 and rows[0].document_id == "a"
    assert index.search("atraso", Filters(start_date="2030-01-01")) == ([], 0)


def test_integrity_failure_does_not_silently_load_changed_vectors(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    (tmp_path / "artifacts/index/embeddings.npy").write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="alterado"):
        VectorIndex(tmp_path, FakeEmbedder())
