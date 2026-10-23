# Arquivos locais

Execute na raiz `uv run python app.py download` para obter o ZIP público da Olist e os
quatro CSVs oficiais de avaliações, pedidos, itens e produtos. A origem é registrada em
`reports/source_manifest.json`. Se necessário, baixe manualmente pelo Kaggle e use
`uv run python app.py download --zip /caminho/arquivo.zip`.

`prepare` cria `processed/reviews.parquet`; `index` cria os arquivos de `artifacts/index`.
Esses diretórios ficam fora do Git. Não copie tabelas de cadastro de clientes ou
credenciais. O pipeline não depende dos dados de alfabetização da fase anterior.
