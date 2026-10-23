"""Interface de demonstração. Executar: uv run streamlit run streamlit_app.py."""

import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from voc.domain.entities import Filters  # noqa: E402
from voc.infrastructure.storage import read_json  # noqa: E402
from voc.views.cli import make_service  # noqa: E402

if TYPE_CHECKING:
    from voc.usecase.rag import RagService

st.set_page_config(page_title="Voz do Cliente · Olist", page_icon="💬", layout="wide")


@st.cache_resource(show_spinner="Carregando o índice e o modelo de busca local…")
def service() -> "RagService":
    return make_service(ROOT)


st.caption("FIAP · TECH CHALLENGE FASE 4 · ANDRÉ MOHALLEM FERRAZ")
st.title("Voz do Cliente")
st.write("Explore experiências de compra da Olist. Cada insight começa nas avaliações.")

if not (ROOT / "artifacts/index/manifest.json").exists():
    st.info("Prepare a base e o índice antes de iniciar as consultas.")
    st.code(
        "uv sync --frozen\nuv run python app.py download\nuv run python app.py models\nuv run python app.py prepare\nuv run python app.py index",
        language="bash",
    )
    st.stop()

quality = read_json(ROOT / "reports/data_quality.json")
c1, c2, c3 = st.columns(3)
c1.metric("Avaliações com texto", f"{quality['documents']:,}".replace(",", "."))
c2.metric("Fonte", "Olist · histórico")
c3.metric("Execução", "Local · sem API")

with st.sidebar:
    st.header("Recorte da pesquisa")
    score_range = st.slider("Nota da avaliação", 1, 5, (1, 5))
    period = st.checkbox("Filtrar período da compra")
    start, end = "", ""
    if period:
        a = st.date_input("Compra a partir de", value=date(2016, 1, 1))
        b = st.date_input("Compra até", value=date(2018, 12, 31))
        start, end = a.isoformat(), b.isoformat()
    category = st.text_input("Categoria exata (opcional)", placeholder="ex.: moveis_decoracao")
    late = st.checkbox("Somente entregas após a data estimada")
    retrieve_only = st.checkbox("Apenas buscar evidências", value=False)
    st.caption(
        "Os filtros são aplicados antes da busca. Uma categoria pode pertencer a um pedido com vários produtos."
    )

with st.form("question"):
    question = st.text_input(
        "O que você quer investigar?",
        value="O que os clientes relatam sobre atrasos na entrega?",
        max_chars=1000,
    )
    submit = st.form_submit_button("Investigar avaliações", type="primary")

st.caption(
    "Experimente: produtos com defeito · itens faltantes · elogios à entrega · problemas de atendimento"
)
if submit:
    try:
        filters = Filters(score_range[0], score_range[1], start, end, category.strip(), late)
        with st.spinner("Buscando relatos e preparando a resposta…"):
            result = service().ask(question, filters, retrieve_only=retrieve_only)
        st.session_state["result"] = result
    except (ValueError, OSError, RuntimeError) as error:
        st.error(str(error))

if "result" in st.session_state:
    result = st.session_state["result"]
    st.subheader(result.question)
    if result.status == "answered":
        st.markdown(result.answer)
    elif result.status == "retrieval_only":
        st.info(result.answer)
    else:
        st.warning(result.answer)
    for warning in result.warnings:
        st.caption(warning)
    st.caption(
        f"{len(result.evidence)} evidências · {result.matching_documents:,} avaliações no recorte antes da busca · {result.elapsed_seconds:.1f} s".replace(
            ",", "."
        )
    )
    st.subheader("Evidências recuperadas")
    for item in result.evidence:
        with st.expander(
            f"[{item.label}] Nota {item.score}/5 · {item.date or 'data desconhecida'} · similaridade {item.similarity:.3f}",
            expanded=True,
        ):
            st.text(item.text)
            st.caption(f"Avaliação: {item.review_id} · Pedido: {item.order_id}")
            st.caption(f"Categorias: {', '.join(item.categories) or 'não informadas'}")
            st.caption(
                "Similaridade mede proximidade semântica; não é probabilidade nem confiança na resposta."
            )
    import json

    st.download_button(
        "Baixar resposta e evidências (JSON)",
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        file_name="consulta-voc.json",
        mime="application/json",
    )

st.divider()
st.caption(
    "Base histórica de 2016–2018. Síntese por modelo local pequeno, sujeita a erros: confira os relatos. Mascaramento automático de contatos não garante anonimização completa. Não é um indicador atual da Olist."
)
