"""Contratos do domínio, independentes de modelos e ferramentas externas."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Filters:
    min_score: int = 1
    max_score: int = 5
    start_date: str = ""
    end_date: str = ""
    category: str = ""
    late_only: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.min_score <= self.max_score <= 5:
            raise ValueError("As notas devem formar um intervalo entre 1 e 5.")
        from datetime import date

        for value in (self.start_date, self.end_date):
            if value:
                date.fromisoformat(value)
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("A data inicial deve anteceder a final.")


@dataclass(frozen=True)
class Evidence:
    label: str
    document_id: str
    review_id: str
    order_id: str
    text: str
    chunk: str
    score: int
    date: str
    categories: tuple[str, ...]
    late: bool | None
    similarity: float


@dataclass(frozen=True)
class Answer:
    question: str
    status: str
    answer: str
    evidence: tuple[Evidence, ...] = ()
    retrieved_documents: int = 0
    matching_documents: int = 0
    elapsed_seconds: float = 0.0
    model: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)


class Generator(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class Retriever(Protocol):
    def search(self, query: str, filters: Filters, top_k: int) -> tuple[list[Evidence], int]: ...
