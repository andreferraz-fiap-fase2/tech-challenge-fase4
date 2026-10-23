# Voz do Cliente · Olist

**André Mohallem Ferraz · FIAP / Pós Tech · Tech Challenge Fase 4 · Trabalho individual**

Uma aplicação RAG local para investigar avaliações históricas do e-commerce brasileiro.
A pergunta recupera comentários por significado; um modelo de linguagem sintetiza os
relatos e cita as avaliações utilizadas. A interface permite conferir os textos, IDs,
notas e categorias de cada evidência. Não há chave nem cobrança de API.

O enunciado desta fase exige **Voice of Customer Intelligence com RAG sobre a base
Olist**, um problema diferente da classificação de alfabetização da Fase 3. Reaproveitamos
a disciplina de organização, testes e reprodução. Nesta entrega, o código-fonte integra
o repositório e o pacote de avaliação, com acesso direto a cada etapa.

## Executar

Ambiente de referência: Linux / WSL2, Python **3.12**, CPU. Instale o
[uv](https://docs.astral.sh/uv/getting-started/installation/). Execute na raiz deste projeto:

```bash
uv sync --frozen
uv run python app.py download
uv run python app.py models
uv run python app.py prepare
uv run python app.py index
uv run streamlit run streamlit_app.py
```

Abra `http://localhost:8501`. O primeiro preparo baixa a base pública (~43 MB compactados),
as bibliotecas CPU e os pesos dos dois modelos. Reserve aproximadamente 4 GB em disco,
8 GB de RAM e alguns minutos para gerar o índice em CPU. Depois do preparo, consultas
e geração funcionam localmente sem internet. O tempo depende do hardware.

Se o Kaggle exigir autenticação ou bloquear o download automatizado, baixe o ZIP na
[página oficial da Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) e use:

```bash
uv run python app.py download --zip /caminho/brazilian-ecommerce.zip
```

**Não há dados simulados no pipeline.** Os testes automatizados usam pequenas fixtures
declaradamente artificiais; o índice e os exemplos de demonstração utilizam a base real.
Não são necessários dados nem modelos para executar os testes unitários.

## Consultar pela linha de comando

```bash
uv run python app.py ask "O que os clientes relatam sobre atrasos na entrega?"
uv run python app.py ask "Há relatos de produtos quebrados?" --max-score 2
uv run python app.py ask "O que os clientes elogiam?" --min-score 4 --category moveis_decoracao
uv run python app.py ask "Quais relatos mencionam atraso?" --late-only --retrieve-only
uv run python app.py ask "O que dizem sobre a entrega?" --start-date 2018-01-01 --end-date 2018-06-30 --output reports/runs/consulta.json
```

`--retrieve-only` executa somente a busca e identifica essa condição explicitamente.
O modo padrão executa o **LLM real**. Não se substitui a geração por uma resposta pronta.
Se faltarem evidências ou a saída não tiver referências válidas, o sistema se abstém e
permite inspecionar os comentários. Uma falha ao carregar um modelo é um erro operacional,
não é disfarçada como resposta sem evidências.

Os filtros são explícitos: escrever “nota baixa” na pergunta não ativa um filtro de nota.
Selecione o intervalo na interface ou use `--max-score 2`. Datas filtram a **compra**;
a data exibida na evidência é a **criação da avaliação**. “Entrega atrasada” nos metadados
significa entrega registrada em dia posterior à estimativa, sem inferir a causa.

## O que a implementação faz

1. Baixa e registra os hashes dos CSVs de avaliações, pedidos, itens e produtos.
2. Combina título e mensagem, preserva negações e acentos e mascara padrões de contatos.
3. Exclui textos vazios, mantém avaliações distintas com o mesmo `review_id` e agrega
   categorias por pedido antes da junção, evitando multiplicação de documentos.
4. Divide apenas textos longos em janelas de até 120 tokens com sobreposição de 20.
5. Gera embeddings multilíngues normalizados de 384 dimensões e armazena índice NumPy + Parquet.
6. Confere um vocabulário conservador de experiência de compra; aplica os filtros antes
   de calcular a similaridade de cosseno exata e diversifica o
   contexto por MMR entre os 100 candidatos mais próximos, com peso de relevância 0,7.
7. Recupera seis avaliações, evita documentos e textos repetidos no mesmo contexto e exige
   ao menos duas evidências com similaridade ≥ 0,42 antes da geração.
8. Envia somente os trechos e suas referências ao Qwen3 local. Exige referências existentes
   em todos os tópicos; saídas sem esse formato são recusadas.

Modelo de busca: [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).
Gerador: [Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), sem modo de pensamento, geração
greedy, limite de 384 tokens. Revisões exatas e parâmetros em [config/models.json](config/models.json).
Ambos são modelos pré-treinados; não há ajuste fino neste projeto.

## Verificar e reproduzir

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python app.py evaluate --split dev
uv run python app.py evaluate --split test
uv run python app.py evaluate --split test --generate
uv run python app.py reproduce
```

A avaliação separa o gate de evidências da geração. O conjunto autoral é pequeno e inclui
perguntas do domínio, fora do domínio, filtros vazios e uma pergunta quantitativa que o
top-k não permite responder. Consulte o [protocolo](evaluation/PROTOCOL.md) antes de
interpretar os resultados. Referências válidas são uma checagem de formato, não prova de
veracidade. Os exemplos e métricas efetivamente executados ficam em `reports/`.

O comando `reproduce` reconstrói a preparação, chunks e embeddings em uma pasta
temporária, compara os três arquivos por SHA-256 e confere IDs e scores de uma busca.
Os pesos locais são reutilizados e o projeto original é preservado.
Também é possível executar `download`, `prepare` e `index` em uma nova cópia do código.
Compare `source_manifest.json`, `data_quality.json` e `index_manifest.json`. O índice
verifica os hashes de documentos, chunks e vetores ao abrir. Pesos fixos e dependências
congeladas reduzem variações; versões de CPU/BLAS podem alterar scores nas últimas casas.

## Organização e entregáveis

```text
app.py / streamlit_app.py    Entradas CLI e interface
src/voc/domain/              Entidades, política de evidências e prompt
src/voc/infrastructure/      CSVs, armazenamento, embeddings, índice e LLM
src/voc/usecase/             RAG e avaliação
src/voc/views/               CLI
config/                     Modelos e parâmetros congelados
evaluation/                 Perguntas, protocolo e julgamentos de relevância
tests/                      Integridade, metadados, filtros e abstenção
reports/                    Manifestos, resultados executados e exemplos
docs/                       Arquitetura, decisões, mapa do enunciado e roteiro
data/raw / data/processed/   Dados locais, fora do Git
models / artifacts/         Pesos e índice locais, fora do Git
```

- [Arquitetura e decisões](docs/ARCHITECTURE.md)
- [Requisitos e localização do código](docs/REQUIREMENTS.md)
- [Roteiro do vídeo de até sete minutos](docs/VIDEO.md)
- [Fontes e licenças](THIRD_PARTY.md)

O vídeo deve demonstrar a aplicação e ser gravado pelo autor antes da submissão.
Este repositório fornece o código e as instruções; não constitui o envio no portal da FIAP.

## Limites da interpretação

O corpus representa avaliações de 2016–2018, com viés de quem escreveu comentários.
Uma seleção por similaridade não mede os problemas mais frequentes em toda a base.
Por isso, a aplicação descreve os relatos recuperados e recusa percentuais ou totais
solicitados na pergunta. Não há inferência causal, análise de tendência atual nem previsão.

O gate lexical pode recusar perguntas válidas que não explicitem seu tema; reformule
incluindo o contexto de compra, avaliação, produto, entrega ou atendimento.
O limiar de similaridade é heurístico e pode falhar diante de perguntas fora do escopo que
compartilhem palavras com os comentários. O LLM é pequeno e pode produzir sínteses incorretas
mesmo citando IDs existentes. A conferência das evidências continua necessária.
Os comentários são delimitados como dados não confiáveis no prompt; isso reduz, mas não
elimina, ataques por instruções no texto. O mascaramento por regex não garante anonimização
completa. Não se importam nomes ou cadastros de clientes da tabela de consumidores.
