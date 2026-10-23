# Mapa do enunciado para a implementação

Fonte: `[IAST] - Tech Challenge - Fase 4.pdf`, disponível na pasta Fase4 do autor.

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
| Falta de suporte e fora de escopo | Gate de similaridade, recusa de agregações, abstenção do LLM |
| Metadados opcionais | Nota, compra, categorias e entrega após estimativa |
| Código completo e instruções | `src/`, `tests/`, CLI, UI, README e `uv.lock` |
| Arquitetura e justificativas | `docs/ARCHITECTURE.md` |
| Exemplos de perguntas e respostas | `evaluation/questions.json`, exemplos executados em `reports/` |
| Reprodução | README, manifestos e comandos de reconstrução |
| Repositório público | Publicar e conferir a URL no guia da entrega |
| Vídeo até sete minutos | `docs/VIDEO.md`; gravação pelo autor |

O certificado ou comprovante da trilha Databricks é um bônus opcional mencionado no
enunciado. Só o autor pode concluir a formação e fornecer um comprovante verdadeiro.
