# Roteiro do vídeo — até sete minutos

**Autor: André Mohallem Ferraz.** O vídeo segue a apresentação entregue
(`Apresentacao-TechChallenge-Fase4.pptx`, 13 slides principais e 2 anexos). As notas de
cada slide trazem fala sugerida, ação na tela e tempo. Duração planejada: **6min40s**.
O vídeo é a gravação da apresentação com narração e é enviado na plataforma da FIAP; a
demonstração da aplicação está gravada no slide 8.

## Ordem e tempo

| Tempo | Slide | Assunto / ação |
| --- | --- | --- |
| 0:00–0:15 | 1 | Abertura: tema e objetivo. |
| 0:15–0:35 | 2 | Roteiro: os oito itens do enunciado e onde cada um aparece. |
| 0:35–1:00 | 3 | Problema de negócio: nota, comentário e necessidade do gestor. |
| 1:00–1:45 | 4 | Arquitetura: preparação e consulta no diagrama. |
| 1:45–2:15 | 5 | Preparação da base: seleção, limpeza, ausências e junções. |
| 2:15–2:55 | 6 | Estratégia e recuperação: modelos, índice exato, MMR, filtros e limiar. |
| 2:55–3:20 | 7 | Demonstração: apresentar as três perguntas. |
| 3:20–4:20 | 8 | Evidências: gravação da aplicação (60 s) com as três perguntas, respostas [E#], IDs e a recusa de 2025. |
| 4:20–4:40 | 9 | Sem evidências: explicar as três formas de abstenção. |
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

## Demonstração gravada

A gravação do slide 8 mostra a aplicação local (`uv run streamlit run streamlit_app.py`)
executando as três perguntas abaixo. Só a espera da geração foi acelerada na edição; o
tempo real aparece na tela (26,8 s e 17,1 s em CPU).

| # | Pergunta | Filtro na barra lateral | O que aparece |
| --- | --- | --- | --- |
| 1 | O que os compradores elogiam na qualidade dos produtos? | Nota 4–5 | Resposta com [E1]–[E6]; avaliações com nota, data, review_id e order_id |
| 2 | Há relatos de pedidos entregues com itens faltando? | Nota 1–2 | Trechos sobre entrega parcial e um pedido não recebido |
| 3 | O que os clientes relataram sobre atrasos na entrega em 2025? | Nenhum | Recusa antes da busca: a base cobre compras de 2016 a 2018 |

Antes de enviar, confira áudio, legibilidade e duração abaixo de 7:00.
