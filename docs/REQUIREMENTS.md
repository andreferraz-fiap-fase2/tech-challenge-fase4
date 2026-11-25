# Mapa do enunciado para a implementação

Fonte: `[IAST] - Tech Challenge - Fase 4.pdf`, disponível na pasta Fase4 do autor.

## Requisitos da solução

| Exigência | Implementação / evidência |
| --- | --- |
| Base Olist e foco nas avaliações | `infrastructure/dataset.py`; `reports/source_manifest.json` |
| Seleção e limpeza dos textos | `prepare`, `clean_text`; `reports/data_quality.json` |
| Ausências e organização documental | Título + mensagem, exclusão sem texto, ID determinístico |
| Embeddings e indexação | `infrastructure/models.py`, `index.py`; `config/models.json` |
| Processamento da pergunta | `domain/policy.py: normalize_query, search_query` |
| Recuperação semântica | MiniLM + cosseno exato + filtros antes do ranking |
| Seleção do contexto | Top-k, deduplicação, limiar e mínimo de evidências |
| Resposta por modelo de linguagem | `LocalGenerator`, Qwen3 real em CPU |
| Evidências rastreáveis | `Evidence`: texto, review_id, order_id, document_id, nota, data |
| Falta de suporte e fora de escopo | Gate de similaridade, recusa de agregações e de períodos fora da base, abstenção do LLM |
| Metadados opcionais | Nota, compra, categorias e entrega após estimativa |
| Código completo e instruções | `src/`, `tests/`, CLI, UI, README e `uv.lock` |
| Arquitetura e justificativas | `docs/ARCHITECTURE.md` |
| Exemplos de perguntas e respostas | README, seção “Exemplos de perguntas e respostas”; execuções completas em `reports/` |
| Reprodução | README, manifestos e comandos de reconstrução |
| Repositório público | https://github.com/andreferraz-fiap-fase2/tech-challenge-fase4 |

## Entregável 1 — repositório

| Item exigido | Onde está |
| --- | --- |
| Código-fonte da solução | `src/voc/`, `app.py`, `streamlit_app.py`, `tests/` |
| Instruções de instalação e execução | README, seções “Executar” e “Consultar pela linha de comando” |
| README explicando o projeto | `README.md` |
| Descrição da arquitetura | README, “Arquitetura”; `docs/ARCHITECTURE.md` |
| Tecnologias e bibliotecas | README, “Tecnologias e bibliotecas”; `pyproject.toml`, `uv.lock` |
| Estratégia do pipeline RAG | README, “Preparação da base e pipeline RAG”; `docs/ARCHITECTURE.md` |
| Preparação da base | README, itens 1–5 da mesma seção; `reports/data_quality.json` |
| Justificativa das decisões técnicas | README, “Principais decisões técnicas”; `docs/ARCHITECTURE.md` |
| Exemplos de perguntas e respostas | README, “Exemplos de perguntas e respostas”; `reports/evaluation_*_rag.json` |
| Informações para reproduzir | README, “Verificar e reproduzir”; `config/models.json`, manifestos em `reports/` |

## Entregável 2 — vídeo de até sete minutos

Os oito itens exigidos e os slides correspondentes estão em [VIDEO.md](VIDEO.md). A
gravação é feita pelo autor a partir da apresentação entregue.

O certificado ou comprovante da trilha Databricks é um bônus opcional mencionado no
enunciado. Só o autor pode concluir a formação e fornecer um comprovante verdadeiro.
