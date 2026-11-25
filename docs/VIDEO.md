# Roteiro do vídeo — até sete minutos

**Autor: André Mohallem Ferraz.** O vídeo segue a apresentação entregue
(`Apresentacao-TechChallenge-Fase4.pptx`, 13 slides principais e 2 anexos). As notas de
cada slide trazem fala sugerida, ação na tela e tempo. Duração planejada: **6min40s**.

## Ordem e tempo

| Tempo | Slide | Assunto / ação |
| --- | --- | --- |
| 0:00–0:15 | 1 | Abertura: tema e objetivo. |
| 0:15–0:35 | 2 | Roteiro: os oito itens do enunciado e onde cada um aparece. |
| 0:35–1:00 | 3 | Problema de negócio: nota, comentário e necessidade do gestor. |
| 1:00–1:45 | 4 | Arquitetura: preparação e consulta no diagrama. |
| 1:45–2:15 | 5 | Preparação da base: seleção, limpeza, ausências e junções. |
| 2:15–2:55 | 6 | Estratégia e recuperação: modelos, índice exato, MMR, filtros e limiar. |
| 2:55–3:20 | 7 | Demonstração: apresentar as três perguntas e mudar para a aplicação. |
| 3:20–4:15 | 8 | Evidências: executar as perguntas 1 e 2, abrir E1/E2, mostrar IDs e trechos. |
| 4:15–4:40 | 9 | Sem evidências: executar a pergunta 3 e explicar a recusa. |
| 4:40–5:20 | 10 | Validação: testes e reprodução separados de relevância e suporte factual. |
| 5:20–5:55 | 11 | Desafios e decisões: falhas da validação, correções e testes de regressão. |
| 5:55–6:20 | 12 | Código e reprodução: repositório e comandos. |
| 6:20–6:40 | 13 | Fechamento. Os anexos não entram no vídeo. |

## Cobertura dos itens do vídeo

| Item do enunciado | Slides |
| --- | --- |
| 1. Problema de negócio | 3 |
| 2. Arquitetura proposta | 4 |
| 3. Estratégia do pipeline RAG | 5–6 |
| 4. Recuperação das avaliações relevantes | 4 e 6 |
| 5. Demonstração prática | 7–9 |
| 6. Exemplos de perguntas | 7–8 |
| 7. Evidências que fundamentam as respostas | 8–9 |
| 8. Desafios e decisões técnicas | 6 e 10–11 |

## Demonstração na aplicação

Execute `uv run streamlit run streamlit_app.py` e abra http://localhost:8501. Faça uma
consulta antes de gravar para carregar os modelos.

| # | Pergunta | Filtro na barra lateral | Mostrar |
| --- | --- | --- | --- |
| 1 | O que os compradores elogiam na qualidade dos produtos? | Nota 4–5 | Resposta com [E#]; abrir E1 e E2, ler o comentário, nota, data e review_id |
| 2 | Há relatos de pedidos entregues com itens faltando? | Nota 1–2 | Conferir se cada trecho trata de entrega parcial |
| 3 | O que os clientes relataram sobre atrasos na entrega em 2025? | Nenhum | Recusa: a base cobre compras de 2016 a 2018 |

Cada resposta gerada leva 10–25 s em CPU; a espera pode ser cortada na edição, sem trocar
a resposta exibida. Mostre a aplicação executando: um slide estático não substitui a
demonstração. Antes de enviar, confira áudio, legibilidade, duração abaixo de 7:00 e o
acesso do avaliador ao link do vídeo.
