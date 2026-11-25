"""Orquestra busca, gate de evidências, geração local e rastreabilidade."""

import re
import time

from voc.domain.entities import Answer, Filters, Generator, Retriever
from voc.domain.policy import (
    NO_EVIDENCE,
    NOTICE,
    build_prompt,
    has_domain_scope,
    mentioned_years,
    normalize_answer,
    normalize_query,
    period_filter_covers,
    search_query,
    valid_citations,
)

# Status devolvidos sem consultar o índice; a interface não deve exibi-los como busca vazia.
REFUSED_BEFORE_SEARCH = frozenset(
    {"unsupported_aggregate", "out_of_scope", "period_out_of_coverage", "period_needs_filter"}
)


class RagService:
    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        min_similarity: float = 0.5,
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
        refusal = self.refusal_before_search(question, filters)
        if refusal:
            status, message = refusal
            return Answer(question, status, message, elapsed_seconds=time.perf_counter() - start)
        query = search_query(question)
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
        response = normalize_answer(self.generator.generate(build_prompt(question, evidence)))
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

    def refusal_before_search(self, question: str, filters: Filters) -> tuple[str, str] | None:
        """Perguntas que a busca não deve tentar responder: (status, mensagem) ou None."""
        if re.search(
            r"\b(quantos|quantas|percentual|porcentagem|faturamento|receita total)\b",
            question,
            re.IGNORECASE,
        ):
            return (
                "unsupported_aggregate",
                "Esta busca não calcula totais ou percentuais do corpus. Reformule para explorar os relatos e suas evidências.",
            )
        if not has_domain_scope(question):
            return (
                "out_of_scope",
                "Esta base permite investigar relatos de experiências de compra e atendimento. A pergunta está fora desse escopo.",
            )
        return self.period_refusal(question, filters)

    def period_refusal(self, question: str, filters: Filters) -> tuple[str, str] | None:
        """Ano escrito na pergunta não filtra a busca (achado F2 da validação de 17/11/2026)."""
        years = mentioned_years(question)
        if not years:
            return None
        first, last = self.retriever.coverage_years()
        outside = [year for year in years if not first <= year <= last]
        if outside:
            cited = ", ".join(str(year) for year in outside)
            return (
                "period_out_of_coverage",
                f"A base contém compras de {first} a {last}. Não há avaliações de {cited} para sustentar uma resposta.",
            )
        if period_filter_covers(filters.start_date, filters.end_date, years):
            return None
        cited = ", ".join(str(year) for year in years)
        return (
            "period_needs_filter",
            f"A pergunta cita {cited}, mas o texto da pergunta não filtra datas. Aplique o filtro de período da compra para esse intervalo e consulte novamente.",
        )
