# Roteiro do vídeo — até sete minutos

**Autor: André Mohallem Ferraz.** O vídeo é a apresentação narrada
(`Apresentacao-TechChallenge-Fase4.pptx`, 14 slides), enviada na plataforma da FIAP.
A demonstração da aplicação está gravada no slide 8. Duração planejada: **6min35s**.

## Ordem e tempo

| Tempo | Slide | Conteúdo |
| --- | --- | --- |
| 0:00–0:20 | 1 | Capa: “O que os clientes dizem, com a prova em cada resposta”. |
| 0:20–0:45 | 2 | Agenda da apresentação. |
| 0:45–1:10 | 3 | Problema de negócio: a nota não explica toda a experiência. |
| 1:10–1:55 | 4 | Arquitetura: preparar a base uma vez e responder a cada pergunta. |
| 1:55–2:25 | 5 | Preparação: mais da metade das avaliações não tem comentário. |
| 2:25–3:10 | 6 | Como a solução encontra e resume os comentários (entender, escolher, resumir). |
| 3:10–3:30 | 7 | As três perguntas da demonstração e seus filtros. |
| 3:30–4:30 | 8 | Gravação da aplicação (60 s): respostas com [E#], avaliações de origem e recusa de 2025. |
| 4:30–4:50 | 9 | Quando não há base para responder, a solução explica o motivo. |
| 4:50–5:30 | 10 | Como verificamos se dá para confiar. |
| 5:30–6:05 | 11 | Os principais desafios e como os resolvemos. |
| 6:05–6:25 | 12 | Fechamento e próximos passos. |
| 6:25–6:35 | 14 | Referências. O slide 13 (distribuição das notas) é um anexo fora do vídeo. |

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
| 8. Desafios e decisões técnicas | 6, 10 e 11 |

## Demonstração gravada

A gravação do slide 8 mostra a aplicação local (`uv run streamlit run streamlit_app.py`)
executando as três perguntas abaixo. Só a espera da geração foi acelerada na edição; o
tempo real aparece na tela (26,8 s e 17,1 s em CPU).

| # | Pergunta | Filtro na barra lateral | O que aparece |
| --- | --- | --- | --- |
| 1 | O que os compradores elogiam na qualidade dos produtos? | Nota 4–5 | Resposta com [E1]–[E6]; avaliações com nota, data, review_id e order_id |
| 2 | Há relatos de pedidos entregues com itens faltando? | Nota 1–2 | Trechos sobre entrega parcial e um pedido não recebido |
| 3 | O que os clientes relataram sobre atrasos na entrega em 2025? | Nenhum | Recusa antes da busca: a base cobre compras de 2016 a 2018 |
