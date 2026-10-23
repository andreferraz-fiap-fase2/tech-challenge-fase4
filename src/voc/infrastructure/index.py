"""Índice vetorial exato de cosseno: filtro antes do ranking e uma evidência por texto."""

from pathlib import Path

import numpy as np
import pandas as pd

from voc.domain.entities import Evidence, Filters
from voc.infrastructure.models import LocalEmbedder
from voc.infrastructure.storage import digest, read_json, write_json


def build_index(root: Path, embedder: LocalEmbedder) -> dict[str, object]:
    source = root / "data/processed/reviews.parquet"
    documents = pd.read_parquet(source)
    rows: list[dict[str, str | int]] = []
    for doc in documents.itertuples(index=False):
        for number, chunk in enumerate(embedder.chunks(doc.text)):
            rows.append({"document_id": doc.document_id, "chunk_id": number, "chunk": chunk})
    chunks = pd.DataFrame(rows)
    vectors = embedder.encode(chunks.chunk.tolist(), progress=True)
    target = root / "artifacts/index"
    target.mkdir(parents=True, exist_ok=True)
    chunks.to_parquet(target / "chunks.parquet", index=False)
    np.save(target / "embeddings.npy", vectors, allow_pickle=False)
    settings = read_json(root / "config/models.json")
    manifest = {
        "documents": len(documents),
        "chunks": len(chunks),
        "dimensions": vectors.shape[1],
        "embedding_model": settings["embedding_model"],
        "embedding_revision": settings["embedding_revision"],
        "document_tokens": settings["document_tokens"],
        "chunk_overlap_tokens": settings["chunk_overlap_tokens"],
        "metric": "cosine / dot product of normalized float32 vectors",
        "approximate": False,
        "files": {
            "data/processed/reviews.parquet": digest(source),
            "artifacts/index/chunks.parquet": digest(target / "chunks.parquet"),
            "artifacts/index/embeddings.npy": digest(target / "embeddings.npy"),
        },
    }
    write_json(target / "manifest.json", manifest)
    write_json(root / "reports/index_manifest.json", manifest)
    return manifest


class VectorIndex:
    def __init__(self, root: Path, embedder: LocalEmbedder) -> None:
        self.embedder = embedder
        self.manifest = read_json(root / "artifacts/index/manifest.json")
        settings = read_json(root / "config/models.json")
        self.rerank_pool = int(settings.get("rerank_pool", 100))
        self.mmr_lambda = float(settings.get("mmr_lambda", 0.7))
        for name in (
            "embedding_model",
            "embedding_revision",
            "document_tokens",
            "chunk_overlap_tokens",
        ):
            if self.manifest[name] != settings[name]:
                raise ValueError("Configuração do modelo mudou; reconstrua o índice.")
        for name, expected in self.manifest["files"].items():
            if digest(root / name) != expected:
                raise ValueError(f"Arquivo do índice alterado: {name}. Reconstrua o índice.")
        self.documents = pd.read_parquet(root / "data/processed/reviews.parquet")
        self.chunks = pd.read_parquet(root / "artifacts/index/chunks.parquet")
        self.vectors = np.load(
            root / "artifacts/index/embeddings.npy", mmap_mode="r", allow_pickle=False
        )
        self.rows = self.chunks.merge(
            self.documents, on="document_id", validate="many_to_one", how="left"
        )
        if len(self.rows) != len(self.vectors):
            raise ValueError("Quantidade de vetores incompatível com os chunks.")

    def search(self, query: str, filters: Filters, top_k: int = 6) -> tuple[list[Evidence], int]:
        if not 1 <= top_k <= 20:
            raise ValueError("top_k deve estar entre 1 e 20.")
        frame = self.rows
        selected = frame.score.between(filters.min_score, filters.max_score)
        # Datas são do pedido, não da criação do comentário.
        if filters.start_date:
            selected &= frame.purchase_date.ge(filters.start_date)
        if filters.end_date:
            selected &= frame.purchase_date.ne("") & frame.purchase_date.le(filters.end_date)
        if filters.category:
            selected &= frame.categories.str.split("|").map(
                lambda values: filters.category in values
            )
        if filters.late_only:
            selected &= frame.late.astype("boolean").fillna(False)
        candidates = np.flatnonzero(selected.to_numpy(dtype=bool))
        matching = frame.loc[selected, "document_id"].nunique()
        if not len(candidates):
            return [], 0
        query_vector = self.embedder.encode([query])[0]
        scores = self.vectors[candidates] @ query_vector
        # O corpus cabe em RAM. Ranking completo simplifica deduplicação determinística.
        order = np.argsort(-scores, kind="stable")
        evidence: list[Evidence] = []
        seen_docs: set[str] = set()
        seen_texts: set[str] = set()
        pool: list[int] = []
        for position in order:
            row = frame.iloc[candidates[position]]
            key = row.text.casefold().strip()
            if row.document_id in seen_docs or key in seen_texts:
                continue
            seen_docs.add(row.document_id)
            seen_texts.add(key)
            pool.append(int(position))
            if len(pool) == self.rerank_pool:
                break
        # Maximal Marginal Relevance diversifica o contexto entre candidatos relevantes.
        # Sempre preserva o resultado mais próximo; não altera o score de cosseno exibido.
        chosen: list[int] = []
        while pool and len(chosen) < top_k:
            if not chosen:
                position = pool[0]
            else:
                similarities = self.vectors[candidates[pool]] @ self.vectors[candidates[chosen]].T
                values = self.mmr_lambda * scores[pool] - (1 - self.mmr_lambda) * similarities.max(
                    axis=1
                )
                position = pool[int(np.argmax(values))]
            chosen.append(position)
            pool.remove(position)
        for position in chosen:
            row = frame.iloc[candidates[position]]
            evidence.append(
                Evidence(
                    label=f"E{len(evidence) + 1}",
                    document_id=row.document_id,
                    review_id=row.review_id,
                    order_id=row.order_id,
                    text=row.text,
                    chunk=row.chunk,
                    score=int(row.score),
                    date=row.date,
                    categories=tuple(row.categories.split("|")) if row.categories else (),
                    late=None if pd.isna(row.late) else bool(row.late),
                    similarity=float(scores[position]),
                )
            )
            if len(evidence) == top_k:
                break
        return evidence, int(matching)
