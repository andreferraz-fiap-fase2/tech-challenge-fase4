# Protocolo de avaliação

Perguntas em `questions.json`. Os casos de teste foram definidos antes de sua primeira
execução; uma pergunta ampla de desenvolvimento foi acrescentada durante a inspeção de
dev. Dev e test têm casos distintos. Os parâmetros iniciais eram top-k = 6, mínimo de 2 evidências e
cosseno mínimo 0,42; o corte passou a 0,50 na revisão de 22/11/2026 (seção final). Estes
valores são heurísticos, não probabilidades calibradas.

1. Executar dev em modo somente recuperação. Qualquer ajuste motivado por dev deve
   ser registrado antes de observar test.
2. Congelar configuração e executar test com recuperação e com o LLM real.
3. Guardar IDs, textos, scores, filtros, status, tempo e resposta de cada caso.
4. Inspecionar relevância e suporte das respostas separadamente; a métrica automática
   de gate compara apenas a presença/ausência de evidências com a expectativa.

O conjunto é autoral e pequeno, não um benchmark independente. Não contém julgamentos
exaustivos de todos os documentos: **não se estima recall documental**. Questões fora
do domínio são exemplos, não uma certificação de resistência a todos os ataques.

Métricas automáticas: acurácia do gate, cobertura nas perguntas respondíveis, taxa de
abstenção nas não respondíveis e número de respostas com referências aceitas. Uma
abstenção por formatação inválida do LLM não equivale a ausência de documentos relevantes.

Na revisão de relevância, julgar se cada trecho sustenta a pergunta. Na revisão factual,
conferir se cada afirmação da síntese decorre dos comentários citados. IDs existentes
e boa redação, isoladamente, não atendem a esse critério. Os julgamentos feitos pelo
desenvolvedor são identificados como tal, sem atribuí-los a avaliadores externos.

## Ajustes usando somente desenvolvimento

A recuperação inicial gerou contextos repetitivos. A primeira execução foi preservada
em `reports/evaluation_dev_initial_rag.json`. Antes de executar test, acrescentamos MMR
entre os 100 candidatos distintos mais próximos, com lambda 0,7. A similaridade exibida
continua sendo o cosseno original; MMR altera a ordem de seleção para diversificar.

A pergunta ampla de dev recuperou um título genérico como “avaliação do vendedor”.
Foi definida uma expansão lexical somente para perguntas sobre “principais problemas”
ou “principais reclamações” sem tema específico: compra, produto, entrega e atendimento.
Não se infere a frequência de cada tema. A inspeção e a nova execução dev constam em
`reports/dev_broad_refinement.json` e `reports/evaluation_dev_rag.json`.

O corte 0,42 e o mínimo de duas evidências foram mantidos. A primeira avaliação test
teve 8/9 decisões corretas de presença de evidência: uma pergunta eleitoral recuperou
comentários com “Brasil” e gerou uma resposta irrelevante. O resultado foi preservado em
`reports/evaluation_test_before_scope_fix.json`.

Após essa falha, acrescentamos um gate lexical conservador que exige vocabulário de
experiência de compra antes da busca. Essa é uma **correção motivada pelo teste**.
O conjunto test foi reutilizado como **regressão**, com 9/9 decisões de gate corretas.
Não se apresenta essa segunda execução como avaliação independente ou garantia de
generalização. Os hashes do código usado em cada execução estão nos relatórios.

A cobertura de geração é uma medida distinta: somente 3 das 4 perguntas respondíveis
receberam uma síntese aceita; a quarta apresentou evidências, mas o LLM não passou na
checagem de referências. O relatório de inspeção de relevância deve ser lido junto às
métricas de gate: uma pergunta pode recuperar documentos irrelevantes mesmo passando.

## Revisão de 22/11/2026: validação ampliada e troca do gerador

A validação de 17/11/2026 executou perguntas novas e encontrou três falhas: um ano fora
da base (2025) respondido com relatos de 2017–2018; perguntas de pagamento e pós-venda
recusadas como fora do domínio; e consultas acima de 128 tokens truncadas em silêncio.
Também registrou uma pergunta sobre um “Prêmio Nobel” da Olist respondida com comentários
sem relação. Os resultados daquela versão estão em `reports/historico-qwen3-0.6B/`.

A revisão executou ainda as perguntas de exemplo do enunciado. Com o Qwen3-0.6B, a maior
parte das respostas copiava comentários, e a checagem anterior aceitava rótulos inventados
(`[O1]`) e o marcador do formato pedido. A comparação entre geradores, com as mesmas
evidências, está em `reports/comparacao-gerador-20261122/` e em `docs/ARCHITECTURE.md`.

Correções: regra de período (ano fora da base gera abstenção; ano dentro da base exige o
filtro explícito), vocabulário de pagamento e pós-venda, recusa de consultas longas,
validação mais rígida das referências, prompt que agrupa temas, Qwen3-1.7B como gerador
e corte de similaridade 0,50. O corte foi escolhido observando estes mesmos casos: o
“Nobel” tinha evidências máximas de 0,466 e 0,438; nas perguntas respondíveis, todas as
evidências ficaram em 0,512 ou mais. A margem é estreita e o ajuste não é independente.

Foram acrescentados dois splits. `enunciado` contém as perguntas de exemplo do enunciado,
definidas pelo desafio. `regressao` contém os casos de 17/11 e dois casos de período,
escritos **depois** de conhecidas as falhas. O gabarito de “cobrança duplicada no cartão”
foi conferido na base: há relato direto (“passaram duas vezes o meu cartão”). Dev e test
foram reexecutados como regressão; as evidências de test são idênticas às da versão
anterior, de modo que a inspeção de relevância (16/24) continua aplicável a elas.

| Split | Casos | Gate correto | Sínteses aceitas nas respondíveis |
| --- | ---: | ---: | ---: |
| dev | 7 | 7/7 | 4/4 |
| test | 9 | 9/9 | 4/4 |
| enunciado | 8 | 8/8 | 7/8 |
| regressao | 8 | 8/8 | 3/3 |

Tempo médio de 13,9 s por resposta gerada em CPU (8,5–25,4 s). A pergunta sobre padrões
de clientes insatisfeitos teve evidências, mas o modelo terminou os tópicos com
`SEM_EVIDENCIA`, e a saída contraditória foi recusada. Na inspeção do autor da revisão,
algumas sínteses aceitas ainda trazem defeitos que a checagem de formato não detecta:
texto copiado entre colchetes (“[fornecedor]”), comentário sobre a nota, “muitas
reclamações” e tópicos pouco pertinentes na pergunta sobre trocas. Referências válidas
continuam sendo uma checagem de formato, não de suporte factual.
