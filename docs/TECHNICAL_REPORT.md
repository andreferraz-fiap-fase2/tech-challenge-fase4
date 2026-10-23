# Voz do Cliente: RAG local sobre avaliações da Olist

**André Mohallem Ferraz · FIAP / Pós Tech · Tech Challenge Fase 4 · Trabalho individual**

## Problema e objetivo

Comentários de clientes contêm relatos sobre entrega, atendimento e produtos que não
são resumidos por uma nota. O objetivo é permitir investigação em linguagem natural,
recuperar avaliações pertinentes e produzir uma síntese rastreável. A solução utiliza
o Brazilian E-Commerce Public Dataset by Olist, indicado no enunciado, e executa tanto
a busca quanto a geração em CPU local, sem serviço pago ou chave de API.

Esta fase muda de tema em relação à Fase 3. A classificação da alfabetização não foi
reutilizada como modelo ou dataset. Foram mantidos os cuidados de organização, testes
e reprodução. Em resposta ao feedback anterior, o código-fonte completo faz parte do
repositório e do ZIP da entrega; o relatório é documentação complementar.

## Construção da base

Foram usados quatro CSVs oficiais: avaliações, pedidos, itens dos pedidos e produtos.
As entradas e o ZIP original têm SHA-256 registrados em `reports/source_manifest.json`.

| Etapa | Quantidade |
| --- | ---: |
| Linhas originais de avaliações | 99.224 |
| Linhas sem texto utilizável | 56.770 |
| Documentos preparados | 42.454 |
| IDs distintos de avaliação | 42.138 |
| Pedidos distintos representados | 42.307 |
| Trechos indexados | 42.455 |
| Dimensões por embedding | 384 |

O título é combinado à mensagem. Uma avaliação apenas com título é mantida quando
contém texto. Ausências não são substituídas por conteúdo inventado. HTML, entidades e
espaços são normalizados; acentos, negações e erros de escrita relevantes são preservados.
Expressões regulares mascaram padrões de e-mail, telefone, CPF e links. Isso não garante
anonimização completa de nomes ou informações pessoais não padronizadas.

`review_id` não é considerado único: documentos distintos mantêm avaliação, pedido,
nota, data e texto em uma chave determinística. Não houve remoção de duplicatas exatas
neste snapshot. Categorias são agrupadas por pedido antes da junção, impedindo que
vários itens multipliquem as avaliações. Ausência de entrega conhecida permanece nula,
sem virar entrega no prazo. A comparação de atraso utiliza dias civis, pois a estimativa
não fornece um horário de entrega.

Distribuição das notas nos documentos: 1 = 8.817; 2 = 2.161; 3 = 3.628; 4 = 6.222;
5 = 21.626. A nota filtra o recorte, mas não comprova o motivo do comentário.
As avaliações preparadas têm datas de criação entre 02/10/2016 e 31/08/2018. O corpus
é histórico, não uma medida atual da experiência de clientes da Olist.

## Arquitetura implementada

Pergunta e filtros → normalização e gate lexical → embedding da consulta → filtros
antes do ranking → cosseno exato → diversificação MMR → gate de evidências → contexto
com IDs → Qwen3 local → validação das referências → resposta e comentários rastreáveis.

O código segue as camadas `domain`, `infrastructure`, `usecase` e `views`. Domínio contém
entidades e regras; infraestrutura implementa CSVs, modelos e índice; casos de uso
orquestram o RAG; CLI e Streamlit oferecem os pontos de entrada. O mapa completo para
as exigências do enunciado está em `docs/REQUIREMENTS.md`.

O modelo de embeddings é `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
com 384 dimensões e suporte multilíngue. As revisões de busca e geração estão fixadas
em `config/models.json`. Textos longos são divididos por offsets do tokenizer em janelas
de até 120 tokens, com sobreposição de 20. A matriz é NumPy float32 com vetores
normalizados; documentos e trechos são armazenados em Parquet.

A busca exata foi escolhida porque esse corpus cabe em memória e permite auditar os
scores sem serviço vetorial remoto. Produto escalar de vetores normalizados equivale a
cosseno. Entre os 100 candidatos distintos mais próximos, MMR pondera relevância com
0,7 e redundância com 0,3. Um documento e um texto idêntico entram no contexto apenas
uma vez. A diversificação aumenta a variedade, mas pode introduzir trechos menos pertinentes.

Os filtros de nota, categoria, data da compra e entrega após a estimativa são aplicados
antes do ranking. Pedidos com várias categorias mantêm todas, sem atribuir automaticamente
uma reclamação a um item. As regras não inferem filtros a partir da pergunta: o usuário
deve selecioná-los explicitamente na interface ou CLI.

## Geração e tratamento de insuficiência

O gerador é `Qwen/Qwen3-0.6B`, executado localmente por Transformers e PyTorch CPU.
Não há ajuste fino. O modo de pensamento é desabilitado; a geração é greedy, limitada
a 384 novos tokens. O prompt recebe a pergunta e até seis trechos com referências E1–E6.
Instrui a responder em português usando apenas as evidências, sem causas, percentuais,
frequências ou recomendações não sustentadas. Comentários são delimitados como dados,
nunca como instruções para o modelo.

O gate exige pelo menos duas evidências com similaridade de cosseno ≥ 0,42. É uma regra
heurística, não uma probabilidade calibrada. Perguntas sem vocabulário de experiência de
compra são recusadas por um gate lexical conservador. Solicitações de totais e percentuais
são recusadas porque top-k não permite estimar frequência no corpus inteiro.

Cada tópico da síntese deve conter referências existentes no contexto. Saídas sem esse
formato ou com percentuais são recusadas. Essa checagem verifica a integridade das
referências, não a verdade de cada afirmação. A interface mostra texto, nota, data,
categorias, review_id e order_id, permitindo conferir a origem de cada relato.

## Avaliação executada e limitações dos números

O conjunto autoral contém sete perguntas de desenvolvimento e nove de teste. É pequeno
e não representa um benchmark independente. A primeira execução de teste teve 8/9 decisões
corretas de gate. A falha foi uma pergunta eleitoral que recuperou comentários com
“Brasil” e gerou síntese irrelevante. O resultado foi preservado em
`reports/evaluation_test_before_scope_fix.json`.

Essa falha motivou o gate lexical de escopo. O mesmo conjunto foi reexecutado como
regressão, com os resultados a seguir. Portanto, esses resultados não demonstram
generalização para perguntas novas.

| Medida na regressão | Resultado |
| --- | ---: |
| Gate de presença/ausência de evidências | 9/9 |
| Perguntas respondíveis com contexto suficiente | 4/4 |
| Perguntas não respondíveis com abstenção | 5/5 |
| Sínteses aceitas entre perguntas respondíveis | 3/4 |
| Evidências estritamente pertinentes na inspeção | 16/24 |

A inspeção de pertinência foi realizada pelo agente de desenvolvimento, com critério
conservador e justificativa por documento, em `evaluation/relevance_review.json`.
Não é julgamento humano independente. A precisão agrupada observada foi 66,7%; não há
recall documental, pois não foram julgados todos os documentos do corpus.

Itens faltantes recuperaram também relatos de pedidos não recebidos; atendimento
recuperou comentários genéricos de insatisfação; qualidade recuperou elogios à entrega.
Esses erros mostram por que gate correto não equivale a contexto inteiramente pertinente.
O caso de atendimento teve evidências, mas o LLM não gerou saída aceita pela checagem de
referências. Essa abstenção é reportada, sem substituição por resposta pronta.

O código passou em 30 testes automatizados de preparação, preservação de negações,
metadados, filtros antes do ranking, deduplicação, integridade do índice, escopo,
abstenção e referências. Lint e formatação passaram. Os testes unitários usam fixtures
pequenas e não dependem dos dados reais. Os testes de integração utilizaram os dados e
modelos reais, conforme os relatórios de execução.

## Reprodução e execução local

Ambiente verificado: Python 3.12.13, Linux WSL2, PyTorch 2.9.0 CPU, Transformers 4.57.1,
Sentence Transformers 5.1.1. Dependências diretas e transitivas estão fixadas em `uv.lock`.
Após baixar os pesos e preparar os arquivos, a interface foi exercitada com os modelos
em modo offline: nenhuma exceção, resposta aceita e seis evidências.

```bash
uv sync --frozen
uv run python app.py download
uv run python app.py models
uv run python app.py prepare
uv run python app.py index
uv run streamlit run streamlit_app.py
```

O comando `uv run python app.py reproduce` reconstrói preparação, chunks e embeddings
desde o ZIP original em diretório temporário. A execução manteve os três arquivos
idênticos por SHA-256 e os IDs/scores de uma consulta iguais, com tolerância de 1e-7.
Os pesos locais fixos foram reutilizados; a geração foi verificada separadamente.
Evidência completa: `reports/reproducibility.json`.

## Aplicação, riscos de interpretação e evolução

A solução permite levantar hipóteses sobre experiências de compra, explorar temas e
conferir relatos. Os comentários recuperados não medem os problemas mais frequentes de
toda a empresa, não provam causas e não sustentam previsão de desempenho atual ou futuro.
Notas sem texto e clientes que não avaliaram não estão representados na base textual.

O gate lexical pode recusar perguntas válidas pouco explícitas e aceitar perguntas
irrelevantes que usem vocabulário do domínio. O gerador pequeno pode errar mesmo com
referências válidas. Próximas etapas: julgamentos humanos independentes, conjunto maior
de perguntas, comparação com busca lexical/híbrida, reranker multilíngue, avaliação de
suporte por afirmação e estudo de custo/qualidade com modelos locais maiores.

O repositório e o ZIP contêm código, testes, configurações, instruções e evidências.
CSV e pesos são obtidos por comandos reproduzíveis e não entram no Git público. O vídeo
de até sete minutos deve ser gravado pelo autor; o roteiro está em `docs/VIDEO.md`.
O envio no portal e o comprovante opcional da trilha Databricks dependem do autor.

## Fontes

- Olist: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce — CC BY-NC-SA 4.0.
- Sentence Transformers: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — Apache-2.0.
- Qwen: https://huggingface.co/Qwen/Qwen3-0.6B — Apache-2.0.
- Sentence Transformers, similaridade: https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html.

As atribuições completas e a distinção entre licença do código e dos dados estão em
`THIRD_PARTY.md`.
