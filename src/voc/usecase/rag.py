"""Orquestra busca, gate de evidências, geração local e rastreabilidade."""

import re
import time

from voc.domain.entities import Answer, Filters, Generator, Retriever
from voc.domain.policy import (
    NO_EVIDENCE,
    NOTICE,
    build_prompt,
    has_domain_scope,
    normalize_query,
    search_query,
    valid_citations,
)


class RagService:
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        min_similarity: float = 0.42,
        min_evidence: int = 2,
        top_k: int = 6,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.min_similarity = min_similarity
        self.min_evidence = min_evidence
        self.top_k = top_k
        if not 1 <= min_evidence <= top_k <= 20 or not -1 <= min_similarity <= 1:
            raise ValueError("Parâmetros inválidos para a recuperação.")

    def ask(
        self, question: str, filters: Filters = Filters(), retrieve_only: bool = False
    ) -> Answer:
        start = time.perf_counter()
        question = normalize_query(question)
        if re.search(
            r"\b(quantos|quantas|percentual|porcentagem|faturamento|receita total)\b",
            question,
            re.IGNORECASE,
        ):
            return Answer(
                question,
                "unsupported_aggregate",
                "Esta busca não calcula totais ou percentuais do corpus. Reformule para explorar os relatos e suas evidências.",
            )
        query = search_query(question)
        if not has_domain_scope(question):
            return Answer(
                question,
                "out_of_scope",
                "Esta base permite investigar relatos de experiências de compra e atendimento. A pergunta está fora desse escopo.",
                elapsed_seconds=time.perf_counter() - start,
            )
        retrieved, matching = self.retriever.search(query, filters, top_k=self.top_k)
        evidence = [item for item in retrieved if item.similarity >= self.min_similarity]
        common = {
            "evidence": tuple(evidence),
            "retrieved_documents": len(retrieved),
            "matching_documents": matching,
            "warnings": (NOTICE,),
            "model": self.generator.name,
        }
        if len(evidence) < self.min_evidence:
            return Answer(
                question,
                "insufficient_evidence",
                NO_EVIDENCE,
                elapsed_seconds=time.perf_counter() - start,
                **common,
            )
        if retrieve_only:
            return Answer(
                question,
                "retrieval_only",
                "Busca concluída. A geração pelo modelo de linguagem não foi executada.",
                elapsed_seconds=time.perf_counter() - start,
                **common,
            )
        response = self.generator.generate(build_prompt(question, evidence))
        if not valid_citations(response, evidence):
            return Answer(
                question,
                "generation_abstained",
                "O modelo não produziu uma síntese com referências válidas. Consulte as avaliações recuperadas abaixo.",
                elapsed_seconds=time.perf_counter() - start,
                **common,
            )
        return Answer(
            question, "answered", response, elapsed_seconds=time.perf_counter() - start, **common
        )
